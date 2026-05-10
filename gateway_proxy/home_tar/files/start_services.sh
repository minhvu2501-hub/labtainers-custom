#!/bin/bash
# start_services.sh  -  Khởi động ICAP Scrubber + Squid Proxy
# Chạy script này sau khi đã hoàn thiện icap_scrubber.py

set -e
HOMEDIR="$(cd "$(dirname "$0")" && pwd)"

echo "========================================================"
echo "  Gateway Content Disarm  —  Service Startup"
echo "========================================================"

# ── Bước 1: Khởi động ICAP Server ───────────────────────────────
echo ""
echo "[1/3] Khởi động ICAP Scrubber (port 1344)..."
pkill -f "icap_scrubber.py" 2>/dev/null || true
sleep 1
python3 "$HOMEDIR/icap_scrubber.py" >> /tmp/icap_scrubber.log 2>&1 &
ICAP_PID=$!
sleep 2

if kill -0 $ICAP_PID 2>/dev/null; then
    echo "    [OK] ICAP server running (PID=$ICAP_PID)"
else
    echo "    [FAIL] ICAP server failed to start!"
    echo "    → Kiểm tra lại icap_scrubber.py, đặc biệt hàm scrub_wav_lsb()"
    exit 1
fi

# ── Bước 2: Cấu hình Squid ──────────────────────────────────────
echo ""
echo "[2/3] Cấu hình Squid Proxy..."
sudo cp "$HOMEDIR/squid.conf" /etc/squid/squid.conf
sudo mkdir -p /var/log/squid /var/spool/squid
sudo chown -R proxy:proxy /var/log/squid /var/spool/squid 2>/dev/null || true
sudo squid -z -f /etc/squid/squid.conf 2>/dev/null || true
echo "    [OK] Squid config deployed"

# ── Bước 3: Khởi động Squid ─────────────────────────────────────
echo ""
echo "[3/3] Khởi động Squid (port 3128)..."
sudo pkill -f squid 2>/dev/null || true
sleep 1
sudo squid -f /etc/squid/squid.conf
sleep 2
echo "    [OK] Squid running"

echo ""
echo "========================================================"
echo "  Trạng thái:"
echo "    ICAP Scrubber  → port 1344  (PID: $ICAP_PID)"
echo "    Squid Proxy    → port 3128"
echo ""
echo "  Log ICAP: tail -f /tmp/icap_scrubber.log"
echo "  Log Squid: tail -f /var/log/squid/access.log"
echo "========================================================"
echo ""
echo "  Bây giờ chuyển sang máy user_pc và thực hiện:"
echo "    wget --proxy=http://10.0.0.1:3128 http://10.0.0.10/lofi_chill.wav"
echo "========================================================"
