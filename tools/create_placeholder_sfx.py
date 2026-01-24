
import wave
import math
import struct
import random
import os

def create_wav(filename, duration, type='noise', freq=440):
    sample_rate = 14000 # SGDK standard
    num_samples = int(duration * sample_rate)
    
    with wave.open(filename, 'w') as wav_file:
        wav_file.setnchannels(1) # Mono
        wav_file.setsampwidth(1) # 8-bit
        wav_file.setframerate(sample_rate)
        
        data = bytearray()
        
        for i in range(num_samples):
            t = float(i) / sample_rate
            val = 128
            
            if type == 'noise':
                # White noise with decay
                amp = 1.0 - (t / duration)
                val = 128 + int((random.random() * 255 - 127) * amp)
            elif type == 'sine':
                # Sine wave
                val = 128 + int(127 * math.sin(2 * math.pi * freq * t))
            elif type == 'slide':
                # Slide down
                f = freq * (1.0 - (t / duration))
                val = 128 + int(127 * math.sin(2 * math.pi * f * t))
                
            # Clamp
            val = max(0, min(255, val))
            data.append(val)
            
        wav_file.writeframes(data)
    print(f"Created {filename}")

os.makedirs('projects/epoch/res/sfx', exist_ok=True)

# Shoot: Short noise burst
create_wav('projects/epoch/res/sfx/shoot.wav', 0.1, 'noise')

# Hit: Short low thud
create_wav('projects/epoch/res/sfx/hit.wav', 0.1, 'noise')

# Die: Longer slide down
create_wav('projects/epoch/res/sfx/die.wav', 0.5, 'slide', 200)
