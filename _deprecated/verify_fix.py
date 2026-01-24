
import os
import sys
import shutil
from PIL import Image, ImageDraw

# Add tools to path
sys.path.append(os.path.join(os.getcwd(), 'tools'))

from unified_pipeline import UnifiedPipeline, BoundingBox

def verify():
    print("Running verification...")
    
    # 1. Setup paths
    input_img = "test_sprite.png" 
    output_dir = "gfx/test_output_verification"
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
        
    # Check if input exists, if not create a dummy
    if not os.path.exists(input_img):
        print("Creating dummy test image...")
        img = Image.new('RGBA', (256, 256), (0, 0, 0, 255)) # Black background
        draw = ImageDraw.Draw(img)
        # Draw a red square with internal black eyes
        draw.rectangle([50, 50, 100, 100], fill=(255, 0, 0, 255))
        draw.rectangle([60, 60, 70, 70], fill=(0, 0, 0, 255)) # Internal black
        draw.rectangle([80, 60, 90, 70], fill=(0, 0, 0, 255)) # Internal black
        img.save(input_img)

    # 2. Run pipeline WITH AI 
    try:
        pipeline = UnifiedPipeline(
            target_size=32,
            use_ai=True, 
            ai_provider="pollinations",
            platform="nes"
        )
        
        result = pipeline.process(input_img, output_dir, category="test")
        
        # 3. Validation
        debug_dir = os.path.join(output_dir, "debug")
        
        if not os.path.exists(output_dir):
             print("[FAIL] Output directory missing.")
        
        if os.path.exists(debug_dir) and os.path.exists(os.path.join(debug_dir, "ai_response_raw.json")):
             print("[PASS] AI executed (json log found).")
        else:
             print("[WARN] AI execution log missing (maybe API key issue or crash).")

        sprites_dir = os.path.join(output_dir)
        if os.path.exists(sprites_dir):
            files = os.listdir(sprites_dir)
            sprite_files = [f for f in files if f.endswith(".png") and "sprite_" in f]
            if sprite_files:
                print(f"[PASS] {len(sprite_files)} sprites extracted.")
            else:
                print("[FAIL] No sprites extracted.")
        else:
            print("[FAIL] Output dir missing.")

    except Exception as e:
        print(f"[ERROR] Pipeline crashed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verify()
