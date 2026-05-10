#!/usr/bin/env python3
"""
gen_lofi_chill.py  -  Lab Asset Generator (INSTRUCTOR ONLY)
============================================================
Tao 4 file WAV cho lab gateway_content_disarm:
  lofi_clean.wav  - file nhac binh thuong (khong payload)
  lofi_lsb1.wav   - LSB 1-bit: "C2=185.22.10.4:4444"
  lofi_lsb4.wav   - LSB 4-bit: "powershell -enc <base64>"
  lofi_hash.wav   - Pseudo-random LSB: "TOKEN=ABCD-1234-XYZ"

Output dir: fileserver/home_tar/files/
"""

import wave
import struct
import math
import random
import hashlib
import io
import os

# ── Payloads ─────────────────────────────────────────────────────
PAYLOAD_LSB1 = "C2=185.22.10.4:4444" * 300 + "###END###"
PAYLOAD_LSB4 = ("powershell -enc " + "A" * 200) * 20 + "###END###"
PAYLOAD_HASH = "TOKEN=ABCD-1234-XYZ" * 300 + "###END###"


# ── Audio generation ─────────────────────────────────────────────

def generate_cover_wav(duration=6, sample_rate=44100) -> bytes:
    """Lo-fi cover audio with natural LSB bias (not uniform)."""
    n_samples = duration * sample_rate
    rng = random.Random(42)
    frames = []
    for i in range(n_samples):
        t = i / sample_rate
        value = (
            math.sin(2 * math.pi * 261.63 * t) * 0.40 +
            math.sin(2 * math.pi * 329.63 * t) * 0.20 +
            math.sin(2 * math.pi * 392.00 * t) * 0.15 +
            math.sin(2 * math.pi * 130.81 * t) * 0.10 +
            rng.uniform(-0.05, 0.05)
        )
        # Round to even -> LSB=0, flip 28% -> natural bias
        sample = int(round(value * 26000 / 2) * 2)
        sample = max(-32768, min(32766, sample))
        if rng.random() < 0.28:
            sample += 1
            sample = min(32767, sample)
        frames.append(struct.pack("<h", sample))

    buf = io.BytesIO()
    with wave.open(buf, "w") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(sample_rate)
        f.writeframes(b"".join(frames))
    return buf.getvalue()


def wav_bytes_to_raw(wav_bytes):
    buf = io.BytesIO(wav_bytes)
    with wave.open(buf, "rb") as f:
        params = f.getparams()
        raw    = bytearray(f.readframes(f.getnframes()))
    return raw, params


def raw_to_wav_bytes(raw, params):
    buf = io.BytesIO()
    with wave.open(buf, "wb") as f:
        f.setparams(params)
        f.writeframes(bytes(raw))
    return buf.getvalue()


def text_to_bits(text):
    return "".join(format(ord(c), "08b") for c in text)


# ── Embedding methods ─────────────────────────────────────────────

def embed_lsb1(wav_bytes, secret):
    """1-bit sequential LSB embedding."""
    raw, params = wav_bytes_to_raw(wav_bytes)
    bits = text_to_bits(secret)[:len(raw)]
    for i, bit in enumerate(bits):
        raw[i] = (raw[i] & 0xFE) | int(bit)
    return raw_to_wav_bytes(raw, params)


def embed_lsb4(wav_bytes, secret):
    """4-bit LSB embedding (lower nibble)."""
    raw, params = wav_bytes_to_raw(wav_bytes)
    bits = text_to_bits(secret)
    for i in range(0, min(len(bits), len(raw) * 4), 4):
        chunk = bits[i:i + 4].ljust(4, "0")
        idx   = i // 4
        if idx >= len(raw):
            break
        raw[idx] = (raw[idx] & 0xF0) | int(chunk, 2)
    return raw_to_wav_bytes(raw, params)


def embed_hash(wav_bytes, secret, key="lab_key_2024"):
    """Pseudo-random LSB embedding using key-seeded PRNG."""
    raw, params = wav_bytes_to_raw(wav_bytes)
    n           = len(raw)
    seed_int    = int(hashlib.sha256(key.encode()).hexdigest(), 16)
    rng         = random.Random(seed_int)
    positions   = list(range(n))
    rng.shuffle(positions)
    bits = text_to_bits(secret)
    for i, bit in enumerate(bits):
        if i >= n:
            break
        pos        = positions[i]
        raw[pos]   = (raw[pos] & 0xFE) | int(bit)
    return raw_to_wav_bytes(raw, params)


# ── Main ──────────────────────────────────────────────────────────

def save(path, data):
    with open(path, "wb") as f:
        f.write(data)
    size = len(data)
    print(f"  [+] {os.path.basename(path):25s}  {size:>9,} bytes")


if __name__ == "__main__":
    out_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "fileserver", "home_tar", "files"
    )
    os.makedirs(out_dir, exist_ok=True)

    print("=" * 55)
    print("  gateway_content_disarm  -  WAV Asset Generator")
    print("=" * 55)
    print(f"  Output: {out_dir}\n")

    # 1. Cover audio
    cover = generate_cover_wav()
    save(os.path.join(out_dir, "lofi_morning.wav"), cover)

    # 2. LSB 1-bit: C2 beacon
    lsb1 = embed_lsb1(cover, PAYLOAD_LSB1)
    save(os.path.join(out_dir, "lofi_evening.wav"), lsb1)

    # 3. LSB 4-bit: PowerShell command
    lsb4 = embed_lsb4(cover, PAYLOAD_LSB4)
    save(os.path.join(out_dir, "lofi_study.wav"), lsb4)

    # 4. Hash/pseudo-random: API token
    lsb_hash = embed_hash(cover, PAYLOAD_HASH)
    save(os.path.join(out_dir, "lofi_chill.wav"), lsb_hash)

    print()
    print("  PAYLOADS EMBEDDED:")
    print(f"  lofi_evening.wav -> LSB 1-bit : '{PAYLOAD_LSB1[:30]}...'")
    print(f"  lofi_study.wav   -> LSB 4-bit : '{PAYLOAD_LSB4[:30]}...'")
    print(f"  lofi_chill.wav   -> Hash LSB  : '{PAYLOAD_HASH[:30]}...'")
    print("=" * 55)
