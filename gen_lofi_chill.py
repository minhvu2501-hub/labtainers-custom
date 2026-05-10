#!/usr/bin/env python3
"""
gen_lofi_chill.py  -  Lab Asset Generator (INSTRUCTOR ONLY)
============================================================
Tạo file lofi_chill.wav đã bị nhiễm LSB steganography.
File này sẽ được đặt vào container fileserver để phục vụ cho user_pc.

Chạy script này một lần để tạo asset, sau đó đặt file WAV vào:
  fileserver/home_tar/files/lofi_chill.wav

Output:
  lofi_chill_clean.wav   - cover audio (không bị nhiễm) [tham khảo]
  lofi_chill.wav         - infected audio (đã nhúng payload LSB 1-bit)
"""

import wave
import struct
import math
import random
import os

# ── Payload C2 giả lập ──────────────────────────────────────────────
MAGIC_MARKER = "HIDDEN_CONFIDENTIAL_DATA_BLOCK_"
_UNIT   = MAGIC_MARKER
_REPEAT = 600   # lặp đủ để phủ phần đầu file (~18600 ký tự)
SECRET  = (_UNIT * _REPEAT) + "###END###"


def generate_lofi_wav(filename: str, duration: int = 6,
                      sample_rate: int = 44100):
    """Tạo WAV âm thanh lo-fi tự nhiên (cover audio)."""
    n_samples = duration * sample_rate
    rng = random.Random(42)
    frames = []

    for i in range(n_samples):
        t = i / sample_rate
        # Lo-fi chord: C major + light vibrato + gentle noise
        value = (
            math.sin(2 * math.pi * 261.63 * t) * 0.40 +   # C4
            math.sin(2 * math.pi * 329.63 * t) * 0.20 +   # E4
            math.sin(2 * math.pi * 392.00 * t) * 0.15 +   # G4
            math.sin(2 * math.pi * 130.81 * t) * 0.10 +   # C3 (bass)
            rng.uniform(-0.05, 0.05)                        # vinyl noise
        )
        # Bias LSB toward 0 (natural audio characteristic)
        sample = int(round(value * 26000 / 2) * 2)
        sample = max(-32768, min(32766, sample))
        if rng.random() < 0.28:   # 28% chance: add LSB=1
            sample += 1
            sample = min(32767, sample)
        frames.append(struct.pack('<h', sample))

    with wave.open(filename, 'w') as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(sample_rate)
        f.writeframes(b''.join(frames))
    print(f"[+] Cover audio generated  : {filename}  "
          f"({os.path.getsize(filename):,} bytes)")


def text_to_bits(text: str) -> str:
    """Chuyển text thành chuỗi bit."""
    return ''.join(format(ord(c), '08b') for c in text)


def embed_lsb_1bit(wav_in: str, wav_out: str, secret: str):
    """Nhúng payload vào bit LSB của audio samples (1-bit mode)."""
    with wave.open(wav_in, 'rb') as f:
        params = f.getparams()
        raw    = bytearray(f.readframes(f.getnframes()))

    bits = text_to_bits(secret)
    print(f"    Embedding {len(bits)} bits ({len(secret)} chars) "
          f"into {len(raw)} bytes...")

    if len(bits) > len(raw):
        print(f"    [WARN] Payload too large! Truncating to {len(raw)} bits.")
        bits = bits[:len(raw)]

    for i, bit in enumerate(bits):
        raw[i] = (raw[i] & 0xFE) | int(bit)

    with wave.open(wav_out, 'wb') as f:
        f.setparams(params)
        f.writeframes(bytes(raw))

    print(f"[+] Infected audio generated: {wav_out}  "
          f"({os.path.getsize(wav_out):,} bytes)")


if __name__ == "__main__":
    out_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "fileserver", "home_tar", "files"
    )
    os.makedirs(out_dir, exist_ok=True)

    clean_path    = os.path.join(out_dir, "lofi_chill_clean.wav")
    infected_path = os.path.join(out_dir, "lofi_chill.wav")

    print("=" * 55)
    print("  Gateway Content Disarm  —  Asset Generator")
    print("=" * 55)

    generate_lofi_wav(clean_path)
    embed_lsb_1bit(clean_path, infected_path, SECRET)

    print()
    print("=" * 55)
    print("  FILES READY:")
    print(f"  Clean    : {clean_path}")
    print(f"  Infected : {infected_path}")
    print()
    print("  Infected file chứa MAGIC_MARKER trong LSB.")
    print("  Gateway phải scrub LSB để dropper.py fail.")
    print("=" * 55)
