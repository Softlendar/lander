import re

# Read files
with open("files/index.html", "r") as f:
    html = f.read()

with open("files/landing.css", "r") as f:
    css = f.read()

with open("main.py", "r") as f:
    py = f.read()

# 1. Update dobart in main.py
old_dobart = """    "dobart": {
        "title": "dobart",
        "tagline": "task management",
        "body": "A minimal, fast task and project management tool for small teams and solo builders.",
        "stack": "Rust, HTMX, SQLite",
        "live": "",
        "status": "coming soon",
    },"""

new_dobart = """    "dobart": {
        "title": "dobart",
        "tagline": "chat + tasks, frontend like Slack, backend like Proton + powers",
        "body": "A chatting area where every frontend is as good as Slack, and the backend is like Proton with special power and staff features. Built for teams who value privacy, speed, and real connection.",
        "stack": "Rust, HTMX, SQLite",
        "live": "",
        "status": "coming soon",
    },"""

if old_dobart in py:
    py = py.replace(old_dobart, new_dobart)
    print("Updated main.py dobart")
else:
    print("Could not find dobart in main.py")

# 2. Add dobart product detail card in HTML (after wildo card)
wildo_card_end = """                <div class="product-detail-card" data-slug="wildo">
                    <div class="pd-icon">🕸️</div>
                    <div class="pd-name">Wildo</div>
                    <div class="pd-tagline">Web framework for Wilgo</div>
                    <div class="pd-body">
                        Wildo is the web framework built for Wilgo. Batteries-included,
                        async by default, and warm like the rest of the ecosystem.
                    </div>
                    <a href="/wildo" class="pd-link">🚀 Visit Wildo</a>
                </div>"""

new_dobart_card = """                <div class="product-detail-card" data-slug="wildo">
                    <div class="pd-icon">🕸️</div>
                    <div class="pd-name">Wildo</div>
                    <div class="pd-tagline">Web framework for Wilgo</div>
                    <div class="pd-body">
                        Wildo is the web framework built for Wilgo. Batteries-included,
                        async by default, and warm like the rest of the ecosystem.
                    </div>
                    <a href="/wildo" class="pd-link">🚀 Visit Wildo</a>
                </div>

                <div class="product-detail-card" data-slug="dobart">
                    <div class="pd-icon">💬</div>
                    <div class="pd-name">Dobart</div>
                    <div class="pd-tagline">Chat + tasks, frontend like Slack, backend like Proton + powers</div>
                    <div class="pd-body">
                        A chatting area where every frontend is as good as Slack, and the backend
                        is like Proton with special power and staff features. Built for teams who
                        value privacy, speed, and real connection.
                    </div>
                    <a href="/dobart" class="pd-link">🚀 Visit Dobart</a>
                </div>"""

if wildo_card_end in html:
    html = html.replace(wildo_card_end, new_dobart_card)
    print("Added dobart product card")
else:
    print("Could not find wildo card end")

# 3. Add dobart slot to the ring after wildo
# Current last slot is nametermer at pos=8, style="--slot-angle: 320deg;"
old_last_slot = """                        <div class="net-slot" data-slug="nametermer" data-pos="8" style="--slot-angle: 320deg;" title="Nametermer">
                            <div class="net-slot-inner">
                                <svg viewBox="0 0 100 100"><path d="M25,75 L50,25 L75,75" fill="none" stroke="#ff8c42" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/><text x="50" y="72" text-anchor="middle" fill="#ff3c7f" font-size="24" font-weight="800">N</text></svg>
                            </div>
                        </div>
                    </div>"""

new_last_slots = """                        <div class="net-slot" data-slug="nametermer" data-pos="8" style="--slot-angle: 320deg;" title="Nametermer">
                            <div class="net-slot-inner">
                                <svg viewBox="0 0 100 100"><path d="M25,75 L50,25 L75,75" fill="none" stroke="#ff8c42" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/><text x="50" y="72" text-anchor="middle" fill="#ff3c7f" font-size="24" font-weight="800">N</text></svg>
                            </div>
                        </div>
                        <div class="net-slot" data-slug="dobart" data-pos="9" style="--slot-angle: 360deg;" title="Dobart">
                            <div class="net-slot-inner">
                                <svg viewBox="0 0 100 100"><rect x="20" y="20" width="60" height="60" rx="12" fill="none" stroke="#ff8c42" stroke-width="3"/><text x="50" y="62" text-anchor="middle" fill="#ff3c7f" font-size="32" font-weight="800">D</text></svg>
                            </div>
                        </div>
                    </div>"""

