# Stage 1: build nsjail (needs GCC 10+ for C++20)
FROM ubuntu:22.04 AS nsjail-builder

RUN apt-get update && apt-get install -y \
    bison flex g++ gcc git \
    libprotobuf-dev libnl-route-3-dev libprotoc-dev \
    make pkg-config protobuf-compiler \
    && rm -rf /var/lib/apt/lists/*

RUN git clone --depth=1 https://github.com/google/nsjail.git /nsjail \
    && cd /nsjail && make -j$(nproc)

# Stage 2: extract ld-linux matching the bundled libc.so.6 (Debian GLIBC 2.42)
FROM debian:sid AS ld-extractor

RUN cp /lib/x86_64-linux-gnu/ld-linux-x86-64.so.2 /ld-linux-x86-64.so.2

# Stage 3: challenge image
# The challenge uses its own bundled ld-linux-x86-64.so.2 + libc.so.6 (GLIBC 2.42)
# so the system glibc version does not affect the binary.
FROM ubuntu:22.04

RUN apt-get update && apt-get install -y socat \
    libprotobuf23 libnl-route-3-200 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

COPY --from=nsjail-builder /nsjail/nsjail /usr/local/bin/nsjail
COPY --from=ld-extractor   /ld-linux-x86-64.so.2 /home/ctf/ld-linux-x86-64.so.2

RUN useradd -m -u 2000 -s /bin/sh ctf

WORKDIR /home/ctf

COPY svc        ./svc
COPY libc.so.6  ./libc.so.6
COPY flag.txt   ./flag.txt
COPY run.sh     /run.sh

RUN chmod +x svc ld-linux-x86-64.so.2 /run.sh && \
    chmod 444 flag.txt && \
    chown root:root flag.txt

EXPOSE 1337

CMD socat TCP-LISTEN:1337,reuseaddr,fork "EXEC:/run.sh,pty,rawer,stderr"
