from PIL import Image
from pathlib import Path
import sys

path = Path("projects/epoch/res/sprites/hero_sheet_final.png")
if not path.exists():
    print("File not found")
    sys.exit(1)

img = Image.open(path).convert("RGBA")
colors = img.getcolors(maxcolors=256)

if not colors:
    print("More than 256 colors!")
else:
    print(f"Unique colors: {len(colors)}")
    for count, color in colors:
        print(f"  {color}: {count}")
