================================================================================
  GATEWAY_PROXY  -  Kịch bản: Cổng Mạng Vô Trùng (Content Disarm)
================================================================================

MÔ HÌNH MẠNG
-------------
  fileserver  (10.0.0.10) → phục vụ file lofi_chill.wav (bị nhiễm LSB)
  gateway_proxy (10.0.0.1) → MÁY NÀY — Squid Proxy + ICAP Scrubber
  user_pc       (10.0.0.5) → Máy nhân viên tải file qua proxy

NHIỆM VỤ CỦA BẠN (2 bước)
----------------------------

BƯỚC 1: Hoàn thiện ICAP Scrubber
  $ nano ~/icap_scrubber.py

  Tìm hàm scrub_wav_lsb() và implement logic sau:
    - Đọc WAV bytes bằng thư viện wave
    - Lấy toàn bộ audio frames: raw = bytearray(...)
    - AND mỗi byte với 0xFE để xóa bit LSB:
        raw[i] = raw[i] & 0xFE
    - Ghi lại thành WAV bytes và trả về

BƯỚC 2: Khởi động services
  $ bash ~/start_services.sh

  Script sẽ:
    - Khởi động ICAP server (port 1344)
    - Cấu hình và khởi động Squid (port 3128)

KIỂM TRA HOẠT ĐỘNG
-------------------
  Xem log ICAP:
    $ tail -f /tmp/icap_scrubber.log

  Kiểm tra Squid:
    $ sudo squid -N -d 1 -f ~/squid.conf

GỢI Ý KỸ THUẬT
---------------
  Bit LSB là bit thấp nhất (bit 0) của mỗi byte.
  Kẻ tấn công đã dùng LSB steganography để nhúng C2 payload.
  Khi ta AND byte với 0xFE (11111110), bit 0 bị đặt về 0.
  Âm thanh chỉ thay đổi tối thiểu (1 bit/byte) → vẫn nghe được.
  Nhưng payload của kẻ tấn công bị phá hủy hoàn toàn.

================================================================================
