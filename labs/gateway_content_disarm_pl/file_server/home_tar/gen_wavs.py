import wave
import struct
import math
import random
import hashlib

RATE = 44100
DURATION = 3

def text_to_bits(text):
    """Chuyển đổi chuỗi văn bản thành mảng các bit (0 và 1)"""
    bits = bin(int.from_bytes(text.encode('utf-8'), 'big'))[2:]
    return bits.zfill(8 * ((len(bits) + 7) // 8))

def generate_base_samples(freq=440):
    """Tạo sóng âm thanh gốc (Pha trộn 2 tần số cho đỡ chói tai)"""
    samples = []
    for i in range(RATE * DURATION):
        t = i / RATE
        val = math.sin(2 * math.pi * freq * t) * 0.6 + math.sin(2 * math.pi * (freq * 1.25) * t) * 0.4
        sample = int(32767 * val * 0.5) 
        samples.append(sample)
    return samples

def save_wav(filename, samples):
    """Lưu mảng samples ra file .wav"""
    with wave.open(filename, 'w') as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2) # 16-bit audio
        wav.setframerate(RATE)
        for s in samples:
            # Ép kiểu về giới hạn 16-bit signed integer để tránh lỗi
            s = max(-32768, min(32767, s))
            wav.writeframes(struct.pack('<h', s))

def inject_lsb1(samples, payload):
    bits = text_to_bits(payload)
    out = list(samples)
    for i in range(min(len(bits), len(out))):
        out[i] = (out[i] & ~1) | int(bits[i]) # Xóa bit cuối, nhét bit mới vào
    return out

def inject_lsb3(samples, payload):
    bits = text_to_bits(payload)
    out = list(samples)
    bit_idx = 0
    for i in range(len(out)):
        if bit_idx >= len(bits): break
        chunk = bits[bit_idx:bit_idx+3].ljust(3, '0')
        val = int(chunk, 2)
        out[i] = (out[i] & ~7) | val # Xóa 3 bit cuối (~7 là 1111...1000)
        bit_idx += 3
    return out

def inject_hash_random(samples, payload, key="lab_key"):
    bits = text_to_bits(payload)
    out = list(samples)
    
    # Dùng Hash của Key làm Seed để lấy vị trí ngẫu nhiên
    seed = int(hashlib.md5(key.encode()).hexdigest(), 16)
    rng = random.Random(seed)
    
    indices = list(range(len(out)))
    rng.shuffle(indices) # Đảo lộn các vị trí sample
    
    for i, b in enumerate(bits):
        if i >= len(indices): break
        idx = indices[i]
        out[idx] = (out[idx] & ~1) | int(b)
    return out

def inject_lsb_xor(samples, payload):
    bits = text_to_bits(payload)
    out = list(samples)
    for i in range(min(len(bits), len(out))):
        if bits[i] == '1':
            out[i] = out[i] ^ 1 # Phép XOR: Nếu payload là 1 thì lật ngược bit cuối của sample
    return out

# ==========================================
# THỰC THI TẠO FILE
# ==========================================

# 1. Tạo sóng gốc
base_audio = generate_base_samples(440)
save_wav("lofi1.wav", base_audio)
print("[+] Đã tạo file sạch: 1_clean.wav")

# 2. File nhiễm LSB 1-bit
payload1 = "C2=185.22.10.4:8080|CMD:whoami|" * 200
save_wav("lofi2.wav", inject_lsb1(base_audio, payload1))
print("[+] Đã tạo file LSB 1-bit: 2_infected_lsb1.wav")

# 3. File nhiễm LSB 3-bit
payload2 = "POWERSHELL -ENC SQBFAFgAKABOAGUAdwAtAE8AYgBqAGUAYwB0ACAATgBldC...|" * 150
save_wav("lofi3.wav", inject_lsb3(base_audio, payload2))
print("[+] Đã tạo file LSB 3-bit: 3_infected_lsb3.wav")

# 4. File nhiễm Hashed/Random LSB
payload3 = "PTIT_SEC_STUDENT_TOKEN=B22DCAT_ADMIN_ACCESS|" * 200
save_wav("lofi4.wav", inject_hash_random(base_audio, payload3, key="cybersec2026"))
print("[+] Đã tạo file Hashed LSB: 4_infected_hash.wav")

# 5. File nhiễm XOR LSB
payload4 = "MALWARE_DROPPER_URL=http://evil.com/payload.bin|" * 200
save_wav("lofi5.wav", inject_lsb_xor(base_audio, payload4))
print("[+] Đã tạo file XOR LSB: 5_infected_xor.wav")

print("\nHoàn tất! Hệ thống đã sẵn sàng để bạn test tool phòng thủ.")
