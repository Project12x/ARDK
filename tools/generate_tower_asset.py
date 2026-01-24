
import sys
from pathlib import Path

# Add tools directory to path
sys.path.insert(0, str(Path(__file__).parent))

from pipeline.style import StyleManager, StyleProfile
from asset_generators.pixellab_client import PixelLabClient

def generate_tower():
    print("Initializing Style System for Tower...")
    manager = StyleManager()
    client = PixelLabClient(max_calls=5)
    
    # 1. Define "Retro Strategy" Style (matches player generation)
    from pipeline.style import  OutlineStyle, ShadingLevel, DetailLevel
    
    # Try to load if exists, otherwise create fresh
    style = manager.load_style("retro_strategy")
    if not style:
         print("Style not found on disk, using inline definition.")
         style = StyleProfile(
            name="retro_strategy",
            target_platform="genesis",
            outline_style=OutlineStyle.BLACK,
            shading_level=ShadingLevel.MODERATE,
            detail_level=DetailLevel.MEDIUM,
            contrast=0.75,
            saturation=0.7
        )
    
    # 2. Generate Tower Sprite
    base_prompt = "quasi mystical crystal monolith seemingly growing out of the ground, sci-fi ancient technology, glowing runes, center of time travel ark, top-down orthogonal view, herzog zwei style"
    
    # Apply style to params
    base_params = {
        "description": base_prompt,
        "width": 64,  # Increased size
        "height": 64, # Increased size
        "view": "high top-down",
        "direction": "south", 
        "no_background": True
    }
    
    styled_params = manager.apply_style(style, "pixellab", base_params)
    
    print(f"Generating tower sprite...")
    
    # Using V1 pixflux for consistency with player sprite
    result = client.generate_image_pixflux(**styled_params)
    
    if not result.success:
        print(f"Failed to generate tower: {result.error}")
        return

    output_dir = Path("projects/epoch/res/sprites")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save as separate sprite
    fname = output_dir / "tower.png"
    result.image.save(fname)
    print(f"Saved tower sprite to {fname}")

if __name__ == "__main__":
    generate_tower()
