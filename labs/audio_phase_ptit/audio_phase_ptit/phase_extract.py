#!/usr/bin/env python3
"""
phase_extract.py - Tách tin mật được nhúng bằng kỹ thuật mã hóa pha (Phase Coding)
========================================================================
Bài thực hành: Kỹ thuật giấu tin bằng mã hóa pha
PTIT - Học viện Công nghệ Bưu chính Viễn thông

Cách dùng:
    python3 phase_extract.py -i stego.wav -l <độ_dài_thông_điệp> -n 8
"""

import wave
import struct
import math
import sys
import os
import argparse


# ─────────────────────────────────────────────────────────────
# Hàm DFT tự cài đặt (không dùng thư viện ngoài)
# ─────────────────────────────────────────────────────────────

def dft(x):
    """Biến đổi Fourier rời rạc (DFT)"""
    N = len(x)
    X = []
    for k in range(N):
        re = sum(x[n] * math.cos(2 * math.pi * k * n / N) for n in range(N))
        im = sum(-x[n] * math.sin(2 * math.pi * k * n / N) for n in range(N))
        X.append((re, im))
    return X


def bien_do_pha(re, im):
    """Tính biên độ và pha từ phần thực và ảo"""
    bien_do = math.sqrt(re ** 2 + im ** 2)
    pha = math.atan2(im, re)
    return bien_do, pha


# ─────────────────────────────────────────────────────────────
# Hàm đọc WAV
# ─────────────────────────────────────────────────────────────

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


# ─────────────────────────────────────────────────────────────
# Chuyển đổi bits -> thông điệp
# ─────────────────────────────────────────────────────────────

def bits_sang_chuoi(bits):
    chuoi = ""
    for i in range(0, len(bits), 8):
        byte_bits = bits[i:i+8]
        if len(byte_bits) < 8:
            break
        ma = 0
        for b in byte_bits:
            ma = (ma << 1) | b
        chuoi += chr(ma)
    return chuoi


# ─────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Tách tin mật bằng kỹ thuật mã hóa pha (Phase Coding)"
    )
    parser.add_argument('-i', '--input',   required=True,
                        help='File WAV chứa tin mật (stego audio)')
    parser.add_argument('-l', '--length',  type=int, required=True,
                        help='Độ dài thông điệp cần tách (số ký tự)')
    parser.add_argument('-n', '--segment', type=int, default=8,
                        help='Kích thước đoạn (số sample, mặc định: 8)')
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"[!] Không tìm thấy file: {args.input}")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("  TÁCH TIN MẬT - MÃ HÓA PHA (PHASE CODING)")
    print("=" * 60)
    print(f"  File stego     : {args.input}")
    print(f"  Độ dài tin mật : {args.length} ký tự")
    print(f"  Kích thước đoạn: {args.segment} sample")

    # Đọc file âm thanh stego
    try:
        samples, params = doc_wav(args.input)
    except Exception as e:
        print(f"[!] Lỗi khi đọc file WAV: {e}")
        sys.exit(1)

    L = args.segment
    if len(samples) < L:
        print(f"[!] Lỗi: File âm thanh quá ngắn so với kích thước đoạn {L}!")
        sys.exit(1)

    # Lấy đoạn đầu tiên
    doan_0 = samples[:L]

    # Thực hiện DFT cho đoạn đầu tiên
    X0 = dft(doan_0)

    # Số lượng bit cần tách
    so_bit = args.length * 8
    if so_bit > L // 2 - 1:
        print(f"[!] Cảnh báo: Số bit cần tách ({so_bit}) lớn hơn số bit tối đa có thể nhúng trong đoạn ({L // 2 - 1})!")
        print(f"[!] Hãy kiểm tra lại độ dài thông điệp (-l) hoặc kích thước đoạn (-n).")
        sys.exit(1)

    # Tách pha và quyết định bit (bắt đầu từ k = 1 do bỏ qua DC component)
    bits = []
    for idx in range(so_bit):
        k = idx + 1
        re, im = X0[k]
        _, pha = bien_do_pha(re, im)
        
        # Nếu pha >= 0 thì là bit 0, ngược lại pha < 0 là bit 1
        if pha >= 0:
            bits.append(0)
        else:
            bits.append(1)

    # Chuyển đổi dãy bit thành chuỗi văn bản
    thong_diep = bits_sang_chuoi(bits)

    print(f"\n[+] Kết quả tách tin mật:")
    print("-" * 40)
    print(thong_diep)
    print("-" * 40)
    print(f"[+] Hoàn tất tách tin!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
