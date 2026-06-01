#!/usr/bin/env python3
"""
gen_cover.py - Sinh file âm thanh mẫu (cover audio)
===================================================
Bài thực hành: Thủy vân số bảo vệ bản quyền âm thanh (LSB vs Phase Coding)
B22DCAT196 - Vũ Lâm Minh (PTIT)
"""

import wave
import struct
import math

TY_LE_MAU   = 44100   # Hz
THOI_LUONG  = 5       # giây
TAN_SO_1    = 440     # Hz (La chuẩn)
TAN_SO_2    = 660     # Hz (Mi - tạo hợp âm)
BIEN_DO     = 10000   # Biên độ
TEN_FILE    = "cover.wav"

def tao_tin_hieu(ty_le_mau, thoi_luong, tan_so_1, tan_so_2, bien_do):
    so_mau = int(thoi_luong * ty_le_mau)
    samples = []
    for i in range(so_mau):
        t = i / ty_le_mau
        s1 = bien_do * math.sin(2 * math.pi * tan_so_1 * t)
        s2 = (bien_do // 2) * math.sin(2 * math.pi * tan_so_2 * t)
        gia_tri = int(s1 + s2)
        gia_tri = max(-32768, min(32767, gia_tri))
        samples.append(gia_tri)
    return samples

def ghi_wav(ten_file, samples, ty_le_mau):
    with wave.open(ten_file, 'wb') as f:
        f.setnchannels(1)       # Mono
        f.setsampwidth(2)       # 16-bit
        f.setframerate(ty_le_mau)
        for s in samples:
            f.writeframes(struct.pack('<h', s))

def main():
    print("=" * 60)
    print("  Tạo file âm thanh cover (cover.wav) - B22DCAT196")
    print("=" * 60)

    samples = tao_tin_hieu(TY_LE_MAU, THOI_LUONG, TAN_SO_1, TAN_SO_2, BIEN_DO)
    ghi_wav(TEN_FILE, samples, TY_LE_MAU)

    print(f"\n[+] Đã sinh file: {TEN_FILE}")
    print(f"    Thời lượng  : {THOI_LUONG} giây")
    print(f"    Tần số mẫu  : {TY_LE_MAU} Hz")
    print(f"    Số sample   : {len(samples):,}")
    print("\n[>] Tiếp theo: python3 watermark_lsb_embed.py  và  python3 watermark_phase_embed.py")

if __name__ == "__main__":
    main()
