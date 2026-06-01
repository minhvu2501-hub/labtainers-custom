#!/usr/bin/env python3
"""
phase_embed.py - Nhúng tin mật bằng kỹ thuật mã hóa pha (Phase Coding)
========================================================================
Bài thực hành: Kỹ thuật giấu tin bằng mã hóa pha
PTIT - Học viện Công nghệ Bưu chính Viễn thông

Nguyên lý:
    1. Chia tín hiệu âm thanh thành N đoạn bằng nhau (mỗi đoạn dài L sample)
    2. Áp dụng biến đổi Fourier rời rạc (DFT) cho từng đoạn
    3. Trích xuất thành phần pha (phase) của đoạn ĐẦU TIÊN
    4. Mã hóa tin mật vào pha của đoạn đầu tiên:
       - bit=0 -> pha = +pi/2
       - bit=1 -> pha = -pi/2
    5. Điều chỉnh pha các đoạn còn lại để giữ nguyên mối quan hệ pha tương đối
    6. Biến đổi Fourier ngược (IDFT) để khôi phục tín hiệu

Cách dùng:
    python3 phase_embed.py -i cover.wav -o stego.wav -m secret.txt
    python3 phase_embed.py -i cover.wav -o stego.wav -m secret.txt -n 8
"""

import wave
import struct
import math
import sys
import os
import argparse


# ─────────────────────────────────────────────────────────────
# Hàm DFT và IDFT tự cài đặt (không dùng thư viện ngoài)
# ─────────────────────────────────────────────────────────────

def dft(x):
    """Biến đổi Fourier rời rạc (DFT)"""
    N = len(x)
    X = []
    for k in range(N):
        re = sum(x[n] * math.cos(2 * math.pi * k * n / N) for n in range(N))
        im = sum(-x[n] * math.sin(2 * math.pi * k * n / N) for n in range(N))
        X.append((re, im))
    return X


def idft(X):
    """Biến đổi Fourier ngược (IDFT)"""
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
    """Tính biên độ và pha từ phần thực và ảo"""
    bien_do = math.sqrt(re ** 2 + im ** 2)
    pha = math.atan2(im, re)
    return bien_do, pha


# ─────────────────────────────────────────────────────────────
# Hàm đọc/ghi WAV
# ─────────────────────────────────────────────────────────────

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


# ─────────────────────────────────────────────────────────────
# Chuyển đổi thông điệp <-> bits
# ─────────────────────────────────────────────────────────────

def chuoi_sang_bits(chuoi):
    bits = []
    for ky_tu in chuoi:
        ma = ord(ky_tu)
        for vi_tri in range(7, -1, -1):
            bits.append((ma >> vi_tri) & 1)
    return bits


# ─────────────────────────────────────────────────────────────
# Nhúng tin bằng mã hóa pha
# ─────────────────────────────────────────────────────────────

