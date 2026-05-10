#!/usr/bin/env python3
"""
build_windows.py  -  Windows-compatible Lab Builder
====================================================
Chạy script này trên Windows (PowerShell) để:
  1) Tạo file lofi_chill.wav bị nhiễm LSB
  2) Đóng gói home.tar cho từng container
  3) Tạo sys.tar rỗng cho từng container
  4) Tạo file gateway_content_disarm.tar cuối cùng để upload lên GitHub

Usage:
  python build_windows.py

Output:
  gateway_content_disarm.tar  (upload lên GitHub để dùng với imodule)
"""

import tarfile
import os
import io
import wave
import struct
import math
import random

# ── Constants ────────────────────────────────────────────────────────
LAB_NAME = "gateway_content_disarm"
BASE_DIR  = os.path.dirname(os.path.abspath(__file__))

MAGIC_MARKER = "HIDDEN_CONFIDENTIAL_DATA_BLOCK_"
SECRET = (MAGIC_MARKER * 600) + "###END###"


# ════════════════════════════════════════════════════════════════════
#  STEP 1: Generate infected lofi_chill.wav
# ════════════════════════════════════════════════════════════════════

def generate_lofi_wav_bytes(duration=6, sample_rate=44100) -> bytes:
    """Tạo cover WAV audio dưới dạng bytes."""
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
        sample = int(round(value * 26000 / 2) * 2)
        sample = max(-32768, min(32766, sample))
        if rng.random() < 0.28:
            sample += 1
            sample = min(32767, sample)
        frames.append(struct.pack('<h', sample))
    buf = io.BytesIO()
    with wave.open(buf, 'w') as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(sample_rate)
        f.writeframes(b''.join(frames))
    return buf.getvalue()


def embed_lsb_1bit(wav_bytes: bytes, secret: str) -> bytes:
    """Nhúng payload vào bit LSB của WAV audio."""
    buf = io.BytesIO(wav_bytes)
    with wave.open(buf, 'rb') as f:
        params = f.getparams()
        raw    = bytearray(f.readframes(f.getnframes()))

    bits = ''.join(format(ord(c), '08b') for c in secret)
    bits = bits[:len(raw)]  # truncate if needed

    for i, bit in enumerate(bits):
        raw[i] = (raw[i] & 0xFE) | int(bit)

    out = io.BytesIO()
    with wave.open(out, 'wb') as f:
        f.setparams(params)
        f.writeframes(bytes(raw))
    return out.getvalue()


def make_infected_wav() -> bytes:
    print("  [1/4] Generating infected lofi_chill.wav...")
    clean_bytes    = generate_lofi_wav_bytes()
    infected_bytes = embed_lsb_1bit(clean_bytes, SECRET)
    print(f"        WAV size: {len(infected_bytes):,} bytes  |  "
          f"Payload: {len(SECRET)} chars embedded via LSB")
    return infected_bytes


# ════════════════════════════════════════════════════════════════════
#  STEP 2: Pack home.tar for each container
# ════════════════════════════════════════════════════════════════════

def make_empty_tar_bytes() -> bytes:
    """Tạo tar rỗng (không chứa file nào)."""
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode='w') as t:
        pass
    return buf.getvalue()


def pack_home_tar(container: str, extra_files: dict = None) -> bytes:
    """
    Đóng gói home.tar từ thư mục <container>/home_tar/files/
    extra_files: {arcname: bytes} - file bổ sung thêm vào tar
    """
    files_dir = os.path.join(BASE_DIR, container, "home_tar", "files")
    buf = io.BytesIO()

    with tarfile.open(fileobj=buf, mode='w') as tar:
        # Add files from disk
        if os.path.isdir(files_dir):
            for fname in os.listdir(files_dir):
                fpath = os.path.join(files_dir, fname)
                if os.path.isfile(fpath):
                    # Force LF line endings for text files
                    if fname.endswith(('.py', '.sh', '.conf', '.txt', '.config')):
                        with open(fpath, 'rb') as f:
                            content = f.read().replace(b'\r\n', b'\n')
                        info = tarfile.TarInfo(name=fname)
                        info.size = len(content)
                        info.mode = 0o755 if fname.endswith('.sh') else 0o644
                        tar.addfile(info, io.BytesIO(content))
                    else:
                        tar.add(fpath, arcname=fname)

        # Add extra files (e.g., generated WAV)
        if extra_files:
            for arcname, data in extra_files.items():
                info = tarfile.TarInfo(name=arcname)
                info.size = len(data)
                info.mode = 0o644
                tar.addfile(info, io.BytesIO(data))

    return buf.getvalue()


# ════════════════════════════════════════════════════════════════════
#  STEP 3: Build the final lab tar
# ════════════════════════════════════════════════════════════════════

