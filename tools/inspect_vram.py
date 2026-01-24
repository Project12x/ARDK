"""
BlastEm VRAM/VDP Remote Inspector
Uses GDB monitor commands to dump VDP registers, sprite list, and VRAM state.
"""
import socket
import time
import sys
import os

class VRAMInspector:
    def __init__(self, host='localhost', port=1234):
        self.host = host
        self.port = port
        self.sock = None

    def connect(self):
        retries = 10
        while retries > 0:
            try:
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.sock.settimeout(5.0)
                self.sock.connect((self.host, self.port))
                print(f"Connected to {self.host}:{self.port}")
                return True
            except Exception as e:
                print(f"Connection failed ({retries} left): {e}")
                time.sleep(1)
                retries -= 1
        return False

    def send_command(self, cmd):
        """Send a GDB RSP command"""
        chk = sum(ord(c) for c in cmd) % 256
        packet = f"${cmd}#{chk:02x}"
        try:
            self.sock.sendall(packet.encode('ascii'))
            # Read ACK
            self.sock.recv(1)
            # Read response
            res = b""
            while True:
                try:
                    chunk = self.sock.recv(4096)
                    if not chunk:
                        break
                    res += chunk
                    if b'#' in res and len(res.split(b'#')[-1]) >= 2:
                        break
                except socket.timeout:
                    break
            return res.decode('ascii', errors='replace')
        except Exception as e:
            print(f"Error: {e}")
            return ""

    def monitor_cmd(self, cmd):
        """Send a monitor command (qRcmd,hex-encoded-command)"""
        # GDB RSP: qRcmd,HEX
        hex_cmd = cmd.encode('ascii').hex()
        resp = self.send_command(f"qRcmd,{hex_cmd}")
        # Response is hex-encoded output
        if '$' in resp:
            data = resp.split('$')[1].split('#')[0]
            # Decode hex to ASCII
            try:
                return bytes.fromhex(data).decode('ascii', errors='replace')
            except:
                return data
        return resp

    def read_vram(self, addr, length):
        """
        Read VRAM directly.
        VRAM is memory-mapped but not directly accessible via standard 'm' command.
        We need to use monitor commands or read VDP registers to get VRAM content.
        BlastEm: 'monitor vram' might dump VRAM content.
        """
        return self.monitor_cmd("vram")

    def inspect(self, output_dir="artifacts/vram_dump"):
        """Run full VDP inspection"""
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Halt execution
        print("Halting emulation...")
        self.sock.sendall(b"\x03")
        time.sleep(0.1)
        # Flush stop reply
        try:
            self.sock.setblocking(False)
            self.sock.recv(4096)
        except:
            pass
        self.sock.setblocking(True)
        self.sock.settimeout(10.0)

        # 1. VDP Registers
        print("\n=== VDP Registers ===")
        vr_output = self.monitor_cmd("vr")
        print(vr_output if vr_output else "(No output from 'vr')")
        with open(os.path.join(output_dir, "vdp_registers.txt"), "w") as f:
            f.write(vr_output)

        # 2. Sprite List
        print("\n=== Sprite List ===")
        vs_output = self.monitor_cmd("vs")
        print(vs_output if vs_output else "(No output from 'vs')")
        with open(os.path.join(output_dir, "sprite_list.txt"), "w") as f:
            f.write(vs_output)

        # 3. VRAM Dump (if supported)
        print("\n=== VRAM Dump ===")
        vram_output = self.monitor_cmd("vram")
        if vram_output and len(vram_output) > 10:
            print(f"VRAM data received: {len(vram_output)} bytes")
            with open(os.path.join(output_dir, "vram_raw.txt"), "w") as f:
                f.write(vram_output)
        else:
            print("(No VRAM dump command available or empty response)")

        # 4. Planes info
        print("\n=== Planes ===")
        planes_output = self.monitor_cmd("planes")
        print(planes_output if planes_output else "(No output from 'planes')")
        with open(os.path.join(output_dir, "planes.txt"), "w") as f:
            f.write(planes_output)

        # 5. Help (list all available monitor commands)
        print("\n=== Available Monitor Commands ===")
        help_output = self.monitor_cmd("help")
        print(help_output if help_output else "(No help available)")
        with open(os.path.join(output_dir, "monitor_help.txt"), "w") as f:
            f.write(help_output)

        # Resume
        print("\nResuming emulation...")
        self.send_command("c")

        print(f"\nDump saved to: {output_dir}/")

    def close(self):
        if self.sock:
            try:
                self.send_command("k")
            except:
                pass
            self.sock.close()

if __name__ == "__main__":
    inspector = VRAMInspector()
    if inspector.connect():
        # Let game run for a few seconds first
        print("Resuming emulation for 3 seconds...")
        inspector.send_command("c")
        time.sleep(3)
        
        # Now inspect
        inspector.inspect()
        inspector.close()
    else:
        print("Failed to connect.")
        sys.exit(1)
