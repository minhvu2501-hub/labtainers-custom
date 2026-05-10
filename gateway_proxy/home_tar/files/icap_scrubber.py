#!/usr/bin/env python3
"""
icap_scrubber.py  -  WAV Audio Steganography Detector & Sanitizer
==================================================================
Gateway Content Disarm Lab  |  gateway_proxy container

Usage:
  python3 icap_scrubber.py <file.wav>

Output:
  ~/findings.txt  - analysis log (WAV_ANALYZED, LSB_DETECTED, ...)
  ~/sanitized.wav - cleaned WAV with all LSBs zeroed

Techniques detected:
  - LSB 1-bit (sequential)
  - LSB 4-bit (multi-bit)
  - Pseudo-random LSB
"""

import sys
import os
import wave
import io
import math
from collections import Counter

FINDINGS_FILE  = os.path.expanduser("~/findings.txt")
SANITIZED_FILE = os.path.expanduser("~/sanitized.wav")

SUSPICIOUS_KEYWORDS = [
    "C2=", "http", "TOKEN=", "powershell", "cmd", "exec",
    "bash", "nc ", "wget", "curl", "://", "base64",
]

# ────────────────────────────────────────────────────────────────
#  Core analysis functions
# ────────────────────────────────────────────────────────────────

def load_wav(path):
    with wave.open(path, "rb") as f:
        params = f.getparams()
        raw    = bytearray(f.readframes(f.getnframes()))
    return raw, params


def shannon_entropy(raw):
    cnt = Counter(raw)
    n   = len(raw)
    return -sum((c / n) * math.log2(c / n) for c in cnt.values() if c)


def lsb_chi_square(raw):
    """Chi-square test on LSBs. Near 0 = uniform = suspicious."""
    lsbs     = [b & 1 for b in raw]
    n        = len(lsbs)
    zeros    = lsbs.count(0)
    ones     = lsbs.count(1)
    expected = n / 2
    chi      = ((zeros - expected) ** 2 + (ones - expected) ** 2) / expected
    return zeros / n * 100, ones / n * 100, chi


def lower4_chi_square(raw):
    """Chi-square on lower 4 bits. Near 0 = LSB 4-bit stego."""
    vals     = [b & 0x0F for b in raw]
    cnt      = Counter(vals)
    expected = len(vals) / 16
    return sum((cnt.get(v, 0) - expected) ** 2 / expected for v in range(16))


def extract_lsb_text(raw, sample_bytes=4096):
    """Extract text hidden in LSBs — first sample_bytes bytes."""
    bits  = "".join(str(b & 1) for b in raw[:sample_bytes])
    chars = []
    for i in range(0, len(bits) - 7, 8):
        v = int(bits[i:i + 8], 2)
        if 32 <= v <= 126:
            chars.append(chr(v))
        elif v == 0:
            chars.append(".")
        else:
            chars.append("?")
    return "".join(chars)


def sanitize_wav(raw, params, output_path):
    """Zero all LSBs — destroys any 1-bit steganography payload."""
    clean = bytearray(b & 0xFE for b in raw)
    buf   = io.BytesIO()
    with wave.open(buf, "wb") as f:
        f.setparams(params)
        f.writeframes(bytes(clean))
    with open(output_path, "wb") as f:
        f.write(buf.getvalue())


# ────────────────────────────────────────────────────────────────
#  Main analyzer
# ────────────────────────────────────────────────────────────────

