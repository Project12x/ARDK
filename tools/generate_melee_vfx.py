"""
Generate a 16x16 melee slash VFX sprite
"""
from PIL import Image

def create_melee_vfx():
    """Create a 16x16 slash arc sprite for melee attack VFX"""
    size = 16
    
    # Create indexed image
    img = Image.new('P', (size, size))
    
    # Define palette (first color is transparency magenta)
    palette = [
        255, 0, 255,    # 0: Magenta (transparent)
        255, 255, 255,  # 1: White (bright flash)
        200, 220, 255,  # 2: Light blue (energy)
        100, 150, 255,  # 3: Mid blue
        50, 80, 200,    # 4: Dark blue (edge)
    ]
    # Pad to 768 bytes
    palette.extend([0] * (768 - len(palette)))
    img.putpalette(palette)
    
    pixels = img.load()
    
    # Fill with transparent
    for y in range(size):
        for x in range(size):
            pixels[x, y] = 0
    
    # Draw a curved slash arc (like a crescent moon shape)
    # Arc goes from bottom-left to top-right
    import math
    
    for angle in range(-30, 120):
        rad = math.radians(angle)
        # Outer arc
        for r in range(5, 8):
            px = int(8 + r * math.cos(rad))
            py = int(8 - r * math.sin(rad))
            if 0 <= px < size and 0 <= py < size:
                if r == 7:
                    pixels[px, py] = 4  # Dark edge
                elif r == 6:
                    pixels[px, py] = 3  # Mid
                else:
                    pixels[px, py] = 2  # Light
    
    # Inner bright core
    for angle in range(0, 90, 2):
        rad = math.radians(angle)
        px = int(8 + 5 * math.cos(rad))
        py = int(8 - 5 * math.sin(rad))
        if 0 <= px < size and 0 <= py < size:
            pixels[px, py] = 1  # White flash
    
    output_path = r"c:\Users\estee\Desktop\My Stuff\Code\Antigravity\SurvivorNES\projects\epoch\res\sprites\melee_vfx.png"
    img.save(output_path)
    print(f"Created: {output_path}")

if __name__ == "__main__":
    create_melee_vfx()
