#!/usr/bin/env python3
"""
gen_cover.py - Tạo file âm thanh WAV mẫu cho bài mã hóa pha
=============================================================
Bài thực hành: Kỹ thuật giấu tin bằng mã hóa pha (Phase Coding)
PTIT - Học viện Công nghệ Bưu chính Viễn thông
"""

import wave
import struct
import math

TY_LE_MAU  = 8000    # 8 kHz (thấp hơn để phù hợp với phase coding)
THOI_LUONG = 4       # giây
BIEN_DO    = 10000
TEN_FILE   = "cover.wav"


def tao_tin_hieu_phuc_hop(ty_le_mau, thoi_luong, bien_do):
    """Tạo tín hiệu phức hợp nhiều tần số"""
    so_mau = int(thoi_luong * ty_le_mau)
    # Dùng nhiều tần số để tạo tín hiệu phong phú hơn
    tan_so_list = [200, 400, 600, 800, 1000]
    bien_do_list = [1.0, 0.7, 0.5, 0.3, 0.2]

    samples = []
    for i in range(so_mau):
        t = i / ty_le_mau
        gia_tri = 0
        for f, a in zip(tan_so_list, bien_do_list):
            gia_tri += a * math.sin(2 * math.pi * f * t)
        # Chuẩn hóa và nhân biên độ
        gia_tri = int(gia_tri / sum(bien_do_list) * bien_do)
        gia_tri = max(-32768, min(32767, gia_tri))
        samples.append(gia_tri)
    return samples


def ghi_wav(ten_file, samples, ty_le_mau):
    with wave.open(ten_file, 'wb') as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(ty_le_mau)
        for s in samples:
            f.writeframes(struct.pack('<h', s))


def main():
    print("=" * 58)
    print("  Tạo file âm thanh cover cho bài mã hóa pha")
    print("=" * 58)

    samples = tao_tin_hieu_phuc_hop(TY_LE_MAU, THOI_LUONG, BIEN_DO)
    ghi_wav(TEN_FILE, samples, TY_LE_MAU)

    print(f"\n[+] Đã tạo: {TEN_FILE}")
    print(f"    Tần số lấy mẫu : {TY_LE_MAU} Hz")
    print(f"    Thời lượng     : {THOI_LUONG} giây")
    print(f"    Số sample      : {len(samples):,}")
    print(f"    Thành phần tần số: 200, 400, 600, 800, 1000 Hz")
    print(f"\n[>] Tiếp theo: python3 info_audio.py cover.wav")


if __name__ == "__main__":
    main()
