from PIL import Image
import collections
import os

# Path to artifact
path = r"C:\Users\estee\.gemini\antigravity\brain\0458fced-211e-489c-8a75-814f0f85a901\rom_test_gameplay.png"

if not os.path.exists(path):
    print(f"Error: File not found at {path}")
    exit(1)

try:
    img = Image.open(path)
    img = img.convert("RGB") # Ensure RGB for comparison
    pixels = list(img.getdata())
    colors = collections.Counter(pixels)

    total_pixels = len(pixels)
    distinct_colors = len(colors)
    
    print(f"--- Visual Audit Report ---")
    print(f"Image: {os.path.basename(path)}")
    print(f"Dimensions: {img.size}")
    print(f"Total Pixels: {total_pixels}")
    print(f"Distinct Colors: {distinct_colors}")

    print("\n[Top 5 Colors]")
    for c, count in colors.most_common(5):
        pct = (count / total_pixels) * 100
        print(f"  RGB{c}: {count} ({pct:.1f}%)")

    # Critical Checks
    pink_count = colors.get((255, 0, 255), 0)
    msg_pink = "FAIL (Pink Border Detected)" if pink_count > 100 else "PASS (No Pink Border)"
    print(f"\n[Check: Pink Border] {msg_pink} (Count: {pink_count})")

    black_count = colors.get((0, 0, 0), 0)
    black_pct = (black_count / total_pixels) * 100
    msg_content = "FAIL (Screen is Empty)" if black_pct > 99.0 else "PASS (Content Detected)"
    print(f"[Check: Content] {msg_content} (Black: {black_pct:.1f}%)")

    # Check for specific game colors (heuristic)
    # Player Skin (Typical beige/brown), Green (Grass), Grey (Stone)
    # Just checking for variety is usually enough vs a broken screen
    if distinct_colors > 4:
        print("[Check: Palette] PASS (Rich Palette Detected)")
    else:
        print("[Check: Palette] WARNING (Low Color Count)")

except Exception as e:
    print(f"An error occurred: {e}")
