# Mesen Quick Debug Guide - Step by Step

## Part 1: Basic Memory Viewer (Easiest Method)

### Step 1: Open Memory Viewer
1. Load your ROM in Mesen
2. Click **Debug** menu at the top
3. Click **Memory Tools**
4. Click **Memory Viewer**

A window will open showing hex values.

### Step 2: Look at Zero Page Memory
In the Memory Viewer window:
1. At the top, there's a dropdown that says "CPU Memory"
2. Make sure "CPU Memory" is selected
3. In the **"Go To"** box (usually at the bottom), type: `0000`
4. Press Enter

You'll now see memory starting at address $0000.

### Step 3: What You're Looking At
The memory viewer shows:
- **Left column**: Memory addresses (0000, 0010, 0020, etc.)
- **Middle**: Hex values (the actual data at those addresses)
- **Right**: ASCII representation (ignore this for now)

### Step 4: Find Our Key Variables
Look at these specific addresses:

```
Address | What It Is           | What You Should See
--------|----------------------|--------------------
0000    | temp1                | Could be anything
0001    | temp2                | Could be anything
0002    | temp3                | Could be anything
0003    | temp4                | Could be anything
0004    | frame_counter        | Should be changing!
0005    | nmi_complete         | Should be 00 or 01, toggling
0010    | scroll_x             | Should be 00
0011    | scroll_y             | Should be 00
0012    | ppu_ctrl_shadow      | Should be 90 (hex)
```

### Step 5: Watch for Changes
1. Let the game run (press F5 or click Continue if paused)
2. Watch address **0004** and **0005**
3. **If they're changing**: ✅ NMI is working!
4. **If they stay at 00**: ❌ NMI is NOT firing

## Part 2: Check If NMI Is Enabled

### Step 1: Open PPU Viewer
1. Click **Debug** menu
2. Click **PPU Viewer**

### Step 2: Check Current State
Look at the window - you'll see several tabs:
- **Palette**: Shows the color palettes
- **Nametable**: Shows the background tiles
- **CHR Viewer**: Shows the sprite graphics
- **Sprite List**: Shows active sprites

### Step 3: Check Palettes
1. Click the **Palette** tab
2. **Good sign**: You see actual colors (not all black)
3. **Bad sign**: Everything is black

### Step 4: Check CHR Graphics
1. Click the **CHR Viewer** tab
2. Look at the left side (Pattern Table 0)
3. **Good sign**: You see some tile graphics/patterns
4. **Bad sign**: Everything is empty/black

## Part 3: Simple Screenshot Method

If the above is confusing, just take screenshots!

### What to Screenshot:
1. **Memory Viewer** showing addresses 0000-0020
   - Debug > Memory Tools > Memory Viewer
   - Type "0000" in Go To box
   - Take screenshot

2. **PPU Palette Viewer**
   - Debug > PPU Viewer > Palette tab
   - Take screenshot

3. **CPU Trace** (last 50 lines)
   - Debug > Debugger
   - Let it run a bit
   - Scroll to bottom
   - Take screenshot

Send me these 3 screenshots and I can diagnose the issue!

## Part 4: Super Simple Test

### Easiest Way to Check NMI:

1. **Open Debugger**:
   - Debug > Debugger

2. **Look at the bottom pane** (Execution Log)
   - You'll see lines like: `C000  LDA $05`
   - Let it run for 1 second
   - **Is the address changing?** (C000, C010, C020, etc. moving around)
   - **Or stuck?** (Same address repeating forever like C053, C055, C053, C055...)

3. **If stuck at two addresses repeating**:
   - That's the infinite loop we saw!
   - NMI is not firing

4. **If addresses are changing all over**:
   - NMI is working!
   - Code is running normally

## What to Tell Me

You don't need to understand it all - just tell me:

**Option A - Simple Description:**
- "Stuck at two addresses repeating"
- "Addresses are changing"
- "Screen is black"
- "Screen has colors but no sprite"

**Option B - Screenshots:**
Just send screenshots of:
1. The Debugger window (execution log at bottom)
2. Memory Viewer showing 0000-0020
3. PPU Viewer palette tab

**Option C - Copy Last Lines:**
From the Debugger window, copy and paste the last 20-30 lines of the execution log (like you did before - that was perfect!)

## Quick Reference Card

### Address $0005 (nmi_complete)
- **Should be**: Toggling between 00 and 01
- **If stuck at 00**: NMI not firing ❌
- **If changing**: NMI working ✅

### Address $0012 (ppu_ctrl_shadow)
- **Should be**: 90 (hex)
- **If 00**: Problem! NMI won't fire ❌
- **If 90**: Correct ✅

### Screen Behavior
- **Black screen + stuck loop**: NMI not firing
- **Black screen + code running**: Graphics not loaded
- **Sprite visible**: Everything working! ✅

## Don't Worry!

You don't need to understand all the technical details. Just:
1. Open Memory Viewer
2. Type "0000" in Go To
3. Look at address 0005
4. Tell me if the number is changing or not

That's enough for me to help you!

---

## TROUBLESHOOTING: $05 Is Zero (NMI Not Firing)

If you found that $05 stays at zero, here's what to check:

### Check 1: Is $12 Also Zero?
Look at address $0012 in the memory viewer.
- **If it's 00**: The ppu_ctrl_shadow wasn't initialized!
- **If it's 90**: PPU_CTRL is set correctly, but NMI still isn't firing

### Check 2: What Does PPU Register Show?
In Mesen, you can check the actual PPU registers:
1. Debug > **Event Viewer**
2. Or check in the PPU Viewer window
3. Look for "PPU Control" or "$2000"
4. Should have bit 7 set (value >= $80)

### Most Likely Cause
The NMI enable bit in PPU_CTRL ($2000) is not set, or is being cleared by something.

### Common Fixes:
1. **ppu_ctrl_shadow not initialized** - We initialize it, but something might clear it
2. **NMI handler clears it** - The NMI writes back the shadow value, if shadow=0, NMI gets disabled
3. **Timing issue** - NMI gets enabled but immediately disabled

## Next Steps Based on $12 Value

### If $12 = 00 (Zero)
The shadow variable is zero, which means when NMI fires, it writes 00 to PPU_CTRL and disables itself!

**Fix**: Make sure ppu_ctrl_shadow is set BEFORE we enable NMI in entry.asm.

### If $12 = 90 (Correct Value)
The shadow is correct, but PPU_CTRL might not be getting the value.

**Check**: Use Mesen's Event Viewer to see writes to $2000 (PPU_CTRL)

### If $12 = Something Else
Tell me what value you see and I can diagnose it!

## Advanced: Set a Breakpoint on NMI

If you want to see if NMI ever fires:

1. **Open Debugger**: Debug > Debugger
2. **Find NMI address**: Look for "nmi:" in the code (should be around $C000-$C100)
3. **Set breakpoint**: Click in the left margin next to the first line of NMI handler
4. **Run**: Press F5
5. **Does it break?**
   - **YES**: NMI fires at least once
   - **NO**: NMI never fires at all

This tells us if NMI fired even once, or if it's completely disabled.
