Chào mừng đến với máy forensics_lab (Phòng Điều Tra)

Nhiệm vụ của bạn (vai Điều Tra Viên):
1. Nhận file stego_audio.wav từ máy suspect_pc (IP: 10.0.0.10) đang mở cổng 8000.
   Gợi ý lệnh: `wget http://10.0.0.10:8000/stego_audio.wav`
2. Thử trích xuất dữ liệu bằng kỹ thuật phổ biến nhất (LSB) trước:
   Chạy `python3 lsb_extract.py`
   LƯU Ý: Bạn sẽ thấy kết quả trả về là một chuỗi ký tự rác vô nghĩa! Lý do là vì kẻ gian đã giấu Cờ Thật bằng kỹ thuật Phase Coding đè lên. Việc thay đổi góc pha đã phá vỡ hoàn toàn lớp giấu tin LSB bên dưới.
3. Hãy thử trích xuất bằng kỹ thuật Phase Coding để tìm Cờ Thật:
   Chạy `python3 phase_extract.py`
4. Ghi nhận Cờ Thật tìm được vào file `answers.txt`. Mở file bằng lệnh `nano answers.txt` và điền chính xác.
