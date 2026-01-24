
import sys
import os
import pixellab
from PIL import Image
from dotenv import load_dotenv

# Load env vars
load_dotenv()

def test_rotation():
    print("Testing V2 Rotation with Official SDK...")
    
    # helper to get api key
    from configs.api_keys import PIXELLAB_API_KEY
    
    client = pixellab.Client(secret=PIXELLAB_API_KEY)
    
    # Create a dummy base image if not exists
    if os.path.exists("player_base.png"):
        img = Image.open("player_base.png")
    else:
        print("Creating dummy base image...")
        img = Image.new("RGBA", (32, 32), (255, 0, 0, 255))
    
    # Try V2 Rotation
    print("Sending V2 Rotation Request...")
    try:
        # Check actual SDK method name via dir() if uncertain, but assuming generate_8_rotations
        # The audit said the endpoint is /v2/generate-8-rotations-v2
        # Let's try to inspect the client first or just guess based on SDK patterns
        # Usually SDKs map endpoints to snake_case methods
        
        # If the SDK is well-structured, it might be client.generate_8_rotations_v2 or similar.
        # Let's print dir(client) to safely find it.
        print(f"Client methods: {[m for m in dir(client) if 'generate' in m or 'rotate' in m]}")
        
        # Inspect rotate
        print(f"SDK Version: {pixellab.__version__ if hasattr(pixellab, '__version__') else 'unknown'}")
        help(client.rotate)
        
        # Try a rotation
        print("Attempting single rotation to 'north'...")
        # usually rotate(image, angle) or rotate(image, direction)
        # Audit says /rotate endpoint.
        
        # Let's guess schema or wait for help() output.
        # But to prevent crashing, let's wrap in try/except or just dump help first.


        print("Response received.")
        # SDK response usually has .images list
        if hasattr(result, 'images'):
            for i, rot_img in enumerate(result.images):
                # result.images might be objects with .url or .base64 or just PIL images
                # The audit said: response.image.pil_image() for single. 
                # For multiple, it's likely a list of Image wrappers.
                
                # Check type
                print(f"Image {i} type: {type(rot_img)}")
                
                # If it's the SDK wrapper, getting PIL image:
                if hasattr(rot_img, 'pil_image'):
                    pil_img = rot_img.pil_image()
                    pil_img.save(f"test_rot_{i}.png")
                else:
                    # Might be raw dict if SDK is minimal?
                    print(f"Unknown image format: {rot_img}")

        else:
            print(f"Unknown result format: {result}")
            
    except Exception as e:
        print(f"SDK Error: {e}")

if __name__ == "__main__":
    test_rotation()
