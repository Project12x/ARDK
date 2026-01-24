import socket
import subprocess
import time
import os
import sys
from PIL import ImageGrab

# Configuration
BLASTEM_PATH = r"C:\Users\estee\Desktop\blastem-win32-0.6.2\blastem.exe"
ROM_PATH = r"projects\epoch\out\rom.bin"
OUTPUT_DIR = r"artifacts/automation_test"

# Memory Addresses (from map file + struct offsets)
ADDR_GAME_SCORE = 0xE0FF044E  # Game.score (u32)
ADDR_PLAYER_HP  = 0xE0FF132A  # PlayerData.currentHP (u16)
ADDR_INPUT      = 0xE0FF1338  # InputState.current (u16)

class BlastEmRemote:
    def __init__(self, host='localhost', port=1234):
        self.host = host
        self.port = port
        self.sock = None
        self.proc = None

    def launch(self):
        print(f"Launching BlastEm: {BLASTEM_PATH}")
        # -D enables GDB remote server
        if not os.path.exists(BLASTEM_PATH):
            raise FileNotFoundError(f"BlastEm not found at {BLASTEM_PATH}")
        
        # Use valid absolute path for ROM
        abs_rom = os.path.abspath(ROM_PATH)
        self.proc = subprocess.Popen([BLASTEM_PATH, abs_rom, "-D"])
        time.sleep(3) # Wait for init

    def connect(self):
        print(f"Connecting to GDB stub at {self.host}:{self.port}...")
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.host, self.port))
            # Handshake? GDB RSP starts with '+' or just commands?
            # Usually client sends first.
            # Let's send a query to check status.
            # '?' -> queries halt reason
            resp = self.send_command("?")
            print(f"Connected. Status: {resp}")
        except ConnectionRefusedError:
            print("Connection failed. BlastEm might not be listening.")
            raise

    def send_command(self, cmd):
        # Format: $data#checksum
        # Checksum is two-digit hex sum mod 256
        chkString = sum(ord(c) for c in cmd) % 256
        chk = f"{chkString:02x}"
        packet = f"${cmd}#{chk}"
        
        self.sock.sendall(packet.encode('ascii'))
        
        # Responses:
        # '+' (ACK) then '$...#xx'
        # We need to read until we get a full response packet
        # Simplified: Read header, then until '#' and checksum
        
        # Read ACK
        ack = self.sock.recv(1)
        if ack != b'+':
            print(f"Warning: Expected ACK (+), got {ack}")
            
        # Read Packet
        res = b""
        while True:
            chunk = self.sock.recv(4096)
            res += chunk
            if b'#' in res:
                # Check for end of packet logic?
                # Format $...#XX
                # We should stop 2 chars after #
                if len(res.split(b'#')[-1]) >= 2:
                    break
        return res.decode('ascii')

    def read_memory(self, addr, length):
        # Command: m addr,length
        # Addr/Length in HEX
        cmd = f"m{addr:x},{length:x}"
        resp = self.send_command(cmd)
        # Resp: $bytes#XX
        # Extract content between $ and #
        content = resp.split('$')[1].split('#')[0]
        return content

    def write_memory(self, addr, data_hex):
        # Command: M addr,length:data
        length = len(data_hex) // 2
        cmd = f"M{addr:x},{length:x}:{data_hex}"
        return self.send_command(cmd)

    def continue_exec(self):
        # 'c' command continues execution. Note: It does NOT reply until halted!
        # Do NOT wait for simple reply if we want to run async.
        # But for 'step' we wait.
        # For 'c', we just send it.
        # However, BlastEm GDB stub might behave differently.
        # Usually 'c' blocks GDB interaction until breakpoint/pause.
        pass

    def close(self):
        if self.sock:
            self.send_command("k") # Kill
            self.sock.close()
        if self.proc:
            self.proc.terminate()

    def hex_to_int(self, hex_str, endian='big'):
        # Genesis is Big Endian (m68k)
        # GDB returns bytes in mem order? usually.
        # hex_str "0064" -> 100
        val = int(hex_str, 16)
        return val

def main():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    remote = BlastEmRemote()
    try:
        remote.launch()
        remote.connect()
        
        # 1. Start Execution (Boot Game)
        print("Starting Game Execution...")
        remote.sock.sendall(b"$c#63") # 'c' command
        
        # Wait for game to boot and reach gameplay (5s)
        time.sleep(5)
        
        # 2. Interrupt (Halt to read memory)
        print("Interrupting...")
        remote.sock.sendall(b"\x03") # Ctrl+C
        # Wait for Stop Reply ($S...)
        stop_reply = remote.sock.recv(1024)
        print(f"Stopped: {stop_reply.decode('ascii', errors='ignore')}")

        # 3. Read Game State
        print("Reading Game State...")
        # Score (4 bytes)
        score_hex = remote.read_memory(ADDR_GAME_SCORE, 4)
        print(f"Score Raw: {score_hex} -> {int(score_hex, 16)}")
        
        # HP (2 bytes)
        hp_hex = remote.read_memory(ADDR_PLAYER_HP, 2)
        print(f"HP Raw: {hp_hex} -> {int(hp_hex, 16)}")

        # 4. Capture Screenshot
        print("Capturing Screenshot...")
        path = os.path.join(OUTPUT_DIR, "automation_capture.png")
        ImageGrab.grab().save(path)
        print(f"Saved to {path}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        try:
            remote.close()
        except:
            pass

if __name__ == "__main__":
    main()
