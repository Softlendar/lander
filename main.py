import json
import os
import re
import smtplib
from datetime import datetime, timezone
from email.mime.text import MIMEText

import psycopg2
from dotenv import load_dotenv
from flask import Flask, Response, jsonify, request, send_from_directory

load_dotenv()

app = Flask(__name__, static_folder=".")

DATABASE_URL = os.getenv("DATABASE_URL")


def get_conn():
    return psycopg2.connect(DATABASE_URL, sslmode="require")


def init_db():
    """Create user_messages table if it doesn't exist."""
    if not DATABASE_URL:
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
                        msg TEXT NOT NULL
                    )
                    """
                )
                conn.commit()
    except Exception:
        pass


class UserMsg:
    @staticmethod
    def save(email: str, msg: str) -> dict:
        if not DATABASE_URL:
            # fallback: in-memory (ephemeral)
            return {
                "id": None,
                "time": datetime.now(timezone.utc).isoformat(),
                "email": email,
                "msg": msg,
            }
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO user_messages (email, msg) VALUES (%s, %s) RETURNING id, time",
                    (email, msg),
                )
                row = cur.fetchone()
                conn.commit()
                return {
                    "id": row[0],
                    "time": row[1].isoformat(),
                    "email": email,
                    "msg": msg,
                }

    @staticmethod
    def all() -> list:
        if not DATABASE_URL:
            return []
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, time, email, msg FROM user_messages ORDER BY time DESC"
                )
                rows = cur.fetchall()
                return [
                    {"id": r[0], "time": r[1].isoformat(), "email": r[2], "msg": r[3]}
                    for r in rows
                ]


# Init table on startup
init_db()

# Project data
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
        "tagline": "name + terminal",
        "body": "A terminal tool for managing, generating, and exploring names for projects, domains, and more.",
        "stack": "Python, JavaScript",
        "live": "",
        "status": "active",
    },
    "haster": {
        "title": "haster",
        "tagline": "speed-first tooling",
        "body": "A suite of fast, lightweight tools for developers who value speed and minimal overhead.",
        "stack": "Rust, Shell",
        "live": "",
        "status": "in development",
    },
    "setomoly": {
        "title": "setomoly",
        "tagline": "a universe-vibed game",
        "body": "Explore the cosmos, build worlds, and discover mysteries in this space-themed adventure game.",
        "stack": "Rust, WebAssembly, WebGL",
        "live": "",
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
        "tagline": "task management",
        "body": "A minimal, fast task and project management tool for small teams and solo builders.",
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
        return send_from_directory(".", "404.html")

    with open("project.html", "r", encoding="utf-8") as f:
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
    return send_from_directory(".", "index.html")


@app.route("/api/health")
def health():
    return jsonify({"status": "ok", "static": True})


@app.route("/api/projects")
def api_projects():
    return jsonify(PROJECTS)


# Dynamic project pages
for slug in PROJECTS:
    app.add_url_rule(f"/{slug}", f"project_{slug}", lambda s=slug: render_project(s))


# interType AI assistant
@app.route("/interType", strict_slashes=False)
def intertype_page():
    return send_from_directory(".", "intertype.html")


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


@app.route("/api/contact", methods=["POST"])
def api_contact():
    data = request.get_json() or {}
    email = data.get("email", "").strip()
    msg = data.get("msg", "").strip()
    if not email or not msg:
        return jsonify({"error": "email and msg required"}), 400
    if "@" not in email or "." not in email.split("@")[-1]:
        return jsonify({"error": "invalid email"}), 400
    entry = UserMsg.save(email, msg)
    return jsonify({"ok": True, "id": entry.get("id")})


@app.route("/api/messages", methods=["GET"])
def api_messages():
    return jsonify(UserMsg.all())


# Static assets
@app.route("/<path:filename>")
def static_files(filename):
    return send_from_directory(".", filename)


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=5000)
