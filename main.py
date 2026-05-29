import os
import re
import smtplib
from email.mime.text import MIMEText

from dotenv import load_dotenv
from flask import Flask, Response, jsonify, request, send_from_directory

load_dotenv()

app = Flask(__name__, static_folder=".")

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
        "body": "Explore cat facts, pick toys, chat with an AI assistant, run power commands, and join a community of cat lovers.",
        "stack": "Ruby on Rails 8, PostgreSQL",
        "live": "https://catlearning.fyi",
        "status": "live",
    },
    "termirator": {
        "title": "termirator",
        "tagline": "terminal-style interactive web app",
        "body": "Run power commands, switch contexts (softlendar / cyberdyne / termitoria), explore systems, and experience a cyberpunk HUD.",
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

    # Simple string replacement
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


# Static assets
@app.route("/<path:filename>")
def static_files(filename):
    return send_from_directory(".", filename)


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=5000)
