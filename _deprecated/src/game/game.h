/**
 * =============================================================================
 * NEON SURVIVORS - Game Header
 * =============================================================================
 * Platform-agnostic game API. Includes only HAL and common engine code.
 * NO platform-specific includes here!
 *
 * This file is the game's interface to the engine and HAL layers.
 * =============================================================================
 */

#ifndef GAME_H
#define GAME_H

/* HAL provides platform abstraction */
#include "../hal/hal.h"

/* Common engine provides entity system, state machine, collision */
#include "../engines/common/common.h"

/* =============================================================================
 * Game Configuration
 * =========================================================================== */

/* Game title (shown on title screen) */
#define GAME_TITLE      "NEON SURVIVORS"
#define GAME_VERSION    "0.1.0"

/* Sprite sizes */
#define PLAYER_WIDTH    32
#define PLAYER_HEIGHT   32
#define ENEMY_WIDTH     16
#define ENEMY_HEIGHT    16
#define PROJECTILE_SIZE 8
#define PICKUP_SIZE     8

/* Gameplay constants */
#define PLAYER_SPEED        2
#define ENEMY_BASE_SPEED    1
#define PROJECTILE_SPEED    4
#define PICKUP_MAGNET_RANGE 32

/* XP thresholds for leveling */
#define XP_LEVEL_1      0
#define XP_LEVEL_2      100
#define XP_LEVEL_3      300
#define XP_LEVEL_4      600
#define XP_LEVEL_5      1000

/* =============================================================================
 * Entity Types (game-specific subtypes)
 * =========================================================================== */

/* Player subtypes (0x10-0x1F) */
#define ENT_PLAYER          (ENT_CAT_PLAYER | 0x00)

/* Enemy subtypes (0x20-0x2F) */
#define ENT_ENEMY_BASIC     (ENT_CAT_ENEMY | 0x00)
#define ENT_ENEMY_FAST      (ENT_CAT_ENEMY | 0x01)
#define ENT_ENEMY_TANK      (ENT_CAT_ENEMY | 0x02)
#define ENT_ENEMY_BOSS      (ENT_CAT_ENEMY | 0x0F)

/* Projectile subtypes (0x30-0x3F) */
#define ENT_PROJ_LASER      (ENT_CAT_PROJECTILE | 0x00)
#define ENT_PROJ_SPREAD     (ENT_CAT_PROJECTILE | 0x01)
#define ENT_PROJ_ORBIT      (ENT_CAT_PROJECTILE | 0x02)
#define ENT_PROJ_ENEMY      (ENT_CAT_PROJECTILE | 0x0F)

/* Pickup subtypes (0x40-0x4F) */
#define ENT_PICKUP_XP       (ENT_CAT_PICKUP | 0x00)
#define ENT_PICKUP_HEALTH   (ENT_CAT_PICKUP | 0x01)
#define ENT_PICKUP_BOMB     (ENT_CAT_PICKUP | 0x02)

/* Effect subtypes (0x50-0x5F) */
#define ENT_EFFECT_EXPLODE  (ENT_CAT_EFFECT | 0x00)
#define ENT_EFFECT_HIT      (ENT_CAT_EFFECT | 0x01)
#define ENT_EFFECT_LEVELUP  (ENT_CAT_EFFECT | 0x02)

/* =============================================================================
 * Game State
 * =========================================================================== */

/* Player data (beyond entity struct) */
typedef struct {
    entity_t*   entity;         /* Pointer to player entity */
    u16         xp;             /* Experience points */
    u8          level;          /* Current level */
    u8          max_health;     /* Maximum health */
    u8          weapon_type;    /* Current weapon */
    u8          weapon_level;   /* Weapon upgrade level */
    u8          fire_cooldown;  /* Frames until can fire again */
    u8          invuln_timer;   /* Invulnerability frames remaining */
} player_state_t;

/* Game globals */
typedef struct {
    entity_manager_t    entities;
    state_machine_t     state;
    player_state_t      player;
    u16                 score;
    u16                 wave;
    u16                 wave_timer;
    u8                  enemies_remaining;
    u8                  pause_selected;
} game_state_t;

/* Global game state (defined in main.c) */
extern game_state_t g_game;

/* =============================================================================
 * Game Functions
 * =========================================================================== */

/* Initialization */
void game_init(void);

/* State handlers */
void state_title_enter(void);
void state_title_update(void);
void state_title_exit(void);

void state_playing_enter(void);
void state_playing_update(void);
void state_playing_exit(void);

void state_paused_enter(void);
void state_paused_update(void);
void state_paused_exit(void);

void state_levelup_enter(void);
void state_levelup_update(void);
void state_levelup_exit(void);

void state_gameover_enter(void);
void state_gameover_update(void);
void state_gameover_exit(void);

/* Player */
void player_init(void);
void player_update(void);
void player_fire(void);
void player_take_damage(u8 amount);
void player_gain_xp(u16 amount);

/* Enemies */
void enemy_spawn(u8 type, fixed8_8 x, fixed8_8 y);
void enemy_update_all(void);
void enemy_on_death(entity_t* enemy);

/* Projectiles */
void projectile_spawn(u8 type, fixed8_8 x, fixed8_8 y, i8 vx, i8 vy);
void projectile_update_all(void);

/* Pickups */
void pickup_spawn(u8 type, fixed8_8 x, fixed8_8 y);
void pickup_update_all(void);

/* Effects */
void effect_spawn(u8 type, fixed8_8 x, fixed8_8 y);
void effect_update_all(void);

/* Collision handlers */
void on_player_enemy_collision(entity_t* player, entity_t* enemy);
void on_projectile_enemy_collision(entity_t* proj, entity_t* enemy);
void on_player_pickup_collision(entity_t* player, entity_t* pickup);

/* Wave/spawning */
void wave_init(void);
void wave_update(void);
void wave_spawn_enemies(u8 count, u8 type);

/* UI/Rendering */
void ui_draw_hud(void);
void ui_draw_levelup_menu(void);

/* =============================================================================
 * Platform Hot Paths (Assembly Overrides)
 * =========================================================================== */

/* These functions have platform-specific assembly implementations
 * in game/src/hotpaths/ for critical performance sections.
 *
 * The C versions in this file serve as fallbacks and documentation.
 */

#ifdef USE_HOTPATH_ASM
    /* Defined in nes_hotpaths.asm or genesis_hotpaths.asm */
    extern void hotpath_entity_update(entity_manager_t* em);
    extern void hotpath_collision_check(entity_manager_t* em);
    extern void hotpath_render_sprites(entity_manager_t* em);
#else
    /* Use C implementations */
    #define hotpath_entity_update(em)   entity_update_all(em)
    #define hotpath_collision_check(em) /* use collision_check_types */
    #define hotpath_render_sprites(em)  /* use hal_sprite_set */
#endif

#endif /* GAME_H */
