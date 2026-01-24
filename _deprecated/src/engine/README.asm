; =============================================================================
; NEON SURVIVORS - Engine Architecture Overview
; =============================================================================
;
; This file documents the modular engine architecture designed for portability
; across NES, Sega Mega Drive/Genesis, and PC Engine/TurboGrafx-16.
;
; =============================================================================
; DIRECTORY STRUCTURE
; =============================================================================
;
; src/
; ├── engine/          <- PORTABLE: Platform-agnostic game systems
; │   ├── entity.asm   <- Entity management (create, destroy, update)
; │   ├── collision.asm<- AABB collision detection (pure math)
; │   ├── random.asm   <- PRNG (portable algorithm)
; │   └── math.asm     <- Fixed-point math, lookup tables
; │
; ├── game/            <- PORTABLE: Game-specific logic
; │   ├── player.asm   <- Player state machine
; │   ├── enemies.asm  <- Enemy behaviors
; │   ├── weapons.asm  <- Weapon definitions
; │   ├── pickups.asm  <- XP gems, items
; │   ├── levelup.asm  <- Upgrade tree logic
; │   └── waves.asm    <- Wave spawning rules
; │
; ├── platform/nes/    <- NES-SPECIFIC: Hardware abstraction
; │   ├── ppu.asm      <- PPU control, VRAM updates
; │   ├── apu.asm      <- Sound driver interface
; │   ├── mapper.asm   <- MMC3 bank switching
; │   └── input.asm    <- Controller reading
; │
; ├── data/            <- PORTABLE: Game data (can be converted)
; │   ├── enemies.asm  <- Enemy stat tables
; │   ├── weapons.asm  <- Weapon stat tables
; │   └── upgrades.asm <- Upgrade tree definitions
; │
; └── system/          <- NES-SPECIFIC: Core system
;     ├── reset.asm    <- Hardware init
;     └── nmi.asm      <- VBlank handler
;
; =============================================================================
; PORTABILITY GUIDELINES
; =============================================================================
;
; 1. ABSTRACTION LAYER
;    Game logic should call abstract routines, not hardware directly:
;    - draw_sprite(x, y, tile, palette) instead of OAM writes
;    - play_sound(sfx_id) instead of APU register writes
;    - read_input() returns a platform-independent button mask
;
; 2. COORDINATE SYSTEM
;    Use a consistent coordinate system across platforms:
;    - 256x240 logical resolution (NES native)
;    - MD/PCE: Scale or letterbox as needed
;    - Fixed-point for sub-pixel movement (8.8 format)
;
; 3. ENTITY STRUCTURE
;    Entities use a consistent memory layout:
;    entity:
;        .byte type      ; Entity type ID
;        .byte flags     ; Active, visible, etc.
;        .word x         ; 8.8 fixed-point X
;        .word y         ; 8.8 fixed-point Y
;        .byte vx        ; X velocity (signed)
;        .byte vy        ; Y velocity (signed)
;        .byte hp        ; Health points
;        .byte timer     ; General-purpose timer
;
; 4. LOOKUP TABLES
;    Use lookup tables instead of complex math:
;    - Sin/cos tables for circular motion
;    - Distance approximation tables
;    - Pre-calculated damage values
;
; 5. PLATFORM DEFINES
;    Use conditional assembly for platform differences:
;    .ifdef NES
;        MAX_SPRITES = 64
;    .endif
;    .ifdef GENESIS
;        MAX_SPRITES = 80
;    .endif
;    .ifdef PCE
;        MAX_SPRITES = 64
;    .endif
;
; =============================================================================
; PORTING CHECKLIST
; =============================================================================
;
; When porting to a new platform:
; [ ] Create platform/ directory with hardware abstraction
; [ ] Implement draw_sprite, draw_tile, clear_screen
; [ ] Implement play_sound, play_music, stop_music
; [ ] Implement read_input with consistent button mapping
; [ ] Convert CHR graphics to platform format
; [ ] Convert music to platform sound format
; [ ] Adjust entity limits for platform capabilities
; [ ] Test collision at new frame rate (MD=60Hz, PCE=60Hz)
;
; =============================================================================
