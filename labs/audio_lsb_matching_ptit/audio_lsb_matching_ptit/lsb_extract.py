#!/usr/bin/env python3
"""
lsb_extract.py - Tách tin mật từ file âm thanh WAV (LSB)
==========================================================
Bài thực hành: Kỹ thuật giấu tin LSB Matching & Steganalysis
B22DCAT196 - Vũ Lâm Minh (PTIT)
"""

import wave
import struct
import sys
import os
import argparse

DIEU_KIEN_KET_THUC = "<<PTIT>>"

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
    return samples, params

def tach_lsb(samples):
    noi_dung = ""
    bits_dem  = 0
    byte_hien_tai = 0

    for sample in samples:
        bit = sample & 1
        byte_hien_tai = (byte_hien_tai << 1) | bit
        bits_dem += 1

        if bits_dem == 8:
            ky_tu = chr(byte_hien_tai)
            noi_dung += ky_tu
            byte_hien_tai = 0
            bits_dem = 0

            # Kiểm tra chuỗi kết thúc
            if noi_dung.endswith(DIEU_KIEN_KET_THUC):
                return noi_dung[:-len(DIEU_KIEN_KET_THUC)]
    return None

def main():
    parser = argparse.ArgumentParser(description="Tách tin mật bằng LSB Extraction")
    parser.add_argument('-i', '--input', default='stego_replace.wav', help='File WAV stego đầu vào')
    parser.add_argument('-o', '--output', default='extracted.txt', help='File lưu tin mật trích xuất')
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"[!] Không tìm thấy file: {args.input}")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("  TÁCH TIN MẬT LSB - B22DCAT196")
    print("=" * 60)
    print(f"  File stego : {args.input}")

    samples, params = doc_wav(args.input)
    noi_dung = tach_lsb(samples)

    if noi_dung is None:
        print("\n[!] Không tìm thấy tin mật trong file này!")
        sys.exit(1)

    print(f"\n[+] Tách thành công!")
    print(f"--- Nội dung tin mật ---")
    print(noi_dung)
    print("------------------------")

    with open(args.output, 'w', encoding='utf-8') as f:
        f.write(noi_dung)
    print(f"\n[+] Đã lưu kết quả vào: {args.output}")
    print("=" * 60 + "\n")

if __name__ == "__main__":
    main()
