target remote :8888
symbol-file projects/epoch/out/rom.out
set pagination off
continue
# Wait a bit (simulated by script? GDB continue runs until break)
# We need to break to inspect.
# Let's break main loop or just interrupt?
# "continue" will block.
# We should set a breakpoint at main or game_update
break game_update
continue
print playerData.currentHP
print game.score
print director.waveNumber
quit
