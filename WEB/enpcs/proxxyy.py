import socket, threading, sys

LISTEN = ('127.0.0.1', 8888)
TARGET = ('127.0.0.1', 3000)

def pipe(src, dst, buf):
    try:
        while True:
            data = src.recv(65536)
            if not data: break
            buf.append(data)
            dst.sendall(data)
    except Exception: pass
    finally:
        try: dst.shutdown(socket.SHUT_WR)
        except Exception: pass

def handle(client):
    up = socket.create_connection(TARGET)
    req, resp = [], []
    t1 = threading.Thread(target=pipe, args=(client, up, req))
    t2 = threading.Thread(target=pipe, args=(up, client, resp))
    t1.start(); t2.start(); t1.join(); t2.join()
    status = b''.join(resp).split(b'\r\n', 1)[0]
    if b' 500' in status:
        print("\n===== 500 HIT =====", flush=True)
        print("-- REQUEST --", flush=True)
        print(b''.join(req).decode(errors='replace'), flush=True)
        print("-- RESPONSE --", flush=True)
        print(b''.join(resp).decode(errors='replace')[:800], flush=True)
        print("===== END =====\n", flush=True)
    client.close(); up.close()

s = socket.socket()
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(LISTEN); s.listen(200)
print(f"proxy {LISTEN} -> {TARGET}", flush=True)
while True:
    c, _ = s.accept()
    threading.Thread(target=handle, args=(c,), daemon=True).start()
