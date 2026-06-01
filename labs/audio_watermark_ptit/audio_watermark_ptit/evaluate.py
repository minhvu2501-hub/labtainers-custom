#!/usr/bin/env python3
"""
evaluate.py - Tính toán tỷ lệ lỗi bit (BER) và đánh giá độ bền bỉ của thủy vân sử dụng Numpy
===========================================================================================
Bài thực hành: Thủy vân số bản quyền âm thanh (LSB vs Phase Coding)
B22DCAT196 - Vũ Lâm Minh (PTIT)
"""

import wave
import struct
import numpy as np
import sys
import os

KICH_THUOC_DOAN = 1024

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
    return samples

def chuoi_sang_bits(chuoi):
    bits = []
    for ky_tu in chuoi:
        ma = ord(ky_tu)
        for vi_tri in range(7, -1, -1):
            bits.append((ma >> vi_tri) & 1)
    return bits

def trich_xuat_lsb(samples, length):
    bits = []
    for i in range(length):
        bits.append(samples[i] & 1)
    return bits

def trich_xuat_phase(samples, length):
    doan_0 = np.array(samples[:KICH_THUOC_DOAN], dtype=np.float64)
    X0 = np.fft.fft(doan_0)
    bits = []
    for idx in range(length):
        k = idx + 1
        pha = np.angle(X0[k])
        bits.append(0 if pha > 0 else 1)
    return bits

def tinh_ber(bits_goc, bits_trich):
    sai_biet = sum(1 for a, b in zip(bits_goc, bits_trich) if a != b)
    return sai_biet / len(bits_goc)

def main():
    secret_file = "secret.txt"
    if not os.path.exists(secret_file):
        print("[!] Không tìm thấy secret.txt. Hãy chạy gen_cover.py trước.")
        sys.exit(1)

    with open(secret_file, 'r', encoding='utf-8') as f:
        watermark = f.read().strip()

    bits_goc = chuoi_sang_bits(watermark)
    length = len(bits_goc)

    # Các tệp tin cần kiểm tra
    files = {
        "lsb_clean": "watermark_lsb.wav",
        "lsb_vol": "attack_vol_lsb.wav",
        "lsb_noise": "attack_noise_lsb.wav",
        "phase_clean": "watermark_phase.wav",
        "phase_vol": "attack_vol_phase.wav",
        "phase_noise": "attack_noise_phase.wav"
    }

    # Kiểm tra sự tồn tại của các file
    for name, path in files.items():
        if not os.path.exists(path):
            print(f"[!] Thiếu file {path}. Hãy chạy đầy đủ các bước nhúng và tấn công trước.")
            sys.exit(1)

    print("\n[*] Đang tính toán tỷ lệ lỗi bit (BER) cho các phương pháp...")

    # Đọc mẫu
    samples = {name: doc_wav(path) for name, path in files.items()}

    # Trích xuất và tính BER cho LSB
    ber_lsb_clean = tinh_ber(bits_goc, trich_xuat_lsb(samples["lsb_clean"], length))
    ber_lsb_vol   = tinh_ber(bits_goc, trich_xuat_lsb(samples["lsb_vol"], length))
    ber_lsb_noise = tinh_ber(bits_goc, trich_xuat_lsb(samples["lsb_noise"], length))

    # Trích xuất và tính BER cho Phase Coding
    ber_phase_clean = tinh_ber(bits_goc, trich_xuat_phase(samples["phase_clean"], length))
    ber_phase_vol   = tinh_ber(bits_goc, trich_xuat_phase(samples["phase_vol"], length))
    ber_phase_noise = tinh_ber(bits_goc, trich_xuat_phase(samples["phase_noise"], length))

    report = f"""============================================================
  BÁO CÁO ĐÁNH GIÁ ĐỘ BỀN BỈ CỦA THỦY VÂN (BER COMPARISON)
  B22DCAT196 - Vũ Lâm Minh (PTIT)
============================================================
  Chuỗi thủy vân bản quyền: {watermark}
  Độ dài khóa bản quyền : {length} bits

------------------------------------------------------------
  1. KẾT QUẢ THỬ NGHIỆM VỚI THỦY VÂN LSB (FRAGILE)
------------------------------------------------------------
  - Trạng thái sạch (No Attack)   : BER = {ber_lsb_clean * 100:.2f}%
  - Tấn công âm lượng (Volume *0.9): BER = {ber_lsb_vol * 100:.2f}%
  - Tấn công cộng nhiễu (Noise)   : BER = {ber_lsb_noise * 100:.2f}%

------------------------------------------------------------
  2. KẾT QUẢ THỬ NGHIỆM VỚI THỦY VÂN PHASE CODING (ROBUST)
------------------------------------------------------------
  - Trạng thái sạch (No Attack)   : BER = {ber_phase_clean * 100:.2f}%
  - Tấn công âm lượng (Volume *0.9): BER = {ber_phase_vol * 100:.2f}%
  - Tấn công cộng nhiễu (Noise)   : BER = {ber_phase_noise * 100:.2f}%

============================================================
  3. KẾT LUẬN VÀ ĐÁNH GIÁ (B22DCAT196)
============================================================
  - Tỷ lệ lỗi bit (Bit Error Rate - BER) thể hiện khả năng khôi phục thủy vân.
    BER = 0% nghĩa là chữ ký bản quyền được khôi phục nguyên vẹn 100%.
  - Thủy vân LSB là "thủy vân dễ vỡ" (Fragile Watermark). Chỉ cần thay đổi nhẹ
    âm lượng (Volume) hoặc cộng thêm nhiễu nhỏ, cấu hình bit cuối cùng sẽ bị
    xáo trộn hoàn toàn, khiến BER vọt lên rất cao (~30% - 50%).
  - Thủy vân Phase Coding là "thủy vân bền vững" (Robust Watermark). 
    + Khi thay đổi âm lượng, ta chỉ tác động lên phổ biên độ, phần pha hoàn toàn
      được giữ nguyên. Do đó BER dưới tấn công âm lượng bằng 0.00%!
    + Khi cộng nhiễu nhỏ, sự tác động lên góc pha là không đáng kể, do đó
      thủy vân vẫn được khôi phục chính xác (BER gần 0%).
============================================================
"""

    print(report)

    with open("watermark_report.txt", "w", encoding="utf-8") as f:
        f.write(report)
    print("[+] Báo cáo đối chiếu đã được ghi nhận vào file: watermark_report.txt")

if __name__ == "__main__":
    main()
