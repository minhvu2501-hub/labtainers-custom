from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.request
import urllib.error
import subprocess
import os

# IP của máy File Server trong Labtainers
FILESERVER = "http://10.0.0.10:80"

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Chặn các request rỗng
        if self.path == "/" or self.path == "/favicon.ico":
            self.send_response(400)
            self.end_headers()
            return

        filename = self.path.strip("/")
        raw_url = f"{FILESERVER}/{filename}"
        
        raw_file = f"/tmp/{filename}"
        clean_file = f"/tmp/clean_{filename}"

        try:
            print(f"\n[Gateway] Đang tải {filename} từ Server về vùng cách ly...")
            # urllib có sẵn trong Python, không cần pip install requests
            urllib.request.urlretrieve(raw_url, raw_file)
            print(f"[Gateway] Tải thành công. Kích hoạt inspect_audio.py...")
            
        except urllib.error.HTTPError as e:
            print(f"[Gateway] Lỗi: Server trả lời {e.code} cho file {filename}")
            self.send_response(e.code)
            self.end_headers()
            self.wfile.write(f"Gateway Error: Lỗi từ File Server ({e.code})".encode())
            return
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            return

        # ---------------------------------------------------------
        # CHẠY TOOL CDR (inspect_audio.py)
        # ---------------------------------------------------------
        result = subprocess.run([
            "python3",
            "/home/ubuntu/inspect_audio.py", # Gọi đúng tool bạn đã tạo
            raw_file,
            clean_file
        ], capture_output=True, text=True)

        # In log quét của tool ra màn hình Gateway để admin theo dõi
        print(result.stdout)

        # ---------------------------------------------------------
        # TRẢ FILE SẠCH CHO USER
        # ---------------------------------------------------------
        if os.path.exists(clean_file):
            with open(clean_file, "rb") as f:
                data = f.read()

            self.send_response(200)
            self.send_header("Content-type", "audio/wav")
            self.send_header("Content-Disposition", f"attachment; filename={filename}")
            self.end_headers()
            self.wfile.write(data)
            
            print(f"[Gateway] Đã gửi bản sạch đến User ({self.client_address[0]}).")

            # Dọn rác
            os.remove(raw_file)
            os.remove(clean_file)
        else:
            print("[Gateway] LỖI: Không tìm thấy file đầu ra từ CDR!")
            self.send_response(500)
            self.end_headers()

if __name__ == "__main__":
    PORT = 8000
    print(f"[*] Gateway Reverse Proxy đang lắng nghe tại cổng {PORT}...")
    print(f"[*] Chuyển tiếp luồng tải về File Server: {FILESERVER}")
    HTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
