FROM ubuntu:20.04

RUN apt update && apt install -y gcc

WORKDIR /ctf
COPY chall.c .

# Compile your binary inside the container
RUN gcc chall.c -o chall \


    -z relro -z now \
    -O0
