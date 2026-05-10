#!/usr/bin/env python3
"""
build_windows.py  -  Windows-compatible Lab Builder
====================================================
Builds the complete gateway_content_disarm.tar for imodule upload.

Steps:
  1) Generate 4 WAV files via gen_lofi_chill logic
  2) Pack home.tar for each container
  3) Create empty sys.tar files
  4) Build final gateway_content_disarm.tar

Usage: python build_windows.py
"""

import tarfile, os, io, wave, struct, math, random, hashlib

LAB_NAME = "gateway_content_disarm"
BASE_DIR  = os.path.dirname(os.path.abspath(__file__))

# ── WAV generation (mirrors gen_lofi_chill.py) ───────────────────
import zlib

def xor(data, key):
    return bytes([b ^ key[i % len(key)] for i, b in enumerate(data)])

_KEY1 = b"\x4B\x7A\x3F\x91"
_KEY2 = b"\xAB\xCD\xEF\x12"
_C2   = b"C2=185.22.10.4:4444|interval=60|campaign=APT2024|cmd=whoami"
_TOK  = b"API_TOKEN=XyZ-9a2b-Kp7q|sig=0xDEADBEEF|exp=2099"

_rng_study = random.Random(0xDEADBEEF)
PAYLOAD_EVENING = xor(_C2, _KEY1)
PAYLOAD_STUDY   = bytes([_rng_study.randint(0, 255) for _ in range(10000)])
PAYLOAD_CHILL   = xor(_TOK, _KEY2)


def generate_cover_wav_bytes():
    rng = random.Random(42)
    frames = []
    for i in range(6 * 44100):
        t = i / 44100
        v = (math.sin(2*math.pi*261.63*t)*0.40 +
             math.sin(2*math.pi*329.63*t)*0.20 +
             math.sin(2*math.pi*392.00*t)*0.15 +
             math.sin(2*math.pi*523.25*t)*0.08 +
             rng.gauss(0, 0.04))
        s = int(round(v * 26000 / 2) * 2)
        s = max(-32768, min(32766, s))
        if rng.random() < 0.30:
            s = min(32767, s + 1)
        frames.append(struct.pack("<h", s))
    buf = io.BytesIO()
    with wave.open(buf, "w") as f:
        f.setnchannels(1); f.setsampwidth(2); f.setframerate(44100)
        f.writeframes(b"".join(frames))
    return buf.getvalue()


def make_noisy_radio():
    rng = random.Random(99)
    frames = []
    for i in range(6 * 44100):
        t = i / 44100
        v = math.sin(2*math.pi*440.0*t)*0.9 + rng.gauss(0, 0.5)
        v = max(-1.0, min(1.0, v))
        s = int(round(int(v * 32000) / 2) * 2)
        s = max(-32768, min(32766, s))
        if rng.random() < 0.31:
            s = min(32767, s + 1)
        frames.append(struct.pack("<h", s))
    buf = io.BytesIO()
    with wave.open(buf, "w") as f:
        f.setnchannels(1); f.setsampwidth(2); f.setframerate(44100)
        f.writeframes(b"".join(frames))
    return buf.getvalue()


def wav_rw(data):
    buf = io.BytesIO(data)
    with wave.open(buf, "rb") as f:
        p = f.getparams(); r = bytearray(f.readframes(f.getnframes()))
    return r, p


def to_wav(raw, params):
    buf = io.BytesIO()
    with wave.open(buf, "wb") as f:
        f.setparams(params); f.writeframes(bytes(raw))
    return buf.getvalue()


def cycled_bits(payload, n):
    bits = [int(b) for byte in payload for b in format(byte, "08b")]
    out = []
    while len(out) < n:
        out.extend(bits)
    return out[:n]


def embed_full_lsb1(wav, payload):
    """Full sequential LSB — cycles payload to fill entire file. chi2 near 0."""
    r, p = wav_rw(wav)
    bits = cycled_bits(payload, len(r))
    for i, b in enumerate(bits):
        r[i] = (r[i] & 0xFE) | b
    return to_wav(r, p)


def embed_4bit_lsb(wav, payload):
    """Lower 4-bit nibble embedding with random bytes. chi4 near 0."""
    r, p = wav_rw(wav)
    bits = cycled_bits(payload, len(r) * 4)
    for i in range(0, len(r) * 4, 4):
        idx = i // 4
        nib = int("".join(str(b) for b in bits[i:i+4]), 2)
        r[idx] = (r[idx] & 0xF0) | nib
    return to_wav(r, p)


def embed_adaptive(wav, payload, key="lab_adap_2024", threshold=8000):
    """Adaptive embedding in high-energy regions only."""
    r, p = wav_rw(wav)
    n_s = len(r) // 2
    eligible = [i*2 for i in range(n_s)
                if abs(struct.unpack_from("<h", r, i*2)[0]) > threshold]
    rng = random.Random(int(hashlib.sha256(key.encode()).hexdigest(), 16))
    rng.shuffle(eligible)
    bits = cycled_bits(payload, len(eligible))
    for pos, b in zip(eligible, bits):
        r[pos] = (r[pos] & 0xFE) | b
    return to_wav(r, p)


