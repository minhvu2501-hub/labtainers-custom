#!/usr/bin/env python3
"""
dropper.py  -  Simulated Steganography Dropper / Grading Tool
==============================================================
Giả lập phần mềm độc hại đang cố trích xuất C2 payload
từ bit LSB (Least Significant Bit) của file WAV.

Nếu gateway_proxy đã làm sạch đúng (xóa tất cả LSB về 0),
dữ liệu trích xuất ra sẽ là "rác" — không chứa MAGIC_MARKER.

Usage:
  python3 dropper.py lofi_chill.wav

Exit codes:
  0 = payload trích xuất THÀNH CÔNG  → phòng thủ THẤT BẠI
  1 = payload bị corrupt / không hợp lệ → phòng thủ THÀNH CÔNG ✅
  2 = lỗi (file không tồn tại hoặc rỗng)
"""

import sys
import os
import wave

# ── Magic marker mà kẻ tấn công đã nhúng vào file WAV ─────────────
MAGIC_MARKER = "HIDDEN_CONFIDENTIAL_DATA_BLOCK_"
MIN_VALID_LEN = len(MAGIC_MARKER)


def extract_lsb_bits(wav_path: str) -> str:
    """Trích xuất tất cả bit LSB từ audio frames của file WAV."""
    with wave.open(wav_path, 'rb') as f:
        raw = bytearray(f.readframes(f.getnframes()))
    # Lấy bit 0 (LSB) của mỗi byte
    return ''.join(str(b & 1) for b in raw)


def bits_to_text(bits: str) -> str:
    """Chuyển bit string thành ASCII text."""
    chars = []
    for i in range(0, len(bits) - 7, 8):
        byte_val = int(bits[i:i + 8], 2)
        if byte_val == 0:
            # Null byte: nếu gateway đã scrub, toàn bộ LSB = 0
            # → mỗi byte decoded = 0x00 = null character
            chars.append('\x00')
        else:
            try:
                chars.append(chr(byte_val))
            except ValueError:
                chars.append('?')
    return ''.join(chars)


def main():
    # ── Validate input ────────────────────────────────────────────
    if len(sys.argv) < 2:
        wav_path = "lofi_chill.wav"
    else:
        wav_path = sys.argv[1]

    if not os.path.exists(wav_path):
        print(f"[DROPPER] ERROR: File '{wav_path}' not found.")
        sys.exit(2)

    if os.path.getsize(wav_path) == 0:
        print(f"[DROPPER] ERROR: File '{wav_path}' is empty.")
        sys.exit(2)

    print(f"[DROPPER] Target file: {wav_path} ({os.path.getsize(wav_path):,} bytes)")
    print("[DROPPER] Extracting LSB payload...")

    # ── Extract LSB ───────────────────────────────────────────────
    try:
        bits    = extract_lsb_bits(wav_path)
        payload = bits_to_text(bits)
    except Exception as e:
        print(f"[DROPPER] ERROR: Cannot read WAV: {e}")
        sys.exit(2)

    # ── Validate payload ──────────────────────────────────────────
    # Kiểm tra null bytes — nếu LSB đã bị xóa về 0, toàn payload là null
    null_ratio = payload.count('\x00') / max(len(payload), 1)

    if null_ratio > 0.9:
        print("[DROPPER] Payload is all null bytes — LSB has been scrubbed!")
        print("[DROPPER] Garbage extracted. Payload corrupted. Aborting.")
        print("[DROPPER] C2 connection FAILED.")
        sys.exit(1)   # ← Phòng thủ THÀNH CÔNG

    if MAGIC_MARKER not in payload[:10000]:
        print("[DROPPER] Magic marker not found — payload is corrupted/garbage.")
        print("[DROPPER] Garbage extracted. Payload corrupted. Aborting.")
        print("[DROPPER] C2 connection FAILED.")
        sys.exit(1)   # ← Phòng thủ THÀNH CÔNG

    # ── Payload intact — defense failed ───────────────────────────
    idx = payload.index(MAGIC_MARKER)
    print(f"[DROPPER] Magic marker found at bit-offset {idx * 8}!")
    print(f"[DROPPER] Payload extracted successfully: '{payload[idx:idx+40]}...'")
    print("[DROPPER] Launching reverse shell to C2...")
    print("[DROPPER] C2 connection ESTABLISHED — defense FAILED!")
    sys.exit(0)   # ← Phòng thủ THẤT BẠI


if __name__ == "__main__":
    main()
