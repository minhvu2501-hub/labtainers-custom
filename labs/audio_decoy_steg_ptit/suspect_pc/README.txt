Chào mừng đến với máy suspect_pc (Kẻ Tình Nghi)

Nhiệm vụ của bạn (vai Hacker):
1. Chạy `python3 gen_cover.py` để tạo file nhạc nền mẫu cover.wav.
2. Giấu một cờ giả (Decoy Flag) bằng LSB để giăng bẫy điều tra viên: 
   Chạy `python3 lsb_embed.py` (file tạo ra là decoy.wav)
3. Giấu cờ thật (Real Flag) đè lên file vừa giấu bằng Phase Coding: 
   Chạy `python3 phase_embed.py` (file tạo ra là stego_audio.wav)
4. Sử dụng lệnh HTTP server để chia sẻ file sang máy forensics_lab (địa chỉ IP máy điều tra là 10.0.0.20, máy hiện tại là 10.0.0.10).
   Gợi ý lệnh: `python3 -m http.server 8000`
