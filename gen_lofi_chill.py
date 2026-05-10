#!/usr/bin/env python3
"""
gen_lofi_chill.py  -  Realistic WAV Asset Generator (Instructor only)
======================================================================
5 file WAV:
  lofi_morning.wav  - CLEAN  (cover audio binh thuong)
  lofi_evening.wav  - EASY   (full sequential LSB, XOR payload → chi2~0)
  lofi_study.wav    - MEDIUM (4-bit nibble, zlib → chi4~0)
  lofi_chill.wav    - HARD   (adaptive random in high-energy → partial)
  noisy_radio.wav   - FALSE POSITIVE (nhieu nhung sach)
"""

import wave, struct, math, random, io, hashlib, zlib, os

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "fileserver", "home_tar", "files")

# ── XOR encode ────────────────────────────────────────────────────
def xor(data: bytes, key: bytes) -> bytes:
    return bytes([b ^ key[i % len(key)] for i, b in enumerate(data)])

# ── Payloads (binary encoded — not readable as text) ─────────────
_KEY1 = b"\x4B\x7A\x3F\x91"
_KEY2 = b"\xAB\xCD\xEF\x12"

# Evening: XOR encoded C2 beacon
_C2   = b"C2=185.22.10.4:4444|interval=60|campaign=APT2024|cmd=whoami"
PAYLOAD_EVENING = xor(_C2, _KEY1)  # short template, will be cycled

# Study: seeded pseudo-random binary blob -> uniform nibble distribution -> chi4~0
_rng_study = random.Random(0xDEADBEEF)
PAYLOAD_STUDY = bytes([_rng_study.randint(0, 255) for _ in range(10000)])

# Chill: XOR encoded token
_TOK  = b"API_TOKEN=XyZ-9a2b-Kp7q|sig=0xDEADBEEF|exp=2099"
PAYLOAD_CHILL   = xor(_TOK, _KEY2)

# ── Audio generation ──────────────────────────────────────────────

def make_cover(seed=42, sr=44100, dur=6) -> bytes:
    """Lo-fi mono 16-bit WAV with natural LSB bias (~60% zeros)."""
    rng = random.Random(seed)
    frames = []
    for i in range(dur * sr):
        t = i / sr
        v = (math.sin(2 * math.pi * 261.63 * t) * 0.40 +
             math.sin(2 * math.pi * 329.63 * t) * 0.20 +
             math.sin(2 * math.pi * 392.00 * t) * 0.15 +
             math.sin(2 * math.pi * 523.25 * t) * 0.08 +
             rng.gauss(0, 0.04))
        s = int(round(v * 26000 / 2) * 2)
        s = max(-32768, min(32766, s))
        if rng.random() < 0.30:
            s = min(32767, s + 1)
        frames.append(struct.pack("<h", s))
    buf = io.BytesIO()
    with wave.open(buf, "w") as f:
        f.setnchannels(1); f.setsampwidth(2); f.setframerate(sr)
        f.writeframes(b"".join(frames))
    return buf.getvalue()


def make_noisy_radio(sr=44100, dur=6) -> bytes:
    """False positive: hard-clipped distorted audio — clean LSBs."""
    rng = random.Random(99)
    frames = []
    for i in range(dur * sr):
        t = i / sr
        v = (math.sin(2 * math.pi * 440.0 * t) * 0.9 +
             rng.gauss(0, 0.5))
        v = max(-1.0, min(1.0, v))
        s = int(v * 32000)
        # Preserve natural LSB bias via even rounding
        s = int(round(s / 2) * 2)
        s = max(-32768, min(32766, s))
        if rng.random() < 0.31:
            s = min(32767, s + 1)
        frames.append(struct.pack("<h", s))
    buf = io.BytesIO()
    with wave.open(buf, "w") as f:
        f.setnchannels(1); f.setsampwidth(2); f.setframerate(sr)
        f.writeframes(b"".join(frames))
    return buf.getvalue()


# ── Wav helpers ───────────────────────────────────────────────────

def rw(data: bytes):
    buf = io.BytesIO(data)
    with wave.open(buf, "rb") as f:
        p = f.getparams(); r = bytearray(f.readframes(f.getnframes()))
    return r, p

def tw(raw: bytearray, params) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as f:
        f.setparams(params); f.writeframes(bytes(raw))
    return buf.getvalue()

