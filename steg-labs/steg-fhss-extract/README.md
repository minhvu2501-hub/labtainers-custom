# Bài lab Tách tin trong âm thanh dùng kỹ thuật trải phổ nhảy tần (FHSS)
Từ lý thuyết tại [[03_Steg_tách_tin_lab_ver1]], lúc này sẽ đi làm bài lab dựa trên phần code Tách tin với nhiều nhiễu kết hợp + hopping quay vòng + chuẩn hóa điểm dừng + BER (ver4)

Đầu vào của quy trình:

- stego_audio.wav
- original_bits.txt (nhằm tính BER cho việc quan sát và nhận xét đánh giá phương pháp giấu tin)
- Và các thông tin đã được thống nhất giữa hai bên.
  > [!info] Người gửi và người nhận cần thống nhất trước với nhau điều gì?
  >
  > - **khóa bí mật** và **chiều dài của hopping_pattern** (dãy này có chiều dài hữu hạn nhưng nó có thể lặp đi lặp lại) → tạo ra được hopping_pattern đồng bộ giữa hai bên
  > - **Thời gian mỗi bước nhảy (hop duration)**: ví dụ: 10ms
  > - Tần số gốc và delta
  > - Tóm lại:
  >
  > | Thông số          | Ý nghĩa                             | Ghi chú                   |
  > | ----------------- | ----------------------------------- | ------------------------- |
  > | `base_freq`       | Tần số gốc bắt đầu cho hop đầu tiên | Ví dụ: 2000 Hz            |
  > | `delta`           | Bước thay đổi tần số giữa các hop   | Ví dụ: 100 Hz             |
  > | `hopping_pattern` | Danh sách các chỉ số hop            | Cần giống nhau giữa 2 bên |
  > | `bit_duration`    | Thời gian cho mỗi bit               | Ví dụ: 10 ms              |

# Fast Testing commands
Toàn bộ câu lệnh cần thực hiện như sau:

```sh
python3 step0_add_noise.py stego_audio.wav

python3 step1_generate_hopping_pattern.py 96 PTITsecretkey123
python3 step2_extract_bits.py noisy.wav hopping_pattern.txt
python3 step3_bits_to_message.py extracted_bits.txt

python3 step4_calculate_ber.py extracted_bits.txt original_bits.txt

=========Đánh giá file âm thanh dài hơn và chứa nhiều bit bản tin hơn===========
python3 step0_add_noise.py stego_audio2.wav

python3 step1_generate_hopping_pattern.py 96 PTITsecretkey123
python3 step2_extract_bits.py noisy.wav hopping_pattern.txt
python3 step3_bits_to_message.py extracted_bits.txt

python3 step4_calculate_ber.py extracted_bits.txt original_bits2.txt

```

# Các bước tuần tự như sau

### 🔥 File 0: `step0_add_noise.py` (thêm nhiễu)

#### ver1 - không hay lắm

```python
# step0_add_noise.py
import sys
import numpy as np
import scipy.io.wavfile as wav
import os

def add_gaussian_noise(signal, snr_db):
    signal_power = np.mean(signal ** 2)
    snr_linear = 10 ** (snr_db / 10)
    noise_power = signal_power / snr_linear
    noise = np.random.normal(0, np.sqrt(noise_power), signal.shape)
    return signal + noise

def add_impulse_noise(signal, prob):
    impulse = np.random.choice([0, 1], size=signal.shape, p=[1-prob, prob])
    impulse_noise = impulse * np.random.uniform(-1, 1, size=signal.shape)
    return signal + impulse_noise

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Cách dùng: python3 step1_add_noise.py <input_wav>")
        sys.exit(1)

    input_wav = sys.argv[1]
    output_wav = "noisy.wav"  # Đầu ra là bản âm thanh tượng trưng cho bản âm thanh đã bị nhiễu trên kênh truyền

    if not os.path.exists(input_wav):
        print(f"Lỗi: File {input_wav} không tồn tại.")
        sys.exit(1)

    rate, data = wav.read(input_wav)
    data = data.astype(np.float32) / 32768.0

	# Thêm nhiễu trắng (giả lập nhiễu kênh truyền)
    data_noisy = add_gaussian_noise(data, snr_db=20)
    # Nhiễu trắng + thêm Nhiễu xung (giả lập môi trường nhiễu mạnh -> tình huống rất tệ)
    # data_noisy = add_impulse_noise(data_noisy, prob=0.01)

    data_noisy = np.clip(data_noisy, -1.0, 1.0)
    data_noisy = (data_noisy * 32768.0).astype(np.int16)
    wav.write(output_wav, rate, data_noisy)

    print(f"Đã lưu file nhiễu tại: {output_wav}")
```

#### Mẫu hàm `add_impulse_noise()` khác:

