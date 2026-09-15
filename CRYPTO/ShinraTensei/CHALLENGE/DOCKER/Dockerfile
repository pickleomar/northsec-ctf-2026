FROM ubuntu:20.04

RUN useradd --no-create-home -u 1000 user

RUN apt update && \
    apt install -y socat python3 python3-pip && \
    pip3 install pycryptodome && \
    rm -rf /var/lib/apt/lists/*

COPY code.py /home/user/code.py
COPY run.sh /home/user/run.sh

RUN chmod +x /home/user/run.sh
RUN chown -R user:user /home/user

WORKDIR /home/user

USER user

EXPOSE 5551

CMD socat TCP-LISTEN:5551,reuseaddr,fork EXEC:"/home/user/run.sh"