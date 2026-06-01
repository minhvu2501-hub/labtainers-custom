#!/usr/bin/env python3
"""
evaluate.py - Đánh giá chất lượng file âm thanh sau khi giấu tin
==================================================================
Bài thực hành: Kỹ thuật giấu tin trong âm thanh - LSB
PTIT - Học viện Công nghệ Bưu chính Viễn thông

Các chỉ số đánh giá:
    MSE  - Mean Squared Error (Sai số bình phương trung bình)
    PSNR - Peak Signal-to-Noise Ratio (dB) - càng cao càng tốt
    SNR  - Signal-to-Noise Ratio (dB) - càng cao càng tốt

Cách dùng:
    python3 evaluate.py -c cover.wav -s stego.wav
    python3 evaluate.py -c cover.wav -s stego.wav -o ketqua.txt
"""

import wave
import struct
import math
import sys
import os
import argparse


def doc_wav(ten_file):
    """Đọc file WAV, trả về danh sách sample và tham số"""
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


def tinh_mse(mau1, mau2):
    """Tính Mean Squared Error giữa hai danh sách sample"""
    n = min(len(mau1), len(mau2))
    tong = sum((int(a) - int(b)) ** 2 for a, b in zip(mau1[:n], mau2[:n]))
    return tong / n


def tinh_psnr(mse, max_gia_tri):
    """
    Tính Peak Signal-to-Noise Ratio (dB)
    PSNR = 20 * log10(MAX / sqrt(MSE))
    MAX = 32767 với 16-bit signed
    """
    if mse == 0:
        return float('inf')
    return 20 * math.log10(max_gia_tri / math.sqrt(mse))


def tinh_snr(mau_goc, mau_stego):
    """Tính Signal-to-Noise Ratio (dB)"""
    n = min(len(mau_goc), len(mau_stego))
    cong_suat_tin = sum(int(a) ** 2 for a in mau_goc[:n]) / n
    nhieu = sum((int(a) - int(b)) ** 2
                for a, b in zip(mau_goc[:n], mau_stego[:n])) / n
    if nhieu == 0:
        return float('inf')
    return 10 * math.log10(cong_suat_tin / nhieu)


def dem_bit_khac(mau1, mau2):
    """Đếm số sample có LSB khác nhau"""
    n = min(len(mau1), len(mau2))
    return sum(1 for a, b in zip(mau1[:n], mau2[:n]) if (a & 1) != (b & 1))


def main():
    parser = argparse.ArgumentParser(
        description="Đánh giá chất lượng sau khi giấu tin LSB"
    )
    parser.add_argument('-c', '--cover',  required=True,
                        help='File WAV gốc (cover audio)')
    parser.add_argument('-s', '--stego',  required=True,
                        help='File WAV stego (đã giấu tin)')
    parser.add_argument('-o', '--output', default='ketqua.txt',
                        help='File lưu kết quả (mặc định: ketqua.txt)')
    args = parser.parse_args()

    for f in [args.cover, args.stego]:
        if not os.path.exists(f):
            print(f"[!] Không tìm thấy file: {f}")
            sys.exit(1)

    mau_cover, params_c = doc_wav(args.cover)
    mau_stego, params_s = doc_wav(args.stego)

    max_gt = 32767 if params_c.sampwidth == 2 else 255

    mse  = tinh_mse(mau_cover, mau_stego)
    psnr = tinh_psnr(mse, max_gt)
    snr  = tinh_snr(mau_cover, mau_stego)
    so_bit_khac = dem_bit_khac(mau_cover, mau_stego)

    ket_qua = f"""{'=' * 58}
  KẾT QUẢ ĐÁNH GIÁ CHẤT LƯỢNG - KỸ THUẬT LSB
  PTIT - Học viện Công nghệ Bưu chính Viễn thông
{'=' * 58}
  File cover  : {args.cover}
  File stego  : {args.stego}
  Số sample   : {min(len(mau_cover), len(mau_stego)):,}
{'-' * 58}
  MSE         : {mse:.6f}
  PSNR        : {psnr:.4f} dB
  SNR         : {snr:.4f} dB
  Số sample thay đổi LSB : {so_bit_khac:,}
  Tỷ lệ thay đổi         : {so_bit_khac/min(len(mau_cover),len(mau_stego))*100:.3f}%
{'-' * 58}
  Nhận xét:
  - PSNR > 40 dB : Chất lượng rất tốt, hầu như không nghe thấy sự khác biệt
  - PSNR > 30 dB : Chất lượng tốt, khó phân biệt bằng tai nghe
  - PSNR < 20 dB : Chất lượng kém, có thể nghe thấy sự khác biệt
  -> Kết luận PSNR = {psnr:.2f} dB : {'RẤT TỐT' if psnr > 40 else 'TỐT' if psnr > 30 else 'TRUNG BÌNH'}
{'=' * 58}
"""

    print(ket_qua)

    with open(args.output, 'w', encoding='utf-8') as f:
        f.write(ket_qua)

    print(f"[+] Đã lưu kết quả vào: {args.output}")


if __name__ == "__main__":
    main()
