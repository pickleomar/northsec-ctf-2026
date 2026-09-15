#!/bin/sh
exec timeout 60 setpriv --reuid=2000 --regid=2000 --init-groups -- \
    /home/ctf/ld-linux-x86-64.so.2 --library-path /home/ctf /home/ctf/svc
