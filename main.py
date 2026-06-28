import json
import os
import random
import time
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

import psycopg
from dotenv import load_dotenv
from flask import Flask, Response, jsonify, request, send_from_directory

load_dotenv()

app = Flask(__name__, static_folder="files")

DATABASE_URL = os.getenv("DATABASE_URL")

MAILTRAP_API_TOKEN = os.getenv("MAILTRAP_API_TOKEN", "")
MAILTRAP_FROM_EMAIL = os.getenv("MAILTRAP_FROM_EMAIL", "noreply@softlendar.com")
MAILTRAP_FROM_NAME = os.getenv("MAILTRAP_FROM_NAME", "Softlendar")


def get_conn():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL not set")
    return psycopg.connect(DATABASE_URL)


def init_db():
    """Create tables if they don't exist."""
    if not DATABASE_URL:
        print("[init_db] DATABASE_URL not set — skipping table creation")
        return
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS user_messages (
                        id SERIAL PRIMARY KEY,
                        time TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        email TEXT NOT NULL,
                        msg TEXT NOT NULL,
                        status TEXT DEFAULT 'pending'
                    )
                    """
                )
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS user_profiles (
                        id SERIAL PRIMARY KEY,
                        username TEXT,
                        logo_url TEXT,
                        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    )
                    """
                )
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS user_verifications (
                        id SERIAL PRIMARY KEY,
                        email TEXT NOT NULL,
                        code TEXT NOT NULL,
                        msg TEXT NOT NULL,
                        expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
                        verified BOOLEAN DEFAULT FALSE,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    )
                    """
                )
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS trusted_emails (
                        id SERIAL PRIMARY KEY,
                        email TEXT NOT NULL UNIQUE,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    )
                    """
                )
                # migrate old tables: add status column if missing
                try:
                    cur.execute(
                        "ALTER TABLE user_messages ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'approved'"
                    )
                except Exception:
                    pass
                conn.commit()
        print("[init_db] tables ready")
    except Exception as e:
        print("[init_db] error:", e)
        raise


class UserMsg:
    @staticmethod
    def save(email: str, msg: str, status: str = "pending") -> dict:
        if not DATABASE_URL:
            return {
                "id": None,
                "time": datetime.now(timezone.utc).isoformat(),
                "email": email,
                "msg": msg,
                "status": status,
            }
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO user_messages (email, msg, status) VALUES (%s, %s, %s) RETURNING id, time",
                    (email, msg, status),
                )
                row = cur.fetchone()
                conn.commit()
                return {
                    "id": row[0],
                    "time": row[1].isoformat(),
                    "email": email,
                    "msg": msg,
                    "status": status,
                }

    @staticmethod
    def all() -> list:
        if not DATABASE_URL:
            return []
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, time, email, msg, status FROM user_messages ORDER BY time DESC"
                )
                rows = cur.fetchall()
                return [
                    {
                        "id": r[0],
                        "time": r[1].isoformat(),
                        "email": r[2],
                        "msg": r[3],
                        "status": r[4] or "approved",
                    }
                    for r in rows
                ]

    @staticmethod
    def update_status(msg_id: int, status: str) -> bool:
        if not DATABASE_URL:
            return False
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE user_messages SET status = %s WHERE id = %s",
                    (status, msg_id),
                )
                conn.commit()
                return cur.rowcount > 0


def is_trusted_email(email: str) -> bool:
    if not DATABASE_URL:
        return False
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM trusted_emails WHERE email = %s", (email,))
            return cur.fetchone() is not None


def add_trusted_email(email: str) -> bool:
    if not DATABASE_URL:
        return False
    with get_conn() as conn:
        with conn.cursor() as cur:
            try:
                cur.execute(
                    "INSERT INTO trusted_emails (email) VALUES (%s) ON CONFLICT (email) DO NOTHING",
                    (email,),
                )
                conn.commit()
                return True
            except Exception:
                return False


def is_real_email(email: str) -> bool:
    """Check email format + domain validity."""
    import re

    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    if not re.match(pattern, email):
        return False
    domain = email.split("@")[1]
    try:
        import dns.resolver

        try:
            dns.resolver.resolve(domain, "MX")
            return True
        except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
            dns.resolver.resolve(domain, "A")
            return True
    except ImportError:
        return True
    except Exception:
        return False


# In-memory rate limit store: {email: last_request_timestamp}
_rate_limit = {}


def generate_code() -> str:
    return str(random.randint(1000000, 9999999))


