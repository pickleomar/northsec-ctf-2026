from __future__ import annotations

import os
import random
import socketserver
from pathlib import Path

from common import DEFAULT_FLAG, recover_state, validate_command


HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "31337"))
FLAG = os.getenv("FLAG", DEFAULT_FLAG)
DOWLINK_PATH = Path(os.getenv("DOWNLINK", "relay_downlink.bin"))


class ChallengeServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True

    def __init__(self, address, handler, state, flag: str):
        super().__init__(address, handler)
        self.state = state
        self.flag = flag


class ChallengeHandler(socketserver.StreamRequestHandler):
    def handle(self) -> None:
        nonce = random.getrandbits(32)
        self.wfile.write(b"LRS-7 WINDOW OPEN\n")
        self.wfile.write(f"NONCE {nonce:08X}\n".encode("ascii"))
        self.wfile.write(b"SEND HEX TC FRAME:\n")
        self.wfile.flush()

        line = self.rfile.readline(256).strip()
        if not line:
            self.wfile.write(b"NO DATA\n")
            self.wfile.flush()
            return

        try:
            frame = bytes.fromhex(line.decode("ascii"))
        except ValueError:
            self.wfile.write(b"BAD HEX\n")
            self.wfile.flush()
            return

        error = validate_command(frame, self.server.state, nonce)
        if error:
            self.wfile.write(f"{error}\n".encode("ascii"))
            self.wfile.flush()
            return

        self.wfile.write(b"TC ACCEPTED\n")
        self.wfile.write(b"SAFE MODE CLEARED\n")
        self.wfile.write(f"{self.server.flag}\n".encode("ascii"))
        self.wfile.flush()


def main() -> None:
    state = recover_state(DOWLINK_PATH)
    with ChallengeServer((HOST, PORT), ChallengeHandler, state, FLAG) as server:
        print(f"Listening on {HOST}:{PORT}")
        server.serve_forever()


if __name__ == "__main__":
    main()
