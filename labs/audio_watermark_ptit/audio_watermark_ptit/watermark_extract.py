#!/usr/bin/env python3
"""
watermark_extract.py - Trích xuất thủy vân bằng LSB và Phase Coding
===================================================================
Bài thực hành: Thủy vân số bản quyền âm thanh (LSB vs Phase Coding)
B22DCAT196 - Vũ Lâm Minh (PTIT)
"""

import wave
import struct
import math
import sys
import os
import argparse

KICH_THUOC_DOAN = 1024

def dft(x):
    N = len(x)
    X = []
    for k in range(N):
        re = sum(x[n] * math.cos(2 * math.pi * k * n / N) for n in range(N))
        im = sum(-x[n] * math.sin(2 * math.pi * k * n / N) for n in range(N))
        X.append((re, im))
    return X

def doc_wav(ten_file):
    with wave.open(ten_file, 'rb') as f:
        params = f.getparams()
        raw    = f.readframes(f.getnframes())
    sw = params.sampwidth
    n  = len(raw) // sw
    if sw == 2:
        samples = list(struct.unpack(f'{n}h', raw))
    else:
        raise ValueError("Chỉ hỗ trợ WAV 16-bit.")
    return samples

def bits_sang_chuoi(bits):
    chuoi = ""
    for i in range(0, len(bits), 8):
        byte_bits = bits[i:i+8]
        if len(byte_bits) < 8:
            break
        val = 0
        for b in byte_bits:
            val = (val << 1) | b
        # Chỉ lấy ký tự in được (printable ASCII) để tránh lỗi hiển thị khi bị lỗi bit
        if 32 <= val <= 126:
            chuoi += chr(val)
        else:
            chuoi += "?"
    return chuoi

def main():
    parser = argparse.ArgumentParser(description="Trích xuất thủy vân LSB hoặc Phase")
    parser.add_argument('-i', '--input', required=True, help='File WAV cần trích xuất')
    parser.add_argument('-m', '--method', choices=['lsb', 'phase'], required=True, help='Phương pháp trích xuất')
    parser.add_argument('-l', '--length', type=int, default=176, help='Số lượng bit cần trích xuất (mặc định: 176 bits = 22 ký tự)')
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"[!] Không tìm thấy file: {args.input}")
        sys.exit(1)

    samples = doc_wav(args.input)
    bits = []

    if args.method == 'lsb':
        # Trích xuất LSB
        for i in range(args.length):
            bits.append(samples[i] & 1)
    else:
        # Trích xuất Phase Coding (DFT phân đoạn đầu tiên)
        doan_0 = samples[:KICH_THUOC_DOAN]
        X0 = dft(doan_0)
        for idx in range(args.length):
            k = idx + 1
            re, im = X0[k]
            pha = math.atan2(im, re)
            # bit = 0 nếu pha > 0 (gần pi/2), bit = 1 nếu pha < 0 (gần -pi/2)
            bits.append(0 if pha > 0 else 1)

    text = bits_sang_chuoi(bits)
    print("\n" + "=" * 60)
    print(f"  TRÍCH XUẤT THỦY VÂN - PHƯƠNG PHÁP {args.method.upper()}")
    print("=" * 60)
    print(f"  File đầu vào: {args.input}")
    print(f"  Chuỗi ký tự trích xuất: {text}")
    print(f"  Dãy bit (10 bit đầu)  : {bits[:10]}")
    print("=" * 60 + "\n")

if __name__ == "__main__":
    main()
