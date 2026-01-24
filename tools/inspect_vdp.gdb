# Force architecture to avoid auto-detection issues
set architecture m68k
set tdesc filename none

# Connect to BlastEm
target remote :1234

# Load symbols
file projects/epoch/out/rom.out

# Break at main loop (safe point)
break main
continue

# Inspect
print "--- VDP STATE ---"
print 'src/main.c'::bgMap
print playerSprite
print "--- ENTITY STATE ---"
# Check the first enemy (Slot 0 is Player, 1-9 Reserved, 10+ Enemies)
print entities[10]

# Check BlastEm Monitor Capabilities
monitor help
monitor vram
monitor planes

quit
