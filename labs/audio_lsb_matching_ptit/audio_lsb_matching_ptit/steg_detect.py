#!/usr/bin/env python3
"""
steg_detect.py - Dò tìm giấu tin LSB bằng phương pháp thống kê Chi-Square (PoVs)
================================================================================
Bài thực hành: Kỹ thuật giấu tin LSB Matching & Steganalysis
B22DCAT196 - Vũ Lâm Minh (PTIT)
"""

import wave
import struct
import sys
import os
import math
from collections import Counter

def doc_wav(ten_file):
    with wave.open(ten_file, 'rb') as f:
        params = f.getparams()
        raw    = f.readframes(f.getnframes())

    sw = params.sampwidth
    n  = len(raw) // sw

    if sw == 1:
        samples = list(struct.unpack(f'{n}B', raw))
    elif sw == 2:
        samples = list(struct.unpack(f'{n}h', raw))
    else:
        raise ValueError("Chỉ hỗ trợ 8-bit và 16-bit WAV.")
    return samples

def chi2_steganalysis(samples, num_samples=10000):
    # Lấy phân đoạn đầu tiên của file âm thanh (nơi thường giấu tin)
    segment = samples[:num_samples]
    freqs = Counter(segment)
    
    # Tập hợp các chỉ số cặp giá trị PoVs: (2k, 2k+1)
    # k = v // 2 (sử dụng dịch bit v >> 1)
    povs = set(v >> 1 for v in segment)
    
    chi_square = 0.0
    df = 0
    
    for k in povs:
        val_even = k << 1
        val_odd = val_even + 1
        
        o_even = freqs.get(val_even, 0)
        o_odd = freqs.get(val_odd, 0)
        
        # Giá trị kỳ vọng nếu giấu tin (tần suất hai giá trị bằng nhau)
        e = (o_even + o_odd) / 2.0
        
        # Chỉ xét các cặp có tần suất xuất hiện đáng kể (> 5)
        if e > 5:
            chi_square += ((o_even - e) ** 2) / e + ((o_odd - e) ** 2) / e
            df += 1
            
    df = df - 1
    if df <= 0:
        return 0.0, 0.0
        
    # Tính p-value sử dụng phép xấp xỉ Wilson-Hilferty cho hàm phân phối tích lũy Chi-Square
    try:
        val = chi_square / df
        z = (val**(1.0/3.0) - (1.0 - 2.0 / (9.0 * df))) / math.sqrt(2.0 / (9.0 * df))
        # Hàm phân phối chuẩn tích lũy (Normal CDF)
        normal_cdf = 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))
        # Xác suất H0 đúng (stego hiện diện): p-value = 1.0 - normal_cdf
        p_stego = 1.0 - normal_cdf
    except:
        return 0.0, 0.0
        
    return chi_square, max(0.0, min(1.0, p_stego))

def main():
    if len(sys.argv) < 2:
        print("Cách dùng: python3 steg_detect.py <ten_file.wav> [so_mau_kiem_tra]")
        print("Ví dụ    : python3 steg_detect.py stego_replace.wav")
        sys.exit(1)

    ten_file = sys.argv[1]
    num_samples = 15000
    if len(sys.argv) > 2:
        num_samples = int(sys.argv[2])

    if not os.path.exists(ten_file):
        print(f"[!] Không tìm thấy file: {ten_file}")
        sys.exit(1)

    samples = doc_wav(ten_file)
    chi_sq, p_stego = chi2_steganalysis(samples, num_samples)

    print("\n" + "=" * 60)
    print("  CHI-SQUARE STEGANALYSIS DETECTOR - B22DCAT196")
    print("=" * 60)
    print(f"  File kiểm tra    : {os.path.basename(ten_file)}")
    print(f"  Số sample kiểm tra: {num_samples}")
    print(f"  Chi-Square Value : {chi_sq:.4f}")
    print(f"  Xác suất giấu tin: {p_stego * 100:.2f}%")
    print("-" * 60)
    if p_stego > 0.90:
        print("[!] CẢNH BÁO: Phát hiện bất thường! Khả năng có tin mật ẩn bằng LSB.")
    else:
        print("[V] AN TOÀN: Không phát hiện dấu vết giấu tin bằng LSB Replacement.")
    print("=" * 60 + "\n")

if __name__ == "__main__":
    main()
