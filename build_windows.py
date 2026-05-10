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

# ── WAV generation (inline copy from gen_lofi_chill.py) ──────────

PAYLOAD_LSB1 = "C2=185.22.10.4:4444" * 300 + "###END###"
PAYLOAD_LSB4 = ("powershell -enc " + "A" * 200) * 20 + "###END###"
PAYLOAD_HASH = "TOKEN=ABCD-1234-XYZ" * 300 + "###END###"


def generate_cover_wav_bytes():
    rng = random.Random(42)
    frames = []
    for i in range(6 * 44100):
        t = i / 44100
        value = (math.sin(2*math.pi*261.63*t)*0.40 +
                 math.sin(2*math.pi*329.63*t)*0.20 +
                 math.sin(2*math.pi*392.00*t)*0.15 +
                 math.sin(2*math.pi*130.81*t)*0.10 +
                 rng.uniform(-0.05, 0.05))
        sample = int(round(value * 26000 / 2) * 2)
        sample = max(-32768, min(32766, sample))
        if rng.random() < 0.28:
            sample = min(32767, sample + 1)
        frames.append(struct.pack("<h", sample))
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


def t2b(text): return "".join(format(ord(c), "08b") for c in text)


def embed_lsb1(wav, secret):
    r, p = wav_rw(wav); bits = t2b(secret)[:len(r)]
    for i, b in enumerate(bits): r[i] = (r[i] & 0xFE) | int(b)
    return to_wav(r, p)


def embed_lsb4(wav, secret):
    r, p = wav_rw(wav); bits = t2b(secret)
    for i in range(0, min(len(bits), len(r)*4), 4):
        idx = i // 4
        if idx >= len(r): break
        r[idx] = (r[idx] & 0xF0) | int(bits[i:i+4].ljust(4,"0"), 2)
    return to_wav(r, p)


def embed_hash(wav, secret, key="lab_key_2024"):
    r, p = wav_rw(wav); n = len(r)
    rng = random.Random(int(hashlib.sha256(key.encode()).hexdigest(), 16))
    pos = list(range(n)); rng.shuffle(pos)
    bits = t2b(secret)
    for i, b in enumerate(bits):
        if i >= n: break
        r[pos[i]] = (r[pos[i]] & 0xFE) | int(b)
    return to_wav(r, p)


def make_wavs():
    print("  [1/4] Generating 4 WAV files...")
    cover  = generate_cover_wav_bytes()
    wavs   = {
        "lofi_morning.wav" : cover,
        "lofi_evening.wav" : embed_lsb1(cover, PAYLOAD_LSB1),
        "lofi_study.wav"   : embed_lsb4(cover, PAYLOAD_LSB4),
        "lofi_chill.wav"   : embed_hash(cover, PAYLOAD_HASH),
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
