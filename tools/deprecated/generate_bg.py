import pixellab
from PIL import Image
import os

# Initialize client
if os.path.exists(".env"):
    from dotenv import load_dotenv
    load_dotenv()

API_KEY = os.getenv("PIXELLAB_API_KEY")
if not API_KEY:
    print("Error: PIXELLAB_API_KEY not found.")
    exit(1)

client = pixellab.Client(secret=API_KEY)

print("Generating background tile...")
try:
    img = client.generate_image_pixflux(
        description="seamless texture of dark rocky ground, dirt and small stones, 16-bit pixel art style, top down view, retro game background, low contrast, dark earth colors",
        image_size={"width": 256, "height": 256},
    ).image.pil_image()

    output_path = "projects/epoch/res/tilesets/background.png"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    img.save(output_path)
    print(f"Saved background to {output_path}")

except Exception as e:
    print(f"Generation Failed: {e}")
