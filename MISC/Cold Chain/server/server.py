from __future__ import annotations

import os
import socketserver
from typing import List

try:
    from .instance_gen import generate_instance
    from .protocol import DiagnosticSession
except ImportError:  # pragma: no cover
    from instance_gen import generate_instance
    from protocol import DiagnosticSession


HOST = "0.0.0.0"
PORT = int(os.environ.get("COLD_CHAIN_PORT", "31337"))


class ReusableThreadingTCPServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True


class ColdChainHandler(socketserver.StreamRequestHandler):
    def handle(self) -> None:
        seed_text = os.environ.get("COLD_CHAIN_SEED")
        seed = int(seed_text, 0) if seed_text else None
        session = DiagnosticSession(generate_instance(seed))
        self._send(session.briefing())
        while True:
            raw = self.rfile.readline()
            if not raw:
                return
            line = raw.decode("utf-8", "replace").strip()
            if not line:
                continue
            if line == "BEGIN":
                schedule_lines: List[str] = ["BEGIN"]
                while True:
                    raw_schedule = self.rfile.readline()
                    if not raw_schedule:
                        self._send("SCHEDULE FORMAT ERROR: missing END")
                        return
                    schedule_line = raw_schedule.decode("utf-8", "replace").rstrip("\r\n")
                    schedule_lines.append(schedule_line)
                    if schedule_line.strip() == "END":
                        break
                    if len(schedule_lines) > 2000:
                        self._send("SCHEDULE FORMAT ERROR: too many lines")
                        return
                self._send(session.verify("\n".join(schedule_lines)))
                return
            self._send(session.calibration_command(line))

    def _send(self, text: str) -> None:
        self.wfile.write(text.encode() + b"\n.\n")
        self.wfile.flush()


def main() -> None:
    with ReusableThreadingTCPServer((HOST, PORT), ColdChainHandler) as server:
        print(f"Cold Chain listening on {HOST}:{PORT}", flush=True)
        server.serve_forever()


if __name__ == "__main__":
    main()
