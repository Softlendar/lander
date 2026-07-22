with open("files/index.html", "r") as f:
    content = f.read()

old = """                        <div class="net-slot" data-slug="nametermer" data-pos="8" style="--slot-angle: 320deg;" title="Nametermer">
                            <div class="net-slot-inner"><img src="logo/nametermer_logo.svg" alt="Nametermer" class="net-slot-img" /></div>
                        </div>
                    </div>"""

new = """                        <div class="net-slot" data-slug="nametermer" data-pos="8" style="--slot-angle: 320deg;" title="Nametermer">
                            <div class="net-slot-inner"><img src="logo/nametermer_logo.svg" alt="Nametermer" class="net-slot-img" /></div>
                        </div>
                        <div class="net-slot" data-slug="dobart" data-pos="9" style="--slot-angle: 360deg;" title="Dobart">
                            <div class="net-slot-inner">
                                <svg viewBox="0 0 100 100"><rect x="20" y="20" width="60" height="60" rx="12" fill="none" stroke="#ff8c42" stroke-width="3"/><text x="50" y="62" text-anchor="middle" fill="#ff3c7f" font-size="32" font-weight="800">D</text></svg>
                            </div>
                        </div>
                    </div>"""

if old in content:
    content = content.replace(old, new)
    with open("files/index.html", "w") as f:
        f.write(content)
    print("Added dobart slot")
else:
    print("Could not find slot")
