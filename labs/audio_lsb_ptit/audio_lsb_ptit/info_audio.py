#!/usr/bin/env python3
"""
info_audio.py - Hiển thị thông tin chi tiết của file âm thanh WAV
===================================================================
Bài thực hành: Kỹ thuật giấu tin trong âm thanh - LSB
PTIT - Học viện Công nghệ Bưu chính Viễn thông

Cách dùng:
    python3 info_audio.py <ten_file.wav>
    python3 info_audio.py cover.wav
"""

import wave
import struct
import math
import sys
import os
from collections import Counter


def doc_wav(ten_file):
    """Đọc file WAV, trả về danh sách sample và tham số"""
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
    """Tính entropy Shannon (bits/sample)"""
    dem = Counter(samples)
    n   = len(samples)
    return -sum((c / n) * math.log2(c / n) for c in dem.values() if c)


def phan_tich_lsb(samples):
    """Thống kê phân bố LSB"""
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
    dung_luong_max = len(samples) // 8

    print("\n" + "=" * 58)
    print("  THÔNG TIN FILE ÂM THANH WAV")
    print("=" * 58)
    print(f"  Tên file         : {os.path.basename(ten_file)}")
    print(f"  Kích thước       : {kich_thuoc:,} bytes ({kich_thuoc / 1024:.1f} KB)")
    print(f"  Tần số lấy mẫu   : {params.framerate:,} Hz")
    print(f"  Số kênh          : {params.nchannels} ({'mono' if params.nchannels == 1 else 'stereo'})")
    print(f"  Độ sâu bit       : {params.sampwidth * 8}-bit")
    print(f"  Tổng số sample   : {params.nframes:,}")
    print(f"  Thời lượng       : {thoi_luong:.2f} giây")
    print()
    print("  [Phân tích LSB]")
    print(f"  Bit=0            : {so_0:,}  ({so_0/len(samples)*100:.1f}%)")
    print(f"  Bit=1            : {so_1:,}  ({so_1/len(samples)*100:.1f}%)")
    print(f"  Chi-square LSB   : {chi_sq:.4f}", end="")
    if chi_sq < 100:
        print("  <-- Rất đều (có thể đã giấu tin)")
    elif chi_sq < 5000:
        print("  <-- Tương đối đều")
    else:
        print("  <-- Không đều (audio tự nhiên)")
    print()
    print(f"  [Entropy Shannon]: {entropy:.4f} bits/sample")
    print()
    print(f"  [Khả năng giấu tin tối đa (LSB 1-bit)]:")
    print(f"  --> {dung_luong_max:,} bytes  ({dung_luong_max // 1024} KB)")
    print("=" * 58 + "\n")


if __name__ == "__main__":
    main()