def add_bytes_to_tar(tar: tarfile.TarFile, arcpath: str, data: bytes,
                     mode: int = 0o644):
    """Thêm bytes data vào tar với path cho trước."""
    info = tarfile.TarInfo(name=arcpath)
    info.size = len(data)
    info.mode = mode
    tar.addfile(info, io.BytesIO(data))


def add_file_to_tar(tar: tarfile.TarFile, arcpath: str, disk_path: str,
                    force_lf: bool = True, mode: int = None):
    """Thêm file từ disk vào tar, tùy chọn convert CRLF→LF."""
    with open(disk_path, 'rb') as f:
        content = f.read()
    if force_lf:
        content = content.replace(b'\r\n', b'\n')
    info = tarfile.TarInfo(name=arcpath)
    info.size = len(content)
    if mode is not None:
        info.mode = mode
    elif disk_path.endswith('.sh'):
        info.mode = 0o755
    else:
        info.mode = 0o644
    tar.addfile(info, io.BytesIO(content))


def build_lab_tar(infected_wav: bytes):
    """Build the complete lab tar file."""
    print("  [2/4] Packing home.tar files...")

    # Pack home.tar for each container
    home_tars = {}

    # gateway_proxy: standard files
    home_tars['gateway_proxy'] = pack_home_tar('gateway_proxy')
    print("        gateway_proxy/home_tar/home.tar  OK")

    # user_pc: standard files
    home_tars['user_pc'] = pack_home_tar('user_pc')
    print("        user_pc/home_tar/home.tar        OK")

    # fileserver: standard files + infected WAV
    home_tars['fileserver'] = pack_home_tar('fileserver',
                                             extra_files={'lofi_chill.wav': infected_wav})
    print("        fileserver/home_tar/home.tar     OK  (+ lofi_chill.wav)")

    empty_sys = make_empty_tar_bytes()

    print("  [3/4] Building final gateway_content_disarm.tar...")

    out_tar_path = os.path.join(BASE_DIR, f"{LAB_NAME}.tar")

    with tarfile.open(out_tar_path, 'w') as tar:
        lab = LAB_NAME  # prefix all paths

        # ── Walk all source files ──────────────────────────────────
        for root, dirs, files in os.walk(BASE_DIR):
            # Skip .git, __pycache__, and generated tars
            dirs[:] = [d for d in dirs
                       if d not in ('.git', '__pycache__', 'home_tar')]

            for fname in files:
                if fname in (f'{LAB_NAME}.tar', 'build_windows.py',
                             'gen_lofi_chill.py'):
                    continue
                if fname.endswith('.pyc'):
                    continue

                disk_path = os.path.join(root, fname)
                rel_path  = os.path.relpath(disk_path, BASE_DIR)
                arc_path  = os.path.join(lab, rel_path).replace('\\', '/')

                is_text = fname.endswith(
                    ('.py', '.sh', '.conf', '.txt', '.config',
                     '.list', '.md', 'Dockerfile', 'treataslocal',
                     'fixlocal.sh'))

                add_file_to_tar(tar, arc_path, disk_path,
                                force_lf=is_text)

        # ── Add pre-built home.tar files ───────────────────────────
        for container, tar_bytes in home_tars.items():
            arc_path = f"{lab}/{container}/home_tar/home.tar"
            add_bytes_to_tar(tar, arc_path, tar_bytes)
            print(f"        Added: {arc_path}")

        # ── Add empty sys.tar for each container ───────────────────
        for container in ('gateway_proxy', 'user_pc', 'fileserver'):
            arc_path = f"{lab}/{container}/sys_tar/sys.tar"
            add_bytes_to_tar(tar, arc_path, empty_sys)

        # ── Add lab-level sys tar (required by Labtainer) ─────────
        add_bytes_to_tar(tar,
                         f"{lab}/sys_{lab}.tar.gz",
                         make_empty_tar_bytes())
        add_bytes_to_tar(tar,
                         f"{lab}/{lab}.tar.gz",
                         make_empty_tar_bytes())

    size_mb = os.path.getsize(out_tar_path) / (1024 * 1024)
    print(f"  [4/4] Done! -> {out_tar_path}  ({size_mb:.2f} MB)")
    return out_tar_path


# ════════════════════════════════════════════════════════════════════
#  Main
# ════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print(f"  Lab Builder: {LAB_NAME}")
    print("=" * 60)

    infected_wav = make_infected_wav()
    out_path     = build_lab_tar(infected_wav)

    print()
    print("=" * 60)
    print("  BUILD COMPLETE!")
    print(f"  Output: {out_path}")
    print()
    print("  After pushing to GitHub, run on Ubuntu VM:")
    print(f"  imodule https://raw.githubusercontent.com/minhvu2501-hub/")
    print(f"          labtainers-custom/main/{LAB_NAME}.tar")
    print("=" * 60)
