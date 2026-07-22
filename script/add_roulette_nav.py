with open("files/index.html", "r") as f:
    content = f.read()

old = """                <a href="/interType" class="hero-nav-link">interType</a>"""
new = """                <a href="/roulete_wheel" class="hero-nav-link">🎰 Roulette</a>
                <a href="/interType" class="hero-nav-link">interType</a>"""

if old in content:
    content = content.replace(old, new)
    with open("files/index.html", "w") as f:
        f.write(content)
    print("Added roulette link to nav")
else:
    print("Could not find interType link")
