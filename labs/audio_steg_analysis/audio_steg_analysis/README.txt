================================================================================
  BÀI LAB: PHÂN TÍCH STEGANOGRAPHY ÂM THANH (Audio LSB Forensics)
================================================================================

GIỚI THIỆU
-----------
Bạn là nhà phân tích pháp chứng kỹ thuật số. Bạn nhận được 4 file âm thanh
bị ẩn danh: audio_A.wav, audio_B.wav, audio_C.wav, audio_D.wav.

Tình báo cho biết:
  - 1 file là âm thanh GỐC (không bị can thiệp)
  - 1 file có thông tin ẩn bằng kỹ thuật LSB 1-bit
  - 1 file có thông tin ẩn bằng kỹ thuật LSB 4-bit
  - 1 file có thông tin ẩn bằng kỹ thuật Hash-based LSB

NHIỆM VỤ
---------
Phân tích các file âm thanh và xác định file nào thuộc loại nào.

CÁC FILE TRONG THƯ MỤC NÀY
----------------------------
  audio_A.wav   - File âm thanh thứ nhất (ẩn danh)
  audio_B.wav   - File âm thanh thứ hai  (ẩn danh)
  audio_C.wav   - File âm thanh thứ ba   (ẩn danh)
  audio_D.wav   - File âm thanh thứ tư   (ẩn danh)
  analyze.py    - Script Python để phân tích các file
  answers.txt   - File điền câu trả lời của bạn

HƯỚNG DẪN
----------
Bước 1: Đọc code của script phân tích để hiểu công cụ
  $ cat analyze.py

Bước 2: Phân tích các file âm thanh bằng script
  $ python3 analyze.py

Bước 2: Đọc kỹ kết quả (LSB distribution, MSE, Chi-square, Entropy)

Bước 3: Xác định từng file và điền vào answers.txt:
  $ nano answers.txt
  (hoặc: gedit answers.txt)

  Định dạng:
    original=audio_X
    lsb1bit=audio_X
    lsb4bit=audio_X
    lsb_hash=audio_X

  (thay X bằng A, B, C hoặc D)

GỢI Ý KỸ THUẬT
---------------
1. LSB (Least Significant Bit): bit thấp nhất của mỗi byte âm thanh

2. Âm thanh TỰ NHIÊN: phân phối LSB KHÔNG đồng đều (lệch về 0 hoặc 1)

3. Steganography LSB 1-bit: phân phối LSB RẤT ĐỀU (~50/50)
   → Chi-square LSB thấp, MSE nhỏ (chỉ 1 bit/byte bị thay đổi)

4. Steganography LSB 4-bit: 4 bit thấp bị thay đổi
   → MSE LỚN HƠN nhiều so với 1-bit (biến dạng nhiều hơn)
   → Chi-square của 4-bit thấp rất nhỏ

5. Hash-based: giống 1-bit về LSB nhưng BIT BỊ THAY ĐỔI Ở VỊ TRÍ NGẪU NHIÊN
   → Khó phân biệt với 1-bit hơn, nhưng pattern phân tán khác

CÔNG CỤ THAM KHẢO
------------------
  sox <file.wav> -n stat          # thống kê âm thanh cơ bản
  python3 analyze.py <file.wav>   # phân tích chi tiết 1 file
  python3 analyze.py --compare    # chỉ xem bảng MSE

================================================================================
