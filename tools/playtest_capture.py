"""
Interactive Game Test - Launch BlastEm and capture screenshots while user plays
"""
from PIL import ImageGrab
import subprocess
import time
import os

# Config
BLASTEM_PATH = r"C:\Users\estee\Desktop\blastem-win32-0.6.2\blastem.exe"
ROM_PATH = r"C:\Users\estee\Desktop\My Stuff\Code\Antigravity\SurvivorNES\projects\epoch\out\rom.bin"
OUTPUT_DIR = r"C:\Users\estee\.gemini\antigravity\brain\0458fced-211e-489c-8a75-814f0f85a901"

def main():
    print("Launching BlastEm for interactive testing...")
    print("Play the game - I will capture screenshots every 10 seconds.")
    print("Close BlastEm window when done testing.")
    
    # Launch BlastEm (no -D flag - normal play mode)
    proc = subprocess.Popen([BLASTEM_PATH, ROM_PATH])
    
    # Wait for game to load
    time.sleep(3)
    
    screenshot_count = 0
    try:
        while proc.poll() is None:  # While BlastEm is running
            # Capture screenshot
            screenshot_count += 1
            screenshot = ImageGrab.grab()
            filename = os.path.join(OUTPUT_DIR, f"playtest_{screenshot_count}.png")
            screenshot.save(filename)
            print(f"Captured: playtest_{screenshot_count}.png")
            
            # Wait 10 seconds before next capture
            time.sleep(10)
    except KeyboardInterrupt:
        pass
    
    print(f"\n=== Test Complete ===")
    print(f"Captured {screenshot_count} screenshots to: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
