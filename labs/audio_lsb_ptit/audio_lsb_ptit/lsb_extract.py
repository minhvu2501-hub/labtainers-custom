#!/usr/bin/env python3
"""
lsb_extract.py - Tách tin mật từ file âm thanh WAV (LSB)
==========================================================
Bài thực hành: Kỹ thuật giấu tin trong âm thanh - LSB
PTIT - Học viện Công nghệ Bưu chính Viễn thông

Nguyên lý:
    Đọc LSB của từng sample liên tiếp, ghép 8 bit thành 1 byte,
    chuyển byte thành ký tự ASCII cho đến khi gặp chuỗi kết thúc.

Cách dùng:
    python3 lsb_extract.py -i stego.wav
    python3 lsb_extract.py -i stego.wav -o extracted.txt
"""

import wave
import struct
import sys
import os
import argparse

DIEU_KIEN_KET_THUC = "<<PTIT>>"


def doc_wav(ten_file):
    """Đọc file WAV, trả về danh sách sample"""
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
    """
    Tách thông điệp từ LSB của các sample.
    Dừng khi gặp chuỗi kết thúc DIEU_KIEN_KET_THUC.
    """
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
                # Bỏ chuỗi kết thúc và trả về
                return noi_dung[:-len(DIEU_KIEN_KET_THUC)]

    return None  # Không tìm thấy chuỗi kết thúc


def main():
    parser = argparse.ArgumentParser(
        description="Tách tin mật từ file WAV (LSB)"
    )
    parser.add_argument('-i', '--input',  required=True,
                        help='File WAV stego đầu vào')
    parser.add_argument('-o', '--output', default='extracted.txt',
                        help='File văn bản lưu kết quả (mặc định: extracted.txt)')
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"[!] Không tìm thấy file: {args.input}")
        sys.exit(1)

    print("\n" + "=" * 58)
    print("  TÁCH TIN MẬT - KỸ THUẬT LSB")
    print("=" * 58)
    print(f"  File stego : {args.input}")

    samples, params = doc_wav(args.input)
    print(f"  Số sample  : {len(samples):,}")
    print(f"  Đang tách tin mật...")

    noi_dung = tach_lsb(samples)

    if noi_dung is None:
        print("\n[!] Không tìm thấy tin mật trong file này.")
        print("    Hãy kiểm tra lại file có được nhúng bằng lsb_embed.py không.")
        sys.exit(1)

    print(f"\n[+] Tách thành công!")
    print(f"[+] Độ dài thông điệp: {len(noi_dung)} ký tự")
    print(f"\n--- Nội dung tin mật ---")
    print(noi_dung)
    print("------------------------")

    # Lưu ra file
    with open(args.output, 'w', encoding='utf-8') as f:
        f.write(noi_dung)

    print(f"\n[+] Đã lưu kết quả vào: {args.output}")
    print(f"\n[>] Tiếp theo: python3 evaluate.py -c cover.wav -s {args.input}")
    print("=" * 58 + "\n")


if __name__ == "__main__":
    main()
