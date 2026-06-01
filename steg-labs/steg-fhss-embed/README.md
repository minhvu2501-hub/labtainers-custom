
## Flow đơn giản giải thích quy trình tuần tự với input output 


### **Bước 1: Chuyển đổi thông điệp từ file `message.txt` thành chuỗi bit**

#### **Code của Bước 1**: `step1_text_to_bits.py`

```python
import sys

def text_to_bits(text):
    return ''.join(format(ord(c), '08b') for c in text)

# Đọc file message.txt
if len(sys.argv) != 2:
    print("Vui lòng nhập tên file thông điệp. Hint: python3 step1_text_to_bits.py <file-chua-ban-tin-can-giau>")
    sys.exit(1)

input_file = sys.argv[1]

with open(input_file, 'r') as f:
    message = f.read()

# Chuyển đổi thông điệp thành bit
bits = text_to_bits(message)

# Lưu chuỗi bit vào file
output_file = 'bits.txt'
with open(output_file, 'w') as f:
    f.write(bits)
print("Stored: bits.txt")
# In ra chuỗi bit
print("Thông điệp dưới dạng bit:")
print(bits)
print(f"Length:{len(bits)} bits")
```

#### **Hướng dẫn thực hiện**:

- **Mục tiêu**: Sinh viên cần đọc nội dung thông điệp từ file `message.txt` và chuyển nó thành chuỗi bit.
    
- **Lệnh cần gõ**:
    
    ```bash
    python3 step1_text_to_bits.py message.txt
    ```
    

### **Bước 2: Tạo dãy nhảy tần (Hopping Pattern) ngẫu nhiên**

#### **Code của Bước 2**: `step2_generate_hopping_pattern.py`

```python
import random
import sys

def generate_hopping_pattern(length, hop_range=(1, 5)):
    return [random.randint(*hop_range) for _ in range(length)]

# Sinh dãy nhảy tần
if len(sys.argv) != 2:
    print("Vui lòng nhập chiều dài dãy nhảy tần. Hint: python3 step2_generate_hopping_pattern.py <chiều_dài_dãy_nhảy_tần>")
    sys.exit(1)

length = int(sys.argv[1])

hopping_pattern = generate_hopping_pattern(length)
output_file = 'hopping_pattern.txt'
with open(output_file, 'w') as f:
    f.write(" ".join(map(str, hopping_pattern)))

print(f"Dãy nhảy tần đã được tạo và lưu vào file {output_file}")

print("Dãy nhảy tần:")
print(hopping_pattern)

```

#### **Hướng dẫn thực hiện**:

- **Mục tiêu**: Sinh viên cần tạo ra một dãy nhảy tần ngẫu nhiên cho quá trình điều chế.
    
- **Lệnh cần gõ**:
    
    ```bash
    python3 step2_generate_hopping_pattern.py <chiều_dài_dãy_nhảy_tần>
    ```
    
    **Ví dụ**:
    
    ```bash
    python3 step2_generate_hopping_pattern.py 100
    ```
    

### **Bước 3: Điều chế tín hiệu FSK với dãy nhảy tần**

#### **Code của Bước 3**: `step3_modulate_fsk.py`

```python
import numpy as np
import sys
import soundfile as sf

def modulate_fsk(bits, fs, base_freq=2000, delta=100, hopping_pattern=None):
    t = np.linspace(0, 0.01, int(fs * 0.01), endpoint=False)  # 10ms mỗi bit
    signal = np.array([])
    for i, bit in enumerate(bits):
        hop = hopping_pattern[i]
        if bit == '0':
            freq = base_freq + hop * delta
        else:
            freq = base_freq + (hop + 1) * delta
        tone = np.sin(2 * np.pi * freq * t)
        signal = np.concatenate((signal, tone))
    return signal

# Đọc chuỗi bit và dãy nhảy tần từ tham số
if len(sys.argv) != 3:
    print("Vui lòng nhập tên file thông điệp dạng bit và dãy nhảy tần. Hint: python3 step3_modulate_fsk.py <file_bits> <file_hopping_pattern>")
    sys.exit(1)

bits_file = sys.argv[1]
hopping_pattern_file = sys.argv[2]

with open(bits_file, 'r') as f:
    bits = f.read().strip()

with open(hopping_pattern_file, 'r') as f:
    hopping_pattern = [int(x) for x in f.read().strip().split()]

# Thực hiện điều chế FSK
fs = 44100  # Sample rate
modulated_signal = modulate_fsk(bits, fs, hopping_pattern=hopping_pattern)

#=================
modulated_signal *= 0.0005  # giảm mức ảnh hưởng lên âm thanh
#========================

# luu modulated_signal lai de chut nua combine voi original.wav
sf.write('modulated_signal.wav', modulated_signal.astype(np.float32), fs)
print("Saved: modulated_signal.wav")

print("Tín hiệu đã điều chế FSK:")
print(modulated_signal)

```

