
import os
import sys
import shutil
from PIL import Image, ImageDraw

sys.path.append(os.path.join(os.getcwd(), 'tools'))
from unified_pipeline import FloodFillBackgroundDetector

def test_bg_case(name, img_data, expected_color, expected_full_frame):
    print(f"\nTesting {name}...")
    
    # Save temp image
    img_path = f"test_bg_{name}.png"
    img_data.save(img_path)
    
    detector = FloodFillBackgroundDetector(tolerance=10)
    
    # Test 1: Color Detection
    bg_color = detector.detect_background_color(img_data)
    print(f"  Detected Color: {bg_color}")
    
    if expected_full_frame:
        if bg_color is None:
            print("  [PASS] Correctly identified Full Frame (None)")
        else:
            print(f"  [FAIL] Expected Full Frame (None), got {bg_color}")
    else:
        if bg_color == expected_color:
            print(f"  [PASS] Correctly detected {expected_color}")
        else:
            print(f"  [FAIL] Expected {expected_color}, got {bg_color}")

    # Test 2: Mask Generation
    mask = detector.get_content_mask(img_data)
    # Check simple stats
    w, h = mask.size
    total_pixels = w * h
    content_pixels = 0
    for y in range(h):
        for x in range(w):
            if mask.getpixel((x, y)) > 0:
                content_pixels += 1
                
    fill_ratio = content_pixels / total_pixels
    print(f"  Mask Fill Ratio: {fill_ratio:.2f}")

    if expected_full_frame:
        if fill_ratio > 0.99:
             print("  [PASS] Mask is Full Frame")
        else:
             print(f"  [FAIL] Expected Full Frame mask > 0.99, got {fill_ratio}")
    else:
        if fill_ratio < 0.9:
            print("  [PASS] Mask successfully cropped background")
        else:
            print(f"  [FAIL] Expected cropped mask < 0.9, got {fill_ratio}")

    # Clean up
    if os.path.exists(img_path):
        os.remove(img_path)

def verify_backgrounds():
    print("Running Smart Background Verification...")
    
    # Case 1: Solid Black Background (Standard)
    img_black = Image.new('RGBA', (100, 100), (0, 0, 0, 255))
    draw = ImageDraw.Draw(img_black)
    draw.rectangle([30, 30, 70, 70], fill=(255, 0, 0, 255)) # Red square
    test_bg_case("black_bg", img_black, (0, 0, 0), False)
    
    # Case 2: Solid White Background (AI Deviation)
    img_white = Image.new('RGBA', (100, 100), (255, 255, 255, 255))
    draw = ImageDraw.Draw(img_white)
    draw.rectangle([30, 30, 70, 70], fill=(255, 0, 0, 255)) # Red square
    test_bg_case("white_bg", img_white, (255, 255, 255), False)
    
    # Case 3: Mismatched Corners (Full Frame Painting)
    img_full = Image.new('RGBA', (100, 100), (0, 0, 0, 255))
    draw = ImageDraw.Draw(img_full)
    # Paint corners different colors
    draw.rectangle([0, 0, 10, 10], fill=(255, 0, 0, 255)) # Top-Left Red
    draw.rectangle([90, 0, 100, 10], fill=(0, 255, 0, 255)) # Top-Right Green
    draw.rectangle([0, 90, 10, 100], fill=(0, 0, 255, 255)) # Bottom-Left Blue
    draw.rectangle([90, 90, 100, 100], fill=(255, 255, 0, 255)) # Bottom-Right Yellow
    test_bg_case("full_frame", img_full, None, True)

if __name__ == "__main__":
    verify_backgrounds()