def nhung_pha(samples, bits, kich_thuoc_doan):
    """
    Nhúng bits vào pha của đoạn đầu tiên.

    Với N bit cần nhúng, đoạn đầu tiên phải có ít nhất N thành phần tần số.
    - bit=0 -> pha_moi = +pi/2
    - bit=1 -> pha_moi = -pi/2
    """
    L = kich_thuoc_doan
    so_doan = len(samples) // L

    if so_doan < 1:
        raise ValueError("File âm thanh quá ngắn!")

    if len(bits) > L // 2 - 1:
        raise ValueError(
            f"Thông điệp quá dài! Có thể nhúng tối đa {L // 2 - 1} bit "
            f"với kích thước đoạn {L}. "
            f"Thử tăng kích thước đoạn (-n) hoặc rút ngắn thông điệp."
        )

    # Chia thành các đoạn
    doan_list = [samples[i * L:(i + 1) * L] for i in range(so_doan)]
    phan_du   = samples[so_doan * L:]  # phần dư nếu không chia hết

    # DFT từng đoạn
    dft_list = [dft(doan) for doan in doan_list]

    # Trích xuất biên độ và pha từng đoạn
    bien_do_list = []
    pha_list     = []
    for Xk in dft_list:
        bien_do_k = []
        pha_k     = []
        for re, im in Xk:
            bd, ph = bien_do_pha(re, im)
            bien_do_k.append(bd)
            pha_k.append(ph)
        bien_do_list.append(bien_do_k)
        pha_list.append(pha_k)

    # Tính chênh lệch pha giữa các đoạn liền kề (giữ lại để điều chỉnh)
    chenh_lech_pha = []
    for i in range(1, so_doan):
        delta = [pha_list[i][k] - pha_list[0][k] for k in range(L)]
        chenh_lech_pha.append(delta)

    # Mã hóa bit vào pha đoạn đầu tiên (bắt đầu từ k=1 để giữ đối xứng liên hợp)
    pha_moi_doan_0 = list(pha_list[0])
    for idx, bit in enumerate(bits):
        k = idx + 1
        if bit == 0:
            pha_moi_doan_0[k] = math.pi / 2
            pha_moi_doan_0[L - k] = -math.pi / 2
        else:
            pha_moi_doan_0[k] = -math.pi / 2
            pha_moi_doan_0[L - k] = math.pi / 2

    # Điều chỉnh pha các đoạn còn lại để giữ nguyên chênh lệch
    pha_moi_list = [pha_moi_doan_0]
    for i in range(so_doan - 1):
        pha_moi_k = [pha_moi_doan_0[k] + chenh_lech_pha[i][k] for k in range(L)]
        pha_moi_list.append(pha_moi_k)

    # Tái tạo DFT từ biên độ cũ và pha mới
    dft_moi_list = []
    for i in range(so_doan):
        Xk_moi = []
        for k in range(L):
            re = bien_do_list[i][k] * math.cos(pha_moi_list[i][k])
            im = bien_do_list[i][k] * math.sin(pha_moi_list[i][k])
            Xk_moi.append((re, im))
        dft_moi_list.append(Xk_moi)

    # IDFT để lấy lại tín hiệu thời gian
    ket_qua = []
    for Xk_moi in dft_moi_list:
        doan_moi = idft(Xk_moi)
        ket_qua.extend(doan_moi)

    ket_qua.extend(phan_du)  # thêm phần dư vào cuối
    return ket_qua


# ─────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Nhúng tin mật bằng kỹ thuật mã hóa pha (Phase Coding)"
    )
    parser.add_argument('-i', '--input',   required=True,
                        help='File WAV đầu vào (cover)')
    parser.add_argument('-o', '--output',  required=True,
                        help='File WAV đầu ra (stego)')
    parser.add_argument('-m', '--message', required=True,
                        help='File văn bản chứa tin mật')
    parser.add_argument('-n', '--segment', type=int, default=8,
                        help='Kích thước đoạn (số sample, mặc định: 8)')
    args = parser.parse_args()

    for f in [args.input, args.message]:
        if not os.path.exists(f):
            print(f"[!] Không tìm thấy file: {f}")
            sys.exit(1)

    with open(args.message, 'r', encoding='utf-8') as f:
        noi_dung = f.read().strip()

    bits = chuoi_sang_bits(noi_dung)

    print("\n" + "=" * 60)
    print("  NHÚNG TIN MẬT - MÃ HÓA PHA (PHASE CODING)")
    print("=" * 60)
    print(f"  File cover     : {args.input}")
    print(f"  File output    : {args.output}")
    print(f"  File tin mật   : {args.message}")
    print(f"  Kích thước đoạn: {args.segment} sample")
    print(f"  Nội dung       : \"{noi_dung[:40]}{'...' if len(noi_dung)>40 else ''}\"")
    print(f"  Số bit cần nhúng: {len(bits)}")
    print(f"  Dung lượng tối đa: {args.segment // 2} bit với đoạn {args.segment}")

    samples, params = doc_wav(args.input)
    print(f"  Tổng số sample : {len(samples):,}")

    print("\n  [*] Đang thực hiện mã hóa pha (có thể mất vài giây)...")

    try:
        samples_moi = nhung_pha(samples, bits, args.segment)
    except (ValueError, OverflowError) as e:
        print(f"\n[!] Lỗi: {e}")
        sys.exit(1)

    ghi_wav(args.output, samples_moi, params)

    print(f"\n[+] Nhúng thành công!")
    print(f"[+] File stego đã lưu: {args.output}")
    print(f"\n[>] Tiếp theo: python3 phase_extract.py -i {args.output} "
          f"-l {len(noi_dung)} -n {args.segment}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