#### **Hướng dẫn thực hiện**:

- **Mục tiêu**: Sinh viên cần điều chế tín hiệu FSK với các chuỗi bit và dãy nhảy tần đã có.
    
- **Lệnh cần gõ**:
    
    ```bash
    python3 step3_modulate_fsk.py <file_bits> <file_hopping_pattern>
    ```
    
    **Ví dụ**:
    
    ```bash
    python3 step3_modulate_fsk.py bits.txt hopping_pattern.txt
    ```
    

### **Bước 4: Nhúng tín hiệu đã điều chế vào âm thanh gốc**

#### **Code của Bước 4**: `step4_embed_message.py`

```python
import numpy as np
from scipy.io.wavfile import read, write
import sys
import soundfile as sf

def embed_message(audio, modulated_signal):
    combined = np.copy(audio)
    if len(modulated_signal) > len(audio):
        raise ValueError("Tín hiệu quá dài so với âm thanh gốc")
    combined[:len(modulated_signal)] += modulated_signal
    # CẮT BỚT nếu vượt ngưỡng [-1, 1] để tránh méo
    combined = np.clip(combined, -1.0, 1.0)
    return combined

# Đọc âm thanh gốc từ file
if len(sys.argv) != 3:
    print("Vui lòng nhập tên file âm thanh gốc và file modulated_signal. Hint: python3 step4_embed_message.py original_audio.wav stego_audio.wav")
    sys.exit(1)

audio_file = sys.argv[1]
modulated_signal_file = sys.argv[2]

fs, original_audio = read(audio_file)
original_audio = original_audio.astype(np.float32) / 32768.0  # Chuyển sang float32 & CHUẨN HÓA 

modulated_signal, fs = sf.read(modulated_signal_file, dtype='float32')

# Nhúng thông điệp vào âm thanh
message_file = 'bits.txt'
with open(message_file, 'r') as f:
    message_bits = f.read().strip()

stego_audio = embed_message(original_audio, modulated_signal)

# Lưu âm thanh đã nhúng vào file mới
output_file = 'stego_audio.wav'
write(output_file, fs, (stego_audio * 32767).astype(np.int16))  # ✅ Chuẩn hóa về int16 khi lưu
print(f"Tín hiệu đã nhúng vào {output_file}")

```

#### **Hướng dẫn thực hiện**:

- **Mục tiêu**: Sinh viên cần nhúng tín hiệu đã điều chế vào một tệp âm thanh gốc và lưu kết quả.
    
- **Lệnh cần gõ**:
    
    ```bash
    python3 step4_embed_message.py original_audio.wav stego_audio.wav
    ```
    

### **Bước 5: Giải điều chế và lấy lại thông điệp**

#### **Code của Bước 5**: `step5_extract_message.py`

