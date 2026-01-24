#!/usr/bin/env python3
"""Fetch tileset metadata and analyze tile edge types."""
import urllib.request
import json
import sys

API_KEY = "b68c2160-d218-4cfb-81f2-ccb619108419"
TILESET_ID = "47a5d905-3169-485a-a16c-dc9c98592978"

print("=" * 60)
print("TILESET METADATA ANALYSIS")
print("=" * 60)
sys.stdout.flush()

url = f"https://api.pixellab.ai/v2/tilesets/{TILESET_ID}"
headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Accept": "application/json",
}

try:
    req = urllib.request.Request(url, headers=headers, method="GET")
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode())
        
        # Pretty print metadata
        print(f"Metadata keys: {list(data.get('metadata', {}).keys())}")
        metadata = data.get("metadata", {})
        print(f"Full metadata: {json.dumps(metadata, indent=2)}")
        
        tileset = data.get("tileset", {})
        tiles = tileset.get("tiles", [])
        print(f"\n{len(tiles)} tiles:")
        
        for tile in tiles:
            tile_id = tile.get("id", "?")
            name = tile.get("name", "?")
            # Check for edge info
            edges = {k: v for k, v in tile.items() if k not in ["id", "name", "image"]}
            print(f"  {tile_id}: {name} | {edges}")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("=" * 60)
