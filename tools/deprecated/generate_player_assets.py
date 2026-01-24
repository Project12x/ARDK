
import sys
from pathlib import Path

# Add tools directory to path
sys.path.insert(0, str(Path(__file__).parent))

from pipeline.style import StyleManager, StyleProfile, OutlineStyle, ShadingLevel, DetailLevel
from asset_generators.pixellab_client import PixelLabClient, generate_genesis_8_directions
from PIL import Image
import os

def generate_player():
    print("Initializing Style System...")
    manager = StyleManager()
    client = PixelLabClient(max_calls=10)
    
    # 1. Define "Retro Strategy" Style
    # "Zelda Link to the Past" / "Herzog Zwei" style:
    # - Top-down/Orthogonal
    # - Black outlines (readable)
    # - Moderate shading
    # - 16-bit Genesis palette
    style = StyleProfile(
        name="retro_strategy",
        target_platform="genesis",
        outline_style=OutlineStyle.BLACK,
        shading_level=ShadingLevel.MODERATE,
        detail_level=DetailLevel.MEDIUM,
        contrast=0.75,
        saturation=0.7
    )
    
    print(f"Defined Style: {style.name}")
    
    # 2. Generate Base Sprite (South Facing)
    base_prompt = "sci-fi soldier with futuristic gun, wearing power armor, top-down orthogonal view, herzog zwei style, zelda link to the past style"
    
    # Apply style to params
    base_params = {
        "description": base_prompt,
        "width": 32,
        "height": 32,
        "view": "high top-down",
        "direction": "south", 
        "no_background": True
    }
    
    # Use StyleManager to inject style parameters
    # We use 'pixellab' provider
    styled_params = manager.apply_style(style, "pixellab", base_params)
    
    print(f"Generating base sprite with params: {styled_params}...")
    
    # Execute generation (Using v2 for best quality if available, else v1)
    # Using generate_image_v2 directly via client if possible, or pixflux
    # Let's use pixflux (v1) for the base as it's reliable for initial creation, 
    # but v2 is better for style. The adapter supports both.
    # checking pixellab_client, generate_image_v2 is available.
    
    # Note: styled_params keys might need mapping to specific function args if unpacking **kwargs
    # But generate_image_v2 takes **kwargs.
    
    # Use generate_image_pixflux (v1) because it supports explicit 'view' and 'direction' params
    # which are critical for the initial orthogonal angle.
    result = client.generate_image_pixflux(**styled_params)
    
    if not result.success:
        print(f"Failed to generate base sprite: {result.error}")
        return

    base_sprite = result.image
    
    # Save base for inspection
    base_sprite.save("player_base.png")
    print("Base sprite saved to player_base.png")

    # 3. Generate 8-Way Rotations (Manual Generation for distinct views)
    print("Generating 8 distinct directional sprites (avoiding rotate API)...")
    
    # Map directions to params
    # valid V1 directions: south, south-west, west, north-west, north, north-east, east, south-east
    ordered_directions = ["north", "north-east", "east", "south-east", "south", "south-west", "west", "north-west"]
    
    rotations = []
    failed = False
    
    for direction in ordered_directions:
        print(f"Generating {direction}...")
        dir_params = base_params.copy()
        dir_params["direction"] = direction
        
        # Inject style again to be safe/consistent
        styled_dir = manager.apply_style(style, "pixellab", dir_params)
        
        result_dir = client.generate_image_pixflux(**styled_dir)
        if result_dir.success:
            rotations.append(result_dir.image)
        else:
            print(f"Failed {direction}: {result_dir.error}")
            failed = True
            break
            
    if failed:
        print("Aborting due to rotation failure.")
        return
        
    # 4. Save Assets
    output_dir = Path("projects/epoch/res/sprites")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    directions = ["n", "ne", "e", "se", "s", "sw", "w", "nw"]
    
    for i, img in enumerate(rotations):
        # Format filename: player_iso_DIRECTION.png
        # But for spritesheet generation, we might want sequential or a single strip.
        # SGDK SPR_addSprite usually takes a spritesheet with frames.
        # For 8-way movement, it's often 8 animations (rows) or 1 animation with 8 frames?
        # A generic spritesheet is usually best.
        
        fname = f"player_8way_{directions[i]}.png"
        img.save(output_dir / fname)
        print(f"Saved {fname}")
        
    # Create a composite sheet for preview
    sheet = Image.new("RGBA", (32*8, 32))
    for i, img in enumerate(rotations):
        sheet.paste(img, (i*32, 0))
    sheet.save(output_dir / "player_8way_sheet.png")
    print(f"Saved composite sheet to {output_dir / 'player_8way_sheet.png'}")

if __name__ == "__main__":
    generate_player()
