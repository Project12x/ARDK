; =============================================================================
; NEON SURVIVORS - Zero Page Variable Allocations
; This file contains the actual .res allocations for engine zero page variables
; =============================================================================

.include "nes.inc"

; -----------------------------------------------------------------------------
; Zero Page Allocations
; -----------------------------------------------------------------------------
.segment "ZEROPAGE"

; Engine core temps ($00-$0F)
.exportzp temp1, temp2, temp3, temp4
temp1:              .res 1      ; $00
temp2:              .res 1      ; $01
temp3:              .res 1      ; $02
temp4:              .res 1      ; $03

.exportzp frame_counter, nmi_complete, engine_flags
frame_counter:      .res 1      ; $04
nmi_complete:       .res 1      ; $05
engine_flags:       .res 1      ; $06
; $07-$0F reserved

; HAL/Hardware ($10-$1F)
.exportzp scroll_x, scroll_y, ppu_ctrl_shadow, ppu_mask_copy
scroll_x:           .res 1      ; $10
scroll_y:           .res 1      ; $11
ppu_ctrl_shadow:    .res 1      ; $12
ppu_mask_copy:      .res 1      ; $13
; $14-$1F reserved

; Input ($20-$21) - defined in input.asm

; Player state ($22-$2F)
.exportzp player_x, player_y, player_vx, player_vy
.exportzp player_health, player_xp, player_coins, player_level, player_flags
player_x:       .res 1      ; $22
player_y:       .res 1      ; $23
player_vx:      .res 1      ; $24
player_vy:      .res 1      ; $25
player_health:  .res 1      ; $26
player_xp:      .res 2      ; $27-$28 (16-bit)
player_coins:   .res 2      ; $29-$2A (16-bit)
player_level:   .res 1      ; $2B
player_flags:   .res 1      ; $2C
; $2D-$2F reserved

; Entity system ($30-$3F)
.exportzp entity_spawn_x, entity_spawn_y, entity_spawn_type, entity_spawn_health
entity_spawn_x:     .res 1  ; $30
entity_spawn_y:     .res 1  ; $31
entity_spawn_type:  .res 1  ; $32
entity_spawn_health:.res 1  ; $33

; Collision temps ($34-$37)
.exportzp collision_x, collision_y, collision_w, collision_h
collision_x:    .res 1      ; $34
collision_y:    .res 1      ; $35
collision_w:    .res 1      ; $36
collision_h:    .res 1      ; $37

; Rendering ($38-$3F)
.exportzp oam_index, render_flags
oam_index:      .res 1      ; $38 - Current OAM write index
render_flags:   .res 1      ; $39
; $3A-$3F reserved

; CHR Animation ($40-$47)
.exportzp chr_anim_timer, chr_anim_frame, chr_anim_speed, chr_anim_bank_base
chr_anim_timer:     .res 1  ; $40 - Frame counter for animation
chr_anim_frame:     .res 1  ; $41 - Current animation frame (0-7)
chr_anim_speed:     .res 1  ; $42 - Frames between animation updates
chr_anim_bank_base: .res 1  ; $43 - Base CHR bank for animated tiles
; $44-$47 reserved for animation expansion

; Module zero page allocations start at $48 (defined in module_config.inc)
