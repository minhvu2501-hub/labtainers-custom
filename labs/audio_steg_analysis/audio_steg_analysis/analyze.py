#!/usr/bin/env python3
"""
analyze.py  -  Audio Steganography Analysis Tool
=================================================
Usage:
  python3 analyze.py                          # analyze all 4 default files
  python3 analyze.py audio_A.wav audio_B.wav  # analyze specific files
  python3 analyze.py --compare                # show only MSE comparison table
"""

import wave
import math
import sys
import os
from collections import Counter

# ──────────────────────────────────────────────
#  Helpers
# ──────────────────────────────────────────────

def load_wav(filename):
    """Load WAV file, return raw bytearray and params."""
    with wave.open(filename, 'rb') as f:
        params = f.getparams()
        raw = bytearray(f.readframes(f.getnframes()))
    return raw, params


def mse(data1, data2):
    """Mean Squared Error between two byte arrays."""
    n = min(len(data1), len(data2))
    return sum((int(a) - int(b)) ** 2 for a, b in zip(data1[:n], data2[:n])) / n


def lsb_stats(raw):
    """Statistics of the Least Significant Bits."""
    lsbs = [b & 1 for b in raw]
    n = len(lsbs)
    zeros = lsbs.count(0)
    ones  = lsbs.count(1)
    expected = n / 2
    chi_sq = ((zeros - expected)**2 + (ones - expected)**2) / expected
    return zeros / n * 100, ones / n * 100, chi_sq


def lower4_chi(raw):
    """Chi-square uniformity test on the lower 4 bits (values 0-15)."""
    vals = [b & 0x0F for b in raw]
    cnt  = Counter(vals)
    expected = len(vals) / 16
    return sum((cnt.get(v, 0) - expected)**2 / expected for v in range(16))


def entropy(raw):
    """Shannon entropy (bits per byte)."""
    cnt = Counter(raw)
    n = len(raw)
    return -sum((c / n) * math.log2(c / n) for c in cnt.values() if c)


def snr_db(ref, other):
    """Signal-to-Noise Ratio in dB. Higher = more similar to ref."""
    n = min(len(ref), len(other))
    sig_pwr  = sum(int(a)**2 for a in ref[:n]) / n
    noise_pwr = sum((int(a) - int(b))**2 for a, b in zip(ref[:n], other[:n])) / n
    if noise_pwr == 0:
        return float('inf')
    return 10 * math.log10(sig_pwr / noise_pwr)


# ──────────────────────────────────────────────
#  Display helpers
# ──────────────────────────────────────────────

W = 62

def banner(text):
    print("\n" + "=" * W)
    print(f"  {text}")
    print("=" * W)


def section(title):
    print(f"\n  [{title}]")


def analyze_single(filename):
    """Full analysis of a single WAV file."""
    raw, params = load_wav(filename)
    name = os.path.basename(filename)

    print(f"\n+-- {name} " + "-" * max(1, W - len(name) - 5))
    print(f"|  Sample rate : {params.framerate} Hz | "
          f"Channels: {params.nchannels} | "
          f"Bit depth: {params.sampwidth * 8}-bit")
    print(f"|  Total bytes : {len(raw):,}")

    # --- LSB distribution ---
    z_pct, o_pct, chi = lsb_stats(raw)
    print("|")
    print("|  [LSB Distribution]")
    print(f"|    Bit=0: {z_pct:6.2f}%   Bit=1: {o_pct:6.2f}%")
    print(f"|    Chi-square (LSB): {chi:12.4f}", end="   ")
    if chi < 5:
        print("<-- Very uniform  (steganography likely!)")
    elif chi < 50:
        print("<-- Fairly uniform")
    else:
        print("<-- Non-uniform   (likely natural audio)")

    # --- Lower 4-bit distribution ---
    chi4 = lower4_chi(raw)
    print("|")
    print("|  [Lower 4-bit Distribution]")
    print(f"|    Chi-square (4-bit): {chi4:10.4f}", end="   ")
    if chi4 < 80:
        print("<-- Very uniform  (4-bit LSB stego likely!)")
    elif chi4 < 500:
        print("<-- Fairly uniform")
    else:
        print("<-- Non-uniform   (likely natural audio)")

    # --- Entropy ---
    ent = entropy(raw)
    print("|")
    print(f"|  [Entropy]  Shannon entropy: {ent:.4f} bits/byte")
    print("+" + "-" * (W - 1))

    return raw


