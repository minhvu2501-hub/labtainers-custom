#!/usr/bin/env python3
"""
icap_scrubber.py  -  WAV Steganography Analyzer & Gateway CDR Tool
===================================================================
Gateway Content Disarm Lab  |  gateway_proxy container

Usage:
  python3 icap_scrubber.py <file.wav>

Output:
  ~/findings.txt   - analysis log with risk score
  ~/sanitized.wav  - sanitized file (if SANITIZE or BLOCK)

Risk Levels:
  0-39   -> ALLOW    (clean or low suspicion)
  40-69  -> SANITIZE (suspicious, sanitize before forwarding)
  70-100 -> BLOCK    (high confidence steganography)
"""

import sys, os, wave, io, math, struct
from collections import Counter

FINDINGS_FILE  = os.path.expanduser("~/findings.txt")
SANITIZED_FILE = os.path.expanduser("~/sanitized.wav")

# ────────────────────────────────────────────────────────────────
#  Statistical analysis functions
# ────────────────────────────────────────────────────────────────

def load_wav(path):
    with wave.open(path, "rb") as f:
        params = f.getparams()
        raw    = bytearray(f.readframes(f.getnframes()))
    return raw, params


def shannon_entropy(raw):
    cnt = Counter(raw); n = len(raw)
    return -sum((c / n) * math.log2(c / n) for c in cnt.values() if c)


def lsb_chi_square(raw):
    """Chi-square on LSBs. Near 0 = suspiciously uniform."""
    lsbs     = [b & 1 for b in raw]
    n        = len(lsbs)
    zeros    = lsbs.count(0)
    expected = n / 2
    chi      = ((zeros - expected) ** 2 + (n - zeros - expected) ** 2) / expected
    return zeros / n * 100, (n - zeros) / n * 100, chi


def lower4_chi_square(raw):
    """Chi-square on lower 4 bits. Near 0 = 4-bit stego."""
    vals     = [b & 0x0F for b in raw]
    cnt      = Counter(vals)
    expected = len(vals) / 16
    return sum((cnt.get(v, 0) - expected) ** 2 / expected for v in range(16))


def lsb_sample_variance(raw):
    """Variance of LSB run lengths. Stego LSBs have shorter runs."""
    lsbs = [b & 1 for b in raw[:20000]]
    runs = []; cur = 1
    for i in range(1, len(lsbs)):
        if lsbs[i] == lsbs[i - 1]:
            cur += 1
        else:
            runs.append(cur); cur = 1
    if not runs: return 0
    mean = sum(runs) / len(runs)
    return sum((r - mean) ** 2 for r in runs) / len(runs)


def extract_lsb_sample(raw, n_bytes=512):
    """Extract text from sequential LSBs — first n_bytes worth."""
    bits = "".join(str(b & 1) for b in raw[:n_bytes * 8])
    chars = []
    for i in range(0, len(bits) - 7, 8):
        v = int(bits[i:i + 8], 2)
        chars.append(chr(v) if 32 <= v <= 126 else ("." if v == 0 else "\x00"))
    text = "".join(chars)
    printable = sum(1 for c in text if 32 <= ord(c) <= 126) / max(len(text), 1)
    keywords   = ["C2=", "TOKEN=", "powershell", "http://", "https://",
                  "cmd", "exec", "bash", "wget", "curl", "base64"]
    found_kw   = [k for k in keywords if k.lower() in text.lower()]
    return text, printable, found_kw


def sanitize_wav(raw, params, path):
    """Zero all LSBs (1-bit sanitize) — destroys sequential stego."""
    clean = bytearray(b & 0xFE for b in raw)
    buf   = io.BytesIO()
    with wave.open(buf, "wb") as f:
        f.setparams(params); f.writeframes(bytes(clean))
    with open(path, "wb") as f: f.write(buf.getvalue())


# ────────────────────────────────────────────────────────────────
#  Risk scoring
# ────────────────────────────────────────────────────────────────

def compute_risk(chi2, chi4, entropy, printable, found_kw, run_var):
    score = 0; reasons = []

    # Chi-square on LSBs (primary detector)
    if chi2 < 200:
        score += 55; reasons.append(f"LSB_CHI2_CRITICAL({chi2:.1f})")
    elif chi2 < 2000:
        score += 25; reasons.append(f"LSB_CHI2_LOW({chi2:.1f})")
    elif chi2 < 5000:
        score += 10; reasons.append(f"LSB_CHI2_MODERATE({chi2:.1f})")

    # Chi-square on lower 4 bits
    if chi4 < 50:
        score += 35; reasons.append(f"4BIT_CHI2_CRITICAL({chi4:.1f})")
    elif chi4 < 700:
        score += 20; reasons.append(f"4BIT_CHI2_LOW({chi4:.1f})")
    elif chi4 < 5000:
        score += 8;  reasons.append(f"4BIT_CHI2_MODERATE({chi4:.1f})")

    # Entropy anomaly
    if entropy < 7.2:
        score += 15; reasons.append(f"LOW_ENTROPY({entropy:.3f})")
    elif entropy > 7.95:
        score += 5;  reasons.append(f"HIGH_ENTROPY({entropy:.3f})")

    # Printable keywords (plaintext payload — easy mode)
    if found_kw:
        score += 20; reasons.append(f"KEYWORDS:{found_kw}")
    elif printable > 0.75:
        score += 10; reasons.append(f"HIGH_PRINTABLE({printable:.0%})")

    # Run-length variance (shorter runs = more uniform = stego)
    if run_var < 1.2:
        score += 10; reasons.append(f"LOW_RUN_VAR({run_var:.2f})")

    return min(score, 100), reasons


