import os

def combine():
    try:
        # Load Player
        with open('gfx/converted/player/sprites.chr', 'rb') as f:
            player_data = f.read()
            
        # Load Enemy (Try Alt first, then Enemy, then Player Frame 1)
        enemy_data = None
        if os.path.exists('gfx/converted/enemy_alt/sprites.chr'):
            with open('gfx/converted/enemy_alt/sprites.chr', 'rb') as f:
                 enemy_data = f.read()
                 print("Using Enemy Alt sprites.")
        elif os.path.exists('gfx/converted/enemy/sprites.chr') and os.path.getsize('gfx/converted/enemy/sprites.chr') > 0:
            with open('gfx/converted/enemy/sprites.chr', 'rb') as f:
                 enemy_data = f.read()
        
        # Load Projectile
        with open('gfx/converted/projectile/sprites.chr', 'rb') as f:
            proj_data = f.read()
        
        # Load Background (and truncate)
        bg_path = 'gfx/converted/background/background.chr'
        # Check original location? Pipeline outputs to provided dir.
        # I previously ran BG pipeline... where to?
        # I need to check where current background.chr is.
        # It's in projects/hal_demo/assets/processed/background.chr usually.
        # I'll preserve it.
        
        # Extract Frames (32x32 = 256 bytes)
        player_frame = player_data[0:256]
        
        if enemy_data and len(enemy_data) >= 256:
             enemy_frame = enemy_data[0:256]
        else:
             print("Warning: No valid enemy data. Using Player Frame 1.")
             if len(player_data) >= 512:
                 enemy_frame = player_data[256:512]
             else:
                 enemy_frame = player_data[0:256]

        bullet_frame = proj_data[0:256]

        print(f"Player Frame Sum: {sum(player_frame)}")
        print(f"Enemy Frame Sum: {sum(enemy_frame)}")
        print(f"Bullet Frame Sum: {sum(bullet_frame)}")

        # Create Sprites CHR (8KB)
        final_chr = bytearray(8192)
        final_chr[0:256] = player_frame   # $00
        final_chr[256:512] = enemy_frame  # $10
        final_chr[512:768] = bullet_frame # $20
        
        # Save Sprites
        os.makedirs('projects/hal_demo/assets/processed', exist_ok=True)
        out_path = 'projects/hal_demo/assets/processed/sprites.chr'
        with open(out_path, 'wb') as f:
            f.write(final_chr)
        print(f"Combined sprites.chr created at {out_path}")
        
        # Fix Background CHR
        # Assume source is 'projects/hal_demo/assets/processed/background.chr' (or verify)
        # Assuming current file exists there.
        bg_target = 'projects/hal_demo/assets/processed/background.chr'
        if os.path.exists(bg_target):
            with open(bg_target, 'rb') as f:
                bg_data = f.read()
            if len(bg_data) > 4096:
                print(f"Truncating Background: {len(bg_data)} -> 4096 bytes.")
                bg_fixed = bg_data[0:4096]
                with open(bg_target, 'wb') as f:
                     f.write(bg_fixed)
            else:
                print("Background size OK.")
        
    except FileNotFoundError as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    combine()
