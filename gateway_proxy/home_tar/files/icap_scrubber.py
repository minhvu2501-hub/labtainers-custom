#!/usr/bin/env python3
"""
icap_scrubber.py  -  ICAP Content Disarm Server
================================================
Chạy trên gateway_proxy, lắng nghe tại port 1344 (ICAP standard).
Squid sẽ gửi HTTP response chứa file audio/wav đến đây trước khi
chuyển cho user_pc.

Server này thực hiện "Bit Scrubbing": xóa tất cả bit LSB (bit thấp
nhất) của các audio sample về 0, phá hủy payload steganography mà
không làm hỏng chất lượng âm thanh đáng kể.

Khởi động: python3 icap_scrubber.py
Log file:  /tmp/icap_scrubber.log
"""

import socket
import wave
import io
import struct
import threading
import sys
import os
from datetime import datetime

ICAP_PORT = 1344
LOG_FILE  = "/tmp/icap_scrubber.log"

# ════════════════════════════════════════════════════════════════════
#  PHẦN SINH VIÊN CẦN HOÀN THIỆN
# ════════════════════════════════════════════════════════════════════

def scrub_wav_lsb(wav_bytes: bytes) -> bytes:
    """
    Đọc dữ liệu WAV, xóa bit LSB của toàn bộ audio samples về 0,
    và trả về WAV đã được làm sạch dưới dạng bytes.

    Tham số:
        wav_bytes (bytes): Nội dung file WAV gốc (bị nhiễm LSB stego)

    Trả về:
        bytes: Nội dung file WAV đã làm sạch (LSB = 0)

    Yêu cầu:
        - Giữ nguyên WAV header (nchannels, sampwidth, framerate, ...)
        - Chỉ thay đổi audio frames (không thay đổi metadata)
        - AND mỗi byte của audio data với 0xFE để xóa bit 0

    Gợi ý (bỏ comment từng dòng để dùng):
        inp = io.BytesIO(wav_bytes)
        with wave.open(inp, 'rb') as f:
            params = f.getparams()
            raw    = bytearray(f.readframes(f.getnframes()))

        # TODO: xóa LSB của mỗi byte audio
        # for i in range(len(raw)):
        #     raw[i] = raw[i] & 0xFE

        out = io.BytesIO()
        with wave.open(out, 'wb') as f:
            f.setparams(params)
            f.writeframes(bytes(raw))
        return out.getvalue()
    """
    # ── BẮT ĐẦU CODE SINH VIÊN (xóa dòng raise bên dưới) ──────────
    raise NotImplementedError(
        "\n[ICAP] TODO: Bạn chưa implement hàm scrub_wav_lsb()!\n"
        "  Mở file icap_scrubber.py, tìm hàm này và viết code.\n"
        "  Gợi ý: dùng io.BytesIO + wave module + AND 0xFE\n"
    )
    # ── KẾT THÚC CODE SINH VIÊN ────────────────────────────────────


# ════════════════════════════════════════════════════════════════════
#  ICAP SERVER INFRASTRUCTURE (đã cho sẵn, không cần sửa)
# ════════════════════════════════════════════════════════════════════

def log(msg: str):
    """Ghi log ra console và file."""
    ts   = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    try:
        with open(LOG_FILE, 'a') as f:
            f.write(line + "\n")
    except Exception:
        pass


def recv_headers(sock) -> bytes:
    """Nhận dữ liệu từ socket cho đến khi gặp double-CRLF (end of headers)."""
    buf = b""
    while b"\r\n\r\n" not in buf:
        chunk = sock.recv(4096)
        if not chunk:
            break
        buf += chunk
    return buf


def read_chunked(sock, prefetch: bytes) -> bytes:
    """
    Đọc HTTP chunked-transfer body.
    prefetch: bytes đã đọc thừa từ socket trước đó.
    """
    buf  = prefetch
    body = b""
    while True:
        # Đảm bảo có đủ dữ liệu cho chunk-size line
        while b"\r\n" not in buf:
            more = sock.recv(4096)
            if not more:
                return body
            buf += more

        nl         = buf.index(b"\r\n")
        size_str   = buf[:nl].split(b";")[0].strip()  # ignore chunk extensions
        buf        = buf[nl + 2:]

        try:
            chunk_size = int(size_str, 16)
        except ValueError:
            break

        if chunk_size == 0:
            break  # last chunk

        # Đọc đủ chunk_size bytes
        while len(buf) < chunk_size + 2:
            more = sock.recv(4096)
            if not more:
                body += buf[:chunk_size]
                return body
            buf += more

        body += buf[:chunk_size]
        buf   = buf[chunk_size + 2:]  # skip trailing \r\n

    return body


def encode_chunked(data: bytes) -> bytes:
    """Encode bytes thành HTTP chunked transfer format."""
    size  = hex(len(data))[2:].encode()
    return size + b"\r\n" + data + b"\r\n" + b"0\r\n\r\n"