```python
# step0_add_noise.py
import sys
import numpy as np
import scipy.io.wavfile as wav
import os

def add_gaussian_noise(signal, snr_db):
    signal_power = np.mean(signal ** 2)
    snr_linear = 10 ** (snr_db / 10)
    noise_power = signal_power / snr_linear
    noise = np.random.normal(0, np.sqrt(noise_power), signal.shape)
    return signal + noise

def add_impulse_noise(signal, num_impulses=10, amplitude=2.0):
    noisy_signal = signal.copy()
    for _ in range(num_impulses):
        idx = np.random.randint(0, len(signal))
        noisy_signal[idx] += amplitude * np.random.choice([-1, 1])
    return noisy_signal

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Cách dùng: python3 step1_add_noise.py <input_wav>")
        sys.exit(1)

    input_wav = sys.argv[1]
    output_wav = "noisy.wav"  # Đầu ra là bản âm thanh tượng trưng cho bản âm thanh đã bị nhiễu trên kênh truyền

    if not os.path.exists(input_wav):
        print(f"Lỗi: File {input_wav} không tồn tại.")
        sys.exit(1)

    rate, data = wav.read(input_wav)
    data = data.astype(np.float32) / 32768.0

	# 00_Thêm nhiễu trắng (giả lập nhiễu kênh truyền)
    data_noisy = add_gaussian_noise(data, snr_db=20)

	# Hãy cố gắng test với nhiều hệ số khác nhau để thấy được khả năng chống chịu của phương pháp fhss này trước tác động của nhiễu thông qua BER tại bước cuối.
    # 01_nhiễu trắng + thêm nhiễu xung nhẹ (Giả lập môi trường nhiễu khá lớn khi có  nhiễu cùng tác động lên bản âm thanh)
    data_noisy = add_impulse_noise(data_noisy, num_impulses=15, amplitude= 0.5)
    # 02_nhiễu trắng + thêm nhiễu xung trung bình (Giả lập môi trường nhiễu mạnh -> có thể là do bị tấn công chèn nhiễu)
    # data_noisy = add_impulse_noise(data_noisy, num_impulses=30, amplitude= 0.7)
    # 03_Nhiễu trắng + thêm Nhiễu xung cực mạnh (giả lập môi trường nhiễu cực mạnh -> tình huống rất rất tệ, gần như là bản âm thanh đã bị phá hoại)
    # data_noisy = add_impulse_noise(data_noisy, num_impulses=50, amplitude=2.5)

    data_noisy = np.clip(data_noisy, -1.0, 1.0)
    data_noisy = (data_noisy * 32768.0).astype(np.int16)
    wav.write(output_wav, rate, data_noisy)

    print(f"Đã lưu file nhiễu tại: {output_wav}")
```

**Mục tiêu**: Sinh viên giả lập nhiễu kênh truyền để mô phỏng lại việc tách tin, đồng thời thử nghiệm với các loại nhiễu khác nhau sẽ ảnh hưởng thế nào đến bản âm thanh cũng như bản tin được giấu bên trong nó.

**Câu lệnh mẫu chạy:**

```bash
python3 step0_add_noise.py input.wav
```

Kết quả: Tạo file `noisy.wav`

[[Lý giải các nhiễu và thông số của nó]]

---

### 🔥 File 1: `step1_generate_hopping_pattern.py`

```python
import random
import sys

def generate_hopping_pattern(length, hop_range=(1, 5)):
    return [random.randint(*hop_range) for _ in range(length)]

# Sinh dãy nhảy tần
if len(sys.argv) != 3:
    print("Vui lòng nhập chiều dài dãy nhảy tần và khóa bí mật.")
    print("Hint: python3 step1_generate_hopping_pattern.py <chiều_dài_dãy> <khóa_bí_mật>")
    sys.exit(1)

length = int(sys.argv[1])
secret_key = sys.argv[2]

random.seed(secret_key)  # ✅ Thiết lập seed để đảm bảo sinh ra cùng một dãy nếu cùng khóa

hopping_pattern = generate_hopping_pattern(length)
output_file = 'hopping_pattern.txt'
with open(output_file, 'w') as f:
    f.write(" ".join(map(str, hopping_pattern)))

print(f"Dãy nhảy tần đã được tạo và lưu vào file {output_file}")
print("Dãy nhảy tần:")
print(hopping_pattern)
```

**Mục tiêu:** Sinh viên bắt đầu đóng vai người tách tin, khi này người tách tin (bên nhận) cần đồng bộ chuỗi hopping_pattern với bên gửi thông qua khóa bí mật đã được thống nhất bởi hai bên.
**Câu lệnh mẫu chạy:**

```sh
python3 step1_generate_hopping_pattern.py <chiều_dài_dãy> <khóa_bí_mật>
```

**Ví dụ:**

```sh
python3 step1_generate_hopping_pattern.py 96 PTITsecretkey123
```

