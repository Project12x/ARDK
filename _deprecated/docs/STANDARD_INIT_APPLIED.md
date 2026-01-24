# Standard NES Initialization Applied

## What Changed

I've completely rewritten the initialization code using **proven, standard NES patterns** that have been used successfully in thousands of homebrew games over 30+ years.

## Key Changes from Standard NES Patterns

### 1. **Standard Reset Sequence** (from Nerdy Nights, NESdev Wiki)
```asm
sei                 ; Disable IRQs
cld                 ; Disable decimal mode
ldx #$40
stx $4017          ; Disable APU frame IRQ
ldx #$FF
txs                ; Set up stack
```

### 2. **Proper PPU Warmup** (CRITICAL!)
```asm
; First VBlank wait
bit PPU_STATUS
: bit PPU_STATUS
  bpl :-

; Clear ALL RAM here

; Second VBlank wait - PPU is now stable
: bit PPU_STATUS
  bpl :-
```

The PPU needs **2 VBlank periods** to stabilize after power-on. This is documented in every NES programming guide.

### 3. **Complete RAM Clearing**
```asm
lda #0
tax
: sta $0000, x
  sta $0100, x
  sta $0200, x
  sta $0300, x
  sta $0400, x
  sta $0500, x
  sta $0600, x
  sta $0700, x
  inx
  bne :-
```

Uninitialized RAM can contain **random values** that cause unpredictable behavior.

### 4. **OAM Sprite Hiding**
```asm
ldx #0
lda #$FF
: sta $0200, x
  inx
  bne :-
```

Setting Y position to $FF hides all sprites initially.

### 5. **Palette Loading Before Rendering**
```asm
jsr load_palette    ; Load palette BEFORE enabling rendering
```

Palette must be loaded while rendering is OFF.

### 6. **Simple, Clear Main Loop**
```asm
main_loop:
:
    lda #0
    sta nmi_complete
@wait_nmi:
    lda nmi_complete
    beq @wait_nmi

    jsr Debug_Update
    jmp :-
```

This is the **standard NES game loop pattern** - wait for NMI, update game, repeat.

## What Was Removed

- ❌ MMC3 initialization (not needed for basic boot - can add later)
- ❌ Complex early initialization before VBlank stabilization
- ❌ Multiple separate init functions that could fail

## What This Fixes

### Problem: NMI Not Firing
**Root Cause**: Variables initialized before PPU stabilization, or RAM not cleared causing random values in critical flags.

**Fix**: Standard 2-VBlank wait, complete RAM clear, then initialize.

### Problem: Blank Screen
**Root Cause**: Palette not loaded, or loaded at wrong time.

**Fix**: Load palette AFTER PPU stabilization, BEFORE rendering enable.

### Problem: Infinite Loop
**Root Cause**: `nmi_complete` had random value or was never initialized.

**Fix**: Complete RAM clear ensures all variables start at $00.

## Testing Instructions

1. **Load ROM**: [build/neon_survivors.nes](build/neon_survivors.nes) in Mesen
2. **Expected Result**: Should boot immediately, no errors
3. **Check Memory**:
   - Debug → Memory Tools → Memory Viewer
   - Type "0000" in Go To
   - Address $05 (nmi_complete) should be **toggling between $00 and $01**
4. **Screen**: Should see palette color (not black)
5. **Sprite**: Should see sprite that moves with D-pad
6. **Audio**: A/B/START/SELECT should make sounds

## Why This Should Work

This initialization follows the **exact pattern** used in:
- Nerdy Nights tutorials (most popular NES programming tutorial)
- NESdev Wiki examples
- bunnyboy's "NES 101" guide
- Every successful homebrew game from 1990-2025

It's the **absolute minimal**, proven code to boot an NES program.

## Sources

Based on 30+ years of proven NES homebrew patterns:
- [Nerdy Nights](http://nerdy-nights.nes.science/)
- [NESdev Wiki - Init Code](https://www.nesdev.org/wiki/Init_code)
- [bbbradsmith/NES-ca65-example](https://github.com/bbbradsmith/NES-ca65-example)
- [Safyrus/NES-Boilerplate-Game](https://github.com/Safyrus/NES-Boilerplate-Game)

## Next Steps

Once this boots:
1. Add MMC3 initialization back (if needed for bank switching)
2. Expand Debug_Update with more features
3. Test audio system
4. Add actual game code

But first - **test this ROM** and confirm:
✅ ROM loads in Mesen without errors
✅ Address $05 toggles every frame
✅ Screen shows color
✅ Sprite visible and moves

This is the foundation everything else builds on.
