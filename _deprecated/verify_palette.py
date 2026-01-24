
import os
import sys
import shutil
from PIL import Image, ImageDraw

sys.path.append(os.path.join(os.getcwd(), 'tools'))
from unified_pipeline import PaletteExtractor, UnifiedPipeline

# Mock AI Analyzer to print prompt instead of calling API
class MockAnalyzer:
    def __init__(self):
        self.available = True
        self.provider_name = "MockProvider"
        
    def analyze_prompt(self, img, prompt):
        print("\n--- Mock AI Prompt ---")
        print(prompt)
        print("----------------------")
        # Return a dummy NES palette
        return {'palette': [0x0F, 0x16, 0x27, 0x30]}

def verify_palette():
    print("Running Hybrid Palette Verification...")
    
    # 1. Create Test Image (Red, Green, Blue, Black)
    img = Image.new('RGBA', (64, 64), (0, 0, 0, 255)) # Black bg
    draw = ImageDraw.Draw(img)
    draw.rectangle([10, 10, 30, 30], fill=(255, 0, 0, 255)) # Red
    draw.rectangle([34, 10, 54, 30], fill=(0, 255, 0, 255)) # Green
    draw.rectangle([10, 34, 30, 54], fill=(0, 0, 255, 255)) # Blue
    
    img_path = "test_palette.png"
    img.save(img_path)
    
    # 2. Initialize Extractor
    extractor = PaletteExtractor()
    analyzer = MockAnalyzer()
    
    # 3. specific test for Hybrid Extraction
    print("\n[Test] Extract Hybrid (Mock AI)")
    palette = extractor.extract_with_ai(img, analyzer, num_colors=4)
    print(f"Extracted: {[hex(c) for c in palette]}")
    
    # Check if the prompt contained our RGB values
    # The output of MockAnalyzer should show the prompt with RGB(255, 0, 0) etc.

    # 4. Cleanup
    if os.path.exists(img_path):
        os.remove(img_path)

if __name__ == "__main__":
    verify_palette()
