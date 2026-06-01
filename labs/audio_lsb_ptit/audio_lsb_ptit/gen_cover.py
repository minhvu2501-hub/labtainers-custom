#!/usr/bin/env python3
"""
gen_cover.py - Tạo file âm thanh WAV mẫu (cover audio)
==========================================================
Bài thực hành: Kỹ thuật giấu tin trong âm thanh - LSB
PTIT - Học viện Công nghệ Bưu chính Viễn thông

Cách dùng:
    python3 gen_cover.py
"""

import wave
import struct
import math

TY_LE_MAU   = 44100   # Hz
THOI_LUONG  = 5       # giây
TAN_SO_1    = 440     # Hz  (La chuẩn)
TAN_SO_2    = 880     # Hz  (La quãng 8)
BIEN_DO     = 12000   # biên độ (max 32767 với 16-bit)
TEN_FILE    = "cover.wav"


def tao_tin_hieu(ty_le_mau, thoi_luong, tan_so_1, tan_so_2, bien_do):
    """Tạo tín hiệu tổ hợp hai sóng sine"""
    so_mau = int(thoi_luong * ty_le_mau)
    samples = []
    for i in range(so_mau):
        t = i / ty_le_mau
        s1 = bien_do * math.sin(2 * math.pi * tan_so_1 * t)
        s2 = (bien_do // 3) * math.sin(2 * math.pi * tan_so_2 * t)
        gia_tri = int(s1 + s2)
        # Giới hạn trong khoảng 16-bit signed
        gia_tri = max(-32768, min(32767, gia_tri))
        samples.append(gia_tri)
    return samples


def ghi_wav(ten_file, samples, ty_le_mau):
    """Ghi danh sách sample vào file WAV mono 16-bit"""
    with wave.open(ten_file, 'wb') as f:
        f.setnchannels(1)       # mono
        f.setsampwidth(2)       # 16-bit = 2 bytes
        f.setframerate(ty_le_mau)
        for s in samples:
            f.writeframes(struct.pack('<h', s))


def main():
    print("=" * 55)
    print("  Tạo file âm thanh cover (cover.wav)")
    print("=" * 55)

    samples = tao_tin_hieu(TY_LE_MAU, THOI_LUONG, TAN_SO_1, TAN_SO_2, BIEN_DO)
    ghi_wav(TEN_FILE, samples, TY_LE_MAU)

    dung_luong_toi_da = len(samples) // 8

    print(f"\n[+] Đã tạo file: {TEN_FILE}")
    print(f"    Thời lượng  : {THOI_LUONG} giây")
    print(f"    Tần số mẫu  : {TY_LE_MAU} Hz")
    print(f"    Số kênh     : 1 (mono)")
    print(f"    Độ sâu bit  : 16-bit")
    print(f"    Số sample   : {len(samples):,}")
    print(f"\n[*] Dung lượng tối đa có thể giấu: {dung_luong_toi_da:,} bytes "
          f"({dung_luong_toi_da // 1024} KB)")
    print("\n[>] Tiếp theo: chạy  python3 info_audio.py  để xem thông tin chi tiết")


if __name__ == "__main__":
    main()
