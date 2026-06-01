#!/usr/bin/env python3
"""
lsb_extract.py - Trích xuất dữ liệu bằng kỹ thuật LSB
"""
import wave
import struct

def extract_lsb(stego_file, text_length):
    with wave.open(stego_file, 'rb') as f:
        raw = f.readframes(f.getnframes())
        
    samples = list(struct.unpack(f"{len(raw)//2}h", raw))
    
    bits = []
    for i in range(text_length * 8):
        bits.append(str(samples[i] & 1))
        
    chars = []
    for i in range(0, len(bits), 8):
        byte = "".join(bits[i:i+8])
        chars.append(chr(int(byte, 2)))
        
    extracted_text = "".join(chars)
    print(f"[*] Dữ liệu trích xuất (LSB): {extracted_text}")

if __name__ == "__main__":
    # Cờ giả dài 28 ký tự (FLAG{fake_lsb_haha_you_lose})
    extract_lsb("stego_audio.wav", 28)
