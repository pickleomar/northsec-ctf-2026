import sys

def solve():
    try:
        with open("nostalgia.com", "rb") as f:
            data = f.read()
    except FileNotFoundError:
        print("[-] Error: nostalgia.com not found in current directory.")
        return

    print("[*] Analyzing nostalgia.com...")

    # Pattern for the start of the encrypted flag:
    # "IDE" -> 'I' ^ 0x37 = 0x7E
    #          'D' ^ 0x37 = 0x73
    #          'E' ^ 0x37 = 0x72
    # Pattern: 0x7E, 0x73, 0x72
    
    pattern = bytes([0x7E, 0x73, 0x72])
    offset = data.find(pattern)

    if offset == -1:
        print("[-] Could not find encrypted flag pattern.")
        return

    print(f"[+] Found encrypted data at offset: {hex(offset)}")

    # Extract bytes until we hit the null terminator (0x00)
    encrypted_bytes = []
    current_idx = offset
    
    while current_idx < len(data):
        byte = data[current_idx]
        if byte == 0x00:
            break
        encrypted_bytes.append(byte)
        current_idx += 1

    # Decrypt using the key found in disassembly (0x37)
    key = 0x37
    decrypted_flag = "".join([chr(b ^ key) for b in encrypted_bytes])

    print("-" * 40)
    print(f"[SUCCESS] {decrypted_flag}")
    print("-" * 40)

if __name__ == "__main__":
    solve()
