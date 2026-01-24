#!/usr/bin/env python3
"""
Generate tileable Genesis background - SINGLE RUN ONLY.
Run once and exit. No loops.
"""
import sys
import os

OUTPUT_PATH = '../projects/epoch/res/tilesets/background.png'
MARKER_FILE = os.path.join(os.path.dirname(OUTPUT_PATH), '.generated')

# Check if already generated this session
if os.path.exists(MARKER_FILE):
    print(f"Already generated this session. Delete {MARKER_FILE} to regenerate.")
    sys.exit(0)

print("=" * 60)
print("PIXELLAB TILEABLE BACKGROUND GENERATOR")
print("=" * 60)

try:
    import pixellab
    from PIL import Image
    
    API_KEY = 'b68c2160-d218-4cfb-81f2-ccb619108419'
    
    print("Creating client...")
    client = pixellab.Client(secret=API_KEY)
    
    print("Generating 128x128 tileable background tile...")
    print("(This is a SINGLE API call)")
    
    response = client.generate_image_pixflux(
        description='seamless tileable 16-bit pixel art texture, dark purple wasteland ground, cracked earth surface, game background tile, simple repeating pattern, Sega Genesis style',
        image_size={'width': 128, 'height': 128},
        no_background=False,
        text_guidance_scale=7.0,
    )
    
    print("Generation complete!")
    img = response.image.pil_image()
    print(f"Raw image: {img.size} {img.mode}")
    
    # Convert to Genesis-compatible indexed
    if img.mode == 'RGBA':
        rgb = Image.new('RGB', img.size, (0, 0, 0))
        rgb.paste(img, mask=img.split()[3])
    else:
        rgb = img.convert('RGB')
    
    indexed = rgb.quantize(colors=15, method=Image.Quantize.MEDIANCUT)
    
    # Save
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    indexed.save(OUTPUT_PATH)
    print(f"SAVED: {OUTPUT_PATH}")
    
    # Create marker to prevent re-running
    with open(MARKER_FILE, 'w') as f:
        f.write('generated')
    
    print("=" * 60)
    print("SUCCESS! Background saved.")
    print("=" * 60)
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
