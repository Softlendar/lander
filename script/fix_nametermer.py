with open("files/index.html", "r") as f:
    content = f.read()

old = """                    <div class="pd-tagline">Name + terminal</div>
                    <div class="pd-body">
                        A terminal tool for managing, generating, and exploring
                        names for projects, domains, and more. Built with Python
                        and JavaScript.
                    </div>
                    <a href="/nametermer" class="pd-link"
                        >🚀 Visit Nametermer</a"""

new = """                    <div class="pd-tagline">AI domain name generator</div>
                    <div class="pd-body">
                        Give details about your company or project and we generate
                        names for you to buy as a domain. Built with Python and
                        JavaScript.
                    </div>
                    <a href="/nametermer" class="pd-link"
                        >🚀 Visit Nametermer</a"""

if old in content:
    content = content.replace(old, new)
    with open("files/index.html", "w") as f:
        f.write(content)
    print("Updated nametermer card")
else:
    print("Could not find nametermer card")
