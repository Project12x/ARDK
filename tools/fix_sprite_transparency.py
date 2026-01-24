"""
Fix sprite transparency by ensuring index 0 is magenta (255,0,255)
"""
from PIL import Image
import os

def fix_sprite_transparency(input_path, output_path=None):
    """Fix a sprite so index 0 is magenta for transparency"""
    if output_path is None:
        output_path = input_path
    
    if not os.path.exists(input_path):
        print(f"NOT FOUND: {input_path}")
        return False
    
    img = Image.open(input_path)
    print(f"\n=== Fixing {os.path.basename(input_path)} ===")
    print(f"Size: {img.size}, Mode: {img.mode}")
    
    if img.mode != 'P':
        print(f"Converting from {img.mode} to P")
        if img.mode == 'RGBA':
            # Convert RGBA to P, treating fully transparent as magenta
            img = img.convert('RGB')
        img = img.convert('P', palette=Image.ADAPTIVE, colors=15)
    
    palette = list(img.getpalette())
    
    # Check if index 0 is already magenta
    if palette[0] == 255 and palette[1] == 0 and palette[2] == 255:
        print("Index 0 is already magenta - no fix needed")
        return True
    
    print(f"Current Index 0: RGB({palette[0]}, {palette[1]}, {palette[2]})")
    
    # Find magenta in palette (search first 16 colors)
    magenta_idx = -1
    for i in range(16):
        r, g, b = palette[i*3], palette[i*3+1], palette[i*3+2]
        if r == 255 and g == 0 and b == 255:
            magenta_idx = i
            break
    
    if magenta_idx == -1:
        # No magenta found - we need to remap black pixels to magenta
        print("No magenta found - remapping index 0 color to magenta")
        # Save original index 0 color
        old_r, old_g, old_b = palette[0], palette[1], palette[2]
        
        # Set index 0 to magenta
        palette[0] = 255
        palette[1] = 0
        palette[2] = 255
        
        # Move old index 0 color to unused slot if it's not black
        if not (old_r == 0 and old_g == 0 and old_b == 0):
            # Find first unused slot
            for i in range(1, 16):
                if palette[i*3] == 0 and palette[i*3+1] == 0 and palette[i*3+2] == 0:
                    palette[i*3] = old_r
                    palette[i*3+1] = old_g
                    palette[i*3+2] = old_b
                    break
    else:
        print(f"Magenta found at index {magenta_idx} - swapping with index 0")
        # Swap palette entries
        old_0 = (palette[0], palette[1], palette[2])
        palette[0] = 255
        palette[1] = 0
        palette[2] = 255
        palette[magenta_idx*3] = old_0[0]
        palette[magenta_idx*3+1] = old_0[1]
        palette[magenta_idx*3+2] = old_0[2]
        
        # Also need to swap pixel indices
        pixels = list(img.getdata())
        new_pixels = []
        for p in pixels:
            if p == 0:
                new_pixels.append(magenta_idx)
            elif p == magenta_idx:
                new_pixels.append(0)
            else:
                new_pixels.append(p)
        img.putdata(new_pixels)
    
    img.putpalette(palette)
    img.save(output_path)
    print(f"Saved to: {output_path}")
    return True

# Fix sprites 
sprites_dir = r"c:\Users\estee\Desktop\My Stuff\Code\Antigravity\SurvivorNES\projects\epoch\res\sprites"

fix_sprite_transparency(os.path.join(sprites_dir, "enemy.png"))
