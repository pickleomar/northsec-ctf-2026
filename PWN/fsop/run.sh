#!/bin/sh
exec 2>/dev/null
exec nsjail --mode e \
    --disable_clone_newuser --disable_clone_newnet --disable_clone_newns \
    --user ctf --group ctf \
    --time_limit 120 --max_cpus 1 --rlimit_as 512 \
    --cwd /home/ctf -- /home/ctf/ld-2.27.so /home/ctf/chall