def make_wavs():
    print("  [1/4] Generating 5 WAV files...")
    cover = generate_cover_wav_bytes()
    wavs = {
        "lofi_morning.wav" : cover,
        "lofi_evening.wav" : embed_full_lsb1(cover, PAYLOAD_EVENING),
        "lofi_study.wav"   : embed_4bit_lsb(cover,  PAYLOAD_STUDY),
        "lofi_chill.wav"   : embed_adaptive(cover,   PAYLOAD_CHILL),
        "noisy_radio.wav"  : make_noisy_radio(),
    }
    for name, data in wavs.items():
        print(f"        {name:25s}  {len(data):>9,} bytes")
    return wavs


# ── Tar helpers ───────────────────────────────────────────────────

def add_bytes(tar, arcpath, data, mode=0o644):
    info = tarfile.TarInfo(name=arcpath)
    info.size = len(data); info.mode = mode
    tar.addfile(info, io.BytesIO(data))


def add_file(tar, arcpath, disk_path, force_lf=True):
    with open(disk_path, "rb") as f:
        content = f.read()
    if force_lf:
        content = content.replace(b"\r\n", b"\n")
    mode = 0o755 if disk_path.endswith(".sh") else 0o644
    add_bytes(tar, arcpath, content, mode)


def empty_tar():
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w"): pass
    return buf.getvalue()


def pack_home_tar(container, extra_files=None):
    files_dir = os.path.join(BASE_DIR, container, "home_tar", "files")
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w") as tar:
        if os.path.isdir(files_dir):
            for fname in sorted(os.listdir(files_dir)):
                fpath = os.path.join(files_dir, fname)
                if os.path.isfile(fpath):
                    is_text = fname.endswith((".py",".sh",".conf",".txt",".config"))
                    add_file(tar, fname, fpath, force_lf=is_text)
        if extra_files:
            for name, data in extra_files.items():
                add_bytes(tar, name, data)
    return buf.getvalue()


# ── Main build ────────────────────────────────────────────────────

def build():
    print("=" * 60)
    print(f"  Lab Builder: {LAB_NAME}")
    print("=" * 60)

    wavs = make_wavs()

    print("  [2/4] Packing home.tar files...")
    home_tars = {
        "gateway_proxy": pack_home_tar("gateway_proxy"),
        "user_pc"      : pack_home_tar("user_pc"),
        "fileserver"   : pack_home_tar("fileserver", extra_files=wavs),
    }
    for c, data in home_tars.items():
        print(f"        {c}/home_tar/home.tar  {len(data):>9,} bytes")

    print("  [3/4] Building final tar...")
    out_path = os.path.join(BASE_DIR, f"{LAB_NAME}.tar")
    SKIP = {".git", "__pycache__", "home_tar", f"{LAB_NAME}.tar", ".github"}
    TEXT_EXT = (".py",".sh",".conf",".txt",".config",".list",".md","Dockerfile","treataslocal","fixlocal.sh")

    with tarfile.open(out_path, "w") as tar:
        lab = LAB_NAME
        for root, dirs, files in os.walk(BASE_DIR):
            dirs[:] = [d for d in dirs if d not in SKIP]
            for fname in files:
                if fname in (f"{LAB_NAME}.tar","build_windows.py","gen_lofi_chill.py"): continue
                if fname.endswith(".pyc"): continue
                disk_path = os.path.join(root, fname)
                rel       = os.path.relpath(disk_path, BASE_DIR)
                arc       = os.path.join(lab, rel).replace("\\","/")
                is_text   = any(fname.endswith(e) for e in TEXT_EXT)
                add_file(tar, arc, disk_path, force_lf=is_text)

        # Pre-built home.tar
        for c, data in home_tars.items():
            add_bytes(tar, f"{lab}/{c}/home_tar/home.tar", data)
            print(f"        Added: {lab}/{c}/home_tar/home.tar")

        # Empty sys.tar for each container
        et = empty_tar()
        for c in ("gateway_proxy","user_pc","fileserver"):
            add_bytes(tar, f"{lab}/{c}/sys_tar/sys.tar", et)

        # Lab-level placeholders
        add_bytes(tar, f"{lab}/sys_{lab}.tar.gz", empty_tar())
        add_bytes(tar, f"{lab}/{lab}.tar.gz",     empty_tar())

    size_mb = os.path.getsize(out_path) / (1024*1024)
    print(f"  [4/4] Done! -> {out_path}  ({size_mb:.2f} MB)")
    print()
    print("=" * 60)
    print("  BUILD COMPLETE!")
    print(f"  imodule URL:")
    print(f"  https://raw.githubusercontent.com/minhvu2501-hub/")
    print(f"  labtainers-custom/main/{LAB_NAME}.tar")
    print("=" * 60)


if __name__ == "__main__":
    build()
