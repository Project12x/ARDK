"""
BlastEm Automation: GDB Control + Internal Screenshot
Uses GDB socket for execution control and pyautogui for 'p' key trigger.
"""
import socket
import subprocess
import time
import sys
import os
import glob
import shutil

try:
    import pyautogui
except ImportError:
    print("Installing pyautogui...")
    subprocess.run([sys.executable, "-m", "pip", "install", "pyautogui", "-q"])
    import pyautogui

BLASTEM = r"tools\emulators\blastem\blastem.exe"
ROM = r"projects\epoch\out\rom.bin"
GDB_PORT = 1234
HOME = os.path.expanduser("~")
OUTPUT_DIR = r"C:\Users\estee\.gemini\antigravity\brain\0458fced-211e-489c-8a75-814f0f85a901"

def gdb_checksum(data):
    return sum(ord(c) for c in data) & 0xFF

def gdb_send(sock, cmd):
    packet = f"${cmd}#{gdb_checksum(cmd):02x}"
    sock.sendall(packet.encode())
    time.sleep(0.1)
    try:
        return sock.recv(4096).decode(errors='ignore')
    except:
        return ""

def find_latest_screenshot():
    """Find most recent BlastEm screenshot in HOME"""
    pattern = os.path.join(HOME, "blastem_*.png")
    files = glob.glob(pattern)
    if files:
        return max(files, key=os.path.getmtime)
    return None

def run_test():
    print("=== BlastEm GDB Test with Screenshot ===\n")
    
    # Note existing screenshots
    before = set(glob.glob(os.path.join(HOME, "blastem_*.png")))
    
    print("Starting BlastEm with GDB server...")
    proc = subprocess.Popen([BLASTEM, ROM, "-D"])
    time.sleep(3)
    
    print(f"Connecting to GDB port {GDB_PORT}...")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        sock.connect(("localhost", GDB_PORT))
        sock.settimeout(2)
        
        # Handshake
        resp = gdb_send(sock, "?")
        print(f"GDB Response: {resp}")
        
        # Continue execution
        print("Sending continue command...")
        sock.sendall(b"$c#63")
        
        # Wait for game to run and render
        print("Game running - waiting 4 seconds...")
        time.sleep(4)
        
        # Take screenshot using PIL (reliable method)
        print("Capturing screenshot 1...")
        from PIL import ImageGrab
        img1 = ImageGrab.grab()
        path1 = os.path.join(OUTPUT_DIR, "rom_test_1.png")
        img1.save(path1)
        print(f"Saved: {path1}")
        
        # Wait more and take second screenshot
        print("Waiting 3 more seconds...")
        time.sleep(3)
        
        print("Capturing screenshot 2...")
        img2 = ImageGrab.grab()
        path2 = os.path.join(OUTPUT_DIR, "rom_test_2.png")
        img2.save(path2)
        print(f"Saved: {path2}")
        
        print("\n=== Test Complete ===")
        print(f"Screenshots in: {OUTPUT_DIR}")
        return 0
        
        print("Test complete, terminating...")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        sock.close()
        proc.terminate()
    
    # Find new screenshots
    after = set(glob.glob(os.path.join(HOME, "blastem_*.png")))
    new_screenshots = after - before
    
    if new_screenshots:
        print(f"\n=== Found {len(new_screenshots)} new screenshot(s) ===")
        for i, src in enumerate(sorted(new_screenshots)):
            dst = os.path.join(OUTPUT_DIR, f"rom_test_{i+1}.png")
            shutil.copy(src, dst)
            print(f"Copied: {dst}")
        return 0
    else:
        print("\nNo new screenshots found in HOME directory")
        return 1

if __name__ == "__main__":
    os.chdir(r"c:\Users\estee\Desktop\My Stuff\Code\Antigravity\SurvivorNES")
    sys.exit(run_test())
