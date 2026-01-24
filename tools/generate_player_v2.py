
import sys
import os
from pathlib import Path
from PIL import Image
import pixellab
from configs.api_keys import PIXELLAB_API_KEY
from pipeline.style import StyleManager, StyleProfile, OutlineStyle, ShadingLevel, DetailLevel

def generate_player_v2():
    print("Initializing V2 Generation (Official SDK)...")
    
    # Initialize client with official SDK
    client = pixellab.Client(secret=PIXELLAB_API_KEY)
    
    # Define Style (Matches previous logic)
    manager = StyleManager()
    style = StyleProfile(
        name="retro_strategy",
        target_platform="genesis",
        outline_style=OutlineStyle.BLACK,
        shading_level=ShadingLevel.MODERATE,
        detail_level=DetailLevel.MEDIUM,
        contrast=0.75,
        saturation=0.7
    )
    
    # 2. General Params
    base_prompt = "sci-fi soldier with futuristic gun, wearing power armor, top-down orthogonal view, herzog zwei style, zelda link to the past style"
    base_params = {
        "description": base_prompt,
        "image_size": {"width": 32, "height": 32},
        "no_background": True,
        "view": "high top-down",
        "direction": "south"
    }
    
    # Inject style parameters via adapter
    # This automatically adds 'outline', 'shading', 'detail' based on the profile
    styled_params = manager.apply_style(style, "pixellab", base_params)
    
    print(f"Generating base sprite with params: {styled_params}...")

    # Generate Base
    try:
        # Pass expanded parameters
        base_result = client.generate_image_pixflux(**styled_params)
        
        # Result is likely a wrapped object with .image -> PIL Image
        # Check if result was successful
        # The SDK wrapper might return a GenerationResult or similar. 
        # Inspecting SDK usage: likely result object has attributes matching API response
        # or it's a Pydantic model. 
        # Assuming it has .image or we access it
        
        if hasattr(base_result, 'image'):
             base_img = base_result.image.pil_image()
        else:
             # Fallback if it's raw dict
             print(f"Unexpected base result format: {base_result}")
             return

        base_img.save("player_base_v2.png")
        print("Saved player_base_v2.png")

        
    except Exception as e:
        print(f"Base Generation Failed: {e}")
        return

    # 2. Generate Rotations (5-way only for mirroring)
    print("Generating 5-way rotations (for mirroring)...")
    # Order: South, South-East, East, North-East, North
    # We will mirror these for SW, W, NW
    ordered_directions = ["south", "south-east", "east", "north-east", "north"]
    
    rotations = []
    
    # Map strings to PixelLab enums
    dir_map = {
        "north": "north",
        "north-east": "north-east", 
        "east": "east",
        "south-east": "south-east",
        "south": "south"
    }
    
    # Try to resolve Enums if available, otherwise pass strings
    try:
        from pixellab import Direction
        print("Loaded PixelLab Direction Enum.")
        # Map to Enums
        enum_map = {
            "north": Direction.NORTH,
            "north-east": Direction.NORTH_EAST,
            "east": Direction.EAST,
            "south-east": Direction.SOUTH_EAST,
            "south": Direction.SOUTH
        }
    except ImportError:
        print("Could not load Direction Enum, using strings.")
        enum_map = dir_map # Fallback to strings if SDK differs

    for direction in ordered_directions:
        if direction == "south":
            rotations.append(base_img)
            continue
            
        print(f"Rotating to {direction}...")
        try:
            target_dir = enum_map.get(direction)
            # ... existing rotation logic matches ...
            if not target_dir:
                print(f"Invalid direction: {direction}")
                rotations.append(base_img)
                continue

            rot_result = client.rotate(
                image_size={"width": 32, "height": 32},
                from_image=base_img,
                from_direction=enum_map["south"], 
                to_direction=target_dir,
                from_view="high top-down",
                to_view="high top-down"
            )
            
            # Extract image
            if hasattr(rot_result, 'image'):
                 rot_img = rot_result.image.pil_image()
                 rotations.append(rot_img)
                 print(f"Successfully rotated to {direction}")
            else:
                print(f"Warning: No image in response for {direction}")
                rotations.append(base_img) # Fallback

        except Exception as e:
            print(f"Rotation Failed for {direction}: {e}")
            import traceback
            traceback.print_exc()
            rotations.append(base_img) # Fallback

    # 3. Save Sheet
    output_dir = Path("projects/epoch/res/sprites")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    sheet_width = 32 * len(rotations)
    sheet = Image.new("RGBA", (sheet_width, 32))
    for i, img in enumerate(rotations):
        sheet.paste(img, (i*32, 0))
        
        # Also save individual for debug
        safe_dir = ordered_directions[i].replace("-", "_") # s-e -> s_e
        img.save(f"player_v2_{safe_dir}.png")
        
    sheet.save(output_dir / "player_8way_sheet.png")
    print(f"Saved consistent spritesheet to {output_dir / 'player_8way_sheet.png'}")

if __name__ == "__main__":
    generate_player_v2()
