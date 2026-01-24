
import sys
import os
from PIL import Image

def png_to_chr(input_path, output_path):
    try:
        img = Image.open(input_path)
    except FileNotFoundError:
        print(f"Error: File {input_path} not found.")
        sys.exit(1)

    # Ensure image is 128 pixels wide (Standard 16 tiles) or handle generic widths
    if img.width % 8 != 0 or img.height % 8 != 0:
        print("Error: Image dimensions must be multiples of 8.")
        sys.exit(1)

    # Convert to palette mode if not already
    if img.mode != 'P':
        print("Converting to P mode...")
        # Assume generic 4 color palette for simplicity or just take pixel values % 4
        img = img.convert('P', palette=Image.ADAPTIVE, colors=4)

    pixels = img.load()
    width, height = img.size
    
    # NES CHR format: 
    # Each 8x8 tile is 16 bytes.
    # First 8 bytes = bit 0 of each pixel row.
    # Next 8 bytes = bit 1 of each pixel row.
    
    binary_data = bytearray()

    # Process in 8x8 blocks
    for y in range(0, height, 8):
        for x in range(0, width, 8):
            # For each tile
            plane0 = []
            plane1 = []
            
            for row in range(8):
                p0_byte = 0
                p1_byte = 0
                for col in range(8):
                    # Get pixel color index (0-3)
                    color = pixels[x + col, y + row]
                    
                    # Extract bits
                    bit0 = (color & 1)
                    bit1 = (color & 2) >> 1
                    
                    # Shift into position (pixel 0 is MSB, pixel 7 is LSB)
                    p0_byte |= (bit0 << (7 - col))
                    p1_byte |= (bit1 << (7 - col))
                
                plane0.append(p0_byte)
                plane1.append(p1_byte)
            
            binary_data.extend(plane0)
            binary_data.extend(plane1)

    with open(output_path, 'wb') as f:
        f.write(binary_data)
    
    print(f"Converted {input_path} to {output_path} ({len(binary_data)} bytes).")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python png2chr.py <input.png> <output.chr>")
        sys.exit(1)
    
    png_to_chr(sys.argv[1], sys.argv[2])
