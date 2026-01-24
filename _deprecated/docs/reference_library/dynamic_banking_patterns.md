# Dynamic CHR Banking Patterns (MMC3)

## Concept

The NES has only 8KB of CHR RAM/ROM visible at once. MMC3 allows you to swap parts of this instantly.

## Pattern 1: The "Status Bar" Split

Most games need a static HUD.

1. **Top of Frame**: Load "Level Graphics" into BG Banks.
2. **Scanline IRQ (e.g., line 192)**: Trigger IRQ.
3. **IRQ Handler**:
    - Write to $8000/$8001 to swap "Level Graphics" out and "HUD Graphics" in.
    - Set scroll to 0,0.
    - Result: HUD appears at bottom using completely different tiles.

## Pattern 2: Animation Banking (Kirby/Batman)

Instead of updating the Name Table (slow) or modifying CHR RAM (slow), just swap the ROM bank!

- **Setup**: Store animation frames in consecutive 1KB banks (Bank 10, 11, 12...).
- **Frame 1**: Map Bank 10 to slot R2.
- **Frame 2**: Map Bank 11 to slot R2.
- **Frame 3**: Map Bank 12 to slot R2.
- **Cost**: Uses almost 0 CPU time.
- **Requirement**: You must organize your assets so animations align to 1KB (64 tile) boundaries.

## Pattern 3: Enemy Slotting

Allocate your 4x 1KB sprite banks (R2, R3, R4, R5) as "slots".

- **R2**: Player (Always loaded).
- **R3**: Enemy Slot A.
- **R4**: Enemy Slot B.
- **R5**: Universal Pickups / Projectiles.

When spawning an enemy:

1. Find a free slot (e.g., Slot A).
2. Load that enemy's Bank ID into R3.
3. Draw that enemy using tile indices $80-$BF (which correspond to R3).

**Conflict**: If you need to draw a Skeleton (Slot A) and a Goblin (Slot A) on the same screen, you can't (without flickering). You must spawn Skeletons only in Slot A and Goblins only in Slot B, or cycle them frame-by-frame.
