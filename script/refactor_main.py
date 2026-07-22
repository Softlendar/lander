import os
import re
import socket
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

import psycopg
from dotenv import load_dotenv
from flask import Flask, Response, jsonify, request, send_from_directory

load_dotenv()


# =============================================================================
# SERVICE: Database
# =============================================================================
class DatabaseService:
    """Handles all PostgreSQL database operations."""

    def __init__(self, database_url: str | None):
        self._url = database_url

    def _conn(self):
        if not self._url:
            raise RuntimeError("DATABASE_URL not set")
        return psycopg.connect(self._url)

    def is_ready(self) -> bool:
        return bool(self._url)

    def init_tables(self) -> None:
        if not self._url:
            print("[init_db] DATABASE_URL not set — skipping")
            return
        try:
            with self._conn() as conn:
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

    # ------------------------------------------------------------------
    # User messages
    # ------------------------------------------------------------------
    def save_message(self, email: str, msg: str, status: str = "pending") -> dict:
        if not self._url:
            return {
                "id": None,
                "time": datetime.now(timezone.utc).isoformat(),
                "email": email,
                "msg": msg,
                "status": status,
            }
        with self._conn() as conn:
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

    def list_messages(self) -> list:
        if not self._url:
            return []
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, time, email, msg, status FROM user_messages ORDER BY time DESC"
                )
                return [
                    {
                        "id": r[0],
                        "time": r[1].isoformat() if r[1] else None,
                        "email": r[2],
                        "msg": r[3],
                        "status": r[4] or "approved",
                    }
                    for r in cur.fetchall()
                ]

    def update_message_status(self, msg_id: int, status: str) -> bool:
        if not self._url:
            return False
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE user_messages SET status = %s WHERE id = %s",
                    (status, msg_id),
                )
                conn.commit()
                return cur.rowcount > 0

    # ------------------------------------------------------------------
    # Trusted emails
    # ------------------------------------------------------------------
    def is_trusted(self, email: str) -> bool:
        if not self._url:
            return False
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM trusted_emails WHERE email = %s", (email,))
                return cur.fetchone() is not None

    def add_trusted(self, email: str) -> bool:
        if not self._url:
            return False
        with self._conn() as conn:
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

    # ------------------------------------------------------------------
    # User profiles
    # ------------------------------------------------------------------
    def save_profile(self, username: str, logo_url: str) -> None:
        if not self._url:
            raise RuntimeError("db not configured")
        with self._conn() as conn:
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

    def get_profile(self) -> dict:
        if not self._url:
            return {"username": None, "logo_url": None}
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT username, logo_url FROM user_profiles WHERE id = 1")
                row = cur.fetchone()
                if row:
                    return {"username": row[0], "logo_url": row[1]}
                return {"username": None, "logo_url": None}

    def delete_profile(self) -> None:
        if not self._url:
            return
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM user_profiles WHERE id = 1")
                conn.commit()

    # ------------------------------------------------------------------
    # Verifications (legacy, kept for compat)
    # ------------------------------------------------------------------
    def save_verification(self, email: str, code: str, msg: str) -> bool:
        if not self._url:
            return False
        expires = datetime.now(timezone.utc) + timedelta(minutes=5)
        with self._conn() as conn:
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

    def verify_code(self, email: str, code: str) -> tuple:
        if not self._url:
            return False, None
        with self._conn() as conn:
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
                cur.execute(
                    "UPDATE user_verifications SET verified = TRUE WHERE id = %s",
                    (vid,),
                )
                conn.commit()
                return True, msg


