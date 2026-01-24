"""
Generate a 16x16 bomb sprite for pickup drops
"""
from PIL import Image

def create_bomb_sprite():
    """Create a 16x16 bomb sprite with Genesis-compatible format"""
    size = 16
    
    # Create indexed image
    img = Image.new('P', (size, size))
    
    # Define palette (first color is transparency magenta)
    palette = [
        255, 0, 255,    # 0: Magenta (transparent)
        0, 0, 0,        # 1: Black (bomb body)
        64, 64, 64,     # 2: Dark gray (shading)
        128, 128, 128,  # 3: Gray (highlight)
        255, 128, 0,    # 4: Orange (fuse spark)
        255, 200, 0,    # 5: Yellow (fuse glow)
        80, 40, 20,     # 6: Brown (fuse)
    ]
    # Pad to 768 bytes
    palette.extend([0] * (768 - len(palette)))
    img.putpalette(palette)
    
    pixels = img.load()
    
    # Fill with transparent
    for y in range(size):
        for x in range(size):
            pixels[x, y] = 0
    
    # Draw bomb body (circle)
    for y in range(4, 14):
        for x in range(3, 13):
            dx = x - 8
            dy = y - 9
            dist = (dx*dx + dy*dy) ** 0.5
            if dist < 5:
                if dist < 3:
                    pixels[x, y] = 1  # Black center
                else:
                    pixels[x, y] = 2  # Dark gray edge
    
    # Highlight
    pixels[5, 6] = 3
    pixels[6, 5] = 3
    pixels[6, 6] = 3
    
    # Fuse stem (brown line going up-right)
    pixels[9, 3] = 6
    pixels[10, 2] = 6
    pixels[11, 1] = 6
    
    # Fuse spark (orange/yellow)
    pixels[12, 0] = 4
    pixels[11, 0] = 5
    pixels[12, 1] = 5
    
    output_path = r"c:\Users\estee\Desktop\My Stuff\Code\Antigravity\SurvivorNES\projects\epoch\res\sprites\bomb_pickup.png"
    img.save(output_path)
    print(f"Created: {output_path}")

if __name__ == "__main__":
    create_bomb_sprite()
