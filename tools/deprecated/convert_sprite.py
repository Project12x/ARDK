"""Convert generated sprite to SGDK-compatible 16-color indexed PNG."""
from PIL import Image

# Load generated sprite  
src = r'C:/Users/estee/.gemini/antigravity/brain/0458fced-211e-489c-8a75-814f0f85a901/player_sprite_90s_dude_1768581417817.png'
dst = r'C:/Users/estee/Desktop/My Stuff/Code/Antigravity/SurvivorNES/projects/epoch/res/sprites/player.png'

img = Image.open(src).convert('RGBA')
print(f'Original size: {img.size}')

# The generated image is 1024x1024 with 4 sprite frames in a row
# Each frame is about 256x256 pixels - need to extract and resize to 32x32

# Create 128x32 sprite sheet (4 frames of 32x32)
sheet = Image.new('RGBA', (128, 32), (0, 0, 0, 0))  # Transparent background

# Extract and resize each frame
for i in range(4):
    x1 = i * (img.width // 4)
    x2 = (i + 1) * (img.width // 4)
    f = img.crop((x1, 0, x2, img.height))
    f = f.resize((32, 32), Image.Resampling.NEAREST)
    sheet.paste(f, (i * 32, 0), f)  # Use alpha as mask

# SGDK wants indexed PNG with 16 colors
# Create RGB version with magenta (255,0,255) for transparency
magenta = (255, 0, 255)
rgb_sheet = Image.new('RGB', sheet.size, magenta)
rgb_sheet.paste(sheet, mask=sheet.split()[3])

# Quantize to 16 colors (including magenta as index 0)
indexed = rgb_sheet.quantize(colors=16, method=Image.Quantize.MEDIANCUT)

# Save as indexed PNG
indexed.save(dst)
print(f'Saved as indexed PNG: {dst}')
print(f'Final size: {indexed.size}, mode: {indexed.mode}')
print('Done!')
