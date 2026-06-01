#!/usr/bin/env python3
"""
watermark_phase_embed.py - Nhúng thủy vân bản quyền bằng Mã hóa pha (Phase Coding)
==================================================================================
Bài thực hành: Thủy vân số bản quyền âm thanh (LSB vs Phase Coding)
B22DCAT196 - Vũ Lâm Minh (PTIT)
"""

import wave
import struct
import math
import sys
import os

KICH_THUOC_DOAN = 1024  # Có thể nhúng tối đa 511 bits

def dft(x):
    N = len(x)
    X = []
    for k in range(N):
        re = sum(x[n] * math.cos(2 * math.pi * k * n / N) for n in range(N))
        im = sum(-x[n] * math.sin(2 * math.pi * k * n / N) for n in range(N))
        X.append((re, im))
    return X

def idft(X):
    N = len(X)
    x = []
    for n in range(N):
        val = sum(
            X[k][0] * math.cos(2 * math.pi * k * n / N) -
            X[k][1] * math.sin(2 * math.pi * k * n / N)
            for k in range(N)
        ) / N
        x.append(val)
    return x

def bien_do_pha(re, im):
    bien_do = math.sqrt(re ** 2 + im ** 2)
    pha = math.atan2(im, re)
    return bien_do, ph

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

    doan_list = [samples[i * L:(i + 1) * L] for i in range(so_doan)]
    phan_du   = samples[so_doan * L:]

    dft_list = [dft(doan) for doan in doan_list]

    bien_do_list = []
    pha_list     = []
    for Xk in dft_list:
        bien_do_k = []
        pha_k     = []
        for re, im in Xk:
            bd = math.sqrt(re ** 2 + im ** 2)
            ph = math.atan2(im, re)
            bien_do_k.append(bd)
            pha_k.append(ph)
        bien_do_list.append(bien_do_k)
        pha_list.append(pha_k)

    chenh_lech_pha = []
    for i in range(1, so_doan):
        delta = [pha_list[i][k] - pha_list[0][k] for k in range(L)]
        chenh_lech_pha.append(delta)

    pha_moi_doan_0 = list(pha_list[0])
    for idx, bit in enumerate(bits):
        k = idx + 1
        if bit == 0:
            pha_moi_doan_0[k] = math.pi / 2
            pha_moi_doan_0[L - k] = -math.pi / 2
        else:
            pha_moi_doan_0[k] = -math.pi / 2
            pha_moi_doan_0[L - k] = math.pi / 2

    pha_moi_list = [pha_moi_doan_0]
    for i in range(so_doan - 1):
        pha_moi_k = [pha_moi_doan_0[k] + chenh_lech_pha[i][k] for k in range(L)]
        pha_moi_list.append(pha_moi_k)

    dft_moi_list = []
    for i in range(so_doan):
        Xk_moi = []
        for k in range(L):
            re = bien_do_list[i][k] * math.cos(pha_moi_list[i][k])
            im = bien_do_list[i][k] * math.sin(pha_moi_list[i][k])
            Xk_moi.append((re, im))
        dft_moi_list.append(Xk_moi)

    ket_qua = []
    for Xk_moi in dft_moi_list:
        doan_moi = idft(Xk_moi)
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
    print("  [*] Đang thực hiện DFT & nhúng pha (có thể mất 1-2 giây)...")

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
