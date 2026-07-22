import os

# Fix main.py
with open("main.py", "r") as f:
    content = f.read()

content = content.replace("roulete_wheel", "roulette_wheel")
with open("main.py", "w") as f:
    f.write(content)
print("Fixed main.py")

# Fix index.html
with open("files/index.html", "r") as f:
    content = f.read()

content = content.replace("roulete_wheel", "roulette_wheel")
with open("files/index.html", "w") as f:
    f.write(content)
print("Fixed index.html")

# Rename HTML file
if os.path.exists("files/roulete_wheel.html"):
    os.rename("files/roulete_wheel.html", "files/roulette_wheel.html")
    print("Renamed roulete_wheel.html to roulette_wheel.html")
else:
    print("roulete_wheel.html not found")
