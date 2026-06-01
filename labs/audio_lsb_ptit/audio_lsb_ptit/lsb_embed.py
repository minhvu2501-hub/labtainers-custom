#!/usr/bin/env python3
"""
lsb_embed.py - Nhúng tin mật vào file âm thanh WAV bằng kỹ thuật LSB
=======================================================================
Bài thực hành: Kỹ thuật giấu tin trong âm thanh - LSB
PTIT - Học viện Công nghệ Bưu chính Viễn thông

Nguyên lý:
    Mỗi sample âm thanh 16-bit được biểu diễn bằng 16 bit nhị phân.
    Bit cuối (LSB - Least Significant Bit) ảnh hưởng rất nhỏ đến chất lượng âm thanh.
    Ta thay thế LSB của mỗi sample bằng 1 bit của thông điệp mật.
    Để đánh dấu kết thúc, ta sử dụng chuỗi kết thúc đặc biệt.

Cách dùng:
    python3 lsb_embed.py -i cover.wav -o stego.wav -m secret.txt
"""

import wave
import struct
import sys
import os
import argparse

# Chuỗi đánh dấu kết thúc thông điệp (8 ký tự = 64 bit)
DIEU_KIEN_KET_THUC = "<<PTIT>>"


def doc_wav(ten_file):
    """Đọc file WAV, trả về danh sách sample và tham số"""
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
        raise ValueError(f"Chỉ hỗ trợ 8-bit và 16-bit WAV.")

    return samples, params


def ghi_wav(ten_file, samples, params):
    """Ghi danh sách sample vào file WAV"""
    sw = params.sampwidth
    if sw == 1:
        raw = struct.pack(f'{len(samples)}B', *samples)
    elif sw == 2:
        raw = struct.pack(f'{len(samples)}h', *samples)

    with wave.open(ten_file, 'wb') as f:
        f.setparams(params)
        f.writeframes(raw)


def chuoi_sang_bits(chuoi):
    """Chuyển chuỗi văn bản thành danh sách bit (MSB trước)"""
    bits = []
    for ky_tu in chuoi:
        ma = ord(ky_tu)
        for vi_tri in range(7, -1, -1):
            bits.append((ma >> vi_tri) & 1)
    return bits


def nhung_lsb(samples, bits):
    """
    Nhúng danh sách bit vào LSB của các sample.
    Trả về danh sách sample mới.
    """
    if len(bits) > len(samples):
        raise OverflowError(
            f"Thông điệp quá dài! Cần {len(bits)} bit, "
            f"file âm thanh chỉ có {len(samples)} sample."
        )

    ket_qua = list(samples)  # copy
    for i, bit in enumerate(bits):
        ket_qua[i] = (ket_qua[i] & ~1) | bit   # xóa LSB rồi đặt bit mới

    return ket_qua


def main():
    parser = argparse.ArgumentParser(
        description="Nhúng tin mật vào file WAV bằng kỹ thuật LSB"
    )
    parser.add_argument('-i', '--input',   required=True,
                        help='File WAV đầu vào (cover audio)')
    parser.add_argument('-o', '--output',  required=True,
                        help='File WAV đầu ra (stego audio)')
    parser.add_argument('-m', '--message', required=True,
                        help='File văn bản chứa tin mật (secret.txt)')
    args = parser.parse_args()

    # Kiểm tra file tồn tại
    for f in [args.input, args.message]:
        if not os.path.exists(f):
            print(f"[!] Không tìm thấy file: {f}")
            sys.exit(1)

    # Đọc tin mật
    with open(args.message, 'r', encoding='utf-8') as f:
        noi_dung = f.read().strip()

    if not noi_dung:
        print("[!] File tin mật rỗng!")
        sys.exit(1)

    # Ghép chuỗi kết thúc
    noi_dung_day_du = noi_dung + DIEU_KIEN_KET_THUC

    # Chuyển thành bits
    bits = chuoi_sang_bits(noi_dung_day_du)

    print("\n" + "=" * 58)
    print("  NHÚNG TIN MẬT - KỸ THUẬT LSB")
    print("=" * 58)
    print(f"  File cover   : {args.input}")
    print(f"  File output  : {args.output}")
    print(f"  File tin mật : {args.message}")
    print(f"  Nội dung     : \"{noi_dung[:50]}{'...' if len(noi_dung)>50 else ''}\"")
    print(f"  Độ dài       : {len(noi_dung)} ký tự")
    print(f"  Tổng bit cần : {len(bits)} bit (gồm chuỗi kết thúc)")

    # Đọc file âm thanh
    samples, params = doc_wav(args.input)
    print(f"  Tổng sample  : {len(samples):,}")
    print(f"  Tỷ lệ sử dụng: {len(bits)/len(samples)*100:.3f}% số sample")

    # Nhúng tin
    try:
        samples_moi = nhung_lsb(samples, bits)
    except OverflowError as e:
        print(f"\n[!] Lỗi: {e}")
        sys.exit(1)

    # Ghi file stego
    ghi_wav(args.output, samples_moi, params)

    print(f"\n[+] Nhúng thành công!")
    print(f"[+] File stego đã lưu: {args.output}")
    print(f"\n[>] Tiếp theo: python3 lsb_extract.py -i {args.output}")
    print("=" * 58 + "\n")


if __name__ == "__main__":
    main()