def verdict(score):
    if score >= 70:
        return "BLOCK",    "*** MALWARE DETECTED — FILE BLOCKED ***"
    elif score >= 40:
        return "SANITIZE", "SUSPICIOUS — sanitizing before forwarding"
    else:
        return "ALLOW",    "CLEAN — forwarding to user"


# ────────────────────────────────────────────────────────────────
#  Main analyzer
# ────────────────────────────────────────────────────────────────

def analyze(wav_path):
    W = 62
    print(f"\n{'='*W}")
    print(f"  GATEWAY CDR ANALYZER  |  {os.path.basename(wav_path)}")
    print(f"{'='*W}")

    try:
        raw, params = load_wav(wav_path)
    except Exception as e:
        print(f"\n  [ERROR] Cannot read WAV: {e}"); sys.exit(1)

    print(f"  Size   : {len(raw):,} bytes")
    print(f"  Format : {params.framerate}Hz | {params.nchannels}ch | {params.sampwidth*8}-bit")

    # ── Tests ──────────────────────────────────────────────────
    ent            = shannon_entropy(raw)
    z_pct, o_pct, chi2 = lsb_chi_square(raw)
    chi4           = lower4_chi_square(raw)
    run_var        = lsb_sample_variance(raw)
    text, pr, kw   = extract_lsb_sample(raw)

    print(f"\n  {'Test':<28} {'Value':>12}  {'Interpretation'}")
    print(f"  {'-'*58}")

    def row(label, val, interp): print(f"  {label:<28} {val:>12}  {interp}")

    row("Entropy (bits/byte)",   f"{ent:.4f}",
        "<-- ANOMALY" if ent < 7.2 else ("HIGH (possible noise)" if ent > 7.95 else "normal"))
    row("LSB Chi-square",        f"{chi2:.2f}",
        "<-- CRITICAL (stego!)" if chi2 < 5 else
        ("<-- LOW (suspicious)" if chi2 < 200 else "normal"))
    row("4-bit Chi-square",      f"{chi4:.2f}",
        "<-- CRITICAL (4-bit stego!)" if chi4 < 30 else
        ("<-- LOW (suspicious)" if chi4 < 500 else "normal"))
    row("LSB Run-length var",    f"{run_var:.3f}",
        "<-- LOW (too uniform)" if run_var < 1.2 else "normal")
    row("LSB Printable ratio",   f"{pr:.1%}",
        f"<-- KEYWORDS: {kw}" if kw else
        ("<-- HIGH" if pr > 0.75 else "normal"))

    print(f"\n  [LSB text sample]")
    display = text[:120].replace("\x00", ".")
    print(f"  '{display}'")

    # ── Scoring ────────────────────────────────────────────────
    score, reasons = compute_risk(chi2, chi4, ent, pr, kw, run_var)
    action, msg    = verdict(score)

    risk_bar = "█" * (score // 5) + "░" * (20 - score // 5)
    print(f"\n  {'='*W}")
    print(f"  Risk Score  : {score}/100  [{risk_bar}]")
    print(f"  Action      : {action}")
    print(f"  Reason      : {msg}")
    print(f"  Evidence    : {', '.join(reasons) if reasons else 'none'}")
    print(f"  {'='*W}")

    # ── Write findings.txt ─────────────────────────────────────
    with open(FINDINGS_FILE, "a") as f:
        f.write(f"\n=== {os.path.basename(wav_path)} ===\n")
        f.write("WAV_ANALYZED\n")
        f.write(f"RISK_SCORE={score}\n")
        f.write(f"ACTION={action}\n")
        if score >= 40:
            f.write("LSB_DETECTED\n")
            for r in reasons:
                f.write(f"  EVIDENCE: {r}\n")
        else:
            f.write("CLEAN\n")
    print(f"\n  [+] Findings written : {FINDINGS_FILE}")

    # ── Sanitize if SANITIZE or BLOCK ─────────────────────────
    if action in ("SANITIZE", "BLOCK"):
        sanitize_wav(raw, params, SANITIZED_FILE)
        ssize = os.path.getsize(SANITIZED_FILE)
        print(f"  [+] Sanitized WAV    : {SANITIZED_FILE}  ({ssize:,} bytes)")
        print(f"      (All LSBs zeroed — steganography payload neutralized)")

    return score, action


# ────────────────────────────────────────────────────────────────
#  Entry point
# ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 icap_scrubber.py <file.wav>")
        print()
        print("Risk levels:  0-39 ALLOW | 40-69 SANITIZE | 70-100 BLOCK")
        print()
        print("Example workflow:")
        print("  python3 icap_scrubber.py lofi_morning.wav   # expect: ALLOW")
        print("  python3 icap_scrubber.py lofi_evening.wav   # expect: SANITIZE/BLOCK")
        print("  python3 icap_scrubber.py noisy_radio.wav    # expect: ALLOW (false positive test)")
        sys.exit(1)

    target = sys.argv[1]
    if not os.path.exists(target):
        print(f"[ERROR] File not found: {target}"); sys.exit(1)

    score, action = analyze(target)
    sys.exit(0)
