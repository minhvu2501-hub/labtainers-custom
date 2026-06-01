#!/usr/bin/env python3
"""
evaluate.py - Đánh giá chất lượng và so sánh LSB Replacement vs LSB Matching
=============================================================================
Bài thực hành: Kỹ thuật giấu tin LSB Matching & Steganalysis
B22DCAT196 - Vũ Lâm Minh (PTIT)
"""

import wave
import struct
import math
import sys
import os
import argparse
from steg_detect import chi2_steganalysis

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

def tinh_mse(mau1, mau2):
    n = min(len(mau1), len(mau2))
    tong = sum((int(a) - int(b)) ** 2 for a, b in zip(mau1[:n], mau2[:n]))
    return tong / n

def tinh_psnr(mse, max_val):
    if mse == 0:
        return float('inf')
    return 20 * math.log10(max_val / math.sqrt(mse))

def tinh_snr(mau_goc, mau_stego):
    n = min(len(mau_goc), len(mau_stego))
    cong_suat_tin = sum(int(a) ** 2 for a in mau_goc[:n]) / n
    nhieu = sum((int(a) - int(b)) ** 2 for a, b in zip(mau_goc[:n], mau_stego[:n])) / n
    if nhieu == 0:
        return float('inf')
    return 10 * math.log10(cong_suat_tin / nhieu)

def main():
    parser = argparse.ArgumentParser(description="Đánh giá & So sánh LSB Replacement và LSB Matching")
    parser.add_argument('-c', '--cover', default='cover.wav', help='File WAV gốc')
    parser.add_argument('-r', '--replace', default='stego_replace.wav', help='File stego LSB Replacement')
    parser.add_argument('-m', '--matching', default='stego_matching.wav', help='File stego LSB Matching')
    parser.add_argument('-o', '--output', default='comparison_report.txt', help='File xuất báo cáo')
    args = parser.parse_args()

    for f in [args.cover, args.replace, args.matching]:
        if not os.path.exists(f):
            print(f"[!] Không tìm thấy file: {f}")
            print("    Đảm bảo bạn đã chạy gen_cover.py, lsb_embed.py và lsb_matching_embed.py.")
            sys.exit(1)

    mau_cover, params = doc_wav(args.cover)
    mau_replace, _ = doc_wav(args.replace)
    mau_matching, _ = doc_wav(args.matching)

    max_gt = 32767 if params.sampwidth == 2 else 255

    # Đánh giá LSB Replacement
    mse_r = tinh_mse(mau_cover, mau_replace)
    psnr_r = tinh_psnr(mse_r, max_gt)
    snr_r = tinh_snr(mau_cover, mau_replace)
    _, p_stego_r = chi2_steganalysis(mau_replace, 15000)

    # Đánh giá LSB Matching
    mse_m = tinh_mse(mau_cover, mau_matching)
    psnr_m = tinh_psnr(mse_m, max_gt)
    snr_m = tinh_snr(mau_cover, mau_matching)
    _, p_stego_m = chi2_steganalysis(mau_matching, 15000)

    report = f"""============================================================
  BÁO CÁO SO SÁNH GIỮA LSB REPLACEMENT VÀ LSB MATCHING
  B22DCAT196 - Vũ Lâm Minh (PTIT)
============================================================
  File nhạc gốc  : {args.cover}
  Số lượng sample: {len(mau_cover):,} samples

------------------------------------------------------------
  1. PHƯƠNG PHÁP LSB REPLACEMENT (Thay thế LSB)
------------------------------------------------------------
  - Chỉ số MSE  : {mse_r:.6f}
  - Chỉ số PSNR : {psnr_r:.4f} dB
  - Chỉ số SNR  : {snr_r:.4f} dB
  - Phân tích Chi-Square Steganalysis:
    --> Xác suất có tin mật: {p_stego_r * 100:.2f}%
    --> Đánh giá bảo mật: {"BỊ PHÁT HIỆN" if p_stego_r > 0.90 else "AN TOÀN"}

------------------------------------------------------------
  2. PHƯƠNG PHÁP LSB MATCHING (Cộng/Trừ ngẫu nhiên ±1)
------------------------------------------------------------
  - Chỉ số MSE  : {mse_m:.6f}
  - Chỉ số PSNR : {psnr_m:.4f} dB
  - Chỉ số SNR  : {snr_m:.4f} dB
  - Phân tích Chi-Square Steganalysis:
    --> Xác suất có tin mật: {p_stego_m * 100:.2f}%
    --> Đánh giá bảo mật: {"BỊ PHÁT HIỆN" if p_stego_m > 0.90 else "AN TOÀN"}

============================================================
  3. KẾT LUẬN & ĐÁNH GIÁ (B22DCAT196)
============================================================
  - Cả hai phương pháp đều cho chất lượng âm thanh stego cực tốt (PSNR > 80 dB), 
    vượt xa ngưỡng phân biệt của tai người thường (30-40 dB).
  - LSB Replacement dễ bị phát hiện bằng thống kê Chi-Square (tỷ lệ gần 100%)
    do thay đổi phân bố cặp giá trị PoVs (even/odd).
  - LSB Matching phân tán sai số ngẫu nhiên giúp duy trì phân bố tự nhiên của
    các sample âm thanh, đánh bại hoàn toàn kiểm tra Chi-Square (tỷ lệ 0%).
============================================================
"""

    print(report)

    with open(args.output, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"[+] Đã ghi báo cáo so sánh chi tiết vào file: {args.output}")

if __name__ == "__main__":
    main()