def build_icap_200(http_resp_headers: bytes, body: bytes) -> bytes:
    """Xây dựng ICAP/1.0 200 OK response với body đã được sửa."""
    res_hdr_offset  = 0
    res_body_offset = len(http_resp_headers)
    icap_hdr = (
        b"ICAP/1.0 200 OK\r\n"
        b"Server: ICAP-WAV-Scrubber/1.0\r\n"
        b"ISTag: \"scrubber-v1\"\r\n"
        + b"Encapsulated: res-hdr=" + str(res_hdr_offset).encode()
        + b", res-body=" + str(res_body_offset).encode() + b"\r\n"
        + b"\r\n"
    )
    return icap_hdr + http_resp_headers + encode_chunked(body)


def handle_options(conn: socket.socket):
    """Trả lời ICAP OPTIONS request."""
    resp = (
        b"ICAP/1.0 200 OK\r\n"
        b"Methods: RESPMOD\r\n"
        b"Service: WAV-LSB-Scrubber 1.0\r\n"
        b"ISTag: \"scrubber-v1\"\r\n"
        b"Max-Connections: 50\r\n"
        b"Options-TTL: 3600\r\n"
        b"Allow: 204\r\n"
        b"\r\n"
    )
    conn.sendall(resp)
    log("  → OPTIONS replied")


def handle_respmod(conn: socket.socket, raw: bytes):
    """
    Xử lý ICAP RESPMOD request.
    Nếu Content-Type là audio/wav → scrub LSB.
    Nếu không → trả 204 No Modifications.
    """
    # Tách ICAP header block
    icap_end  = raw.index(b"\r\n\r\n")
    remainder = raw[icap_end + 4:]   # bytes đọc thừa sau ICAP headers

    # Đọc HTTP response headers (kết thúc bằng \r\n\r\n)
    while b"\r\n\r\n" not in remainder:
        more = conn.recv(4096)
        if not more:
            conn.sendall(b"ICAP/1.0 204 No Modifications\r\n\r\n")
            return
        remainder += more

    http_end        = remainder.index(b"\r\n\r\n")
    http_resp_hdrs  = remainder[:http_end + 4]
    prefetch        = remainder[http_end + 4:]

    # Xác định Content-Type
    http_hdr_str = http_resp_hdrs.decode(errors="replace").lower()
    is_wav = ("audio/wav" in http_hdr_str or "audio/x-wav" in http_hdr_str)

    log(f"  is_wav={is_wav}")

    if not is_wav:
        conn.sendall(b"ICAP/1.0 204 No Modifications\r\n\r\n")
        log("  → Pass-through (not WAV)")
        return

    # Đọc body
    body = read_chunked(conn, prefetch)
    log(f"  → WAV body received: {len(body)} bytes. Scrubbing...")

    try:
        clean = scrub_wav_lsb(body)
        log(f"  → Scrub OK. Clean size: {len(clean)} bytes")
        conn.sendall(build_icap_200(http_resp_hdrs, clean))

    except NotImplementedError as e:
        log(str(e))
        log("  → Passing through unmodified (scrubber not implemented yet!)")
        conn.sendall(b"ICAP/1.0 204 No Modifications\r\n\r\n")

    except Exception as e:
        log(f"  → [ERR] Scrubbing error: {e}")
        conn.sendall(b"ICAP/1.0 204 No Modifications\r\n\r\n")


def handle_client(conn: socket.socket, addr):
    """Xử lý một ICAP client connection."""
    log(f"New connection: {addr}")
    try:
        raw = recv_headers(conn)
        if not raw:
            return

        first_line = raw.split(b"\r\n")[0].decode(errors="replace")
        log(f"  {first_line}")

        if first_line.startswith("OPTIONS"):
            handle_options(conn)
        elif first_line.startswith("RESPMOD"):
            handle_respmod(conn, raw)
        else:
            log(f"  [WARN] Unknown ICAP method")
            conn.sendall(b"ICAP/1.0 400 Bad Request\r\n\r\n")

    except Exception as e:
        log(f"  [ERR] {e}")
    finally:
        conn.close()


def main():
    log("=" * 55)
    log("  ICAP WAV Scrubber Server  —  gateway_content_disarm")
    log("=" * 55)
    log(f"Listening on port {ICAP_PORT}  |  Log: {LOG_FILE}")
    log("Waiting for Squid connections...")

    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("0.0.0.0", ICAP_PORT))
    srv.listen(20)

    while True:
        try:
            conn, addr = srv.accept()
            t = threading.Thread(target=handle_client, args=(conn, addr),
                                 daemon=True)
            t.start()
        except KeyboardInterrupt:
            log("Server stopped.")
            break
        except Exception as e:
            log(f"[ERR] accept: {e}")


if __name__ == "__main__":
    main()
