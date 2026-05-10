#!/bin/bash
# serve.sh  -  Khởi động HTTP file server trên port 80
# Phục vụ file lofi_chill.wav (đã nhiễm LSB steganography)
# Container fileserver  |  IP: 10.0.0.10

cd /home/ubuntu
echo "[fileserver] Serving files from $(pwd) on port 80..."
echo "[fileserver] Files available:"
ls -lh *.wav 2>/dev/null || echo "  (no wav files found)"
echo ""
exec python3 -m http.server 80
