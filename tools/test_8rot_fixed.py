#!/usr/bin/env python3
"""Test the fixed generate_8_rotations endpoint."""
import sys
sys.path.insert(0, 'tools')

from asset_generators.pixellab_client import PixelLabClient, generate_genesis_sprite, generate_genesis_8_directions

# Safety: only 3 calls max
client = PixelLabClient(max_calls=3)

print("Step 1: Generate a reference sprite...")
ref = generate_genesis_sprite(client, "simple pixel art robot", width=32, height=32, use_v2=True)
if not ref:
    print("FAILED: Could not generate reference")
    sys.exit(1)
    
print(f"Reference generated: {ref.size}")
ref.save("test_fix_ref.png")

print("\nStep 2: Test FIXED generate_8_rotations...")
rotations = generate_genesis_8_directions(client, ref, width=32, height=32)

if rotations:
    print(f"SUCCESS! Got {len(rotations)} rotations")
    for i, img in enumerate(rotations):
        img.save(f"test_fix_rot_{i}.png")
else:
    print("FAILED: generate_genesis_8_directions returned None")
    print("Check logs above for error details")

print(f"\nTotal cost: ${client.get_session_cost():.4f}")
