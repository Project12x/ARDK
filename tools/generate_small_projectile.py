"""
Generate a smaller 8x8 projectile sprite for better performance
"""
from PIL import Image

def create_small_projectile():
    """Create an 8x8 projectile sprite (1x1 tile)"""
    size = 8
    
    # Create indexed image
    img = Image.new('P', (size, size))
    
    # Define palette (first color is transparency magenta)
    palette = [
        255, 0, 255,    # 0: Magenta (transparent)
        0, 255, 255,    # 1: Cyan (bright core)
        0, 200, 220,    # 2: Medium cyan
        0, 150, 180,    # 3: Dark cyan (edge)
    ]
    # Pad to 768 bytes
    palette.extend([0] * (768 - len(palette)))
    img.putpalette(palette)
    
    pixels = img.load()
    
    # Fill with transparent
    for y in range(size):
        for x in range(size):
            pixels[x, y] = 0
    
    # Draw small 6x6 glowing circle centered in 8x8
    # Pattern:
    #   ..XX..
    #   .XXXX.
    #   XXXXXX (approximated in 8x8)
    
    # Core (bright cyan)
    for y in range(2, 6):
        for x in range(2, 6):
            pixels[x, y] = 1
    
    # Medium cyan ring
    pixels[1, 3] = 2
    pixels[1, 4] = 2
    pixels[6, 3] = 2
    pixels[6, 4] = 2
    pixels[3, 1] = 2
    pixels[4, 1] = 2
    pixels[3, 6] = 2
    pixels[4, 6] = 2
    
    # Dark edge corners
    pixels[2, 2] = 3
    pixels[5, 2] = 3
    pixels[2, 5] = 3
    pixels[5, 5] = 3
    
    output_path = r"c:\Users\estee\Desktop\My Stuff\Code\Antigravity\SurvivorNES\projects\epoch\res\sprites\projectile_8x8.png"
    img.save(output_path)
    print(f"Created: {output_path}")

if __name__ == "__main__":
    create_small_projectile()
