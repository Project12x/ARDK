#!/usr/bin/env python3
"""
Test the /create-character-with-8-directions endpoint which:
1. Takes a text description (no reference image needed)
2. Returns a background_job_id
3. Must be polled for completion
4. Delivers 8 directional views when done
"""
import sys
import time
import json
sys.path.insert(0, 'tools')

from asset_generators.pixellab_client import PixelLabClient

# Safety config
MAX_POLL_ATTEMPTS = 30  # Max ~5 minutes
POLL_INTERVAL = 10  # seconds

client = PixelLabClient(max_calls=35)  # Budget for polling

print("="*60)
print("Testing /create-character-with-8-directions")
print("="*60)

# Build payload per API docs
payload = {
    "description": "90s skater kid, red backwards cap, red flannel shirt, baggy jeans, pixel art",
    "image_size": {"width": 64, "height": 64},
    "outline": "medium",
    "shading": "soft",
    "detail": "medium",
    "view": "side",
}

print(f"Payload: {json.dumps(payload, indent=2)}")
print("\nSubmitting job...")

try:
    result = client._make_request("/create-character-with-8-directions", payload, api_version=2)
    print(f"Response: {json.dumps(result, indent=2)[:500]}")
    
    job_id = result.get("background_job_id")
    character_id = result.get("character_id")
    
    if not job_id:
        print("ERROR: No job_id returned")
        sys.exit(1)
        
    print(f"\nJob ID: {job_id}")
    print(f"Character ID: {character_id}")
    print(f"\nPolling for completion (max {MAX_POLL_ATTEMPTS} attempts)...")
    
    for attempt in range(MAX_POLL_ATTEMPTS):
        time.sleep(POLL_INTERVAL)
        
        status_result = client._make_request(f"/background-jobs/{job_id}", None, method="GET", api_version=2)
        status = status_result.get("status", "unknown")
        print(f"  Attempt {attempt+1}: {status}")
        
        if status == "completed":
            print("\nJOB COMPLETED!")
            print(f"Result: {json.dumps(status_result, indent=2)[:1000]}")
            break
        elif status == "failed":
            print(f"JOB FAILED: {status_result}")
            sys.exit(1)
    else:
        print("TIMEOUT: Job did not complete in time")
        sys.exit(1)
        
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print(f"\nTotal session cost: ${client.get_session_cost():.4f}")
