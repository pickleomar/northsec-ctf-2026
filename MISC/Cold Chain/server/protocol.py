from __future__ import annotations

import hashlib
import os
from typing import List

try:
    from .instance_gen import instance_fingerprint
    from .telemetry import pulse, route_probe, scan_probe, switch_probe, temp_probe
    from .verifier import VerificationError, verify_schedule
    from .warehouse import Instance
except ImportError:  # pragma: no cover
    from instance_gen import instance_fingerprint
    from telemetry import pulse, route_probe, scan_probe, switch_probe, temp_probe
    from verifier import VerificationError, verify_schedule
    from warehouse import Instance


class DiagnosticSession:
    def __init__(self, instance: Instance):
        self.instance = instance
        self.queries = 0
        self.closed = False

    def briefing(self) -> str:
        inst = self.instance
        lines: List[str] = [
            "COLD CHAIN DIAGNOSTIC CONSOLE",
            f"SESSION {instance_fingerprint(inst)}",
            f"NODES {len(inst.nodes)} CRATES {len(inst.crates)} HORIZON {inst.horizon}",
            f"ENTRIES {' '.join(inst.entries)}",
            f"EXITS {' '.join(inst.exits)}",
            f"MAX_CAL {inst.max_calibration}",
            f"SCANNER cycle={inst.scanner_cycle} window={inst.scanner_window}",
            f"BUDGET energy={inst.energy_budget} cooling={inst.cooling_budget}",
            "NODE_MANIFEST",
        ]
        for node in inst.nodes.values():
            lines.append(
                f"NODE {node.name} kind={node.kind} cap={node.capacity} "
                f"heat={node.heat_rate} cool={node.cooling_rate} tag={node.tag}"
            )
        lines.append("JUNCTION_MANIFEST")
        for meta in inst.junctions.values():
            lines.append(
                f"JUNCTION {meta.name} states={','.join(meta.states)} initial={meta.initial}"
            )
        lines.extend(
            [
                "COMMANDS PULSE <node> | ROUTE <src> <dst> | SCAN <sensor> | TEMP <crate> | SWITCH <junction> <state>",
                "SCHEDULE BEGIN ... END with SYNC <phase>, SWITCH, CRATE ENTER/MOVE/EXIT lines",
                "READY",
            ]
        )
        return "\n".join(lines)

    def calibration_command(self, line: str) -> str:
        if self.closed:
            return "ERR SESSION_CLOSED"
        parts = line.strip().split()
        if not parts:
            return "ERR EMPTY"
        cmd = parts[0].upper()
        if cmd in {"PULSE", "ROUTE", "SCAN", "TEMP", "SWITCH"}:
            if self.queries >= self.instance.max_calibration:
                return "ERR CALIBRATION_LIMIT_EXCEEDED"
            self.queries += 1
            remaining = self.instance.max_calibration - self.queries
        else:
            remaining = self.instance.max_calibration - self.queries
        try:
            if cmd == "HELP":
                return self._help()
            if cmd == "PULSE" and len(parts) == 2:
                return pulse(self.instance, parts[1], remaining)
            if cmd == "ROUTE" and len(parts) == 3:
                return route_probe(self.instance, parts[1], parts[2], remaining)
            if cmd == "SCAN" and len(parts) == 2:
                return scan_probe(self.instance, parts[1], remaining)
            if cmd == "TEMP" and len(parts) == 2 and parts[1].isdigit():
                return temp_probe(self.instance, int(parts[1]), remaining)
            if cmd == "SWITCH" and len(parts) == 3:
                return switch_probe(self.instance, parts[1], parts[2], remaining)
        except Exception as exc:  # Defensive: protocol errors should not kill service.
            return f"ERR INTERNAL_DIAG {type(exc).__name__}"
        return "ERR BAD_COMMAND"

    def verify(self, schedule_text: str) -> str:
        self.closed = True
        try:
            verify_schedule(self.instance, schedule_text)
        except VerificationError as exc:
            return str(exc)
        return f"ACCEPTED: {make_flag(self.instance)}"

    def _help(self) -> str:
        return (
            "HELP: calibration commands consume budget except HELP. "
            "Submit a schedule by sending BEGIN, actions, then END."
        )


def make_flag(instance: Instance) -> str:
    secret = os.environ.get("COLD_CHAIN_FLAG_SECRET", "local-test-secret")
    body = f"{secret}:{instance.seed}:{instance_fingerprint(instance)}".encode()
    digest = hashlib.blake2s(body, digest_size=10).hexdigest()
    return "NSC{" + f"c0ld_ch41n_{digest[:16]}" + "}"

