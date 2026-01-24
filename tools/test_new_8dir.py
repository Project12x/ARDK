#!/usr/bin/env python3
"""Quick test of new create_character_8_directions method."""
import sys
sys.path.insert(0, 'tools')

from asset_generators.pixellab_client import PixelLabClient

# Budget for job + polling
client = PixelLabClient(max_calls=35)

print("Testing create_character_8_directions...")
result = client.create_character_8_directions(
    description="simple robot character, metal body, pixel art",
    width=32,
    height=32,
    max_poll_attempts=20,
    poll_interval=5.0
)

if result.success:
    print(f"SUCCESS! Got {len(result.images)} images")
    print(f"Directions: {result.metadata.get('directions', [])}")
    print(f"Cost: ${result.cost_usd:.4f}")
    
    # Save images
    for i, (img, dir_name) in enumerate(zip(result.images, result.metadata.get('directions', []))):
        filename = f"test_{dir_name.replace('-', '_')}.png"
        img.save(filename)
        print(f"  Saved: {filename}")
else:
    print(f"FAILED: {result.error}")
    sys.exit(1)

print(f"\nTotal session cost: ${client.get_session_cost():.4f}")
