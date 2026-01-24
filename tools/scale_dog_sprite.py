"""
Fix dog sprite scaling to preserve transparency (index 0 = magenta)
"""
from PIL import Image

def fix_dog_sprite():
    """Scale dog sprite preserving transparency color at index 0"""
    input_path = r"c:\Users\estee\Desktop\My Stuff\Code\Antigravity\SurvivorNES\projects\epoch\res\sprites\dog_sheet_final.png"
    output_path = r"c:\Users\estee\Desktop\My Stuff\Code\Antigravity\SurvivorNES\projects\epoch\res\sprites\dog_sheet_32x32.png"
    
    # Load original
    img = Image.open(input_path)
    print(f"Original: {img.size}, Mode: {img.mode}")
    
    # Convert to RGBA for proper scaling
    if img.mode == 'P':
        img = img.convert('RGBA')
    
    frame_width = 32
    frame_height_old = 48
    frame_height_new = 32
    num_frames = 256 // frame_width  # 8 frames
    
    # Create new RGBA sheet
    new_sheet = Image.new('RGBA', (frame_width * num_frames, frame_height_new), (255, 0, 255, 255))
    
    for i in range(num_frames):
        left = i * frame_width
        frame = img.crop((left, 0, left + frame_width, frame_height_old))
        
        # Scale using NEAREST for pixel art
        frame_scaled = frame.resize((frame_width, frame_height_new), Image.NEAREST)
        
        new_sheet.paste(frame_scaled, (i * frame_width, 0), frame_scaled)
    
    # Convert back to P (indexed) with first color as transparency
    new_sheet_p = new_sheet.convert('P', palette=Image.ADAPTIVE, colors=15)
    
    # Get palette and ensure index 0 is magenta
    palette = list(new_sheet_p.getpalette())
    
    # Find magenta in palette and swap with index 0
    for i in range(256):
        r, g, b = palette[i*3], palette[i*3+1], palette[i*3+2]
        if r > 200 and g < 50 and b > 200:  # Magenta-ish
            if i != 0:
                # Swap with index 0
                palette[0], palette[i*3] = palette[i*3], palette[0]
                palette[1], palette[i*3+1] = palette[i*3+1], palette[1]
                palette[2], palette[i*3+2] = palette[i*3+2], palette[2]
            break
    
    new_sheet_p.putpalette(palette)
    new_sheet_p.save(output_path)
    print(f"Created: {output_path}")

if __name__ == "__main__":
    fix_dog_sprite()
