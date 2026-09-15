from __future__ import annotations

import hashlib
from statistics import median
from typing import Iterable, List

try:
    from .warehouse import Edge, Instance
except ImportError:  # pragma: no cover
    from warehouse import Edge, Instance


def _digest(instance: Instance, *parts: object, n: int = 4) -> str:
    msg = "|".join(str(part) for part in (instance.seed,) + parts)
    return hashlib.blake2s(msg.encode(), digest_size=8).hexdigest()[:n].upper()


def _quality(instance: Instance, *parts: object) -> int:
    return 55 + int(_digest(instance, "q", *parts, n=2), 16) % 45


def _jitter(sample: int) -> int:
    return (-1, 0, 1)[sample % 3]


def crc(instance: Instance, body: str) -> str:
    return _digest(instance, "crc", body, n=6)


def pulse(instance: Instance, src: str, remaining: int) -> str:
    if src not in instance.nodes:
        return f"ERR UNKNOWN_NODE {src}"
    lines: List[str] = [
        f"TRACE src={src} seq={_digest(instance, 'pulse', src)} remaining={remaining}"
    ]
    outgoing = instance.outgoing(src)
    if not outgoing:
        lines.append("TRACE_EMPTY reason=no_downstream_belt")
        lines.append("ENDTRACE")
        return "\n".join(lines)
    for edge_index, edge in enumerate(outgoing):
        tag = instance.nodes[edge.dst].tag
        for sample in range(3):
            dt = edge.travel + _jitter(sample)
            body = (
                f"sensor={edge.sensor} dst_tag={tag} dt={dt} "
                f"state={edge.state or 'OPEN'} lag={edge.scan_lag} "
                f"energy={edge.energy} heat={edge.heat_rate} cool={edge.cooling_rate} "
                f"sample={sample}"
            )
            lines.append(
                "RX "
                + body
                + f" q={_quality(instance, src, edge.sensor, sample)} crc={crc(instance, body)} ok=1"
            )
        if edge_index == 0:
            bad_body = (
                f"sensor={edge.sensor} dst_tag=???? dt={edge.travel + 5} "
                f"state={edge.state or 'OPEN'} lag={(edge.scan_lag + 4) % instance.scanner_cycle} "
                f"energy={edge.energy + 7} heat={edge.heat_rate} cool={edge.cooling_rate} sample=X"
            )
            lines.append(
                "RX "
                + bad_body
                + f" q={_quality(instance, src, edge.sensor, 'bad')} crc=DROP ok=0"
            )
    lines.append("ENDTRACE")
    return "\n".join(lines)


def switch_probe(instance: Instance, junction: str, state: str, remaining: int) -> str:
    if junction not in instance.junctions:
        return f"ERR UNKNOWN_JUNCTION {junction}"
    meta = instance.junctions[junction]
    if state not in meta.states:
        return f"ERR UNKNOWN_STATE {junction} valid={','.join(meta.states)}"
    lines = [
        f"SWITCH_DIAG junction={junction} request={state} states={','.join(meta.states)} "
        f"initial={meta.initial} remaining={remaining}"
    ]
    for sample in range(3):
        response = meta.response + _jitter(sample)
        cooldown = meta.cooldown + _jitter(sample)
        body = f"junction={junction} response={response} cooldown={cooldown} sample={sample}"
        lines.append(
            f"ACK {body} settle={response + cooldown} "
            f"q={_quality(instance, junction, state, sample)} crc={crc(instance, body)} ok=1"
        )
    lines.append("ENDSWITCH")
    return "\n".join(lines)


def temp_probe(instance: Instance, cid: int, remaining: int) -> str:
    if cid < 0 or cid >= len(instance.crates):
        return f"ERR UNKNOWN_CRATE {cid}"
    crate = instance.crates[cid]
    lines = [
        f"THERM crate={cid} entry={crate.entry} exit={crate.exit} release={crate.release} "
        f"deadline={crate.deadline} budget={crate.heat_budget} sensitivity={crate.sensitivity} "
        f"remaining={remaining}"
    ]
    barcode = crate.barcode
    fragments = [barcode[:4], barcode[4:8], barcode[8:]]
    for sample, frag in enumerate(fragments):
        drift = crate.sensitivity * (sample + 2) + _jitter(sample)
        body = f"crate={cid} frag={frag} slot={sample} drift={drift}"
        lines.append(
            f"BAR {body} parity={_digest(instance, 'bar', body, n=3)} crc={crc(instance, body)} ok=1"
        )
    lines.append("ENDTHERM")
    return "\n".join(lines)


def scan_probe(instance: Instance, sensor: str, remaining: int) -> str:
    edge = instance.sensor_map().get(sensor)
    if edge is None:
        return f"ERR UNKNOWN_SENSOR {sensor}"
    epoch = (instance.scanner_phase + edge.scan_lag) % instance.scanner_cycle
    lines = [
        f"SCAN_DIAG sensor={sensor} cycle={instance.scanner_cycle} window={instance.scanner_window} "
        f"skew={edge.scan_lag} remaining={remaining}"
    ]
    for sample in range(4):
        ok = 0 if sample == 2 else 1
        observed = (epoch + (3 if not ok else 0)) % instance.scanner_cycle
        body = f"sensor={sensor} epoch={observed} sample={sample} skew={edge.scan_lag}"
        lines.append(
            f"FRAME {body} frag={_digest(instance, 'scan', sensor, sample, n=5)} "
            f"crc={crc(instance, body) if ok else 'DROP'} ok={ok}"
        )
    lines.append("ENDSCAN")
    return "\n".join(lines)


def route_probe(instance: Instance, src: str, dst: str, remaining: int) -> str:
    if src not in instance.nodes or dst not in instance.nodes:
        return "ERR UNKNOWN_ENDPOINT"
    best = _fastest_route(instance, src, dst)
    if best is None:
        return f"ROUTE src={src} dst={dst} status=NO_PATH remaining={remaining}"
    path, travel, energy = best
    sensors = [instance.edge_between(a, b).sensor for a, b in zip(path, path[1:])]  # type: ignore[union-attr]
    path_hash = _digest(instance, "route", ">".join(path), n=8)
    return (
        f"ROUTE src={src} dst={dst} status=OK eta={travel - 1}..{travel + 1} "
        f"energy_crc={_digest(instance, 'energy', energy, n=5)} "
        f"sensors={','.join(sensors[:3])}{'...' if len(sensors) > 3 else ''} "
        f"path_hash={path_hash} remaining={remaining}"
    )


def _fastest_route(instance: Instance, src: str, dst: str):
    frontier = [(0, 0, [src])]
    best_seen = {src: 0}
    while frontier:
        frontier.sort(key=lambda item: item[0])
        travel, energy, path = frontier.pop(0)
        node = path[-1]
        if node == dst:
            return path, travel, energy
        for edge in instance.outgoing(node):
            if edge.dst in path:
                continue
            new_travel = travel + edge.travel
            if new_travel >= best_seen.get(edge.dst, 10**9):
                continue
            best_seen[edge.dst] = new_travel
            frontier.append((new_travel, energy + edge.energy, path + [edge.dst]))
    return None

