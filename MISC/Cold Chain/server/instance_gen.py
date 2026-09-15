from __future__ import annotations

import hashlib
import random
import secrets
from typing import Dict, Iterable, List, Tuple

try:
    from .warehouse import Crate, Edge, Instance, Junction, Node, path_edges
except ImportError:  # pragma: no cover - direct script fallback
    from warehouse import Crate, Edge, Instance, Junction, Node, path_edges


STATES3 = ("LEFT", "RIGHT", "BYPASS")


def _tag(seed: int, name: str) -> str:
    digest = hashlib.blake2s(f"{seed}:{name}:node".encode(), digest_size=3).hexdigest()
    return digest.upper()


def _barcode(seed: int, cid: int) -> str:
    digest = hashlib.blake2s(f"{seed}:crate:{cid}".encode(), digest_size=5).hexdigest()
    return f"RX{cid:02d}{digest}".upper()


def fresh_seed() -> int:
    return secrets.randbits(48)


def generate_instance(seed: int | None = None) -> Instance:
    if seed is None:
        seed = fresh_seed()
    rng = random.Random(seed)
    scanner_cycle = 11
    scanner_window = 3
    scanner_phase = rng.randrange(scanner_cycle)

    nodes: Dict[str, Node] = {}

    def add_node(name: str, kind: str, capacity: int, heat_rate: int, cooling_rate: int) -> None:
        nodes[name] = Node(name, kind, capacity, heat_rate, cooling_rate, _tag(seed, name))

    add_node("A", "entry", 2, 2, 0)
    add_node("B", "entry", 2, 2, 0)
    for name in ("J0", "J1", "J2", "J3", "J4", "J5"):
        add_node(name, "junction", 2, 2, 0)
    for name in ("K0", "K1", "K2", "K3"):
        add_node(name, "cold", 2, 0, 2)
    for name in ("W0", "W1", "W2"):
        add_node(name, "warm", 2, 5, 0)
    for name in ("D0", "D1"):
        add_node(name, "buffer", 2, 2, 0)
    add_node("X1", "exit", 99, 0, 0)
    add_node("X2", "exit", 99, 0, 0)

    junctions: Dict[str, Junction] = {}
    for name in ("J0", "J1", "J2", "J3", "J4"):
        junctions[name] = Junction(
            name=name,
            states=STATES3,
            response=rng.randint(1, 3),
            cooldown=rng.randint(3, 5),
            initial=rng.choice(STATES3),
        )
    junctions["J5"] = Junction(
        name="J5",
        states=("LEFT", "RIGHT"),
        response=rng.randint(1, 3),
        cooldown=rng.randint(3, 5),
        initial=rng.choice(("LEFT", "RIGHT")),
    )

    edges: List[Edge] = []
    sensor_id = 0

    def attrs(src: str, dst: str, lane: str) -> Tuple[int, int, int, int]:
        if lane == "cold":
            travel = rng.randint(11, 15)
            heat = 0
            cooling = 2
            energy = max(3, travel // 2 + rng.randint(1, 3))
        elif lane == "warm":
            travel = rng.randint(5, 8)
            heat = 5
            cooling = 0
            energy = travel * 2 + rng.randint(2, 5)
        elif lane == "buffer":
            travel = rng.randint(8, 12)
            heat = 2
            cooling = 0
            energy = travel + rng.randint(1, 3)
        else:
            travel = rng.randint(6, 10)
            heat = 2
            cooling = 0
            energy = travel + rng.randint(1, 3)
        return travel, energy, heat, cooling

    def add_edge(src: str, dst: str, lane: str, state: str | None = None) -> None:
        nonlocal sensor_id
        travel, energy, heat, cooling = attrs(src, dst, lane)
        edges.append(
            Edge(
                src=src,
                dst=dst,
                travel=travel,
                energy=energy,
                heat_rate=heat,
                cooling_rate=cooling,
                sensor=f"S{sensor_id:02d}",
                scan_lag=rng.randrange(scanner_cycle),
                state=state,
            )
        )
        sensor_id += 1

    add_edge("A", "J0", "normal")
    add_edge("A", "J1", "normal")
    add_edge("B", "J1", "normal")
    add_edge("B", "J2", "normal")

    add_edge("J0", "K0", "cold", "LEFT")
    add_edge("J0", "W0", "warm", "RIGHT")
    add_edge("J0", "D0", "buffer", "BYPASS")
    add_edge("J1", "K1", "cold", "LEFT")
    add_edge("J1", "W0", "warm", "RIGHT")
    add_edge("J1", "D0", "buffer", "BYPASS")
    add_edge("J2", "K2", "cold", "LEFT")
    add_edge("J2", "W1", "warm", "RIGHT")
    add_edge("J2", "D1", "buffer", "BYPASS")

    add_edge("K0", "J3", "cold")
    add_edge("K1", "J3", "cold")
    add_edge("K1", "J4", "cold")
    add_edge("K2", "J4", "cold")
    add_edge("W0", "J3", "warm")
    add_edge("W1", "J4", "warm")
    add_edge("D0", "J3", "buffer")
    add_edge("D0", "J4", "buffer")
    add_edge("D1", "J4", "buffer")

    add_edge("J3", "K3", "cold", "LEFT")
    add_edge("J3", "W2", "warm", "RIGHT")
    add_edge("J3", "X1", "normal", "BYPASS")
    add_edge("J4", "K3", "cold", "LEFT")
    add_edge("J4", "W2", "warm", "RIGHT")
    add_edge("J4", "X2", "normal", "BYPASS")
    add_edge("K3", "J5", "cold")
    add_edge("W2", "J5", "warm")
    add_edge("J5", "X1", "normal", "LEFT")
    add_edge("J5", "X2", "normal", "RIGHT")

    partial = Instance(
        seed=seed,
        nodes=nodes,
        edges=edges,
        junctions=junctions,
        crates=[],
        max_calibration=46,
        scanner_cycle=scanner_cycle,
        scanner_window=scanner_window,
        scanner_phase=scanner_phase,
        energy_budget=0,
        cooling_budget=0,
        horizon=260,
    )

    route_templates = {
        ("A", "X1"): [
            ["A", "J0", "K0", "J3", "X1"],
            ["A", "J1", "K1", "J3", "X1"],
            ["A", "J0", "D0", "J3", "X1"],
        ],
        ("A", "X2"): [
            ["A", "J1", "D0", "J4", "X2"],
            ["A", "J1", "K1", "J4", "X2"],
            ["A", "J0", "K0", "J3", "K3", "J5", "X2"],
        ],
        ("B", "X1"): [
            ["B", "J1", "K1", "J3", "X1"],
            ["B", "J2", "K2", "J4", "K3", "J5", "X1"],
            ["B", "J1", "D0", "J3", "X1"],
        ],
        ("B", "X2"): [
            ["B", "J2", "K2", "J4", "X2"],
            ["B", "J2", "D1", "J4", "X2"],
            ["B", "J1", "K1", "J4", "X2"],
        ],
    }

    crate_count = 9 + (seed % 2)
    crates: List[Crate] = []
    reference_energy = 0
    reference_cooling = 0
    for cid in range(crate_count):
        entry = "A" if cid % 2 == 0 else "B"
        exit_name = "X1" if (cid + rng.randint(0, 1)) % 2 == 0 else "X2"
        sensitivity = 2 if cid % 3 == 0 else 1
        release = (cid // 2) * 5 + (cid % 2) * 2
        template = route_templates[(entry, exit_name)][cid % 3]
        edges_for_template = path_edges(partial, template)
        base_time = sum(edge.travel for edge in edges_for_template)
        base_heat = sum(edge.travel * edge.heat_rate * sensitivity for edge in edges_for_template)
        base_cooling = sum(edge.travel * edge.cooling_rate * sensitivity for edge in edges_for_template)
        reference_energy += sum(edge.energy for edge in edges_for_template)
        reference_cooling += base_cooling
        deadline = release + base_time + 190 + rng.randint(0, 24)
        heat_budget = base_heat + 280 + rng.randint(0, 60)
        crates.append(
            Crate(
                cid=cid,
                entry=entry,
                exit=exit_name,
                release=release,
                deadline=deadline,
                heat_budget=heat_budget,
                sensitivity=sensitivity,
                barcode=_barcode(seed, cid),
            )
        )

    partial.crates = crates
    partial.energy_budget = reference_energy + 120 + crate_count * 10
    partial.cooling_budget = reference_cooling + 620 + crate_count * 20
    latest_deadline = max(crate.deadline for crate in crates)
    partial.horizon = max(240, latest_deadline + 45)
    return partial


def instance_fingerprint(instance: Instance) -> str:
    rows: List[str] = [str(instance.seed), str(instance.scanner_phase)]
    for node in instance.nodes.values():
        rows.append(f"N:{node.name}:{node.kind}:{node.capacity}:{node.tag}")
    for edge in instance.edges:
        rows.append(
            f"E:{edge.src}:{edge.dst}:{edge.travel}:{edge.energy}:{edge.heat_rate}:"
            f"{edge.cooling_rate}:{edge.sensor}:{edge.scan_lag}:{edge.state or '-'}"
        )
    for crate in instance.crates:
        rows.append(
            f"C:{crate.cid}:{crate.entry}:{crate.exit}:{crate.release}:"
            f"{crate.deadline}:{crate.heat_budget}:{crate.sensitivity}:{crate.barcode}"
        )
    digest = hashlib.blake2s("\n".join(rows).encode(), digest_size=8).hexdigest()
    return digest
