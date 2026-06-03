with open("index.html", "r") as f:
    c = f.read()

old = "<body>\n        <!-- Top 30%: Glowing Sun Hero -->"
new = """<body>
        <!-- Top Nav -->
        <nav class="site-nav">
            <a href="/" class="nav-logo">
                <img src="logo/softlendar_logo.svg" alt="softlendar" width="32" height="32" />
                <span>Softlendar</span>
            </a>
            <div class="nav-links">
                <a href="/" class="nav-link">Home</a>
                <a href="/termirator" class="nav-link">Projects</a>
                <a href="/" class="nav-link">About</a>
                <a href="/" class="nav-link">Contact</a>
            </div>
        </nav>

        <!-- Top 30%: Glowing Sun Hero -->"""

c = c.replace(old, new)
with open("index.html", "w") as f:
    f.write(c)
print("done")