```python
import numpy as np
from scipy.io.wavfile import read
import soundfile as sf
import sys

def bits_to_text(bits):
    chars = [bits[i:i+8] for i in range(0, len(bits), 8)]
    return ''.join(chr(int(c, 2)) for c in chars if len(c) == 8)

def extract_message(signal, fs, hopping_pattern, base_freq=2000, delta=100):
    samples_per_bit = int(fs * 0.01)
    bits = ''

    for i, hop in enumerate(hopping_pattern):
        f0 = base_freq + hop * delta
        f1 = base_freq + (hop + 1) * delta
        seg = signal[i*samples_per_bit : (i+1)*samples_per_bit]

        # FFT
        spectrum = np.abs(np.fft.rfft(seg))
        freqs = np.fft.rfftfreq(len(seg), 1/fs)

        idx_f0 = np.argmin(np.abs(freqs - f0))
        idx_f1 = np.argmin(np.abs(freqs - f1))

        bits += '0' if spectrum[idx_f0] > spectrum[idx_f1] else '1'

    return bits

# --- Kiểm tra tham số ---
if len(sys.argv) != 3:
    print("Hint: python3 step5_extract_message.py stego_audio.wav hopping_pattern.txt")
    sys.exit(1)

stego_file = sys.argv[1]
hopping_pattern_file = sys.argv[2]

# Đọc file
fs, stego_audio = read(stego_file)
stego_audio = stego_audio.astype(np.float32) / 32768.0

# Đọc hopping pattern
with open(hopping_pattern_file, 'r') as f:
    hopping_pattern = [int(x) for x in f.read().strip().split()]

# Lấy phần chứa thông điệp từ âm thanh stego
samples_per_bit = int(fs * 0.01)
needed_samples = len(hopping_pattern) * samples_per_bit
signal = stego_audio[:needed_samples]

# Trích xuất bit
extracted_bits = extract_message(signal, fs, hopping_pattern)

# Lưu kết quả
with open("recovered_bits.txt", "w") as f:
    f.write(extracted_bits)

recovered_text = bits_to_text(extracted_bits)

with open("recovered_message.txt", "w") as f:
    f.write(recovered_text)

print("Đã lưu recovered_bits.txt và recovered_message.txt")
print("Nội dung tin nhắn:", recovered_text)

```

#### **Hướng dẫn thực hiện**:

- **Mục tiêu**: Sinh viên cần giải điều chế và trích xuất thông điệp từ âm thanh đã nhúng (người nhận cần có hopping_pattern đồng bộ với bên gửi - nghĩa là 2 bộ sinh hopping_pattern phải giống nhau, trong kịch bản code này thì người gửi chỉ đang muốn kiểm tra xem mình đã giấu đúng tin chưa thì ta sẽ lấy luôn hopping_pattern đã sinh trước đó, nhưng với kịch bản của người nhận tách tin thì họ phải sinh ra được hopping_pattern, điều đó sẽ được làm rõ trong bài lab tách tin fhss)
    
- **Lệnh cần gõ**:
```sh
python3 step5_extract_message.py stego_audio.wav hopping_pattern.txt
    ```
    

### **Bước 6: Đánh giá hiệu suất nhúng**

#### **Code của Bước 6**: `step6_evaluate.py`

```python
import os
import numpy as np
from scipy.io.wavfile import read
import sys

def evaluate(original_file, stego_file):
    original_size = os.path.getsize(original_file)
    stego_size = os.path.getsize(stego_file)
    print(f"\nKích thước file gốc: {original_size} bytes")
    print(f"Kích thước file đã nhúng: {stego_size} bytes")

    # So sánh mức độ khác biệt theo năng lượng trung bình (MSE)
    rate1, data1 = read(original_file)
    rate2, data2 = read(stego_file)

    if data1.shape != data2.shape:
        print("Không thể so sánh do khác kích thước tín hiệu.")
        return

    mse = np.mean((data1.astype(np.float32) - data2.astype(np.float32)) ** 2)
    print(f"Sai số trung bình (MSE): {mse:.4f}")

# --------------------- MAIN ----------------------
if len(sys.argv) != 3:
    print("Cách dùng: python3 step6_evaluate.py original_audio.wav stego_audio.wav")
    sys.exit(1)

original_file = sys.argv[1]
stego_file = sys.argv[2]

evaluate(original_file, stego_file)

```

#### **Hướng dẫn thực hiện**:

- **Mục tiêu**: Sinh viên cần đánh giá hiệu suất nhúng.
    
- **Lệnh cần gõ**:
    
    ```bash
    python3 step6_evaluate.py original_audio.wav stego_audio.wav
    ```



# code gốc chạy thành công:

