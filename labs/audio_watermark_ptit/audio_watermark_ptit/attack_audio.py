#!/usr/bin/env python3
"""
attack_audio.py - Mô phỏng tấn công thay đổi âm lượng và cộng nhiễu lên file nhạc
=============================================================================
Bài thực hành: Thủy vân số bản quyền âm thanh (LSB vs Phase Coding)
B22DCAT196 - Vũ Lâm Minh (PTIT)
"""

import wave
import struct
import sys
import os
import random

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

def main():
    lsb_file = "watermark_lsb.wav"
    phase_file = "watermark_phase.wav"

    if not os.path.exists(lsb_file) or not os.path.exists(phase_file):
        print("[!] Không tìm thấy watermark_lsb.wav hoặc watermark_phase.wav.")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("  TIẾN HÀNH TẤN CÔNG ÂM THANH - B22DCAT196")
    print("=" * 60)

    # 1. Đọc dữ liệu các file stego
    samples_lsb, params_lsb = doc_wav(lsb_file)
    samples_phase, params_phase = doc_wav(phase_file)

    # --- TẤN CÔNG ÂM LƯỢNG (Volume Attack - Nhân biên độ với 0.9) ---
    print("  [*] Áp dụng Tấn công âm lượng (Volume Attack * 0.9)...")
    vol_lsb = [int(s * 0.9) for s in samples_lsb]
    vol_phase = [int(s * 0.9) for s in samples_phase]
    ghi_wav("attack_vol_lsb.wav", vol_lsb, params_lsb)
    ghi_wav("attack_vol_phase.wav", vol_phase, params_phase)

    # --- TẤN CÔNG CỘNG NHIỄU (Noise Attack - Cộng ngẫu nhiên từ -3 đến 3) ---
    print("  [*] Áp dụng Tấn công cộng nhiễu (Noise Attack)...")
    random.seed(196) # Cố định seed
    noise_lsb = [s + random.randint(-3, 3) for s in samples_lsb]
    noise_phase = [s + random.randint(-3, 3) for s in samples_phase]
    ghi_wav("attack_noise_lsb.wav", noise_lsb, params_lsb)
    ghi_wav("attack_noise_phase.wav", noise_phase, params_phase)

    print("\n[+] Đã tạo các tệp âm thanh bị tấn công thành công!")
    print("    - attack_vol_lsb.wav, attack_vol_phase.wav")
    print("    - attack_noise_lsb.wav, attack_noise_phase.wav")
    print("\n[>] Tiếp theo: python3 watermark_extract.py")
    print("=" * 60 + "\n")

if __name__ == "__main__":
    main()
