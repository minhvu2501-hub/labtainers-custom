#!/usr/bin/env python3
"""
compare.py - So sánh phổ biên độ (magnitude spectrum) của file cover và file stego
=================================================================================
Bài thực hành: Kỹ thuật giấu tin bằng mã hóa pha (Phase Coding)
PTIT - Học viện Công nghệ Bưu chính Viễn thông

Nguyên lý:
    Kỹ thuật mã hóa pha chỉ thay đổi pha (phase) của tín hiệu âm thanh
    nhưng giữ nguyên phổ biên độ (magnitude spectrum) của nó.
    Script này tính toán DFT của đoạn đầu tiên cho cả hai file và so sánh phổ biên độ.

Cách dùng:
    python3 compare.py -i cover.wav -s stego.wav -n 8
"""

import wave
import struct
import math
import sys
import os
import argparse


def dft(x):
    """Biến đổi Fourier rời rạc (DFT)"""
    N = len(x)
    X = []
    for k in range(N):
        re = sum(x[n] * math.cos(2 * math.pi * k * n / N) for n in range(N))
        im = sum(-x[n] * math.sin(2 * math.pi * k * n / N) for n in range(N))
        X.append((re, im))
    return X


def tinh_bien_do_pha(re, im):
    bien_do = math.sqrt(re ** 2 + im ** 2)
    pha = math.atan2(im, re)
    return bien_do, pha


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
    return samples, params


def main():
    parser = argparse.ArgumentParser(
        description="So sánh phổ biên độ giữa cover WAV và stego WAV"
    )
    parser.add_argument('-i', '--input',  required=True,
                        help='File WAV gốc (cover WAV)')
    parser.add_argument('-s', '--stego',  required=True,
                        help='File WAV đã nhúng tin (stego WAV)')
    parser.add_argument('-n', '--segment', type=int, default=8,
                        help='Kích thước đoạn phân tích (default: 8)')
    args = parser.parse_args()

    for f in [args.input, args.stego]:
        if not os.path.exists(f):
            print(f"[!] Không tìm thấy file: {f}")
            sys.exit(1)

    print("\n" + "=" * 60)
    print("  SO SÁNH PHỔ BIÊN ĐỘ (MAGNITUDE SPECTRUM)")
    print("=" * 60)
    print(f"  File gốc (cover): {args.input}")
    print(f"  File stego      : {args.stego}")
    print(f"  Kích thước đoạn : {args.segment} sample")

    # Đọc 2 file WAV
    try:
        samples_in, params_in = doc_wav(args.input)
        samples_st, params_st = doc_wav(args.stego)
    except Exception as e:
        print(f"[!] Lỗi đọc file WAV: {e}")
        sys.exit(1)

    L = args.segment
    if len(samples_in) < L or len(samples_st) < L:
        print(f"[!] Lỗi: Độ dài file âm thanh nhỏ hơn kích thước đoạn {L}!")
        sys.exit(1)

    # Lấy đoạn đầu tiên
    doan_in = samples_in[:L]
    doan_st = samples_st[:L]

    # Tính DFT
    X_in = dft(doan_in)
    X_st = dft(doan_st)

    # Tính biên độ và pha
    bd_in, ph_in = [], []
    bd_st, ph_st = [], []

    for re, im in X_in:
        bd, ph = tinh_bien_do_pha(re, im)
        bd_in.append(bd)
        ph_in.append(ph)

    for re, im in X_st:
        bd, ph = tinh_bien_do_pha(re, im)
        bd_st.append(bd)
        ph_st.append(ph)

    # In bảng so sánh phổ biên độ và pha
    print(f"\n  BẢNG SO SÁNH PHÂN TÍCH ĐOẠN ĐẦU TIÊN ({L} SAMPLE):")
    print("-" * 75)
    print(f"{'Tần số (k)':<12}{'B.độ Gốc':<15}{'B.độ Stego':<15}{'Pha Gốc (rad)':<16}{'Pha Stego (rad)':<16}")
    print("-" * 75)
    
    sai_so_bien_do = 0.0
    sai_so_pha = 0.0
    
    for k in range(L):
        print(f"{k:<12}{bd_in[k]:<15.4f}{bd_st[k]:<15.4f}{ph_in[k]:<16.4f}{ph_st[k]:<16.4f}")
        sai_so_bien_do += abs(bd_in[k] - bd_st[k])
        sai_so_pha += abs(ph_in[k] - ph_st[k])

    mae_bd = sai_so_bien_do / L
    mae_ph = sai_so_pha / L

    tong_bd_in = sum(bd_in)
    tb_bd_in = tong_bd_in / L if L > 0 else 1
    phan_tram_sai_lech_bd = (mae_bd / tb_bd_in) * 100 if tb_bd_in > 0 else 0

    print("-" * 75)
    print(f"[+] Độ lệch biên độ trung bình (MAE - Magnitude): {mae_bd:.4f} (Sai số tương đối: {phan_tram_sai_lech_bd:.4f}%)")
    print(f"[+] Độ lệch pha trung bình (MAE - Phase)       : {mae_ph:.4f}")
    
    print("\n[>] Nhận xét:")
    if phan_tram_sai_lech_bd < 5.0:
        print("  - Phổ biên độ HẦU NHƯ KHÔNG ĐỔI (sai số cực nhỏ do làm tròn số nguyên 16-bit khi lưu file WAV).")
        print("  - Điều này chứng minh thuật toán mã hóa pha bảo toàn phổ biên độ.")
    else:
        print("  - Cảnh báo: Phổ biên độ có sự sai lệch đáng kể!")

    if mae_ph > 0.05:
        print("  - Pha của tín hiệu đã được thay đổi rõ rệt để nhúng thông tin.")
    else:
        print("  - Pha tín hiệu không thay đổi nhiều (có thể chưa nhúng tin).")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
