
import os
import sys
import shutil
from PIL import Image, ImageDraw

# Add tools to path
sys.path.append(os.path.join(os.getcwd(), 'tools'))

from unified_pipeline import UnifiedPipeline, BoundingBox

def verify_consensus():
    print("Running Consensus Engine verification...")
    
    # 1. Setup paths
    input_img = "test_consensus.png" 
    output_dir = "gfx/test_consensus_output"
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
        
    # Check if input exists, if not create a dummy
    if not os.path.exists(input_img):
        print("Creating dummy test image...")
        img = Image.new('RGBA', (256, 256), (0, 0, 0, 255)) 
        draw = ImageDraw.Draw(img)
        # Draw a big blue square (easy to see)
        draw.rectangle([100, 100, 150, 150], fill=(0, 0, 255, 255))
        img.save(input_img)

    # 2. Run pipeline WITH CONSENSUS
    try:
        # We perform a "dry run" of sorts by checking if the engine initializes
        # and attempts to call the providers.
        pipeline = UnifiedPipeline(
            target_size=32,
            use_ai=True, 
            ai_provider="pollinations", # Base provider
            platform="nes",
            consensus_mode=True # ENABLE CONSENSUS
        )
        
        print("Pipeline initialized. Starting process...")
        result = pipeline.process(input_img, output_dir, category="test")
        
        # 3. Validation
        debug_dir = os.path.join(output_dir, "debug")
        report_path = os.path.join(debug_dir, "consensus_report.txt")
        
        if os.path.exists(report_path):
             print(f"[PASS] Consensus report found at {report_path}")
             with open(report_path, 'r') as f:
                 print("--- Report Content ---")
                 print(f.read())
                 print("----------------------")
        else:
             print("[WARN] Consensus report missing (did AI fail completely?)")

    except Exception as e:
        print(f"[ERROR] Pipeline crashed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verify_consensus()
