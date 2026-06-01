#!/usr/bin/env python3
"""
watermark_phase_embed.py - Nhúng thủy vân bản quyền bằng Mã hóa pha (Phase Coding) sử dụng Numpy
==================================================================================
Bài thực hành: Thủy vân số bản quyền âm thanh (LSB vs Phase Coding)
B22DCAT196 - Vũ Lâm Minh (PTIT)
"""

import wave
import struct
import numpy as np
import sys
import os

KICH_THUOC_DOAN = 1024  # Có thể nhúng tối đa 511 bits

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

def ghi_wav(ten_file, samples, params):
    raw = struct.pack(f'{len(samples)}h',
                      *[max(-32768, min(32767, int(round(s)))) for s in samples])
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

def nhung_pha(samples, bits, L):
    so_doan = len(samples) // L
    if len(bits) > L // 2 - 1:
        raise ValueError(f"Thủy vân quá dài so với phân đoạn {L}")

    # Chuyển mẫu sang numpy array để tính toán nhanh
    samples_arr = np.array(samples, dtype=np.float64)
    doan_list = [samples_arr[i * L:(i + 1) * L] for i in range(so_doan)]
    phan_du   = samples_arr[so_doan * L:]

    # Áp dụng FFT lên tất cả các phân đoạn
    dft_list = [np.fft.fft(doan) for doan in doan_list]

    # Lấy biên độ và pha
    bien_do_list = [np.abs(X) for X in dft_list]
    pha_list     = [np.angle(X) for X in dft_list]

    # Tính chênh lệch pha giữa phân đoạn i và phân đoạn 0
    chenh_lech_pha = []
    for i in range(1, so_doan):
        delta = pha_list[i] - pha_list[0]
        chenh_lech_pha.append(delta)

    # Thay đổi pha phân đoạn 0 để giấu tin
    pha_moi_doan_0 = np.array(pha_list[0])
    for idx, bit in enumerate(bits):
        k = idx + 1
        if bit == 0:
            pha_moi_doan_0[k] = np.pi / 2
            pha_moi_doan_0[L - k] = -np.pi / 2
        else:
            pha_moi_doan_0[k] = -np.pi / 2
            pha_moi_doan_0[L - k] = np.pi / 2

    # Tính pha mới cho tất cả các phân đoạn sau dựa trên chênh lệch pha ban đầu
    pha_moi_list = [pha_moi_doan_0]
    for i in range(so_doan - 1):
        pha_moi_k = pha_moi_doan_0 + chenh_lech_pha[i]
        pha_moi_list.append(pha_moi_k)

    # Tái tạo phổ DFT mới
    dft_moi_list = []
    for i in range(so_doan):
        X_moi = bien_do_list[i] * np.exp(1j * pha_moi_list[i])
        dft_moi_list.append(X_moi)

    # Áp dụng IFFT để chuyển về miền thời gian
    ket_qua = []
    for X_moi in dft_moi_list:
        doan_moi = np.fft.ifft(X_moi).real
        ket_qua.extend(doan_moi)

    ket_qua.extend(phan_du)
    return ket_qua

def main():
    cover_file = "cover.wav"
    output_file = "watermark_phase.wav"
    secret_file = "secret.txt"

    if not os.path.exists(cover_file) or not os.path.exists(secret_file):
        print("[!] Không tìm thấy cover.wav hoặc secret.txt. Hãy chạy gen_cover.py trước.")
        sys.exit(1)

    with open(secret_file, 'r', encoding='utf-8') as f:
        watermark = f.read().strip()

    bits = chuoi_sang_bits(watermark)
    samples, params = doc_wav(cover_file)

    print("\n" + "=" * 60)
    print("  NHÚNG THỦY VÂN MÃ HÓA PHA - B22DCAT196")
    print("=" * 60)
    print(f"  Thủy vân    : {watermark}")
    print(f"  Số bit nhúng: {len(bits)} bits")
    print("  [*] Đang thực hiện DFT & nhúng pha bằng Numpy...")

    try:
        samples_moi = nhung_pha(samples, bits, KICH_THUOC_DOAN)
    except Exception as e:
        print(f"[!] Lỗi nhúng pha: {e}")
        sys.exit(1)

    ghi_wav(output_file, samples_moi, params)
    print(f"[+] Đã tạo file stego: {output_file}")
    print("=" * 60 + "\n")

if __name__ == "__main__":
    main()
