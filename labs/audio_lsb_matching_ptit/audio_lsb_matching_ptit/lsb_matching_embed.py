#!/usr/bin/env python3
"""
lsb_matching_embed.py - Nhúng tin mật vào file âm thanh WAV bằng LSB Matching (LSB±1)
=======================================================================================
Bài thực hành: Kỹ thuật giấu tin LSB Matching & Steganalysis
B22DCAT196 - Vũ Lâm Minh (PTIT)
"""

import wave
import struct
import sys
import os
import argparse
import random

DIEU_KIEN_KET_THUC = "<<PTIT>>"

def doc_wav(ten_file):
    with wave.open(ten_file, 'rb') as f:
        params  = f.getparams()
        raw     = f.readframes(f.getnframes())

    sw  = params.sampwidth
    n   = len(raw) // sw

    if sw == 1:
        samples = list(struct.unpack(f'{n}B', raw))
    elif sw == 2:
        samples = list(struct.unpack(f'{n}h', raw))
    else:
        raise ValueError("Chỉ hỗ trợ 8-bit và 16-bit WAV.")
    return samples, params

def ghi_wav(ten_file, samples, params):
    sw = params.sampwidth
    if sw == 1:
        raw = struct.pack(f'{len(samples)}B', *samples)
    elif sw == 2:
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

def nhung_lsb_matching(samples, bits):
    if len(bits) > len(samples):
        raise OverflowError("Thông điệp quá dài so với số lượng sample âm thanh!")

    # Cố định seed của random để kết quả MSE/PSNR ổn định và đồng nhất giữa các lần chạy
    random.seed(196)

    ket_qua = list(samples)
    for i, bit in enumerate(bits):
        if (ket_qua[i] & 1) != bit:
            # LSB Matching: cộng hoặc trừ 1 ngẫu nhiên để thay đổi LSB
            thay_doi = random.choice([-1, 1])
            # Tránh tràn ngưỡng biên độ âm thanh 16-bit signed
            if ket_qua[i] == -32768:
                ket_qua[i] += 1
            elif ket_qua[i] == 32767:
                ket_qua[i] -= 1
            else:
                ket_qua[i] += thay_doi
    return ket_qua

def main():
    parser = argparse.ArgumentParser(description="Nhúng tin mật bằng LSB Matching (LSB±1)")
    parser.add_argument('-i', '--input', default='cover.wav', help='File WAV đầu vào')
    parser.add_argument('-o', '--output', default='stego_matching.wav', help='File WAV đầu ra')
    parser.add_argument('-m', '--message', default='secret.txt', help='File tin mật')
    args = parser.parse_args()

    if not os.path.exists(args.input) or not os.path.exists(args.message):
        print("[!] Không tìm thấy file đầu vào hoặc file tin mật.")
        sys.exit(1)

    with open(args.message, 'r', encoding='utf-8') as f:
        noi_dung = f.read().strip()

    noi_dung_day_du = noi_dung + DIEU_KIEN_KET_THUC
    bits = chuoi_sang_bits(noi_dung_day_du)

    print("\n" + "=" * 60)
    print("  NHÚNG TIN LSB MATCHING (±1) - B22DCAT196")
    print("=" * 60)
    print(f"  File cover   : {args.input}")
    print(f"  File stego   : {args.output}")
    print(f"  Số bit nhúng : {len(bits)} bits")

    samples, params = doc_wav(args.input)
    try:
        samples_moi = nhung_lsb_matching(samples, bits)
    except OverflowError as e:
        print(f"[!] Lỗi: {e}")
        sys.exit(1)

    ghi_wav(args.output, samples_moi, params)
    print(f"[+] Đã tạo file stego: {args.output}")
    print("=" * 60 + "\n")

if __name__ == "__main__":
    main()