# =============================================================================
# SERVICE: Email
# =============================================================================
class EmailService:
    """Sends transactional emails via Mailtrap REST API."""

    def __init__(self, token: str, from_email: str, from_name: str):
        self._token = token
        self._from_email = from_email
        self._from_name = from_name

    def _post(self, payload: bytes) -> tuple:
        req = urllib.request.Request(
            "https://send.api.mailtrap.io/api/send",
            data=payload,
            headers={
                "Authorization": f"Bearer {self._token}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, resp.read()

    def send(self, to: str, subject: str, body: str) -> bool:
        if not self._token:
            print("[email] MAILTRAP_API_TOKEN not set")
            return False
        try:
            payload = json.dumps(
                {
                    "from": {
                        "email": self._from_email,
                        "name": self._from_name,
                    },
                    "to": [{"email": to}],
                    "subject": subject,
                    "text": body,
                    "category": "Softlender Verification",
                }
            ).encode("utf-8")
            status, _ = self._post(payload)
            print(f"[email] sent status={status}")
            return status in (200, 201, 202)
        except urllib.error.HTTPError as e:
            print(f"[email] HTTP error {e.code}: {e.read().decode()[:200]}")
            return False
        except Exception as e:
            print("[email] error:", e)
            return False

    @property
    def is_ready(self) -> bool:
        return bool(self._token)


# =============================================================================
# SERVICE: Project data
# =============================================================================
class ProjectService:
    """Static project metadata store."""

    DATA = {
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
            "body": "Give details about your company or project and we generate names for you to buy as a domain.",
            "stack": "Python, JavaScript",
            "live": "",
            "status": "active",
        },
        "haster": {
            "title": "haster",
            "tagline": "like Facebook, but more & more & more privacy",
            "body": "A social network that gives you more & more & more privacy — no tracking, no ads, just connection.",
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

    def all(self) -> dict:
        return self.DATA

    def get(self, slug: str) -> dict | None:
        return self.DATA.get(slug)

    def slugs(self):
        return list(self.DATA.keys())

    def render_html(self, slug: str) -> str | None:
        p = self.get(slug)
        if not p:
            return None
        try:
            with open("files/project.html", "r", encoding="utf-8") as f:
                tpl = f.read()
        except FileNotFoundError:
            return None
        for k, v in p.items():
            tpl = tpl.replace(f"{{{{ {k} }}}}", str(v))
        tpl = tpl.replace("{{ slug }}", slug)
        return tpl


# =============================================================================
# SERVICE: Contact form flow
# =============================================================================
class ContactService:
    """Handles email confirmation contact flow."""

    def __init__(self, db: DatabaseService, email: EmailService):
        self._db = db
        self._email = email

    # ------------------------------------------------------------------
    # Validation helpers
    # ------------------------------------------------------------------
    @staticmethod
    def is_valid_format(email: str) -> bool:
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return bool(re.match(pattern, email))

    @staticmethod
    def is_real_domain(email: str) -> bool:
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

    def validate(self, email: str, msg: str) -> str | None:
        if not email or not msg:
            return "plese fil both email and msg"
        if "@" not in email or "." not in email.split("@")[-1] or len(email) < 5:
            return "wrong/unexisting email"
        if not self.is_valid_format(email) or not self.is_real_domain(email):
            return "wrong/unexisting email"
        return None

    # ------------------------------------------------------------------
    # Send confirmation email
    # ------------------------------------------------------------------
    def send_confirmation(self, email: str, msg: str, base_url: str) -> dict:
        entry = self._db.save_message(email, msg, status="pending")
        msg_id = entry["id"]

        yes = (
            f"{base_url}/api/contact/confirm?"
            f"msg_id={msg_id}&action=yes&email={urllib.parse.quote(email)}"
        )
        no = (
            f"{base_url}/api/contact/confirm?"
            f"msg_id={msg_id}&action=no&email={urllib.parse.quote(email)}"
        )

        subject = "Did you send this message to Softlendar?"
        body = (
            f"Hello!\n\n"
            f"Someone sent a message to softlendar.com using this email.\n\n"
            f"Message:\n{msg}\n\n"
            f"Did you send this?\n\nYES: {yes}\n\nNO:  {no}\n\n"
            f"— Softlendar Team"
        )

        sent = self._email.send(email, subject, body)
        return {"ok": True, "id": msg_id, "email_sent": sent}

    # ------------------------------------------------------------------
    # Handle YES / NO confirmation click
    # ------------------------------------------------------------------
    def confirm(self, msg_id: int, action: str, email: str) -> dict:
        if action == "yes":
            self._db.update_message_status(msg_id, "approved")
            self._db.add_trusted(email)
            self._email.send(
                "proof@softlendar.com",
                f"Proof: {email} confirmed message",
                f"Email {email} confirmed message (ID: {msg_id}). Status: APPROVED + TRUSTED",
            )
            self._email.send(
                self._email._from_email,
                "New trusted contact message",
                f"Email {email} confirmed their message (ID: {msg_id}). Status: APPROVED + TRUSTED.\n\nProof sent to proof@softlendar.com",
            )
            return {
                "ok": True,
                "html": self._html(
                    "Thank you!",
                    "Your message has been confirmed. We will reply to your email soon.",
                ),
            }

        elif action == "no":
            self._db.update_message_status(msg_id, "rejected")
            self._email.send(
                self._email._from_email,
                "Contact message REJECTED",
                f"Email {email} REJECTED their message (ID: {msg_id}). Status: REJECTED",
            )
            return {
                "ok": True,
                "html": self._html(
                    "Apologies",
                    "We are sorry for any inconvenience. The message has been discarded and your email has not been added to our trusted list.",
                ),
            }

        return {"ok": False, "error": "Invalid action"}

    @staticmethod
    def _html(title: str, message: str) -> str:
        return (
            f'<!doctype html><html><head><meta charset="UTF-8"/><title>{title}</title>'
            f"<style>body{{font-family:sans-serif;background:#1a0a2e;color:#e0d5f0;"
            f"display:flex;align-items:center;justify-content:center;height:100vh;"
            f"margin:0;text-align:center;}}</style></head>"
            f"<body><div><h1>{title}</h1><p>{message}</p>"
            f'<p><a href="/" style="color:#ff8c42;">Back to Softlendar</a></p></div></body></html>'
        )


# =============================================================================
# SERVICE: interType chat
# =============================================================================
class ChatService:
    """Static reply engine for interType bot."""

    REPLIES = {
        "hello": "Meow! 😺 Welcome to softlendar. I'm 18 interType, here to help with anything about our projects!",
        "hi": "Hey there! 🌙 Ask me about softlendar, termirator, catlearning, or any of our projects!",
        "help": "I can tell you about: softlendar (our brand), termirator (terminal app), ct/catlearning.fyi (cat learning), wilgo (systems lang), wildo (web framework), brose, serch, haster, setomoly, nametermer, redarbot, dobart, bylothon.",
        "projects": "Softlendar projects: termirator (live terminal), catlearning.fyi (live cat app), wilgo + wildo (in dev), brose, serch, haster, setomoly, nametermer, redarbot, dobart, bylothon.",
        "contact": "Reach us at chat@softlendar.com or visit softlendar.com.",
        "email": "chat@softlendar.com — that's our contact email!",
        "github": "github.com/softlendar — check our repos there.",
        "who are you": "I'm 18 interType, the softlendar AI assistant. I know everything about our projects, team, and ecosystem. 🐱",
        "whoami": "You are a visitor to softlendar.com! I'm 18 interType, your guide. 🌙",
        "status": "softlendar is active! termirator and catlearning.fyi are live. wilgo + wildo are in development. redarbot, dobart, bylothon are coming soon.",
        "termirator": "termirator is a terminal-style interactive web app with power commands, context switching (softlendar / cyberdyne / termitoria), and a cyberpunk HUD. Built with Shell, Rust, JS, CSS, HTML. Live at termirator-j795.onrender.com",
        "catlearning": "catlearning.fyi (ct) is a cat-themed interactive web app: cat facts, toy picker, AI chat, and power commands. Built with Ruby on Rails 8 + PostgreSQL.",
        "ct": "ct = catlearning.fyi — our original project! A cat-themed learning app built with Ruby on Rails 8 and PostgreSQL.",
        "wilgo": "wilgo is a friendly systems programming language inspired by Rust. Memory-safe, fast, and warm. Stack: Rust + LLVM. Status: in development.",
        "wildo": "wildo is the web framework for wilgo. Batteries-included, async by default. Stack: Wilgo + HTML + CSS. Status: in development.",
        "softlendar": "softlendar.com is our home. We build interactive web experiences — science, stars, cats, code. Current projects: termirator + catlearning.fyi. In dev: wilgo + wildo + more.",
    }

    def reply(self, msg: str) -> str:
        msg = msg.strip().lower()
        if msg in self.REPLIES:
            return self.REPLIES[msg]
        for key, reply in self.REPLIES.items():
            if key in msg:
                return reply
        return "*purr* I don't know that yet! Try asking about: softlendar, termirator, catlearning, wilgo, wildo, or type 'help' for options."


# =============================================================================
# APP FACTORY
# =============================================================================
def create_app() -> Flask:
    app = Flask(__name__, static_folder="files")

    # --- services ----------------------------------------------------
    db = DatabaseService(os.getenv("DATABASE_URL"))
    email = EmailService(
        os.getenv("MAILTRAP_API_TOKEN", ""),
        os.getenv("MAILTRAP_FROM_EMAIL", "noreply@softlendar.com"),
        os.getenv("MAILTRAP_FROM_NAME", "Softlendar"),
    )
    projects = ProjectService()
    contact = ContactService(db, email)
    chat = ChatService()

    # --- init db -----------------------------------------------------
    db.init_tables()

    # --- CORS --------------------------------------------------------
    @app.after_request
    def add_cors_headers(response):
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return response

    # --- routes: pages -----------------------------------------------
    @app.route("/")
    def home():
        return send_from_directory("files", "index.html")

    @app.route("/interType", strict_slashes=False)
    def intertype_page():
        return send_from_directory("files", "intertype.html")

    @app.route("/roulette_wheel", strict_slashes=False)
    def roulette_wheel():
        return send_from_directory("files", "roulette_wheel.html")

    @app.route("/resume", strict_slashes=False)
    def resume():
        return send_from_directory("files", "resume.html")

    @app.route("/logo/<path:filename>")
    def logo_files(filename):
        return send_from_directory("logo", filename)

    @app.route("/<path:filename>")
    def static_files(filename):
        return send_from_directory("files", filename)

    # --- routes: project pages ---------------------------------------
    for slug in projects.slugs():

        def _make_route(s):
            def route():
                html = projects.render_html(s)
                if html is None:
                    return send_from_directory("files", "404.html")
                return Response(html, mimetype="text/html")

            return route

        app.add_url_rule(f"/{slug}", f"project_{slug}", _make_route(slug))

    # --- routes: API ------------------------------------------------
    @app.route("/api/health")
    def health():
        return jsonify({"status": "ok", "static": True})

    @app.route("/api/projects")
    def api_projects():
        return jsonify(projects.all())

    @app.route("/interType/api/chat", methods=["POST"])
    def intertype_chat():
        data = request.get_json() or {}
        msg = data.get("message", "").strip()
        return jsonify({"reply": chat.reply(msg)})

    @app.route("/api/contact/send-code", methods=["POST"])
    def api_contact_send_code():
        data = request.get_json() or {}
        email = data.get("email", "").strip()
        msg = data.get("msg", "").strip()

        error = contact.validate(email, msg)
        if error:
            return jsonify({"error": error}), 400

        if db.is_trusted(email):
            entry = db.save_message(email, msg, status="approved")
            return jsonify({"ok": True, "id": entry.get("id"), "trusted": True}), 200

        return jsonify(
            contact.send_confirmation(email, msg, request.url_root.rstrip("/"))
        ), 200

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

        result = contact.confirm(msg_id, action, email)
        if result["ok"]:
            return result["html"], 200
        return result.get("error", "Invalid action"), 400

    @app.route("/api/contact/verify", methods=["POST"])
    def api_contact_verify():
        """Kept for backwards compat — immediately saves the message."""
        data = request.get_json() or {}
        email = data.get("email", "").strip()
        msg = data.get("msg", "").strip()
        if not email or not msg:
            return jsonify({"error": "plese fil both email and msg"}), 400
        entry = db.save_message(email, msg)
        return jsonify({"ok": True, "id": entry.get("id")})

    @app.route("/api/messages", methods=["GET"])
    def api_messages():
        return jsonify(db.list_messages())

    @app.route("/api/profile", methods=["POST"])
    def api_profile_save():
        data = request.get_json() or {}
        username = data.get("username", "").strip()
        logo_url = data.get("logo_url", "").strip()
        try:
            db.save_profile(username, logo_url)
            return jsonify({"ok": True})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/profile", methods=["GET"])
    def api_profile_get():
        return jsonify(db.get_profile())

    @app.route("/api/profile", methods=["DELETE"])
    def api_profile_delete():
        db.delete_profile()
        return jsonify({"ok": True})

    return app


# =============================================================================
# ENTRY POINT
# =============================================================================
app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
