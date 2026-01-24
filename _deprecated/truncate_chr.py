
import os
path = r"projects\hal_demo\assets\bg_cyberpunk.chr"
with open(path, "rb") as f:
    data = f.read()

print(f"Original size: {len(data)}")
if len(data) > 4096:
    print("Truncating to 4096 bytes...")
    with open(path, "wb") as f:
        f.write(data[:4096])
else:
    print("Size ok.")
