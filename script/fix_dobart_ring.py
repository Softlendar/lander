import re

with open("files/index.html", "r") as f:
    html = f.read()

with open("files/landing.css", "r") as f:
    css = f.read()

# 1. Fix dobart slot to use inline SVG (same as marquee) instead of generic D
old_dobart_slot = """<div class="net-slot" data-slug="dobart" data-pos="9" style="--slot-angle: 360deg;" title="Dobart">
                            <div class="net-slot-inner">
                                <svg viewBox="0 0 100 100"><rect x="20" y="20" width="60" height="60" rx="12" fill="none" stroke="#ff8c42" stroke-width="3"/><text x="50" y="62" text-anchor="middle" fill="#ff3c7f" font-size="32" font-weight="800">D</text></svg>
                            </div>
                        </div>"""

new_dobart_slot = """<div class="net-slot" data-slug="dobart" data-pos="9" style="--slot-angle: 360deg;" title="Dobart">
                            <div class="net-slot-inner">
                                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
                                    <line x1="5" y1="50" x2="60" y2="50" stroke="#ff8c42" stroke-width="3" stroke-linecap="round"/>
                                    <line x1="10" y1="45" x2="50" y2="45" stroke="#ff3c7f" stroke-width="2" stroke-linecap="round" opacity="0.5"/>
                                    <line x1="10" y1="55" x2="50" y2="55" stroke="#ff3c7f" stroke-width="2" stroke-linecap="round" opacity="0.5"/>
                                    <path d="M30 28 L30 72 L50 72 Q68 72 68 50 Q68 28 50 28 Z" fill="#ff8c42" stroke="#ff3c7f" stroke-width="2.5" stroke-linejoin="round"/>
                                </svg>
                            </div>
                        </div>"""

if old_dobart_slot in html:
    html = html.replace(old_dobart_slot, new_dobart_slot)
    print("Fixed dobart slot SVG")
else:
    print("Could not find dobart slot")

# 2. Fix CSS: increase ring radius to prevent overlap
# Change all translateY(-145px) to translateY(-175px) for more spacing
# Also reduce slot size from 72px to 56px

# Update slot size
old_slot_size = """.net-slot {
    position: absolute;
    top: 50%;
    left: 50%;
    width: 72px;
    height: 72px;
    margin: -36px 0 0 -36px;"""

new_slot_size = """.net-slot {
    position: absolute;
    top: 50%;
    left: 50%;
    width: 56px;
    height: 56px;
    margin: -28px 0 0 -28px;"""

if old_slot_size in css:
    css = css.replace(old_slot_size, new_slot_size)
    print("Reduced slot size to 56px")
else:
    print("Could not find slot size")

# Update ring radius (translateY values)
css = css.replace("translateY(-145px)", "translateY(-175px)")
print("Increased ring radius to 175px")

# Update dot margin
old_dot_margin = "margin: -2px 0 0 -2px;"
new_dot_margin = "margin: -2px 0 0 -2px;"
# Dots are fine, just their translateY needs to match

# Update hover/active transform too
old_hover = """.net-slot:hover,
.net-slot.active {
    transform: scale(1.2) rotate(var(--slot-angle)) translateY(-145px)
        rotate(calc(-1 * var(--slot-angle))) !important;
}"""

new_hover = """.net-slot:hover,
.net-slot.active {
    transform: scale(1.2) rotate(var(--slot-angle)) translateY(-175px)
        rotate(calc(-1 * var(--slot-angle))) !important;
}"""

if old_hover in css:
    css = css.replace(old_hover, new_hover)
    print("Updated hover transform")
else:
    print("Could not find hover transform")

# Update media query
old_media = """    .net-slot[data-pos] {
        transform: rotate(var(--slot-angle)) translateY(-110px)
            rotate(calc(-1 * var(--slot-angle))) !important;
    }
    .net-dot[data-pos] {
        transform: rotate(var(--slot-angle)) translateY(-110px) !important;
    }"""

new_media = """    .net-slot[data-pos] {
        transform: rotate(var(--slot-angle)) translateY(-130px)
            rotate(calc(-1 * var(--slot-angle))) !important;
    }
    .net-dot[data-pos] {
        transform: rotate(var(--slot-angle)) translateY(-130px) !important;
    }"""

if old_media in css:
    css = css.replace(old_media, new_media)
    print("Updated media query")
else:
    print("Could not find media query")

with open("files/index.html", "w") as f:
    f.write(html)

with open("files/landing.css", "w") as f:
    f.write(css)

print("Done!")
