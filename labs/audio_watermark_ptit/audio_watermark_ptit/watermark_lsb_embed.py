#!/usr/bin/env python3
"""
watermark_lsb_embed.py - Nhúng thủy vân bản quyền bằng LSB Replacement
=======================================================================
Bài thực hành: Thủy vân số bản quyền âm thanh (LSB vs Phase Coding)
B22DCAT196 - Vũ Lâm Minh (PTIT)
"""

import wave
import struct
import sys
import os

def doc_wav(ten_file):
    with wave.open(ten_file, 'rb') as f:
        params  = f.getparams()
        raw     = f.readframes(f.getnframes())

    sw  = params.sampwidth
    n   = len(raw) // sw
    if sw == 2:
        samples = list(struct.unpack(f'{n}h', raw))
    else:
        raise ValueError("Chỉ hỗ trợ 16-bit WAV.")
    return samples, params

def ghi_wav(ten_file, samples, params):
    raw = struct.pack(f'{len(samples)}h', *samples)
    with wave.open(ten_file, 'wb') as f:
        f.setparams(params)
        f.writeframes(raw)

def chuoi_sang_bits(chuoi):
    bits = []
    for ky_tu in chuoi:
        ma = ord(ky_tu)
        for vi_tri in range(7, -1, -1):
            bits.append((ma >> vi_tri) & 1)
    return bits

def main():
    cover_file = "cover.wav"
    output_file = "watermark_lsb.wav"
    secret_file = "secret.txt"

    if not os.path.exists(cover_file) or not os.path.exists(secret_file):
        print("[!] Không tìm thấy cover.wav hoặc secret.txt. Hãy chạy gen_cover.py trước.")
        sys.exit(1)

    with open(secret_file, 'r', encoding='utf-8') as f:
        watermark = f.read().strip()

    bits = chuoi_sang_bits(watermark)
    samples, params = doc_wav(cover_file)

    if len(bits) > len(samples):
        print("[!] Thủy vân quá dài so với nhạc.")
        sys.exit(1)

    # Nhúng LSB
    samples_moi = list(samples)
    for i, bit in enumerate(bits):
        samples_moi[i] = (samples_moi[i] & ~1) | bit

    ghi_wav(output_file, samples_moi, params)
    print("\n" + "=" * 60)
    print("  NHÚNG THỦY VÂN LSB - B22DCAT196")
    print("=" * 60)
    print(f"  Thủy vân    : {watermark}")
    print(f"  Số bit nhúng: {len(bits)} bits")
    print(f"  Đầu ra      : {output_file}")
    print("=" * 60 + "\n")

if __name__ == "__main__":
    main()
