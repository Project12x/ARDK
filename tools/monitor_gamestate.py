"""
BlastEm Real-Time RAM Monitor
Connects to BlastEm's GDB stub and polls game state variables.
"""
import socket
import time
import sys

# Memory Addresses (from symbol.txt, use 0xFF prefix for Genesis Work RAM)
# Note: Symbol file shows 0xE0FF..., but hardware maps to 0xFF0000-0xFFFFFF
ADDR_GAME_SCORE = 0xFF044E  # game.score (offset within 64KB RAM)
ADDR_SCORE_STR  = 0xFF15EB  # scoreStr buffer 
ADDR_PLAYER_HP  = 0xFF132A  # playerData.currentHP

class BlastEmMonitor:
    def __init__(self, host='localhost', port=1234):
        self.host = host
        self.port = port
        self.sock = None

    def connect(self):
        retries = 10
        while retries > 0:
            try:
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.sock.settimeout(2.0)
                self.sock.connect((self.host, self.port))
                print(f"Connected to {self.host}:{self.port}")
                return True
            except Exception as e:
                print(f"Connection failed ({retries} left): {e}")
                time.sleep(1)
                retries -= 1
        print("Could not connect to BlastEm.")
        return False

    def send_raw(self, data):
        """Send raw bytes without GDB framing"""
        self.sock.sendall(data)

    def send_command(self, cmd):
        """Send a GDB RSP command with checksum"""
        chk = sum(ord(c) for c in cmd) % 256
        packet = f"${cmd}#{chk:02x}"
        try:
            self.sock.sendall(packet.encode('ascii'))
            # Read ACK
            self.sock.recv(1)
            # Read response until #XX
            res = b""
            while True:
                try:
                    chunk = self.sock.recv(1024)
                    if not chunk:
                        break
                    res += chunk
                    if b'#' in res and len(res.split(b'#')[-1]) >= 2:
                        break
                except socket.timeout:
                    break
            return res.decode('ascii', errors='replace')
        except Exception as e:
            print(f"Comm error: {e}")
            return ""

    def read_mem(self, addr, length):
        """Halt, read memory, resume"""
        # 1. Interrupt (Ctrl+C)
        self.send_raw(b"\x03")
        time.sleep(0.05)
        
        # Flush any stop reply
        try:
            self.sock.setblocking(False)
            self.sock.recv(1024)
        except:
            pass
        self.sock.setblocking(True)
        self.sock.settimeout(2.0)

        # 2. Read memory
        cmd = f"m{addr:x},{length:x}"
        resp = self.send_command(cmd)
        
        # Parse response: $data#XX
        data = ""
        if '$' in resp:
            data = resp.split('$')[1].split('#')[0]

        # 3. Resume
        self.send_command("c")
        
        return data

    def hex_to_ascii(self, hex_str):
        try:
            return bytes.fromhex(hex_str).decode('ascii', errors='replace')
        except:
            return "<BAD>"

    def loop(self, iterations=50):
        """Poll RAM in a loop"""
        print(f"Monitoring RAM for {iterations} samples...")
        for i in range(iterations):
            try:
                # Read scoreStr (16 bytes)
                str_hex = self.read_mem(ADDR_SCORE_STR, 16)
                score_str = self.hex_to_ascii(str_hex)

                # Read game.score (4 bytes, Big Endian)
                score_hex = self.read_mem(ADDR_GAME_SCORE, 4)
                score_val = int(score_hex, 16) if score_hex else -1

                # Read HP (2 bytes)
                hp_hex = self.read_mem(ADDR_PLAYER_HP, 2)
                hp_val = int(hp_hex, 16) if hp_hex else -1

                print(f"[{i+1:03d}] Score={score_val:06d} HP={hp_val:03d} Buf='{score_str}'")
                
                time.sleep(0.2)
                
            except KeyboardInterrupt:
                print("Stopped by user.")
                break
            except Exception as e:
                print(f"Error: {e}")
                break
        print("Done.")

    def close(self):
        if self.sock:
            try:
                self.send_command("k")
            except:
                pass
            self.sock.close()

if __name__ == "__main__":
    mon = BlastEmMonitor()
    if mon.connect():
        # Resume first (BlastEm starts paused with -D)
        print("Resuming emulation...")
        mon.send_command("c")
        time.sleep(2)  # Let game boot
        mon.loop()
        mon.close()
