# Debug Checklist for NEON SURVIVORS

## How to Debug and Provide Info

### 1. CPU Trace (What You're Already Doing - Perfect!)
The CPU trace you provided is extremely helpful. To get it in Mesen:
- Debug > Debugger
- Run the game
- Let it run for a few seconds
- Copy the execution log

**What to look for**:
- Is the PC (program counter) stuck in a loop? (Same addresses repeating)
- What memory address is being read? (e.g., `LDA $05 = $00`)
- Is that address changing or always $00?

### 2. Memory Watch
In Mesen, set up memory watches for key variables:

**Zero Page Addresses to Watch**:
- `$00-$03` - temp1-temp4 (general purpose temps)
- `$04` - frame_counter (should increment each frame)
- `$05` - nmi_complete (should toggle 0→1 each frame)
- `$06` - engine_flags
- `$10` - scroll_x
- `$11` - scroll_y
- `$12` - ppu_ctrl_shadow (should be $90 or similar with NMI bit set)
- `$13` - ppu_mask_copy

**RAM Addresses to Watch**:
- `$0200-$0203` - First sprite (Y, Tile, Attr, X)

In Mesen:
- Debug > Memory Tools > Memory Viewer
- Right-click addresses → Add to Watch

### 3. PPU State Check
In Mesen:
- Debug > PPU Viewer

Check:
- **CHR Viewer**: Are there visible tiles in pattern table 0?
- **Palette Viewer**: Are the palettes loaded? Should see colors, not all black
- **Nametable Viewer**: Should be all black tiles (we haven't written any yet)
- **Sprite Viewer**: Should see one sprite entry

### 4. What to Report

For fastest debugging, provide:
1. **CPU Trace** (last 50-100 lines) - Shows if stuck in loop
2. **Zero Page Memory** (`$00-$20` in hex viewer) - Shows variable states
3. **PPU Status**:
   - Are palettes loaded? (take screenshot of palette viewer)
   - Are there visible tiles in CHR? (screenshot pattern table)
4. **Specific Behavior**: "Blank screen", "Green flash then black", "Sprite visible but not moving", etc.

## Current Expected Behavior

### What SHOULD Happen:
1. **Screen**: Black background (solid color from palette)
2. **Sprite**: One 8x8 pixel sprite at position (120, 100)
3. **Movement**: D-pad moves the sprite
4. **Audio**: A/B/START/SELECT play different sounds

### If You See Black Screen:
This could mean:
- NMI not firing (check $05 nmi_complete - is it changing?)
- PPU not enabled (check PPU registers)
- Sprites hidden (Y = $FF)
- CHR data is empty (check pattern tables)

### If You See "Green Flash":
- Palette is loaded (good!)
- But then something goes wrong
- Check CPU trace to see where it gets stuck

## Quick Mesen Debug Session

1. **Load ROM** in Mesen
2. **Open Debugger**: Debug > Debugger
3. **Set Breakpoint** at NMI handler:
   - In debugger, find address of `nmi` proc (should be around $C000-$C100)
   - Click in margin to set breakpoint
   - Run - does it hit? If NO, NMI never fires!
4. **Check NMI Enable**:
   - Memory viewer → $2000 (PPU_CTRL)
   - Should have bit 7 set (value >= $80)
5. **Watch Variables**:
   - Add $05 to watch
   - Step through code (F10)
   - Does $05 change to $01 after NMI?

## Common Issues and Fixes

### Issue: Stuck in Infinite Loop
**Check**: CPU trace shows same addresses repeating
**Fix**: Find what the loop is waiting for (usually a flag in ZP)

### Issue: NMI Never Fires
**Check**: PPU_CTRL bit 7 (NMI enable) is set
**Fix**: Verify `ppu_ctrl_shadow` is initialized before enabling NMI

### Issue: Black Screen But Code Runs
**Check**: PPU Viewer - are palettes/CHR loaded?
**Fix**: Graphics data might not be present or rendering disabled

### Issue: Sprite Not Visible
**Check**: OAM at $0200 - is Y position $FF? (hidden)
**Check**: Is sprite Y position on screen (< 240)?
**Fix**: Verify Debug_Update is running and setting sprite position

## Latest Build Status

**Build**: ✅ Successful (65,552 bytes)
**iNES Header**: ✅ Correct (2 PRG + 4 CHR banks)
**Zero-Page**: ✅ Fixed (unified variable allocation)
**PPU Shadow**: ✅ Fixed (ppu_ctrl_shadow now initialized)
**Audio**: ✅ Integrated (APU sound effects ready)

## Next Steps Based on Your Findings

**If NMI not firing**: We need to check why PPU_CTRL isn't enabling it
**If NMI firing but stuck**: Check what Debug_Update is doing
**If sprite not visible**: Check CHR data or sprite coordinates
**If audio not working**: APU needs to be checked with register viewer
