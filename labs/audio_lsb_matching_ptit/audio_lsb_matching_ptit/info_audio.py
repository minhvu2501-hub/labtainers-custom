#!/usr/bin/env python3
"""
info_audio.py - Phân tích cấu trúc và đặc trưng thống kê của file âm thanh WAV
========================================================================
Bài thực hành: Kỹ thuật giấu tin LSB Matching & Steganalysis
B22DCAT196 - Vũ Lâm Minh (PTIT)
"""

import wave
import struct
import math
import sys
import os
from collections import Counter

def doc_wav(ten_file):
    with wave.open(ten_file, 'rb') as f:
        params = f.getparams()
        raw = f.readframes(f.getnframes())

    sw = params.sampwidth
    n  = len(raw) // sw
    fmt = {1: f'{n}B', 2: f'{n}h', 4: f'{n}i'}.get(sw)
    if fmt is None:
        raise ValueError(f"Không hỗ trợ sample width: {sw} bytes")

    samples = list(struct.unpack(fmt, raw))
    return samples, params

def tinh_entropy(samples):
    dem = Counter(samples)
    n   = len(samples)
    return -sum((c / n) * math.log2(c / n) for c in dem.values() if c)

def phan_tich_lsb(samples):
    lsbs  = [s & 1 for s in samples]
    n     = len(lsbs)
    so_0  = lsbs.count(0)
    so_1  = lsbs.count(1)
    ki_vong = n / 2
    chi_sq  = ((so_0 - ki_vong) ** 2 + (so_1 - ki_vong) ** 2) / ki_vong
    return so_0, so_1, chi_sq

def main():
    if len(sys.argv) < 2:
        print("Cách dùng: python3 info_audio.py <ten_file.wav>")
        print("Ví dụ    : python3 info_audio.py cover.wav")
        sys.exit(1)

    ten_file = sys.argv[1]
    if not os.path.exists(ten_file):
        print(f"[!] Không tìm thấy file: {ten_file}")
        sys.exit(1)

    samples, params = doc_wav(ten_file)
    kich_thuoc = os.path.getsize(ten_file)
    thoi_luong = params.nframes / params.framerate
    so_0, so_1, chi_sq = phan_tich_lsb(samples)
    entropy = tinh_entropy(samples)
    max_capacity = len(samples) // 8

    print("\n" + "=" * 60)
    print("  PHÂN TÍCH FILE ÂM THANH WAV - B22DCAT196")
    print("=" * 60)
    print(f"  Tên file         : {os.path.basename(ten_file)}")
    print(f"  Kích thước       : {kich_thuoc:,} bytes")
    print(f"  Tần số lấy mẫu   : {params.framerate:,} Hz")
    print(f"  Độ sâu bit       : {params.sampwidth * 8}-bit")
    print(f"  Tổng số sample   : {params.nframes:,}")
    print(f"  Thời lượng       : {thoi_luong:.2f} giây")
    print()
    print("  [Thống kê phân bố LSB]")
    print(f"  Số bit 0         : {so_0:,} ({so_0/len(samples)*100:.2f}%)")
    print(f"  Số bit 1         : {so_1:,} ({so_1/len(samples)*100:.2f}%)")
    print(f"  Chi-Square LSB   : {chi_sq:.4f}")
    print(f"  Entropy Shannon  : {entropy:.4f} bits/sample")
    print(f"  Khả năng giấu tin: {max_capacity:,} bytes")
    print("=" * 60 + "\n")

if __name__ == "__main__":
    main()
