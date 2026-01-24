"""
Fix hero sprite transparency - ensure index 0 is magenta (255,0,255)
"""
from PIL import Image

def fix_hero_transparency():
    """Fix hero sprite so index 0 is magenta for transparency"""
    path = r"c:\Users\estee\Desktop\My Stuff\Code\Antigravity\SurvivorNES\projects\epoch\res\sprites\hero_sheet_final.png"
    
    img = Image.open(path)
    print(f"Original: {img.size}, Mode: {img.mode}")
    
    if img.mode != 'P':
        print("Not indexed - converting")
        img = img.convert('P', palette=Image.ADAPTIVE, colors=15)
    
    palette = list(img.getpalette())
    
    # Check current index 0
    print(f"Current Index 0: RGB({palette[0]}, {palette[1]}, {palette[2]})")
    
    if palette[0] == 255 and palette[1] == 0 and palette[2] == 255:
        print("Index 0 is already magenta - checking pixel data")
    else:
        print("Index 0 is NOT magenta - fixing")
    
    # Convert to RGBA and find/replace any fully transparent or magenta pixels
    img_rgba = img.convert('RGBA')
    pixels = list(img_rgba.getdata())
    width, height = img_rgba.size
    
    new_pixels = []
    magenta_replaced = 0
    for p in pixels:
        # If alpha is 0 (transparent) or pixel is close to magenta, ensure it's pure magenta
        if p[3] == 0 or (p[0] > 200 and p[1] < 50 and p[2] > 200):
            new_pixels.append((255, 0, 255, 255))
            magenta_replaced += 1
        else:
            new_pixels.append(p)
    
    print(f"Normalized {magenta_replaced} pixels to pure magenta")
    
    # Create new RGBA image
    new_img = Image.new('RGBA', (width, height))
    new_img.putdata(new_pixels)
    
    # Convert back to indexed with magenta as first color
    # Use custom quantization to ensure magenta is index 0
    new_img_rgb = new_img.convert('RGB')
    new_img_p = new_img_rgb.quantize(colors=15, method=Image.MEDIANCUT)
    
    # Get palette and ensure index 0 is magenta
    palette = list(new_img_p.getpalette())
    
    # Find magenta in palette
    magenta_idx = -1
    for i in range(16):
        if i*3+2 >= len(palette):
            break
        r, g, b = palette[i*3], palette[i*3+1], palette[i*3+2]
        if r > 250 and g < 10 and b > 250:
            magenta_idx = i
            break
    
    if magenta_idx > 0:
        print(f"Swapping magenta from index {magenta_idx} to index 0")
        old_0 = (palette[0], palette[1], palette[2])
        palette[0], palette[1], palette[2] = 255, 0, 255
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
        print("Warning: Magenta not found in palette, setting index 0 to magenta")
        palette[0], palette[1], palette[2] = 255, 0, 255
        new_img_p.putpalette(palette)
    
    final_palette = new_img_p.getpalette()
    print(f"Final Index 0: RGB({final_palette[0]}, {final_palette[1]}, {final_palette[2]})")
    
    new_img_p.save(path)
    print(f"Saved: {path}")

if __name__ == "__main__":
    fix_hero_transparency()