### 🔥 File 2: `step2_extract_bits.py` (tách bit)

```python
# step2_extract_bits.py
import sys
import numpy as np
import scipy.signal as signal
import scipy.io.wavfile as wav
import os

def bandpass_filter(sig, lowcut, highcut, fs, order=6):
    nyq = 0.5 * fs
    b, a = signal.butter(order, [lowcut/nyq, highcut/nyq], btype='band')
    return signal.filtfilt(b, a, sig)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Cách dùng: python3 step2_extract_bits.py <input_wav> <hopping_pattern.txt>")
        sys.exit(1)

    input_wav = sys.argv[1]
    hopping_file = sys.argv[2]
    output_bits = "extracted_bits.txt"  # Output cố định

    if not os.path.exists(input_wav) or not os.path.exists(hopping_file):
        print(f"Lỗi: File không tồn tại.")
        sys.exit(1)

    fs, noisy_signal = wav.read(input_wav)
    noisy_signal = noisy_signal.astype(np.float32) / 32768.0

    with open(hopping_file, 'r') as f:
        hopping_pattern = list(map(int, f.read().strip().split()))

    # Cấu hình
    bit_duration = 0.01
    base_freq = 2000
    delta = 100

    samples_per_bit = int(bit_duration * fs)
    num_bits = len(noisy_signal) // samples_per_bit # số bit có thể có trong file âm thanh

    # Dùng hopping_pattern quay vòng
    if len(hopping_pattern) < num_bits:
        times = (num_bits // len(hopping_pattern)) + 1
        hopping_pattern = (hopping_pattern * times)[:num_bits]

    extracted_bits = []

    for i in range(num_bits):
        segment = noisy_signal[i * samples_per_bit: (i + 1) * samples_per_bit]
        hop = hopping_pattern[i]

        f0 = base_freq + hop * delta
        f1 = base_freq + (hop + 1) * delta

        filtered_f0 = bandpass_filter(segment, f0 - 30, f0 + 30, fs)
        filtered_f1 = bandpass_filter(segment, f1 - 30, f1 + 30, fs)

        power_f0 = np.sum(filtered_f0 ** 2)
        power_f1 = np.sum(filtered_f1 ** 2)

        if power_f1 > power_f0:
            extracted_bits.append('1')
        else:
            extracted_bits.append('0')

    with open(output_bits, 'w') as f:
        for bit in extracted_bits:
            f.write(str(bit))

    print(f"Đã lưu dãy bit tại: {output_bits}")
```

**Mục tiêu:** Sinh viên cần lọc lại được `modulated_signal` (sóng mang điều chế - xem lại bài lab `steg-fhss-embed` trước để nhớ lại) hay nói cách khác là tìm lại được chuỗi bit thông điệp ( tương ứng với `bits.txt` trong bài `steg-fhss-embed`) nhờ vào BPF (bandpass_filter) với `hopping_pattern` đã được đồng bộ trước đó.

**Câu lệnh mẫu chạy:**

```sh
python3 step2_extract_bits.py <input_wav> <hopping_pattern.txt>
```

**Ví dụ:**

```bash
python3 step2_extract_bits.py noisy.wav hopping_pattern.txt
```

---

### 🔥 File 3: `step3_bits_to_message.py` (giải mã thành thông điệp)

```python
# step3_bits_to_message.py
import sys
import os

def bits_to_string(bits):
    chars = []
    for i in range(0, len(bits), 8):
        byte = bits[i:i+8]
        if len(byte) < 8:
            continue  # bỏ qua nếu thiếu bit cuối
        char = chr(int(byte, 2))
        if char == '\0':   # Gặp kí tự null thì dừng lại
            break
        chars.append(char)
    return ''.join(chars)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Cách dùng: python3 step3_bits_to_message.py <input_bits.txt>")
        sys.exit(1)

    input_bits = sys.argv[1]
    output_message = "message.txt"  # Output cố định

    if not os.path.exists(input_bits):
        print(f"Lỗi: File {input_bits} không tồn tại.")
        sys.exit(1)

    with open(input_bits, 'r') as f:
        bits = f.read().strip()

    message = bits_to_string(bits)

    with open(output_message, 'w') as f:
        f.write(message)

    print(f"Đã lưu thông điệp tại: {output_message}")
    print(f"Thông điệp trích xuất được: {message}")
```

**Mục tiêu:** Sinh viên cần giải mã lại được thành thông điệp. Được biết: hai bên thống nhất với nhau từ đầu rằng chuỗi thông điệp sẽ được kết thúc bằng ký tự `\0` (đây là một điểm mới của bài lab này so với bài `steg-fhss-embed`).

**Câu lệnh mẫu chạy:**

```sh
python3 step3_bits_to_message.py <input_bits.txt>
```

**Ví dụ:**

