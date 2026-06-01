#!/usr/bin/env python3
"""
gen_cover.py - Sinh file nhạc nền cover.wav (Sóng Sine 440Hz)
"""
import wave
import struct
import math

def main():
    sample_rate = 44100
    duration = 2
    num_samples = sample_rate * duration
    freq = 440.0
    
    with wave.open("cover.wav", "w") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(sample_rate)
        
        for i in range(num_samples):
            value = int(15000 * math.sin(2 * math.pi * freq * i / sample_rate))
            data = struct.pack('<h', value)
            f.writeframesraw(data)
            
    print("[+] Đã tạo file cover.wav thành công!")

if __name__ == "__main__":
    main()
