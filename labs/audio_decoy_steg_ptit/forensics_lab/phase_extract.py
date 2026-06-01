#!/usr/bin/env python3
"""
phase_extract.py - Trích xuất dữ liệu bằng kỹ thuật Phase Coding
"""
import wave
import struct
import numpy as np

def extract_phase(stego_file, text_length):
    with wave.open(stego_file, 'rb') as f:
        raw = f.readframes(f.getnframes())
        
    samples = list(struct.unpack(f"{len(raw)//2}h", raw))
    
    N = 1024
    segment = np.array(samples[:N], dtype=np.float64)
    X = np.fft.fft(segment)
    
    phase = np.angle(X)
    
    bits = []
    for i in range(text_length * 8):
        k = i + 1
        if phase[k] > 0:
            bits.append("0")
        else:
            bits.append("1")
            
    chars = []
    for i in range(0, len(bits), 8):
        byte = "".join(bits[i:i+8])
        chars.append(chr(int(byte, 2)))
        
    extracted_text = "".join(chars)
    print(f"[*] Dữ liệu trích xuất (Phase Coding): {extracted_text}")

if __name__ == "__main__":
    # Cờ thật dài 37 ký tự (FLAG{phase_coding_is_the_true_secret})
    extract_phase("stego_audio.wav", 37)
