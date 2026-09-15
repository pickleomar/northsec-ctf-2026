# Inside Me

**Category:** Reverse Engineering / Forensics
**Difficulty:** Medium
**Author:** HoXoN 

## Description
We found this high-performance calculator tool on a suspicious server. It claims to be optimized for speed, but our system admins noticed it's behaving strangely... oddly resource-heavy for simple addition.

## Challenge Files
- `math_calculator`

## Hints
1. Why does a simple calculator need 150MB of RAM?
2. The secret isn't on the disk; it's hiding in the heap.
3. Once you extract the payload, static analysis won't be enough—you'll need to run it (or decode it).

### Configure Secret

```bash
# Compile statically
gcc secret.c -o secret -static

# Strip symbols
strip --strip-all secret

# (Optional) Remove section headers
sstrip secret

# Pack with UPX
upx --best secret -o payload.bin
```
### Inject Payload

Use the Python builder to embed `payload.bin` into the host source code (`challenge.c`).

### Compile Final Challenge

Compile the host calculator. We strip this binary as well.

```bash
gcc challenge.c -o math_calculator
strip --strip-all math_calculator
# OR
sstrip math_calculator
```

## Solve

### Extract the payload.bin from Ghidra

```c
memcpy((void *)((long)DAT_0014fe20 + 0x6400744),&DAT_00104080,0x4bd90); //DAT_00104080 hold the value of payload.bin
```

### Another way Dump the Process Memory

```bash
# Get the PID
ps aux | grep math_calculator
# Dump memory (example using gcore)
sudo gcore <PID>
```

### Extract the Hidden Binary

Use binwalk on the core dump to find the UPX packed executable.
```bash
binwalk -e core.<PID>
```

### Run the Extracted Binary

```bash
cd _core.extracted
./payload
```

After `UPX -d ./payload` And Some Ghidra Stuff That's the python solver ...

```python
import sys

def decrypt(encrypted_bytes, key_bytes):
    decrypted = []
    key_len = len(key_bytes)
    for i, byte in enumerate(encrypted_bytes):
        key_byte = key_bytes[i % key_len]
        decrypted.append(chr(byte ^ key_byte))
    return "".join(decrypted)

# These bytes are found by reverse engineering the extracted 'payload' binary
# or dumping the 'encrypted_flag' array from the static binary.
encrypted_flag = [
    0x90, 0xfe, 0x83, 0xa5, 0xb3, 0x9e, 0xad, 0xee, 
    0xac, 0xd4, 0x9f, 0xba, 0xab, 0xc0, 0xb0, 0x81, 
    0xae, 0xc1, 0xb5, 0xeb, 0x81, 0xdf, 0xb5, 0xb0, 
    0xaa, 0x9c, 0xad, 0xed, 0x81, 0xc9, 0xf3, 0xbd, 
    0xac, 0xd4, 0xb0, 0xaa, 0xef, 0x9d, 0xae, 0xa3
]

key = [0xde, 0xad, 0xc0, 0xde]

print("Flag:", decrypt(encrypted_flag, key))
```

### FLAG:

```text
NSC{m3m0ry_dump_plu5_runt1m3_d3crypt10n}
```
