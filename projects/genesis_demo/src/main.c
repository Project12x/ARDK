/**
 * Genesis Demo - Simple test project
 * Tests SGDK setup and basic sprite/input functionality
 */

#include <genesis.h>

// Simple sprite position
static s16 spriteX = 160;
static s16 spriteY = 112;
static Sprite* playerSprite = NULL;

int main(bool hardReset)
{
    // Initialize
    VDP_setScreenWidth320();
    SPR_init();

    // Display title
    VDP_drawText("GENESIS DEMO", 14, 3);
    VDP_drawText("Use D-Pad to move", 11, 5);
    VDP_drawText("SGDK Test Project", 11, 25);

    // TODO: Load sprite when assets are ready
    // playerSprite = SPR_addSprite(&spr_test, spriteX, spriteY, TILE_ATTR(PAL1, FALSE, FALSE, FALSE));

    // Main loop
    while (TRUE)
    {
        // Read input
        u16 buttons = JOY_readJoypad(JOY_1);

        // Move sprite
        if (buttons & BUTTON_LEFT)  spriteX -= 2;
        if (buttons & BUTTON_RIGHT) spriteX += 2;
        if (buttons & BUTTON_UP)    spriteY -= 2;
        if (buttons & BUTTON_DOWN)  spriteY += 2;

        // Clamp to screen
        if (spriteX < 0) spriteX = 0;
        if (spriteX > 320 - 32) spriteX = 320 - 32;
        if (spriteY < 0) spriteY = 0;
        if (spriteY > 224 - 32) spriteY = 224 - 32;

        // Update sprite position
        if (playerSprite != NULL)
        {
            SPR_setPosition(playerSprite, spriteX, spriteY);
        }

        // Display position
        char posText[32];
        sprintf(posText, "X:%3d Y:%3d", spriteX, spriteY);
        VDP_drawText(posText, 13, 14);

        // Update and wait for VBlank
        SPR_update();
        SYS_doVBlankProcess();
    }

    return 0;
}