```bash
python3 step3_bits_to_message.py extracted_bits.txt
```

Kết quả: Tạo file `message.txt`

---

### 🔥 File 4: `step4_calculate_ber.py` (tính BER)

```python
# step4_calculate_ber.py
import sys
import os


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Cách dùng: python3 step4_calculate_ber.py <extracted_bits.txt> <original_bits.txt>")
        sys.exit(1)

    extracted_bits = sys.argv[1] # file bit vừa trích xuất được
    original_bits = sys.argv[2]  # file bit gốc (người nhận không có, nhưng để đánh giá phương pháp thì ta sẽ dùng nó)
    output_ber = "ber.txt"  # Ghi BER ra file

    if not os.path.exists(extracted_bits) or not os.path.exists(original_bits):
        print(f"Lỗi: Một trong các file không tồn tại.")
        sys.exit(1)

    with open(extracted_bits, 'r') as f:
        bits1 = f.read().strip()

    with open(original_bits, 'r') as f:
        bits2 = f.read().strip()

	# ======= Tính BER ==========
    length = min(len(bits1), len(bits2))
    errors = sum(b1 != b2 for b1, b2 in zip(bits1[:length], bits2[:length]))
    ber = errors / length
    return ber

    with open(output_ber, 'w') as f:
        f.write(f"BER: {ber:.6f}")

	print(f"📈 BER (Bit Error Rate): {ber:.6f} ({errors} errors trên {length} bits)")
    print(f"Đã lưu BER tại: {output_ber}")
```

**Mục tiêu:** Sinh viên cần đánh giá được tỷ lệ bit lỗi của phương pháp này.

> **Bit Error Rate (BER)** là tỷ lệ lỗi bit, biểu thị phần trăm các bit bị truyền sai trong một hệ thống truyền thông số, bao gồm cả giấu tin (steganography). BER được tính bằng công thức:

$$ \text{BER} = \frac{\text{Số bit lỗi}}{\text{Tổng số bit truyền}} $$

> Trong audio steganography, BER đo lường mức độ chính xác khi giải mã thông tin ẩn từ tín hiệu âm thanh sau khi bị ảnh hưởng bởi nhiễu (như nhiễu xung hoặc nhiễu trắng). BER thấp (ví dụ: < 10⁻³) cho thấy hệ thống giấu tin có độ bền cao, trong khi BER cao biểu thị hiệu suất kém. BER là một chỉ số quan trọng để đánh giá khả năng chống nhiễu của hệ thống, đặc biệt trong các kỹ thuật như FHSS.

**Câu lệnh mẫu chạy:**

```sh
python3 step4_calculate_ber.py <extracted_bits.txt> <original_bits.txt>
```

**Ví dụ:**

```bash
python3 step4_calculate_ber.py extracted_bits.txt original_bits.txt
```

Quiz

test thử quiz sau:
```q
0, Preface, "Bài kiểm tra sau nhằm đánh giá hiểu biết của bạn về giấu tin trong âm thanh dùng FHSS"
1, TrueFalse, "Hopping là chuỗi được sinh ra từ khóa bí mật giữa gửi và nhận.", T, "Correct! Người gửi và người nhận có khóa bí mật để tạo ra chuỗi Hopping đồng bộ với nhau", "Incorrect. Người gửi và người nhận cần phải có có khóa bí mật để tạo ra chuỗi Hopping đồng bộ với nhau "
2, TrueFalse, "Trong bài lab này, bên nhận cần phải biết chiều dài thông điệp được giấu thì mới giải mã được tin", F, "Đúng rồi! Người nhận không nhất thiết phải biết chiều dài thông điệp, hai bên có thể thống nhất ký tự kết thúc.", "Sai rồi. Người nhận không nhất thiết phải biết chiều dài thông điệp, hai bên có thể thống nhất ký tự kết thúc."
3, TrueFalse, "Phương pháp  giấu tin trong âm thanh dùng FHSS này có ưu điểm là có khả năng chống nhiễu băng hẹp cao", T, "Chính xác!", "Sai rồi. Phương pháp này có ưu điểm là có khả năng chống nhiễu băng hẹp cao vì tín hiệu nhảy sang một dải tần số khác do đó làm cho nó khó bị đánh cắp hoặc tấn công."
4, TrueFalse, "Phương pháp này có thể dùng chuỗi Hopping quay vòng.", T, "Đúng rồi!", "Sai rồi. Trong phương pháp giấu tin này, chuỗi giả ngẫu nhiên là một danh sách của nhiều tần số mà sóng mang có thể nhảy để chọn tần số truyền. Khi danh sách tần số đã nhảy hết, bên truyền sẽ lặp lại từ đầu danh sách này."
```

Sinh viên nhập lệnh sau để bắt đầu làm test:
```sh
quiz -l steg-fhss-extract
```
![[Pasted image 20250427181356.png]]
