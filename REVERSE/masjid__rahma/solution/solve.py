#!/usr/bin/env python3
from pwn import *

exe = '../challenge/masjid_rahma'
context.binary = elf = ELF(exe)

def solve():
    print("[*] STEP 1: Analyzing Binary for Offsets...")    
    enc_flag_offset = 0x2a60
    static_key_int = 0xfeedc0de12345678
    
    print(f"[+] Using Static Key: {hex(static_key_int)}")
    
    print("[*] STEP 2: Extracting Encrypted Bytes from File...")
    
    
    with open(exe, "rb") as f:
        f.seek(enc_flag_offset)
        enc_bytes = f.read(64) 
    
    print(f"[+] Read {len(enc_bytes)} encrypted bytes")
    print(f"    Bytes: {enc_bytes[:16].hex()}...")

    print("[*] STEP 3: Decrypting...")

    key_bytes = p64(static_key_int)
    
    flag = bytearray()
    for i, b in enumerate(enc_bytes):
        flag.append(b ^ key_bytes[i % 8])
        
    try:
        decoded = flag.decode('utf-8', errors='ignore')
        if "nsc{" in decoded:
            clean_flag = decoded.split('}')[0] + "}"
            print(f"\n[+] FLAG: {clean_flag}")
        else:
            print(f"\n[+] RAW OUTPUT: {decoded}")
            print("[-] Flag pattern 'NSC{' not detected automatically.")
            
    except Exception as e:
        print(f"[-] Error decoding flag: {e}")

if __name__ == "__main__":
    solve()
