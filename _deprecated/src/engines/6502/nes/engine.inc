; =============================================================================
; NEON SURVIVORS - Engine Core Include
; Main include file for the modular NES engine
; =============================================================================

.ifndef ENGINE_INC
ENGINE_INC = 1

; -----------------------------------------------------------------------------
; Hardware Definitions
; -----------------------------------------------------------------------------
.include "nes.inc"

; -----------------------------------------------------------------------------
; Module Configuration
; Include game-specific module configuration (set by build system)
; This defines which modules and features are enabled for this build
; -----------------------------------------------------------------------------
.ifdef GAME_CONFIG_SURVIVOR
    .include "modules/config_survivor.inc"
.endif

.ifdef GAME_CONFIG_SHMUP
    .include "modules/config_shmup.inc"
.endif

.ifdef GAME_CONFIG_ZELDA
    .include "modules/config_zelda.inc"
.endif

.ifdef GAME_CONFIG_PLATFORMER
    .include "modules/config_platformer.inc"
.endif

; If no game config specified, use default (survivor-like)
.ifndef GAME_TYPE_ID
    .include "modules/config_survivor.inc"
.endif

; Include core module configuration system
.include "modules/module_config.inc"

; -----------------------------------------------------------------------------
; Module System Includes
; Each module exports its own interface
; -----------------------------------------------------------------------------

; Action Module (projectiles, spawner, powerups)
.ifdef MODULE_ACTION_ENABLED
    .include "modules/action/action.inc"
.endif

; Adventure Module (inventory, rooms, triggers) - Future
.ifdef MODULE_ADVENTURE_ENABLED
    ; .include "modules/adventure/adventure.inc"
.endif

; Platform Module (gravity, jumping, platforms) - Future
.ifdef MODULE_PLATFORM_ENABLED
    ; .include "modules/platform/platform.inc"
.endif

; -----------------------------------------------------------------------------
; Core Engine Systems
; These are always included regardless of modules
; -----------------------------------------------------------------------------
.global engine_init
.global nmi_handler
.global irq_handler

; Entity System
.global entity_init
.global entity_spawn
.global entity_update_all
.global entity_clear_all

; Collision System
.global collision_aabb
.global collision_point_rect
.global collision_circle

; Random Number Generator
.global random_init
.global random_get

; Input System
.global input_read
.globalzp buttons
.globalzp buttons_pressed

; -----------------------------------------------------------------------------
; Core Engine Constants
; -----------------------------------------------------------------------------
MAX_ENTITIES = 16           ; Maximum active entities (overridable by config)

; Entity structure offsets
ENTITY_X        = 0
ENTITY_Y        = 1
ENTITY_VX       = 2
ENTITY_VY       = 3
ENTITY_TYPE     = 4
ENTITY_HEALTH   = 5
ENTITY_FLAGS    = 6
ENTITY_STATE    = 7

; Entity flags
ENTITY_FLAG_ACTIVE      = $01
ENTITY_FLAG_PLAYER      = $02
ENTITY_FLAG_ENEMY       = $04
ENTITY_FLAG_COLLISION   = $08

; -----------------------------------------------------------------------------
; Zero Page Core Allocation
; $00-$0F: Engine core (16 bytes)
; $10-$1F: HAL/Hardware (16 bytes)
; $20-$3F: Core systems (32 bytes)
; $40+: Modules (as defined in module_config.inc)
; -----------------------------------------------------------------------------
.segment "ZEROPAGE"

; Engine core temps ($00-$0F)
; temp1-temp4, nmi_ready, frame_count, engine_flags are exported from entry.asm or zeropage.asm
.importzp temp1, temp2, temp3, temp4
.importzp nmi_ready, frame_count, engine_flags
; $00-$03: temp1-temp4
; $04: nmi_ready
; $05: frame_count
; $06: engine_flags
; $07-$0F reserved

; HAL/Hardware ($10-$1F)
; scroll_x/y are exported from entry.asm, ppu_ctrl_copy from zeropage.asm
.importzp scroll_x, scroll_y, ppu_ctrl_copy, ppu_mask_copy
; $10: scroll_x
; $11: scroll_y
; $12: ppu_ctrl_copy
; $13: ppu_mask_copy
; $14-$1F reserved

; Input ($20-$21)
; buttons/buttons_pressed are exported from input.asm
.importzp buttons, buttons_pressed
; $20: buttons
; $21: buttons_pressed

; Player state ($22-$2F)
; Exported from zeropage.asm
.importzp player_x, player_y, player_vx, player_vy
.importzp player_health, player_xp, player_coins, player_level, player_flags
; $22: player_x
; $23: player_y
; $24: player_vx
; $25: player_vy
; $26: player_health
; $27-$28: player_xp (16-bit)
; $29-$2A: player_coins (16-bit)
; $2B: player_level
; $2C: player_flags
; $2D-$2F reserved

; Entity system ($30-$3F)
; Exported from zeropage.asm
.importzp entity_spawn_x, entity_spawn_y, entity_spawn_type, entity_spawn_health
; $30-$33: entity spawn parameters

; Collision temps ($34-$37)
; Exported from zeropage.asm
.importzp collision_x, collision_y, collision_w, collision_h
; $34-$37: collision detection temps

; Rendering ($38-$3F)
; Exported from zeropage.asm
.importzp oam_index, render_flags
; $38: oam_index
; $39: render_flags
; $3A-$3F reserved

; Module zero page allocations start at $40 (defined in module_config.inc)

; -----------------------------------------------------------------------------
; Memory Map Reference
; -----------------------------------------------------------------------------
; $0000-$00FF: Zero Page
; $0100-$01FF: Stack
; $0200-$02FF: OAM Buffer (sprite data)
; $0300-$07FF: General Purpose RAM
;   $0300-$04FF: Entity pools
;   $0500-$05FF: Level/game data
;   $0600-$07FF: Module data

.endif ; ENGINE_INC