if old_last_slot in html:
    html = html.replace(old_last_slot, new_last_slots)
    print("Added dobart slot")
else:
    print("Could not find last slot")

# 4. Update CSS for 10 positions (36deg intervals)
# Replace all the 9 slot positions with 10 slot positions
old_positions = """.net-slot[data-pos="0"] {
    transform: rotate(0deg) translateY(-145px) rotate(0deg);
}
.net-slot[data-pos="1"] {
    transform: rotate(40deg) translateY(-145px) rotate(-40deg);
}
.net-slot[data-pos="2"] {
    transform: rotate(80deg) translateY(-145px) rotate(-80deg);
}
.net-slot[data-pos="3"] {
    transform: rotate(120deg) translateY(-145px) rotate(-120deg);
}
.net-slot[data-pos="4"] {
    transform: rotate(160deg) translateY(-145px) rotate(-160deg);
}
.net-slot[data-pos="5"] {
    transform: rotate(200deg) translateY(-145px) rotate(-200deg);
}
.net-slot[data-pos="6"] {
    transform: rotate(240deg) translateY(-145px) rotate(-240deg);
}
.net-slot[data-pos="7"] {
    transform: rotate(280deg) translateY(-145px) rotate(-280deg);
}
.net-slot[data-pos="8"] {
    transform: rotate(320deg) translateY(-145px) rotate(-320deg);
}"""

new_positions = """.net-slot[data-pos="0"] {
    transform: rotate(0deg) translateY(-145px) rotate(0deg);
}
.net-slot[data-pos="1"] {
    transform: rotate(36deg) translateY(-145px) rotate(-36deg);
}
.net-slot[data-pos="2"] {
    transform: rotate(72deg) translateY(-145px) rotate(-72deg);
}
.net-slot[data-pos="3"] {
    transform: rotate(108deg) translateY(-145px) rotate(-108deg);
}
.net-slot[data-pos="4"] {
    transform: rotate(144deg) translateY(-145px) rotate(-144deg);
}
.net-slot[data-pos="5"] {
    transform: rotate(180deg) translateY(-145px) rotate(-180deg);
}
.net-slot[data-pos="6"] {
    transform: rotate(216deg) translateY(-145px) rotate(-216deg);
}
.net-slot[data-pos="7"] {
    transform: rotate(252deg) translateY(-145px) rotate(-252deg);
}
.net-slot[data-pos="8"] {
    transform: rotate(288deg) translateY(-145px) rotate(-288deg);
}
.net-slot[data-pos="9"] {
    transform: rotate(324deg) translateY(-145px) rotate(-324deg);
}"""

if old_positions in css:
    css = css.replace(old_positions, new_positions)
    print("Updated CSS positions for 10 slots")
else:
    print("Could not find CSS positions")

# 5. Add dobart dot position
old_dots = """.net-dot[data-pos="8"] {
    transform: rotate(320deg) translateY(-145px);
}"""

new_dots = """.net-dot[data-pos="8"] {
    transform: rotate(288deg) translateY(-145px);
}
.net-dot[data-pos="9"] {
    transform: rotate(324deg) translateY(-145px);
}"""

if old_dots in css:
    css = css.replace(old_dots, new_dots)
    print("Updated dot positions")
else:
    print("Could not find dot positions")

# 6. Update JavaScript to use 36deg instead of 40deg
old_js = "var targetAngle = -1 * (index * 40) % 360;"
new_js = "var targetAngle = -1 * (index * 36) % 360;"

if old_js in html:
    html = html.replace(old_js, new_js)
    print("Updated JS rotation angle")
else:
    print("Could not find JS rotation angle")

# Write back
with open("files/index.html", "w") as f:
    f.write(html)

with open("files/landing.css", "w") as f:
    f.write(css)

with open("main.py", "w") as f:
    f.write(py)

print("Done!")
