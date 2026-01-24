import struct

with open(r"projects/tech_demo_440/out/rom.bin", "rb") as f:
    data = f.read(256)

print("Vector Table Dump:")
for i in range(0, 64):
    offset = i * 4
    if offset + 4 > len(data): break
    val = struct.unpack(">I", data[offset:offset+4])[0]
    print(f"Vector {i}: 0x{val:08X} (Offset 0x{offset:X})")
