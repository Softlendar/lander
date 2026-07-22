import re

with open("files/roulete_wheel.html", "r") as f:
    content = f.read()

# Map project slug to logo filename (same as in index.html marquee)
logo_map = {
    "softlendar": "softlendar_logo.svg",
    "termirator": "termirator_logo.svg",
    "catlearning": "ct_logo.svg",
    "brose": "brose_logo.svg",
    "serch": "serch_logo.svg",
    "haster": "haster_logo.svg",
    "setomoly": "setomoly_logo.svg",
    "wilgo": "wilgo_logo.svg",
    "wildo": "wildo_logo.svg",
    "nametermer": "nametermer_logo.svg",
    "dobart": "dobart_logo.svg",
    "redarbot": "redarbot_logo.svg",
}

# Find the projects array and the text drawing block
# Replace the text drawing with image drawing

old_text_block = """                    // Text label
                    const midAngle = start + anglePer / 2;
                    const textPos = polarToCartesian(cx, cy, r * 0.65, midAngle);
                    const text = document.createElementNS(
                        "http://www.w3.org/2000/svg",
                        "text",
                    );
                    text.setAttribute("x", textPos.x);
                    text.setAttribute("y", textPos.y);
                    text.setAttribute("text-anchor", "middle");
                    text.setAttribute("dominant-baseline", "middle");
                    text.setAttribute("fill", "#fff");
                    text.setAttribute("font-size", "14");
                    text.setAttribute("font-weight", "700");
                    text.setAttribute("transform", "rotate(" + midAngle + "," + textPos.x + "," + textPos.y + ")");
                    text.textContent = p.name;
                    svg.appendChild(text);"""

new_image_block = """                    // Logo image (instead of text)
                    const midAngle = start + anglePer / 2;
                    const imgPos = polarToCartesian(cx, cy, r * 0.65, midAngle);
                    const imgSize = 36;
                    const img = document.createElementNS(
                        "http://www.w3.org/2000/svg",
                        "image",
                    );
                    img.setAttribute("href", "/logo/" + p.slug + "_logo.svg");
                    img.setAttribute("x", imgPos.x - imgSize / 2);
                    img.setAttribute("y", imgPos.y - imgSize / 2);
                    img.setAttribute("width", imgSize);
                    img.setAttribute("height", imgSize);
                    img.setAttribute("transform", "rotate(" + midAngle + "," + imgPos.x + "," + imgPos.y + ")");
                    svg.appendChild(img);"""

if old_text_block in content:
    content = content.replace(old_text_block, new_image_block)
    with open("files/roulete_wheel.html", "w") as f:
        f.write(content)
    print("Replaced text with logo images")
else:
    print("Could not find text block")