def to_bits(data: bytes) -> list:
    return [int(b) for byte in data for b in format(byte, "08b")]

def cycled_bits(payload: bytes, n: int) -> list:
    """Cycle payload bits to fill n positions."""
    raw_bits = to_bits(payload)
    result = []
    while len(result) < n:
        result.extend(raw_bits)
    return result[:n]


# ── Embedding methods ─────────────────────────────────────────────

def embed_full_lsb1(wav: bytes, payload: bytes) -> bytes:
    """
    EASY: Full sequential LSB — fills ENTIRE file with cycled payload bits.
    chi2 → near 0 (50/50 distribution). Printable ratio low (XOR payload).
    Detection: chi-square primary.
    """
    r, p = rw(wav)
    bits  = cycled_bits(payload, len(r))
    for i, bit in enumerate(bits):
        r[i] = (r[i] & 0xFE) | bit
    return tw(r, p)


def embed_4bit_lsb(wav: bytes, payload: bytes) -> bytes:
    """
    MEDIUM: Lower 4-bit nibble embedding — fills ~50% of file with zlib blob.
    chi4 → near 0. chi2 moderate (50% coverage).
    Detection: 4-bit chi-square primary.
    """
    r, p = rw(wav)
    bits  = cycled_bits(payload, len(r) * 4)  # 4 bits per byte
    for i in range(0, len(r) * 4, 4):
        idx     = i // 4
        nibble  = int("".join(str(b) for b in bits[i:i + 4]), 2)
        r[idx]  = (r[idx] & 0xF0) | nibble
    return tw(r, p)


def embed_adaptive(wav: bytes, payload: bytes,
                   key: str = "lab_adap_2024",
                   threshold: int = 8000) -> bytes:
    """
    HARD: Embed only in high-energy samples (|sample| > threshold).
    Avoids statistical flattening in silent regions.
    ~30-40% coverage → chi2 moderately suspicious.
    Detection: combination of chi2 + entropy + run-length variance.
    """
    r, p  = rw(wav)
    n_s   = len(r) // 2

    eligible = []
    for i in range(n_s):
        sample = struct.unpack_from("<h", r, i * 2)[0]
        if abs(sample) > threshold:
            eligible.append(i * 2)      # byte index of low byte

    # Deterministic shuffle with key
    rng = random.Random(int(hashlib.sha256(key.encode()).hexdigest(), 16))
    rng.shuffle(eligible)

    bits = cycled_bits(payload, len(eligible))
    for pos, bit in zip(eligible, bits):
        r[pos] = (r[pos] & 0xFE) | bit
    return tw(r, p)


# ── Save ──────────────────────────────────────────────────────────

def save(path: str, data: bytes):
    with open(path, "wb") as f: f.write(data)
    print(f"  [+] {os.path.basename(path):22s}  {len(data):>9,} bytes")


# ── Main ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    os.makedirs(OUT_DIR, exist_ok=True)
    print("=" * 60)
    print("  WAV Asset Generator  -  gateway_content_disarm")
    print("=" * 60)
    print(f"  Output: {OUT_DIR}\n")

    cover = make_cover()

    save(f"{OUT_DIR}/lofi_morning.wav", cover)
    save(f"{OUT_DIR}/lofi_evening.wav", embed_full_lsb1(cover, PAYLOAD_EVENING))
    save(f"{OUT_DIR}/lofi_study.wav",   embed_4bit_lsb(cover,  PAYLOAD_STUDY))
    save(f"{OUT_DIR}/lofi_chill.wav",   embed_adaptive(cover,  PAYLOAD_CHILL))
    save(f"{OUT_DIR}/noisy_radio.wav",  make_noisy_radio())

    print()
    print("  TECHNIQUE SUMMARY:")
    print("  lofi_morning.wav  -> CLEAN       (natural cover audio)")
    print("  lofi_evening.wav  -> EASY        full LSB, XOR encoded   -> chi2~0")
    print("  lofi_study.wav    -> MEDIUM      4-bit nibble, random    -> chi4~0")
    print("  lofi_chill.wav    -> HARD        adaptive high-energy    -> partial")
    print("  noisy_radio.wav   -> FALSE POS   clipped clean audio")
    print("=" * 60)
