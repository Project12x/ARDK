"""
Fix enemy sprite transparency - enemy.png has black at index 0, needs magenta
"""
from PIL import Image

def fix_enemy():
    """Fix enemy sprite so index 0 is magenta for transparency"""
    path = r"c:\Users\estee\Desktop\My Stuff\Code\Antigravity\SurvivorNES\projects\epoch\res\sprites\enemy.png"
    
    img = Image.open(path)
    print(f"Original: {img.size}, Mode: {img.mode}")
    
    # Convert to RGBA to properly handle the transparent areas
    if img.mode == 'P':
        img_rgba = img.convert('RGBA')
    else:
        img_rgba = img
    
    print(f"Converted to: {img_rgba.mode}")
    
    # Get pixels
    pixels = list(img_rgba.getdata())
    width, height = img_rgba.size
    
    # Find black pixels (0,0,0) which are currently the "transparent" areas
    # Replace them with magenta
    new_pixels = []
    replaced = 0
    for p in pixels:
        if p[0] == 0 and p[1] == 0 and p[2] == 0:
            # Black -> Magenta
            new_pixels.append((255, 0, 255, 255))
            replaced += 1
        else:
            new_pixels.append(p)
    
    print(f"Replaced {replaced} black pixels with magenta")
    
    # Create new image
    new_img = Image.new('RGBA', (width, height))
    new_img.putdata(new_pixels)
    
    # Convert back to P (indexed) mode
    new_img_p = new_img.convert('RGB').convert('P', palette=Image.ADAPTIVE, colors=15)
    
    # Ensure index 0 is magenta
    palette = list(new_img_p.getpalette())
    
    # Find magenta in palette
    magenta_idx = -1
    for i in range(16):
        if i*3+2 >= len(palette):
            break
        r, g, b = palette[i*3], palette[i*3+1], palette[i*3+2]
        if r > 250 and g < 10 and b > 250:  # Magenta-ish
            magenta_idx = i
            break
    
    if magenta_idx > 0:
        print(f"Swapping magenta from index {magenta_idx} to index 0")
        # Swap palette entries
        old_0 = (palette[0], palette[1], palette[2])
        palette[0], palette[1], palette[2] = palette[magenta_idx*3], palette[magenta_idx*3+1], palette[magenta_idx*3+2]
        palette[magenta_idx*3], palette[magenta_idx*3+1], palette[magenta_idx*3+2] = old_0
        
        # Swap pixel values
        pix = list(new_img_p.getdata())
        new_pix = []
        for p in pix:
            if p == 0:
                new_pix.append(magenta_idx)
            elif p == magenta_idx:
                new_pix.append(0)
            else:
                new_pix.append(p)
        new_img_p.putdata(new_pix)
        new_img_p.putpalette(palette)
    elif magenta_idx == 0:
        print("Magenta already at index 0")
    else:
        print("Error: Magenta not found in palette!")
        return
    
    # Verify
    final_palette = new_img_p.getpalette()
    print(f"Final Index 0: RGB({final_palette[0]}, {final_palette[1]}, {final_palette[2]})")
    
    new_img_p.save(path)
    print(f"Saved: {path}")

if __name__ == "__main__":
    fix_enemy()
