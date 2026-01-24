#!/usr/bin/env python3
"""
Generate tileable background using PixelLab create-tileset API.
Single-run, proper async job handling.
"""
import urllib.request
import urllib.error
import json
import base64
import time
import sys
from PIL import Image
from io import BytesIO

print("=" * 60)
print("PIXELLAB CREATE-TILESET API")
print("=" * 60)

API_KEY = "b68c2160-d218-4cfb-81f2-ccb619108419"
API_URL = "https://api.pixellab.ai/v2/create-tileset"
OUTPUT_PATH = "../projects/epoch/res/tilesets/background.png"

payload = {
    "lower_description": "dark purple wasteland ground, cracked earth, post-apocalyptic ruins, 16-bit Sega Genesis quality",
    "upper_description": "rocky debris and rubble, scattered stone chunks, detailed pixel art, Genesis style",
    "tile_size": {"width": 32, "height": 32},
    "text_guidance_scale": 10.0,
    "view": "high top-down",
    "shading": "detailed shading",
}

print(f"Request: {json.dumps(payload, indent=2)}")
print("Calling API...")
sys.stdout.flush()

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}",
}

data = json.dumps(payload).encode("utf-8")
req = urllib.request.Request(API_URL, data=data, headers=headers, method="POST")

try:
    with urllib.request.urlopen(req, timeout=30) as response:
        result = json.loads(response.read().decode("utf-8"))
        print(f"Response status: {response.status}")
        
        # Get job_id for async processing
        job_id = result.get("background_job_id") or result.get("data", {}).get("background_job_id") or result.get("job_id")
        tileset_id = result.get("tileset_id") or result.get("data", {}).get("tileset_id")
        if not job_id:
            print(f"No job_id found. Full response: {json.dumps(result, indent=2)[:1000]}")
            sys.exit(1)
        
        print(f"Job ID: {job_id}")
        print(f"Tileset ID: {tileset_id}")
        print("Polling for completion...")
        sys.stdout.flush()
        
        # Poll for job status
        for i in range(60):  # 2 minutes max
            time.sleep(3)
            status_url = f"https://api.pixellab.ai/v2/background-jobs/{job_id}"
            status_req = urllib.request.Request(status_url, headers=headers, method="GET")
            
            with urllib.request.urlopen(status_req, timeout=30) as status_resp:
                status = json.loads(status_resp.read().decode("utf-8"))
                job_status = status.get("data", {}).get("status") or status.get("status", "unknown")
                print(f"  [{i+1}/60] Status: {job_status}")
                sys.stdout.flush()
                
                if job_status == "completed":
                    print("Job completed!")
                    # Get the tileset data
                    tileset_data = status.get("data", {})
                    print(f"Keys: {list(tileset_data.keys())}")
                    
                    # Save the tileset image if available
                    if "tiles" in tileset_data:
                        print(f"Got {len(tileset_data['tiles'])} tiles")
                    break
                elif job_status == "failed":
                    print(f"Job failed: {status}")
                    sys.exit(1)
        else:
            print("Timeout waiting for job")
            sys.exit(1)
            
except urllib.error.HTTPError as e:
    print(f"HTTP Error {e.code}: {e.read().decode()}")
    sys.exit(1)
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("=" * 60)
print("DONE")
print("=" * 60)
