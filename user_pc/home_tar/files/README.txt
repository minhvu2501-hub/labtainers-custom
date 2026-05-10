================================================================================
  USER_PC  -  Kịch bản: Kiểm chứng Phòng thủ Stegomalware
================================================================================

MÔ HÌNH MẠNG
-------------
  fileserver    (10.0.0.10) → chứa file nhạc bị nhiễm
  gateway_proxy (10.0.0.1)  → proxy làm sạch LSB
  user_pc       (10.0.0.5)  → MÁY NÀY

LƯU Ý QUAN TRỌNG
-----------------
  Hoàn thiện gateway_proxy TRƯỚC khi thực hiện các bước dưới đây!
  (Đảm bảo ICAP scrubber và Squid đang chạy trên 10.0.0.1)

BƯỚC 3: Tải file âm thanh qua Proxy
--------------------------------------
  $ export http_proxy=http://10.0.0.1:3128
  $ wget http://10.0.0.10/lofi_chill.wav
  $ ls -lh lofi_chill.wav          # phải > 0 bytes

  Hoặc tải thủ công:
  $ wget --proxy=http://10.0.0.1:3128 http://10.0.0.10/lofi_chill.wav

  Kiểm tra file vẫn nghe được (Business Continuity):
  $ sox lofi_chill.wav -n stat     # xem thống kê âm thanh

BƯỚC 4: Kiểm chứng hiệu năng Phòng thủ
-----------------------------------------
  Chạy Dropper — giả lập phần mềm độc hại đang chờ trích xuất C2:
  $ python3 dropper.py lofi_chill.wav

  Kết quả mong đợi:
    [DROPPER] Garbage extracted. Payload corrupted. Aborting.
    (Exit code: 1)  ← Phòng thủ THÀNH CÔNG!

  Nếu thấy:
    [DROPPER] Payload extracted! Launching reverse shell...
    (Exit code: 0)  ← Phòng thủ THẤT BẠI — gateway chưa scrub đúng!

TIÊU CHÍ PASS
--------------
  ✅ File lofi_chill.wav tồn tại và > 0 bytes
  ✅ Dropper trả về exit code 1 (payload bị phá hủy)

================================================================================
