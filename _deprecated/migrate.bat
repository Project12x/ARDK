@echo off
if not exist "src\engine\hal" mkdir "src\engine\hal"
if not exist "src\engine\utils" mkdir "src\engine\utils"
if not exist "src\engine\core" mkdir "src\engine\core"
if not exist "src\engine\external" mkdir "src\engine\external"
if not exist "src\game\src" mkdir "src\game\src"
if not exist "src\game\assets" mkdir "src\game\assets"

if exist "src\system\reset.asm" move "src\system\reset.asm" "src\engine\entry.asm"
if exist "src\system\nmi.asm" move "src\system\nmi.asm" "src\engine\hal\nmi.asm"
if exist "src\header.asm" move "src\header.asm" "src\engine\header.asm"
if exist "src\engine\gamepad.asm" move "src\engine\gamepad.asm" "src\engine\hal\input.asm"
if exist "src\engine\random.asm" move "src\engine\random.asm" "src\engine\utils\random.asm"
if exist "src\engine\collision.asm" move "src\engine\collision.asm" "src\engine\utils\collision.asm"
if exist "src\engine\entity.asm" move "src\engine\entity.asm" "src\engine\core\entity.asm"
if exist "src\main.asm" move "src\main.asm" "src\game\src\game_main.asm"
if exist "src\data\nes.inc" move "src\data\nes.inc" "src\engine\nes.inc"

if exist "src\system" rmdir "src\system"
