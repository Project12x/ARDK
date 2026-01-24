"""
Generate a smaller 16x16 enemy sprite for Grunt/Rusher (not Tank)
"""
from PIL import Image

def create_small_enemy():
    """Create a 16x16 enemy sprite (2x2 tiles)"""
    size = 16
    
    # Create indexed image
    img = Image.new('P', (size, size))
    
    # Define palette (first color is transparency magenta)
    palette = [
        255, 0, 255,    # 0: Magenta (transparent)
        160, 40, 180,   # 1: Purple (body)
        200, 80, 220,   # 2: Light purple (highlight)
        100, 20, 120,   # 3: Dark purple (shadow)
        255, 50, 50,    # 4: Red (eye/angry)
    ]
    # Pad to 768 bytes
    palette.extend([0] * (768 - len(palette)))
    img.putpalette(palette)
    
    pixels = img.load()
    
    # Fill with transparent
    for y in range(size):
        for x in range(size):
            pixels[x, y] = 0
    
    # Draw small blob enemy (12x12 centered in 16x16)
    # Body
    for y in range(3, 13):
        for x in range(3, 13):
            dx = x - 8
            dy = y - 8
            dist = (dx*dx + dy*dy) ** 0.5
            if dist < 5:
                pixels[x, y] = 1  # Purple body
    
    # Highlights
    pixels[5, 5] = 2
    pixels[6, 5] = 2
    pixels[5, 6] = 2
    
    # Shadows
    pixels[10, 10] = 3
    pixels[9, 10] = 3
    pixels[10, 9] = 3
    
    # Angry eye
    pixels[7, 7] = 4
    pixels[8, 7] = 4
    pixels[7, 8] = 4
    pixels[8, 8] = 4
    
    output_path = r"c:\Users\estee\Desktop\My Stuff\Code\Antigravity\SurvivorNES\projects\epoch\res\sprites\enemy_small.png"
    img.save(output_path)
    print(f"Created: {output_path}")

if __name__ == "__main__":
    create_small_enemy()
