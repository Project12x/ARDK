#!/usr/bin/env python3
"""Quick test of 8-rotations fix."""
import sys
sys.path.insert(0, 'tools')

from asset_generators.pixellab_client import PixelLabClient, generate_genesis_sprite, generate_genesis_8_directions

# One-shot test with safeguards
client = PixelLabClient(max_calls=3)

print("Step 1: Generate reference sprite...")
ref = generate_genesis_sprite(client, "simple robot character", width=32, height=32, use_v2=True)
if not ref:
    print("FAILED: Could not generate reference")
    sys.exit(1)
    
print(f"Reference: {ref.size}")
ref.save("test_ref.png")

print("Step 2: Generate 8 rotations...")
rotations = generate_genesis_8_directions(client, ref, width=32, height=32)
if not rotations:
    print("FAILED: 8-rotations returned None - check error logs above")
    sys.exit(1)
    
print(f"SUCCESS: Got {len(rotations)} rotations")
for i, img in enumerate(rotations):
    img.save(f"test_rot_{i}.png")
    
print(f"Total cost: ${client.get_session_cost():.4f}")