[Online Python Compiler with Libraries](https://cliprun.com/online-python-compiler-with-libraries?fullscreen=true)
```python

import numpy as np
import matplotlib.pyplot as plt
from scipy.io.wavfile import write, read
import random
import os

# =============================
# Bước 1: Chuyển đổi dữ liệu cần giấu sang bit
# =============================
def text_to_bits(text):
    return ''.join(format(ord(c), '08b') for c in text)

def bits_to_text(bits):
    chars = [bits[i:i+8] for i in range(0, len(bits), 8)]
    return ''.join(chr(int(c, 2)) for c in chars)

# =============================
# Bước 2: Điều chế dữ liệu bằng FSK (bit 0 và 1 là 2 tần số khác nhau)
# =============================
def modulate_fsk(bits, fs, base_freq=2000, delta=100, hopping_pattern=None):
    t = np.linspace(0, 0.01, int(fs * 0.01), endpoint=False)  # 10ms mỗi bit
    signal = np.array([])
    for i, bit in enumerate(bits):
        hop = hopping_pattern[i]
        if bit == '0':
            freq = base_freq + hop * delta
        else:
            freq = base_freq + (hop + 1) * delta
        tone = np.sin(2 * np.pi * freq * t)
        signal = np.concatenate((signal, tone))
    return signal

# =============================
# Bước 3: Sinh dãy nhảy tần (Hopping Sequence)
# =============================
def generate_hopping_pattern(length, hop_range=(1, 5)):
    return [random.randint(*hop_range) for _ in range(length)]

# =============================
# Bước 4: Nhúng tín hiệu đã điều chế vào âm thanh gốc
# =============================
def embed_message(audio, fs, message):
    bits = text_to_bits(message)
    hopping_pattern = generate_hopping_pattern(len(bits))
    modulated_signal = modulate_fsk(bits, fs, hopping_pattern=hopping_pattern)

    # Chèn tín hiệu đã điều chế vào đầu âm thanh gốc
    combined = np.copy(audio)
    if len(modulated_signal) > len(audio):
        raise ValueError("Tín hiệu quá dài so với âm thanh gốc")
    combined[:len(modulated_signal)] += modulated_signal
    return combined, hopping_pattern, len(bits)

# =============================
# Bước bổ sung: Giải điều chế để tách tin ra
# =============================
def extract_message(stego_audio, fs, bit_length, hopping_pattern, base_freq=2000, delta=100):
    t = np.linspace(0, 0.01, int(fs * 0.01), endpoint=False)
    bits = ''
    for i in range(bit_length):
        hop = hopping_pattern[i]
        f0 = base_freq + hop * delta
        f1 = base_freq + (hop + 1) * delta
        seg = stego_audio[i*len(t):(i+1)*len(t)]
        corr0 = np.sum(seg * np.sin(2 * np.pi * f0 * t))
        corr1 = np.sum(seg * np.sin(2 * np.pi * f1 * t))
        bits += '0' if corr0 > corr1 else '1'
    return bits_to_text(bits)

# =============================
# Bước bổ sung: Đánh giá hiệu suất nhúng
# =============================
def evaluate(original_file, stego_file):
    original_size = os.path.getsize(original_file)
    stego_size = os.path.getsize(stego_file)
    print(f"\nKích thước file gốc: {original_size} bytes")
    print(f"Kích thước file giấu tin: {stego_size} bytes")

    # So sánh mức độ khác biệt (dạng năng lượng trung bình)
    rate1, data1 = read(original_file)
    rate2, data2 = read(stego_file)
    if data1.shape != data2.shape:
        print("Không thể so sánh do khác kích thước tín hiệu")
        return
    mse = np.mean((data1.astype(np.float32) - data2.astype(np.float32)) ** 2)
    print(f"Độ sai lệch trung bình MSE: {mse:.4f}")

# =============================
# Kiểm thử quy trình
# =============================
fs = 44100  # Sample rate
original_audio = np.zeros(fs * 2)  # 2 giây âm thanh im lặng
message = "Hi!"

stego_audio, hopping_pattern, bit_length = embed_message(original_audio, fs, message)
retrieved_message = extract_message(stego_audio, fs, bit_length, hopping_pattern)

print("Tin nhắn gốc:", message)
print("Tin nhắn trích xuất:", retrieved_message)

# Ghi ra file âm thanh
write("original_audio.wav", fs, (original_audio * 32767).astype(np.int16))
write("stego_audio.wav", fs, (stego_audio * 32767).astype(np.int16))

# Đánh giá hiệu suất nhúng
evaluate("original_audio.wav", "stego_audio.wav")

```
