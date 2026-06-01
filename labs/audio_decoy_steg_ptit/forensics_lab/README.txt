Chào mừng đến với máy forensics_lab (Phòng Điều Tra)

Nhiệm vụ của bạn (vai Điều Tra Viên):
1. Nhận file stego_audio.wav từ máy suspect_pc (IP: 10.0.0.10) đang mở cổng 8000.
   Gợi ý lệnh: `wget http://10.0.0.10:8000/stego_audio.wav`
2. Thử trích xuất dữ liệu bằng kỹ thuật phổ biến nhất (LSB) trước: 
   Chạy `python3 lsb_extract.py`
   LƯU Ý: Kẻ gian có thể dùng Cờ Giả (Decoy Flag) để đánh lừa bạn! Đừng vội đắc ý.
3. Kẻ gian thường giấu Cờ Thật bằng kỹ thuật cao cấp hơn (Phase Coding) trên cùng file đó. Hãy thử trích xuất bằng mã hóa pha:
   Chạy `python3 phase_extract.py`
4. Ghi nhận 2 cờ tìm được vào file `answers.txt`. Mở file bằng lệnh `nano answers.txt` và điền chính xác.
