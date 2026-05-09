#!/usr/bin/env python3
"""
gen_audio.py - Lab Asset Generator
Generates 4 audio files for the audio_steg_analysis Labtainer lab.

Output:
  audio_A.wav  ->  original cover (no steganography)
  audio_B.wav  ->  LSB 1-bit steganography
  audio_C.wav  ->  LSB 4-bit steganography
  audio_D.wav  ->  Hash-based LSB steganography

INSTRUCTOR ONLY - do not distribute to students.
"""
import wave
import struct
import math
import hashlib
import os
import random

END_MARKER = "###END###"

# Audio is 529200 bytes.
# To get GLOBAL LSB change visible:
#   1-bit: need to fill >= 50% of file  -> 529200/2 = 264600 bytes of chars
#   4-bit: 264600 / 4 = 66150 chars
# We embed a string long enough to cover the entire file in 1-bit mode.
_UNIT = "HIDDEN_CONFIDENTIAL_DATA_BLOCK_"   # 31 chars
_REPEAT = 529200 // (len(_UNIT) * 8) + 2    # enough repetitions for 1-bit
SECRET = (_UNIT * _REPEAT) + END_MARKER     # ~66KB+


# ── Audio generation ──────────────────────────────────────────── #

def generate_cover_wav(filename, duration=6, sample_rate=44100):
    """
    Generate a WAV whose LSB is biased ~70% zero / 30% one.
    This makes the original file clearly distinguishable from stego files.
    """
    n_samples = duration * sample_rate
    rng = random.Random(7)
    frames = []

    for i in range(n_samples):
        t = i / sample_rate
        value = (
            math.sin(2 * math.pi * 261.63 * t) * 0.55 +
            math.sin(2 * math.pi * 329.63 * t) * 0.25 +
            math.sin(2 * math.pi * 392.00 * t) * 0.15 +
            math.sin(2 * math.pi * 130.81 * t) * 0.05
        )
        # Round to even -> LSB = 0; only flip 30% of the time
        sample = int(round(value * 28000 / 2) * 2)
        sample = max(-32768, min(32766, sample))
        if rng.random() < 0.30:
            sample += 1
            sample = min(32767, sample)
        frames.append(struct.pack('<h', sample))

    with wave.open(filename, 'w') as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(sample_rate)
        f.writeframes(b''.join(frames))
    print(f"[+] Cover audio generated : {filename}")


# ── Steganography helpers ─────────────────────────────────────── #

def text_to_bits(text):
    return ''.join(format(ord(c), '08b') for c in text)


def embed_1bit(raw: bytearray, bits: str) -> bytearray:
    for i, bit in enumerate(bits):
        if i >= len(raw):
            break
        raw[i] = (raw[i] & 0xFE) | int(bit)
    return raw


def embed_4bit(raw: bytearray, bits: str) -> bytearray:
    for i in range(0, len(bits), 4):
        chunk = bits[i:i+4].ljust(4, '0')
        value = int(chunk, 2)
        idx = i // 4
        if idx >= len(raw):
            break
        raw[idx] = (raw[idx] & 0xF0) | value
    return raw


def embed_hash(raw: bytearray, bits: str, key: str = "lab_secret_key") -> bytearray:
    """
    Scatter-write bits at positions derived from key+index.
    Optimised: derive position with a fast LCG seeded by SHA-256,
    rather than calling SHA-256 for every bit.
    """
    n = len(raw)
    # Seed a PRNG from the key (SHA-256 -> 32-byte seed -> int)
    seed_int = int(hashlib.sha256(key.encode()).hexdigest(), 16)
    rng = random.Random(seed_int)

    # Draw n unique positions (Fisher-Yates shuffle of range)
    positions = list(range(n))
    rng.shuffle(positions)

    # Write each bit to its assigned position
    for i, bit in enumerate(bits):
        if i >= n:
            break
        pos = positions[i]
        raw[pos] = (raw[pos] & 0xFE) | int(bit)
    return raw


def write_stego_wav(input_wav: str, output_wav: str, mode: str):
    with wave.open(input_wav, 'rb') as f:
        params = f.getparams()
        raw = bytearray(f.readframes(f.getnframes()))

    bits = text_to_bits(SECRET)
    print(f"    Embedding {len(bits)} bits ({len(SECRET)} chars) into {len(raw)} bytes ...")

    if mode == "1bit":
        raw = embed_1bit(raw, bits)
    elif mode == "4bit":
        raw = embed_4bit(raw, bits)
    elif mode == "hash":
        raw = embed_hash(raw, bits)
    else:
        raise ValueError(f"Unknown mode: {mode}")

    with wave.open(output_wav, 'wb') as f:
        f.setparams(params)
        f.writeframes(bytes(raw))
    print(f"[+] {mode:6s} stego generated: {output_wav}")


# ── Main ─────────────────────────────────────────────────────── #

if __name__ == "__main__":
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "home_tar", "files")
    os.makedirs(out_dir, exist_ok=True)

    cover_path = os.path.join(out_dir, "audio_A.wav")
    generate_cover_wav(cover_path)

    write_stego_wav(cover_path, os.path.join(out_dir, "audio_B.wav"), "1bit")
    write_stego_wav(cover_path, os.path.join(out_dir, "audio_C.wav"), "4bit")
    write_stego_wav(cover_path, os.path.join(out_dir, "audio_D.wav"), "hash")

    print()
    print("=" * 55)
    print("  LAB FILES READY  (INSTRUCTOR ANSWER KEY)")
    print("=" * 55)
    print("  audio_A.wav  =  original  (no steganography)")
    print("  audio_B.wav  =  lsb1bit   (1-bit LSB)")
    print("  audio_C.wav  =  lsb4bit   (4-bit LSB)")
    print("  audio_D.wav  =  lsb_hash  (hash-based LSB)")
    print("=" * 55)
