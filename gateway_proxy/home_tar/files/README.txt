================================================================================
  GATEWAY_PROXY  -  Lab: Phong Thu LSB Steganography
================================================================================

MO HINH MANG
-------------
  fileserver    (10.0.0.10) -> chua 4 file WAV (1 sach, 3 bi nhiem)
  gateway_proxy (10.0.0.1)  -> MAY NAY - phan tich + sanitize
  user_pc       (10.0.0.5)  -> may nhan vien tai file

NHIEM VU
--------
Phan tich cac file WAV tu fileserver va phat hien steganography.

BUOCSTEP 1 - Download WAV files from fileserver:
  wget http://10.0.0.10/lofi_morning.wav
  wget http://10.0.0.10/lofi_evening.wav
  wget http://10.0.0.10/lofi_study.wav
  wget http://10.0.0.10/lofi_chill.wav

STEP 2 - Analyze each file:
  python3 icap_scrubber.py lofi_morning.wav
  python3 icap_scrubber.py lofi_evening.wav
  python3 icap_scrubber.py lofi_study.wav
  python3 icap_scrubber.py lofi_chill.wav

BUOC 3: Xem ket qua phan tich
  cat ~/findings.txt
  ls -lh ~/sanitized.wav

TIEU CHI PASS
-------------
  [x] findings.txt chua "WAV_ANALYZED"
  [x] findings.txt chua "LSB_DETECTED"
  [x] sanitized.wav ton tai va > 0 bytes
  [x] bash_history chua "icap_scrubber.py"

KY THUAT DETECT
---------------
  1. Entropy thap bat thuong  (<7.5 = suspicious)
  2. Chi-square LSB < 10      (very uniform = stego indicator)
  3. 4-bit chi-square < 80    (LSB 4-bit stego)
  4. Printable ASCII trong LSB extraction (C2=, TOKEN=, powershell...)

GHI CHU
-------
  findings.txt   -> ghi vao ~/findings.txt
  sanitized.wav  -> ghi vao ~/sanitized.wav
================================================================================
