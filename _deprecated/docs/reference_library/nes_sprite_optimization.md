# NES Sprite Optimization & Multiplexing

## The Challenge

The NES PPU is limited to:

- **64 Sprites** on screen.
- **8 Sprites** per scanline.

## Technique 1: OAM Cycling (Flicker)

To show more than 64 sprites, or more than 8 per line, you must "share" the hardware slots across frames.

### Standard Rotation

Pseudo-code for the NMI handler:

```
offset = (frame_counter * 13) % 64; // Prime number step
for (i = 0; i < 64; i++) {
   hardware_oam[i] = virtual_oam[(i + offset) % 64];
}
```

**Result**: Sprites flicker individually/randomly.

### Priority Slots (Standard)

Reserve slots 0-4 for the Player (no flicker). Cycle the rest.

- **Player**: OAM[0] - always drawn.
- **Enemies**: OAM[1-63] - cycled.

## Technique 2: "Recca" Style Multiplexing

*Summer Carnival '92: Recca* displays huge numbers of bullets.
**Secret**: It runs the game logic at 30fps (positions update every 2 frames) but renders at 60fps, alternating sprite sets PERFECTLY.

- **Frame A**: Draw Bullet Set 1.
- **Frame B**: Draw Bullet Set 2.
- **Result**: Bullets appear transparent (50% alpha) but perfectly consistent. No random "popping".

## Technique 3: Vertical Distribution

Since the limit is 8 per *line*:

- Use vertical formations for enemy waves.
- Sort your OAM by Y-coordinate. This ensures that if you hit the limit, the sprites at the *bottom* (or top) are the ones dropped, rather than random holes in the middle of a character.

## Technique 4: 8x16 Mode

Setting PPUCTRL ($2000) bit 5 enables 8x16 sprites.

- **Pros**: Double the pixels per sprite (less CPU time to push OAM).
- **Cons**: Can waste VRAM if sprites are small.
- **MMC3 Note**: Makes IRQ counting super reliable.
