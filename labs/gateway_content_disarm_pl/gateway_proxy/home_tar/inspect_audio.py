import wave
import struct
import math
import sys
import os
from collections import Counter

def entropy(bits):
    total = len(bits)
    if total == 0: return 0
    counts = Counter(bits)
    ent = 0
    for c in counts.values():
        p = c / total
        ent -= p * math.log2(p)
    return ent

def inspect_and_disarm(input_path, output_path, log_path="scan_report.txt", chunk_size=10000):
    with wave.open(input_path, 'rb') as wav:
        params = wav.getparams()
        frames = wav.readframes(wav.getnframes())

    samples = list(struct.unpack('<' + 'h'*(len(frames)//2), frames))
    
    print(f"\n{'='*40}")
    print(f" LSB INSPECTOR & CDR SCRUBBER")
    print(f"{'='*40}")
    print(f"File In : {input_path}")
    
    is_infected = False
    suspicious_chunks = []
    
    for i in range(0, len(samples), chunk_size):
        chunk = samples[i:i+chunk_size]
        if not chunk: break
            
        lsb_bits = [s & 1 for s in chunk]
        zeroes = lsb_bits.count(0)
        ones = lsb_bits.count(1)
        ratio = ones / (zeroes + ones) if (zeroes + ones) > 0 else 0
        ent = entropy(lsb_bits)
        
        if 0.48 <= ratio <= 0.52 and ent > 0.98:
            is_infected = True
            chunk_id = i // chunk_size
            suspicious_chunks.append(chunk_id)
            print(f"[!] Chunk {chunk_id:03d} | LSB 1s: {ratio:.2%} | Ent: {ent:.4f} -> SUSPICIOUS!")
            
            for j in range(len(chunk)):
                samples[i+j] = samples[i+j] & ~7 
                
    clean_frames = struct.pack('<' + 'h'*len(samples), *samples)
    with wave.open(output_path, 'wb') as wav_out:
        wav_out.setparams(params)
        wav_out.writeframes(clean_frames)

    with open(log_path, 'a') as log_file:
        log_file.write(f"[{os.path.basename(input_path)}]\n")
        if is_infected:
            log_file.write(f" - Status : THREAT DETECTED (Steganography)\n")
            log_file.write(f" - Action : CDR Activated. Applied '& ~7' bitmask.\n")
            log_file.write(f" - Output : {os.path.basename(output_path)} (Sanitized)\n")
        else:
            log_file.write(f" - Status : CLEAN\n")
        log_file.write("-" * 60 + "\n")
        
    print(f"{'-'*40}")
    if is_infected:
        print(f"[+] RESULT: Payload detected and disarmed!")
    else:
        print(f"[V] RESULT: File is clean.")
    print(f"{'='*40}\n")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(1)
    inspect_and_disarm(sys.argv[1], sys.argv[2])
