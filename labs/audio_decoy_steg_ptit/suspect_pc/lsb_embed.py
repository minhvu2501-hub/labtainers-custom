#!/usr/bin/env python3
"""
lsb_embed.py - Giấu cờ mồi nhử (Decoy Flag) bằng LSB
"""
import wave
import struct

def embed_lsb(cover_file, stego_file, secret_text):
    with wave.open(cover_file, 'rb') as f:
        params = f.getparams()
        raw = f.readframes(f.getnframes())
    
    samples = list(struct.unpack(f"{len(raw)//2}h", raw))
    
    bits = []
    for char in secret_text:
        bits.extend([int(b) for b in format(ord(char), '08b')])
        
    for i in range(len(bits)):
        samples[i] = (samples[i] & ~1) | bits[i]
        
    with wave.open(stego_file, 'w') as f:
        f.setparams(params)
        raw_stego = struct.pack(f"{len(samples)}h", *samples)
        f.writeframes(raw_stego)
        
    print(f"[+] Đã nhúng Cờ mồi (Decoy) bằng LSB vào {stego_file}")

if __name__ == "__main__":
    embed_lsb("cover.wav", "decoy.wav", "FLAG{fake_lsb_haha_you_lose}")
