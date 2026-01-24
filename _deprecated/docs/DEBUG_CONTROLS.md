# Debug Screen Controls

The ROM boots into a debug/test screen for testing all systems.

## Visual Test
- **D-Pad**: Move test sprite around the screen
- You should see a single sprite that moves with the D-pad

## Audio Tests
Press these buttons to test different sound effects:

- **A Button**: Play beep sound (Square Wave 1 - High pitch UI beep)
- **B Button**: Play hit sound (Noise Channel - Collision/damage effect)
- **START Button**: Play shoot sound (Square Wave 2 - Projectile firing)
- **SELECT Button**: Play pickup sound (Triangle Wave - Item collection)

## What to Expect

### Visual
- Black background (no background tiles yet, just palette color)
- Single sprite (8x8 pixel tile) that moves with D-pad
- Sprite should be visible and not flickering

### Audio
- Each button press should produce a distinct sound
- A = High-pitched beep (~440 Hz)
- B = Short noise burst (white noise)
- START = Mid-high square wave
- SELECT = Triangle wave (bass-like tone)

## Troubleshooting

If you see:
- **Blank screen**: Check that sprites.chr has valid tile data
- **No sprite movement**: Input system may not be working
- **No audio**: APU initialization may have failed
- **Green flash then black**: Rendering is enabled but no visible sprites/tiles

## Next Steps

Once basic testing works:
1. Add proper menu system with text rendering
2. Integrate FamiStudio sound engine for music
3. Add graphics tests (sprite animation, CHR bank switching)
4. Add collision detection tests
5. Transition to main game
