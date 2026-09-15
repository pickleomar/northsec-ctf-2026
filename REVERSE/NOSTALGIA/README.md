# Nostalgia
## Author : HoXoN 

**Category:** Reverse Engineering / Retro
**Difficulty:** Easy

## Description
We recovered an old floppy disk image from a dusty box in a Tokyo server room.
It claims to hold a secret flag, but every time we run it on our standard terminals, we get "ACCESS DENIED".

Can you get the program to reveal its secrets?

> "It's not just about running the code; it's about *where* you run it."

## Challenge Files
- `FLOPPY.IMG`

## Hints
1. The strings are obfuscated; `strings` won't help you much.
2. Static analysis will reveal two different execution paths.
3. One path writes to `0xB800` (Standard PC), the other to `0xA000` (???).
4. You might need a specific emulator configuration to see the true output.

## How to Run (For Players)
This challenge is distributed as a floppy disk image. You can inspect it or run it using an emulator.

**To Run in DOSBox:**
```dos
Z:\> IMGMOUNT A FLOPPY.IMG -t floppy
Z:\> A:
A:\> NOSTALGIA.COM
```

## Another Way To Solve This Challenge :

```sh
ndisasm -b 16 nostalgia.com
```

```nasm
00000000  BA5401            mov dx,0x154      ; Prompt string
00000003  B409              mov ah,0x9        ; DOS Print
00000005  CD21              int 0x21
...
00000015  B800B8            mov ax,0xb800     ; TARGET 1: Standard PC Video Memory
00000018  8EC0              mov es,ax
0000001F  E80F00            call 0x31         ; Decrypt Routine A (Fake Flag)
...
00000022  B800A0            mov ax,0xa000     ; TARGET 2: NEC PC-98 Video Memory!
00000025  8EC0              mov es,ax
0000002C  E81400            call 0x43         ; Decrypt Routine B (Real Flag)
...
00000038  3437              xor al,0x37       ; <--- KEY IS 0x37
```

### Python Solver

```python
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
```

### FLAG:

```text
NSC{0xA000_VRAM_M4ST3R}
```
