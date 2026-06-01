#!/usr/bin/env python3
"""
phase_embed.py - Giấu cờ thật (Real Flag) bằng Phase Coding lên file đã giấu LSB
"""
import wave
import struct
import numpy as np

def embed_phase(cover_file, stego_file, secret_text):
    with wave.open(cover_file, 'rb') as f:
        params = f.getparams()
        raw = f.readframes(f.getnframes())
        
    samples = list(struct.unpack(f"{len(raw)//2}h", raw))
    
    bits = []
    for char in secret_text:
        bits.extend([int(b) for b in format(ord(char), '08b')])
        
    N = 1024
    segment = np.array(samples[:N], dtype=np.float64)
    X = np.fft.fft(segment)
    
    mag = np.abs(X)
    phase = np.angle(X)
    
    for i in range(len(bits)):
        k = i + 1
        if bits[i] == 0:
            phase[k] = np.pi / 2
            phase[N - k] = -np.pi / 2
        else:
            phase[k] = -np.pi / 2
            phase[N - k] = np.pi / 2
            
    X_new = mag * np.exp(1j * phase)
    segment_new = np.fft.ifft(X_new).real
    
    for i in range(N):
        samples[i] = int(round(segment_new[i]))
        
    with wave.open(stego_file, 'w') as f:
        f.setparams(params)
        raw_stego = struct.pack(f"{len(samples)}h", *samples)
        f.writeframes(raw_stego)
        
    print(f"[+] Đã nhúng Cờ thật (Real Flag) bằng Phase Coding vào {stego_file}")

if __name__ == "__main__":
    embed_phase("decoy.wav", "stego_audio.wav", "FLAG{phase_coding_is_the_true_secret}")
