#!/usr/bin/env python3
"""
Fetch tileset and create seamless background using ONLY base tiles.
Tile 0 = all lower terrain (purple ground)
Tile 15 = all upper terrain (rocky texture)
These are the only tiles that tile seamlessly with themselves.
"""
import urllib.request
import json
import base64
from PIL import Image
from io import BytesIO
import sys

API_KEY = "b68c2160-d218-4cfb-81f2-ccb619108419"
TILESET_ID = "47a5d905-3169-485a-a16c-dc9c98592978"
OUTPUT_PATH = "../projects/epoch/res/tilesets/background.png"

# Use ONLY the base upper tile (15) - fully rocky texture
# This is the only tile guaranteed to tile seamlessly with itself
BASE_TILE_ID = 15  # Change to 0 for purple ground only

print("=" * 60)
print("SEAMLESS BASE TILE BACKGROUND")
print("=" * 60)
sys.stdout.flush()

url = f"https://api.pixellab.ai/v2/tilesets/{TILESET_ID}"
headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Accept": "application/json",
}

print(f"Fetching tileset {TILESET_ID}...")
print(f"Using base tile ID: {BASE_TILE_ID}")
sys.stdout.flush()

try:
    req = urllib.request.Request(url, headers=headers, method="GET")
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode())
        
        tileset = data.get("tileset", {})
        tiles_data = tileset.get("tiles", [])
        print(f"Got {len(tiles_data)} tiles")
        
        # Find the base tile
        base_tile_img = None
        for tile in tiles_data:
            tile_id = int(tile.get("id", 0))
            if tile_id == BASE_TILE_ID:
                img_obj = tile.get("image", {})
                b64 = img_obj.get("base64", "") if isinstance(img_obj, dict) else img_obj
                if b64:
                    if b64.startswith("data:"):
                        b64 = b64.split(",", 1)[1]
                    img_data = base64.b64decode(b64)
                    base_tile_img = Image.open(BytesIO(img_data))
                    print(f"Found tile {BASE_TILE_ID}: {base_tile_img.size}")
                break
        
        if not base_tile_img:
            print(f"ERROR: Tile {BASE_TILE_ID} not found!")
            sys.exit(1)
        
        # Create background by tiling the base tile
        tile_w, tile_h = base_tile_img.size
        bg_w, bg_h = 256, 224
        
        print(f"Creating {bg_w}x{bg_h} background from tile {BASE_TILE_ID}...")
        
        bg = Image.new("RGBA", (bg_w, bg_h), (0, 0, 0, 255))
        
        for y in range(0, bg_h, tile_h):
            for x in range(0, bg_w, tile_w):
                # Handle partial tiles at edges
                paste_w = min(tile_w, bg_w - x)
                paste_h = min(tile_h, bg_h - y)
                if paste_w < tile_w or paste_h < tile_h:
                    cropped = base_tile_img.crop((0, 0, paste_w, paste_h))
                    bg.paste(cropped, (x, y))
                else:
                    bg.paste(base_tile_img, (x, y))
        
        # Save as indexed
        indexed = bg.convert("RGB").quantize(colors=15, method=Image.Quantize.MEDIANCUT)
        indexed.save(OUTPUT_PATH)
        print(f"SAVED: {OUTPUT_PATH}")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("=" * 60)
print("DONE")
print("=" * 60)
