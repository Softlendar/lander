with open("main.py", "r") as f:
    content = f.read()

old = """@app.route("/roulete_wheel", strict_slashes=False)
def roulete_wheel():
    return send_from_directory("files", "roulete_wheel.html")


@app.route("/<path:filename>")"""

new = """@app.route("/roulete_wheel", strict_slashes=False)
def roulete_wheel():
    return send_from_directory("files", "roulete_wheel.html")


@app.route("/resume", strict_slashes=False)
def resume():
    return send_from_directory("files", "resume.html")


@app.route("/<path:filename>")"""

if old in content:
    content = content.replace(old, new)
    with open("main.py", "w") as f:
        f.write(content)
    print("Added /resume route")
else:
    print("Could not find insertion point")
