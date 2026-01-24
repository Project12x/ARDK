"""
Generate a Genesis-compatible sphere projectile sprite (16x16, indexed palette)
"""
from PIL import Image

def create_sphere_projectile():
    """Create a 16x16 cyan sphere projectile with Genesis-compatible format"""
    size = 16
    
    # Create palette-based image (P mode)
    # Genesis requires indexed color
    img = Image.new('P', (size, size))
    
    # Define a 16-color palette (first color is transparency)
    # 0: Magenta (transparent)
    # 1: Dark blue (outer)
    # 2: Mid blue
    # 3: Light cyan
    # 4: White (highlight)
    palette = [
        255, 0, 255,    # 0: Magenta (transparent)
        0, 64, 128,     # 1: Dark blue
        0, 128, 200,    # 2: Mid cyan
        64, 192, 255,   # 3: Light cyan
        200, 240, 255,  # 4: Near white
        255, 255, 255,  # 5: White
    ]
    # Pad to 256 colors (768 bytes)
    palette.extend([0] * (768 - len(palette)))
    img.putpalette(palette)
    
    # Draw the sphere using pixel indices
    pixels = img.load()
    
    # Fill with transparent (0 = magenta)
    for y in range(size):
        for x in range(size):
            pixels[x, y] = 0
    
    # Draw concentric circles manually
    # Outer ring (dark blue = 1)
    for y in range(2, 14):
        for x in range(2, 14):
            dx, dy = x - 8, y - 8
            dist = (dx*dx + dy*dy) ** 0.5
            if 5.5 <= dist < 6.5:
                pixels[x, y] = 1
    
    # Mid ring (mid cyan = 2)
    for y in range(3, 13):
        for x in range(3, 13):
            dx, dy = x - 8, y - 8
            dist = (dx*dx + dy*dy) ** 0.5
            if 4 <= dist < 5.5:
                pixels[x, y] = 2
    
    # Inner area (light cyan = 3)
    for y in range(4, 12):
        for x in range(4, 12):
            dx, dy = x - 8, y - 8
            dist = (dx*dx + dy*dy) ** 0.5
            if 2.5 <= dist < 4:
                pixels[x, y] = 3
    
    # Highlight (near white = 4)
    for y in range(5, 11):
        for x in range(5, 11):
            dx, dy = x - 8, y - 8
            dist = (dx*dx + dy*dy) ** 0.5
            if 1 <= dist < 2.5:
                pixels[x, y] = 4
    
    # Center (white = 5)
    for y in range(6, 10):
        for x in range(6, 10):
            dx, dy = x - 8, y - 8
            dist = (dx*dx + dy*dy) ** 0.5
            if dist < 1:
                pixels[x, y] = 5
    
    output_path = r"c:\Users\estee\Desktop\My Stuff\Code\Antigravity\SurvivorNES\projects\epoch\res\sprites\sphere_projectile.png"
    img.save(output_path)
    print(f"Created: {output_path}")
    return output_path

if __name__ == "__main__":
    create_sphere_projectile()