def compare_all(files_data):
    """Print pairwise MSE and SNR comparison."""
    banner("PAIRWISE FILE COMPARISON  (MSE & SNR)")
    names = list(files_data.keys())
    header = f"  {'File 1':14s}   {'File 2':14s}   {'MSE':>12s}   {'SNR (dB)':>10s}"
    print(header)
    print("  " + "-" * (len(header) - 2))
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            n1, n2 = names[i], names[j]
            d1, d2 = files_data[n1], files_data[n2]
            m = mse(d1, d2)
            s = snr_db(d1, d2)
            print(f"  {os.path.basename(n1):14s}   {os.path.basename(n2):14s}"
                  f"   {m:12.4f}   {s:10.2f}")


def print_hints():
    """Print identification hints."""
    banner("HINTS FOR IDENTIFICATION")
    hints = [
        ("Original (cover) audio",
         "Chi-square LSB HIGHEST among the 4 files (~21000)\n"
         "     --> Natural audio has biased LSB (not 50/50 random)\n"
         "     --> Chi-sq LSB and Chi-sq 4-bit values are SIMILAR to each other"),
        ("LSB 1-bit steganography",
         "Chi-square LSB LOWER than original (~13700)\n"
         "     --> MSE vs other files is SMALLEST (~0.45) -- only 1 bit/byte changed\n"
         "     --> Entropy similar to original, LOWER than hash-based"),
        ("LSB 4-bit steganography",
         "Chi-square 4-bit EXTREMELY HIGH (~141000) -- far above all other files\n"
         "     --> Entropy LOWEST of all 4 files (~7.766)\n"
         "     --> MSE vs other files is LARGEST (~9.8 to 10.2)"),
        ("Hash-based LSB steganography",
         "Chi-square LSB similar to 1-bit (~13700) -- same amount of bits changed\n"
         "     --> Entropy HIGHEST of all 4 files (~7.897) -- random scatter increases entropy\n"
         "     --> Distinguish from 1-bit: higher entropy + Chi-sq 4-bit slightly lower"),
    ]
    for label, desc in hints:
        print(f"\n  >> {label}")
        print(f"     {desc}")
    print()


# ──────────────────────────────────────────────
#  Main
# ──────────────────────────────────────────────

def main():
    default_files = ["audio_A.wav", "audio_B.wav", "audio_C.wav", "audio_D.wav"]

    args = sys.argv[1:]
    compare_only = "--compare" in args
    args = [a for a in args if a != "--compare"]

    wav_files = args if args else default_files
    missing = [f for f in wav_files if not os.path.exists(f)]
    if missing:
        print(f"[!] Files not found: {missing}")
        sys.exit(1)

    banner("AUDIO STEGANOGRAPHY ANALYSIS TOOL  v1.0")
    print("  Analyzing audio files...\n")

    all_data = {}
    if not compare_only:
        for wav in wav_files:
            raw = analyze_single(wav)
            all_data[wav] = raw
    else:
        for wav in wav_files:
            raw, _ = load_wav(wav)
            all_data[wav] = raw

    if len(all_data) > 1:
        compare_all(all_data)

    print_hints()

    print("  Fill in your answers in answers.txt:")
    print("    original=audio_X")
    print("    lsb1bit=audio_X")
    print("    lsb4bit=audio_X")
    print("    lsb_hash=audio_X")
    print("  (replace X with A, B, C, or D)\n")


if __name__ == "__main__":
    main()
