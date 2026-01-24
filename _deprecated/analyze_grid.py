
from PIL import Image
import numpy as np

def analyze_grid(filename):
    print(f"Analyzing {filename}...")
    try:
        img = Image.open(filename).convert('L') # Gray
        pixels = np.array(img)
        
        # Simple row/col sum
        row_var = np.var(pixels, axis=1)
        col_var = np.var(pixels, axis=0)
        
        # If variance spikes periodically, it's a grid?
        # Simpler: Check if rows/cols are identical
        
        print(f"  Size: {img.size}")
        print(f"  Row Var Mean: {np.mean(row_var):.2f}")
        print(f"  Col Var Mean: {np.mean(col_var):.2f}")
        
    except Exception as e:
        print(f"  Error: {e}")

if __name__ == "__main__":
    analyze_grid("gfx/ai_output/background_cyberpunk.png")
    analyze_grid("gfx/ai_output/player_alt_radical.png")
