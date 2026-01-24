#!/usr/bin/env python3
"""
Generate a single Genesis-quality background.
Single-run, no loops, immediate exit on success or failure.
"""
import sys
import os

# Ensure we only run once
LOCK_FILE = "bg_gen.lock"
if os.path.exists(LOCK_FILE):
    print("Lock file exists - script already ran. Delete bg_gen.lock to run again.")
    sys.exit(0)

# Create lock immediately
with open(LOCK_FILE, "w") as f:
    f.write("running")

try:
    import pixellab
    from PIL import Image
    
    API_KEY = 'b68c2160-d218-4cfb-81f2-ccb619108419'
    OUTPUT_PATH = '../projects/epoch/res/tilesets/background.png'
    
    print("Initializing PixelLab client...")
    client = pixellab.Client(secret=API_KEY)
    
    print("Generating Genesis-quality background (ONE generation only)...")
    response = client.generate_image_pixflux(
        description='16-bit Sega Genesis style pixel art, dramatic post-apocalyptic wasteland background, vibrant purple twilight sky with orange horizon, detailed ruined city silhouettes, crumbling skyscrapers, scattered debris, professional retro game art, high detail, rich color palette',
        image_size={'width': 256, 'height': 224},
        no_background=False,
        text_guidance_scale=9.0,
    )
    
    print("Generation complete, extracting image...")
    img = response.image.pil_image()
    print(f"Raw output: {img.size} {img.mode}")
    
    # Convert to 16-color indexed for Genesis
    if img.mode == 'RGBA':
        rgb = Image.new('RGB', img.size, (0,0,0))
        rgb.paste(img, mask=img.split()[3])
    else:
        rgb = img.convert('RGB')
    
    indexed = rgb.quantize(colors=15, method=Image.Quantize.MEDIANCUT)
    print(f"Indexed: {indexed.size} {indexed.mode}")
    
    # Save
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    indexed.save(OUTPUT_PATH)
    print(f"SAVED: {OUTPUT_PATH}")
    print("SUCCESS - delete bg_gen.lock to run again")
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
    
finally:
    # Remove lock on exit
    if os.path.exists(LOCK_FILE):
        os.remove(LOCK_FILE)
    print("Script complete, exiting.")
    sys.exit(0)
