
import logging
from asset_generators.pixellab_client import PixelLabClient, generate_genesis_sprite

# Setup
logging.basicConfig(level=logging.DEBUG)
client = PixelLabClient(max_calls=5)

# 1. Generate a reference
print("Generating Ref...")
ref = generate_genesis_sprite(client, "test reference", use_v2=True)
if not ref:
    print("Ref failed")
    exit()

# 2. Call 8-way manually and print RAW response
print("\nCalling 8-way...")
import json
import base64
from io import BytesIO

buffer = BytesIO()
ref.save(buffer, format='PNG')
b64_ref = base64.b64encode(buffer.getvalue()).decode('utf-8')

payload = {
    "reference_image": {"base64": b64_ref}, # Try simplified structure first (doc says object | null)
    "image_size": {"width": 32, "height": 32},
    "method": "rotate_character"
}

# Bypass client wrapper to see raw output
try:
    resp = client._make_request("/generate-8-rotations-v2", payload, api_version=2)
    print("RAW RESPONSE:", json.dumps(resp, indent=2))
except Exception as e:
    print("ERROR:", e)