def send_email(to: str, subject: str, body: str) -> bool:
    if not MAILTRAP_API_TOKEN:
        print("[send_email] MAILTRAP_API_TOKEN not set")
        return False
    try:
        payload = json.dumps(
            {
                "from": {"email": MAILTRAP_FROM_EMAIL, "name": MAILTRAP_FROM_NAME},
                "to": [{"email": to}],
                "subject": subject,
                "text": body,
                "category": "Softlendar Verification",
            }
        ).encode("utf-8")
        req = urllib.request.Request(
            "https://send.api.mailtrap.io/api/send",
            data=payload,
            headers={
                "Authorization": f"Bearer {MAILTRAP_API_TOKEN}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            print(f"[send_email] success status={resp.status}")
            return resp.status in (200, 201, 202)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        print(f"[send_email] HTTP error: {e.code} - {body}")
        return False
    except Exception as e:
        print("[send_email] error:", e)
        return False


def save_verification(email: str, code: str, msg: str) -> bool:
    if not DATABASE_URL:
        return False
    expires = datetime.now(timezone.utc) + timedelta(minutes=5)
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO user_verifications (email, code, msg, expires_at)
                VALUES (%s, %s, %s, %s)
                """,
                (email, code, msg, expires),
            )
            conn.commit()
    return True


def verify_code(email: str, code: str) -> tuple:
    if not DATABASE_URL:
        return False, None
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, msg, expires_at FROM user_verifications
                WHERE email = %s AND code = %s AND verified = FALSE
                ORDER BY created_at DESC LIMIT 1
                """,
                (email, code),
            )
            row = cur.fetchone()
            if not row:
                return False, None
            vid, msg, expires = row
            if datetime.now(timezone.utc) > expires:
                return False, None
            # mark verified
            cur.execute(
                "UPDATE user_verifications SET verified = TRUE WHERE id = %s", (vid,)
            )
            conn.commit()
            return True, msg
    return False, None


init_db()

PROJECTS = {
    "softlendar": {
        "title": "Softlendar",
        "tagline": "science · stars · cats · code",
        "body": "Softlendar will get you back to science, glowing stars, cats, latest research, computer science, programming and more.",
        "stack": "Shell, Rust, JavaScript, CSS, HTML",
        "live": "https://softlendar.com",
        "status": "live",
    },
    "catlearning": {
        "title": "catlearning.fyi",
        "tagline": "a cat-themed learning app",
        "body": "Explore cat facts, pick toys, chat with an AI assistant, and run power commands.",
        "stack": "Ruby on Rails 8, PostgreSQL",
        "live": "https://catlearning.fyi",
        "status": "live",
    },
    "termirator": {
        "title": "termirator",
        "tagline": "terminal-style interactive web app",
        "body": "Run power commands, switch contexts (softlender / cyberdyne / termitoria), explore systems, and experience a cyberpunk HUD.",
        "stack": "Shell, Rust, JavaScript, CSS, HTML",
        "live": "https://termirator-j795.onrender.com/",
        "status": "live",
    },
    "brose": {
        "title": "brose",
        "tagline": "the softlendar browser",
        "body": "A lightweight, warm-themed browser concept built for exploring Softlendar projects and the open web.",
        "stack": "Rust, HTML, CSS",
        "live": "",
        "status": "coming soon",
    },
    "serch": {
        "title": "serch",
        "tagline": "the softlendar search engine",
        "body": "Search across Softlendar projects, docs, and the wider web with a focus on privacy and speed.",
        "stack": "Rust, Python, ElasticSearch",
        "live": "",
        "status": "coming soon",
    },
    "nametermer": {
        "title": "nametermer",
        "tagline": "AI domain name generator",
        "body": "Give details about your company or project and we generate names for you to buy as a domain. Built with Python and JavaScript.",
        "stack": "Python, JavaScript",
        "live": "",
        "status": "active",
    },
    "haster": {
        "title": "haster",
        "tagline": "like Facebook, but more &amp; more &amp; more privacy",
        "body": "A social network that gives you more &amp; more &amp; more privacy — no tracking, no ads, just connection.",
        "stack": "Rust, Shell",
        "live": "",
        "status": "in development",
    },
    "setomoly": {
        "title": "setomoly",
        "tagline": "a universe-vibed game",
        "body": "Explore the cosmos, build worlds, and discover mysteries in this space-themed adventure game. Navigate the cosmic abyss in this high-stakes, zero-gravity survival challenge where you must evade relentless shooting stars and escape the pull of encroaching black holes.",
        "stack": "Rust, WebAssembly, WebGL",
        "live": "https://setomoly.base44.app/",
        "status": "in development",
    },
    "redarbot": {
        "title": "redarbot",
        "tagline": "radar automation",
        "body": "An automation platform for monitoring, alerting, and acting on real-time data streams.",
        "stack": "Rust, Kafka, Redis",
        "live": "",
        "status": "coming soon",
    },
    "dobart": {
        "title": "dobart",
        "tagline": "chat + tasks, frontend like Slack, backend like Proton + powers",
        "body": "A chatting area where every frontend is as good as Slack, and the backend is like Proton with special power and staff features. Built for teams who value privacy, speed, and real connection.",
        "stack": "Rust, HTMX, SQLite",
        "live": "",
        "status": "coming soon",
    },
    "wilgo": {
        "title": "wilgo",
        "tagline": "a friendly systems lang",
        "body": "Wilgo is a systems programming language inspired by Rust but designed to be gentler to learn. Memory-safe, fast, and warm.",
        "stack": "Rust, LLVM",
        "live": "",
        "status": "in development",
    },
    "wildo": {
        "title": "wildo",
        "tagline": "web framework for wilgo",
        "body": "Wildo is the web framework built for Wilgo. Batteries-included, async by default, and warm like the rest of the ecosystem.",
        "stack": "Wilgo, HTML, CSS",
        "live": "",
        "status": "in development",
    },
    "bylothon": {
        "title": "bylothon",
        "tagline": "research archive",
        "body": "An open archive for research notes, studies, and experiments in biology, computing, and design.",
        "stack": "Python, PostgreSQL, Jupyter",
        "live": "",
        "status": "active",
    },
}


def render_project(key: str) -> str:
    p = PROJECTS.get(key)
    if not p:
        return send_from_directory("files", "404.html")

    with open("files/project.html", "r", encoding="utf-8") as f:
        tpl = f.read()

    for k, v in p.items():
        tpl = tpl.replace(f"{{{{ {k} }}}}", str(v))
    tpl = tpl.replace("{{ slug }}", key)

    return Response(tpl, mimetype="text/html")


@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response


@app.route("/")
def home():
    return send_from_directory("files", "index.html")


@app.route("/api/health")
def health():
    return jsonify({"status": "ok", "static": True})


@app.route("/api/projects")
def api_projects():
    return jsonify(PROJECTS)


for slug in PROJECTS:
    app.add_url_rule(f"/{slug}", f"project_{slug}", lambda s=slug: render_project(s))


@app.route("/interType", strict_slashes=False)
def intertype_page():
    return send_from_directory("files", "intertype.html")


@app.route("/interType/api/chat", methods=["POST"])
def intertype_chat():
    data = request.get_json() or {}
    msg = data.get("message", "").strip().lower()

    replies = {
        "hello": "Meow! 😺 Welcome to softlendar. I'm 18 interType, here to help with anything about our projects!",
        "hi": "Hey there! 🌙 Ask me about softlendar, termirator, catlearning, or any of our projects!",
        "help": "I can tell you about: softlendar (our brand), termirator (terminal app), ct/catlearning.fyi (cat learning), wilgo (systems lang), wildo (web framework), brose, serch, haster, setomoly, nametermer, redarbot, dobart, bylothon.",
        "projects": "Softlendar projects: termirator (live terminal), catlearning.fyi (live cat app), wilgo + wildo (in dev), brose, serch, haster, setomoly, nametermer, redarbot, dobart, bylothon.",
        "termirator": "termirator is a terminal-style interactive web app with power commands, context switching (softlendar / cyberdyne / termitoria), and a cyberpunk HUD. Built with Shell, Rust, JS, CSS, HTML. Live at termirator-j795.onrender.com",
        "catlearning": "catlearning.fyi (ct) is a cat-themed interactive web app: cat facts, toy picker, AI chat, and power commands. Built with Ruby on Rails 8 + PostgreSQL.",
        "ct": "ct = catlearning.fyi — our original project! A cat-themed learning app built with Ruby on Rails 8 and PostgreSQL.",
        "wilgo": "wilgo is a friendly systems programming language inspired by Rust. Memory-safe, fast, and warm. Stack: Rust + LLVM. Status: in development.",
        "wildo": "wildo is the web framework for wilgo. Batteries-included, async by default. Stack: Wilgo + HTML + CSS. Status: in development.",
        "softlendar": "softlendar.com is our home. We build interactive web experiences — science, stars, cats, code. Current projects: termirator + catlearning.fyi. In dev: wilgo + wildo + more.",
        "contact": "Reach us at chat@softlendar.com or visit softlendar.com.",
        "email": "chat@softlendar.com — that's our contact email!",
        "github": "github.com/softlendar — check our repos there.",
        "who are you": "I'm 18 interType, the softlendar AI assistant. I know everything about our projects, team, and ecosystem. 🐱",
        "whoami": "You are a visitor to softlendar.com! I'm 18 interType, your guide. 🌙",
        "status": "softlendar is active! termirator and catlearning.fyi are live. wilgo + wildo are in development. redarbot, dobart, bylothon are coming soon.",
    }

    if msg in replies:
        return jsonify({"reply": replies[msg]})

    for key, reply in replies.items():
        if key in msg:
            return jsonify({"reply": reply})

    return jsonify(
        {
            "reply": "*purr* I don't know that yet! Try asking about: softlendar, termirator, catlearning, wilgo, wildo, or type 'help' for options."
        }
    )


# Contact flow with email confirmation
@app.route("/api/contact/send-code", methods=["POST"])
def api_contact_send_code():
    data = request.get_json() or {}
    email = data.get("email", "").strip()
    msg = data.get("msg", "").strip()

    if not email or not msg:
        return jsonify({"error": "plese fil both email and msg"}), 400
    if "@" not in email or "." not in email.split("@")[-1] or len(email) < 5:
        return jsonify({"error": "wrong/unexisting email"}), 400
    if not is_real_email(email):
        return jsonify({"error": "wrong/unexisting email"}), 400

    # Check if email is already trusted — if yes, save immediately
    if is_trusted_email(email):
        entry = UserMsg.save(email, msg, status="approved")
        return jsonify({"ok": True, "id": entry.get("id"), "trusted": True}), 200

    # Save as pending
    entry = UserMsg.save(email, msg, status="pending")
    msg_id = entry["id"]

    # Build confirmation email with Yes/No links
    confirm_url = request.url_root.rstrip("/")
    yes_link = f"{confirm_url}/api/contact/confirm?msg_id={msg_id}&action=yes&email={urllib.parse.quote(email)}"
    no_link = f"{confirm_url}/api/contact/confirm?msg_id={msg_id}&action=no&email={urllib.parse.quote(email)}"

    subject = "Did you send this message to Softlendar?"
    body = (
        "Hello!\n\n"
        "Someone sent a message to softlendar.com using this email address.\n\n"
        "Message:\n" + msg + "\n\n"
        "Did you send this message through our contact form?\n\n"
        "YES: " + yes_link + "\n\n"
        "NO:  " + no_link + "\n\n"
        "If you did not send this, please click NO and we will discard it.\n\n"
        "— Softlendar Team"
    )

    sent = send_email(email, subject, body)
    if not sent:
        # Email failed — still save but notify user
        return jsonify({"ok": True, "id": msg_id, "email_sent": False}), 200

    return jsonify({"ok": True, "id": msg_id, "email_sent": True}), 200


@app.route("/api/contact/confirm", methods=["GET"])
def api_contact_confirm():
    msg_id = request.args.get("msg_id", "").strip()
    action = request.args.get("action", "").strip().lower()
    email = request.args.get("email", "").strip()

    if not msg_id or not action or not email:
        return "Invalid confirmation link.", 400

    try:
        msg_id = int(msg_id)
    except ValueError:
        return "Invalid message ID.", 400

    if action == "yes":
        UserMsg.update_status(msg_id, "approved")
        add_trusted_email(email)

        # Build proof report for owner
        all_msgs = UserMsg.all()
        user_msgs = [m for m in all_msgs if m.get("email") == email]
        user_msgs.sort(key=lambda x: x.get("id", 0))
        attempt_num = len(user_msgs)
        this_msg = next((m for m in user_msgs if m.get("id") == msg_id), None)

        proof_lines = [
            f"PROOF REPORT — User Confirmed Contact",
            f"",
            f"User Email: {email}",
            f"Total Messages: {attempt_num}",
            f"This Attempt: #{attempt_num}",
            f"",
            f"--- All Messages from {email} ---",
        ]
        for i, m in enumerate(user_msgs, 1):
            status = m.get("status", "unknown")
            time_str = m.get("time", "unknown")
            msg_text = m.get("msg", "")
            proof_lines.append(
                f"[{i}] ID: {m.get('id')} | Time: {time_str} | Status: {status}"
            )
            proof_lines.append(f"    Message: {msg_text}")

        proof_lines.extend(
            [
                f"",
                f"--- Current Confirmation ---",
                f"Message ID: {msg_id}",
                f"Status: APPROVED + TRUSTED",
                f"Confirmed At: {datetime.now(timezone.utc).isoformat()}",
            ]
        )
        if this_msg:
            proof_lines.append(f"Message Content: {this_msg.get('msg', '')}")

        proof_body = "\n".join(proof_lines)

        # Send proof to owner
        send_email(
            "proof@softlendar.com",
            f"Proof: {email} confirmed message #{attempt_num}",
            proof_body,
        )

        # Also notify the old address as backup
        send_email(
            MAILTRAP_FROM_EMAIL,
            "New trusted contact message",
            f"Email {email} confirmed their message (ID: {msg_id}). Status: APPROVED + TRUSTED.\n\nProof sent to proof@softlendar.com",
        )

        return (
            """<!doctype html><html><head><meta charset="UTF-8"/><title>Confirmed</title>
<style>body{font-family:sans-serif;background:#1a0a2e;color:#e0d5f0;display:flex;align-items:center;justify-content:center;height:100vh;margin:0;text-align:center;}</style>
</head><body><div><h1>Thank you!</h1><p>Your message has been confirmed. We will reply to your email soon.</p>
<p><a href="/" style="color:#ff8c42;">Back to Softlendar</a></p></div></body></html>""",
            200,
        )

    elif action == "no":
        UserMsg.update_status(msg_id, "rejected")

        # Notify owner about rejection
        send_email(
            MAILTRAP_FROM_EMAIL,
            "Contact message REJECTED",
            f"Email {email} REJECTED their message (ID: {msg_id}). Status: REJECTED",
        )

        return (
            """<!doctype html><html><head><meta charset="UTF-8"/><title>Rejected</title>
<style>body{font-family:sans-serif;background:#1a0a2e;color:#e0d5f0;display:flex;align-items:center;justify-content:center;height:100vh;margin:0;text-align:center;}</style>
</head><body><div><h1>Apologies</h1><p>We are sorry for any inconvenience. The message has been discarded and your email has not been added to our trusted list.</p>
<p><a href="/" style="color:#ff8c42;">Back to Softlendar</a></p></div></body></html>""",
            200,
        )

    return "Invalid action.", 400


@app.route("/api/contact/verify", methods=["POST"])
def api_contact_verify():
    """Kept for backwards compat — immediately saves the message."""
    data = request.get_json() or {}
    email = data.get("email", "").strip()
    msg = data.get("msg", "").strip()

    if not email or not msg:
        return jsonify({"error": "plese fil both email and msg"}), 400

    entry = UserMsg.save(email, msg)
    return jsonify({"ok": True, "id": entry.get("id")})


@app.route("/api/messages", methods=["GET"])
def api_messages():
    return jsonify(UserMsg.all())


@app.route("/api/profile", methods=["POST"])
def api_profile_save():
    data = request.get_json() or {}
    username = data.get("username", "").strip()
    logo_url = data.get("logo_url", "").strip()
    if not DATABASE_URL:
        return jsonify({"error": "db not configured"}), 500
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO user_profiles (id, username, logo_url)
                VALUES (1, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    username = EXCLUDED.username,
                    logo_url = EXCLUDED.logo_url,
                    updated_at = NOW()
                """,
                (username, logo_url),
            )
            conn.commit()
    return jsonify({"ok": True})


@app.route("/api/profile", methods=["GET"])
def api_profile_get():
    if not DATABASE_URL:
        return jsonify({"username": None, "logo_url": None})
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT username, logo_url FROM user_profiles WHERE id = 1")
            row = cur.fetchone()
            if row:
                return jsonify({"username": row[0], "logo_url": row[1]})
            return jsonify({"username": None, "logo_url": None})


@app.route("/api/profile", methods=["DELETE"])
def api_profile_delete():
    if not DATABASE_URL:
        return jsonify({"ok": False})
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM user_profiles WHERE id = 1")
            conn.commit()
    return jsonify({"ok": True})


@app.route("/logo/<path:filename>")
def logo_files(filename):
    return send_from_directory("logo", filename)


@app.route("/roulete_wheel", strict_slashes=False)
def roulete_wheel():
    return send_from_directory("files", "roulete_wheel.html")


@app.route("/<path:filename>")
def static_files(filename):
    return send_from_directory("files", filename)


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=5000)
