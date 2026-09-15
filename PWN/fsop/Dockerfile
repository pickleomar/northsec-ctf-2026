# Stage 1: build nsjail (needs GCC 10+ for C++20)
FROM ubuntu:22.04 AS nsjail-builder

RUN apt-get update && apt-get install -y \
    bison flex g++ gcc git \
    libprotobuf-dev libnl-route-3-dev libprotoc-dev \
    make pkg-config protobuf-compiler \
    && rm -rf /var/lib/apt/lists/*

RUN git clone --depth=1 https://github.com/google/nsjail.git /nsjail \
    && cd /nsjail && make -j$(nproc)

# Stage 2: challenge image
# Ubuntu 22.04 is fine — the challenge uses its own bundled ld-2.27.so + libc.so.6
# so the system glibc version does not affect the binary.
FROM ubuntu:22.04

RUN apt-get update && apt-get install -y socat \
    libprotobuf23 libnl-route-3-200 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

COPY --from=nsjail-builder /nsjail/nsjail /usr/local/bin/nsjail

RUN useradd -m -s /bin/sh ctf

WORKDIR /home/ctf

COPY chall        ./chall
COPY libc.so.6    ./libc.so.6
COPY ld-2.27.so   ./ld-2.27.so
COPY flag.txt     ./flag.txt
COPY run.sh       /run.sh

RUN chmod +x chall ld-2.27.so /run.sh && \
    chmod 444 flag.txt && \
    chown root:root flag.txt

EXPOSE 1337

CMD socat TCP-LISTEN:1337,reuseaddr,fork "EXEC:/run.sh,pty,rawer,stderr"
