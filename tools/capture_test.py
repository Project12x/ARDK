"""
ROM Test with Screenshot Capture
Launches BlastEm, waits, captures screen, saves to artifacts.
"""
import subprocess
import time
import os
from PIL import ImageGrab

BLASTEM = r"C:\Users\estee\Desktop\blastem-win32-0.6.2\blastem.exe"
ROM = r"C:\Users\estee\Desktop\My Stuff\Code\Antigravity\SurvivorNES\projects\epoch\out\rom.bin"
OUTPUT_DIR = r"C:\Users\estee\.gemini\antigravity\brain\0458fced-211e-489c-8a75-814f0f85a901"

def capture_screenshot(name):
    """Capture full screen and save to artifacts"""
    img = ImageGrab.grab()
    path = os.path.join(OUTPUT_DIR, f"{name}.png")
    img.save(path)
    print(f"Saved: {path}")
    return path

def main():
    print("Launching BlastEm...")
    proc = subprocess.Popen([BLASTEM, ROM])
    
    # Wait for window to open and game to start
    print("Waiting 5 seconds for game to load...")
    time.sleep(5)
    
    # Capture initial state
    print("Capturing screenshot 1 (initial state)...")
    capture_screenshot("rom_test_initial")
    
    # Wait a bit more for gameplay
    print("Waiting 3 more seconds...")
    time.sleep(3)
    
    # Capture gameplay state
    print("Capturing screenshot 2 (gameplay)...")
    capture_screenshot("rom_test_gameplay")
    
    # Close BlastEm
    print("Terminating BlastEm...")
    proc.terminate()
    
    print("\n=== Test Complete ===")
    print(f"Screenshots saved to: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
