# EPOCH - Resource Definitions
# Sega Genesis / SGDK

# =============================================================================
# PALETTES
# =============================================================================
# Palettes
PALETTE pal_player "sprites/hero_sheet_final.png"
PALETTE pal_tower  "sprites/tower_palette.png"
PALETTE pal_enemy  "sprites/enemy.png"

# Background palette
PALETTE pal_bg "tilesets/background.png"

# =============================================================================
# SPRITES
# =============================================================================
# Player sprite: 32x32 pixels (4x4 tiles), 8 frames
SPRITE spr_player "sprites/hero_sheet_final.png" 4 4 NONE 0

# Fenrir (Dog) sprite: 32x32 pixels (4x4 tiles)
SPRITE spr_fenrir "sprites/dog_sheet_32x32.png" 4 4 NONE 0
PALETTE pal_fenrir "sprites/dog_sheet_32x32.png"

# Enemy sprite (small): 16x16 pixels, 2x2 tiles
SPRITE spr_enemy_small "sprites/enemy_small.png" 2 2 NONE 0

# Enemy sprite (large): 32x32 pixels, 4x4 tiles
SPRITE spr_enemy "sprites/enemy.png" 4 4 NONE 0

# Projectile sprite: 8x8 pixels, 1x1 tile (small for performance)
SPRITE spr_projectile "sprites/projectile_8x8.png" 1 1 NONE 0

# Center Tower: 32x32 pixels, 4x4 tiles
SPRITE spr_tower  "sprites/tower.png"  8 8 NONE 0

# Bomb Pickup: 16x16 pixels, 2x2 tiles
SPRITE spr_bomb "sprites/bomb_pickup.png" 2 2 NONE 0

# Melee VFX: 16x16 pixels, 2x2 tiles
SPRITE spr_melee_vfx "sprites/melee_vfx.png" 2 2 NONE 0

# =============================================================================
# IMAGES (Background)
# =============================================================================
TILESET bg_tileset "tilesets/background.png" BEST
MAP map_background "tilesets/background.png" bg_tileset BEST

# Tower as background image (64x64, 8x8 tiles)
IMAGE img_tower "sprites/tower.png" BEST

# =============================================================================
# AUDIO (SFX)
# =============================================================================
WAV sfx_shoot "sfx/shoot.wav" XGM
WAV sfx_hit   "sfx/hit.wav"   XGM
WAV sfx_die   "sfx/die.wav"   XGM

# =============================================================================
# AUDIO (MUSIC) - Test background music
# =============================================================================
XGM bgm_test "music_test.vgm"