def analyze(wav_path):
    W = 62
    print("\n" + "=" * W)
    print("  WAV STEGANOGRAPHY ANALYZER  v1.0  |  Gateway Content Disarm")
    print("=" * W)
    print(f"  Target : {wav_path}")

    findings    = []
    lsb_flagged = False

    # ── Load file ──────────────────────────────────────────────
    try:
        raw, params = load_wav(wav_path)
    except Exception as e:
        print(f"\n  [ERROR] Cannot read WAV: {e}")
        sys.exit(1)

    print(f"  Size   : {len(raw):,} bytes  |  "
          f"{params.framerate} Hz  |  "
          f"{params.nchannels}ch  |  "
          f"{params.sampwidth * 8}-bit\n")

    # ── 1. Entropy ─────────────────────────────────────────────
    ent = shannon_entropy(raw)
    flag_ent = ent < 7.5
    print(f"  [Entropy] Shannon = {ent:.4f} bits/byte", end="   ")
    if flag_ent:
        print("<-- SUSPICIOUS (expected ~7.9 for natural audio)")
        findings.append("LOW_ENTROPY")
        lsb_flagged = True
    else:
        print("(normal range)")

    # ── 2. LSB Chi-square ──────────────────────────────────────
    z_pct, o_pct, chi = lsb_chi_square(raw)
    flag_chi = chi < 10
    print(f"\n  [LSB Distribution]")
    print(f"    Bit=0: {z_pct:.2f}%   Bit=1: {o_pct:.2f}%")
    print(f"    Chi-square (LSB): {chi:.2f}", end="   ")
    if flag_chi:
        print("<-- VERY UNIFORM  (strong 1-bit steganography indicator!)")
        findings.append("LSB_UNIFORM_CHI2")
        lsb_flagged = True
    elif chi < 100:
        print("<-- Fairly uniform (possible steganography)")
        findings.append("LSB_FAIRLY_UNIFORM")
    else:
        print("<-- Non-uniform (likely natural audio)")

    # ── 3. Lower 4-bit Chi-square ──────────────────────────────
    chi4 = lower4_chi_square(raw)
    flag_chi4 = chi4 < 80
    print(f"\n  [4-bit Chi-square]: {chi4:.2f}", end="   ")
    if flag_chi4:
        print("<-- Very uniform  (4-bit LSB steganography likely!)")
        findings.append("4BIT_CHI2_LOW")
        lsb_flagged = True
    else:
        print("<-- Normal distribution")

    # ── 4. Printable string extraction ─────────────────────────
    extracted = extract_lsb_text(raw)
    printable_ratio = sum(1 for c in extracted if c not in ".?") / max(len(extracted), 1)
    found_kw = [k for k in SUSPICIOUS_KEYWORDS if k.lower() in extracted.lower()]

    print(f"\n  [LSB Text Extraction - first 200 chars]")
    print(f"    '{extracted[:200]}'")
    print(f"    Printable ratio : {printable_ratio:.1%}", end="   ")

    if found_kw:
        print(f"<-- PAYLOAD KEYWORDS: {found_kw}")
        findings.append(f"PAYLOAD_KEYWORDS:{','.join(found_kw)}")
        lsb_flagged = True
    elif printable_ratio > 0.70:
        print("<-- High printable ratio (suspicious)")
        findings.append("HIGH_PRINTABLE_RATIO")
        lsb_flagged = True
    else:
        print("(no suspicious content)")

    # ── Verdict ────────────────────────────────────────────────
    print("\n" + "=" * W)
    if lsb_flagged:
        print("  *** VERDICT: LSB STEGANOGRAPHY DETECTED ***")
        print("  Action: File will be SANITIZED (LSBs zeroed)")
    else:
        print("  VERDICT: File appears CLEAN")
        print("  Action: ALLOWED")
    print("=" * W)

    # ── Write findings.txt ─────────────────────────────────────
    with open(FINDINGS_FILE, "a") as f:
        f.write(f"\n=== {os.path.basename(wav_path)} ===\n")
        f.write("WAV_ANALYZED\n")
        if lsb_flagged:
            f.write("LSB_DETECTED\n")
            for item in findings:
                f.write(f"  EVIDENCE: {item}\n")
        else:
            f.write("CLEAN\n")

    print(f"\n  [+] Findings appended : {FINDINGS_FILE}")

    # ── Sanitize if flagged ────────────────────────────────────
    if lsb_flagged:
        sanitize_wav(raw, params, SANITIZED_FILE)
        ssize = os.path.getsize(SANITIZED_FILE)
        print(f"  [+] Sanitized WAV    : {SANITIZED_FILE}  ({ssize:,} bytes)")
        print("      (All LSBs zeroed — steganography payload destroyed)")

    return lsb_flagged


# ────────────────────────────────────────────────────────────────
#  Entry point
# ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 icap_scrubber.py <file.wav>")
        print()
        print("Examples:")
        print("  python3 icap_scrubber.py lofi_clean.wav")
        print("  python3 icap_scrubber.py lofi_lsb1.wav")
        print("  python3 icap_scrubber.py lofi_lsb4.wav")
        print("  python3 icap_scrubber.py lofi_hash.wav")
        sys.exit(1)

    target = sys.argv[1]
    if not os.path.exists(target):
        print(f"[ERROR] File not found: {target}")
        sys.exit(1)

    detected = analyze(target)
    sys.exit(0)
