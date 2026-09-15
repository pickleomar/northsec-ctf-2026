from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple


@dataclass(frozen=True)
class Node:
    name: str
    kind: str
    capacity: int
    heat_rate: int
    cooling_rate: int
    tag: str


@dataclass(frozen=True)
class Edge:
    src: str
    dst: str
    travel: int
    energy: int
    heat_rate: int
    cooling_rate: int
    sensor: str
    scan_lag: int
    state: Optional[str] = None


@dataclass(frozen=True)
class Junction:
    name: str
    states: Tuple[str, ...]
    response: int
    cooldown: int
    initial: str


@dataclass(frozen=True)
class Crate:
    cid: int
    entry: str
    exit: str
    release: int
    deadline: int
    heat_budget: int
    sensitivity: int
    barcode: str


@dataclass
class Instance:
    seed: int
    nodes: Dict[str, Node]
    edges: List[Edge]
    junctions: Dict[str, Junction]
    crates: List[Crate]
    max_calibration: int
    scanner_cycle: int
    scanner_window: int
    scanner_phase: int
    energy_budget: int
    cooling_budget: int
    horizon: int

    def outgoing(self, node: str) -> List[Edge]:
        return [edge for edge in self.edges if edge.src == node]

    def edge_between(self, src: str, dst: str) -> Optional[Edge]:
        for edge in self.edges:
            if edge.src == src and edge.dst == dst:
                return edge
        return None

    def sensor_map(self) -> Dict[str, Edge]:
        return {edge.sensor: edge for edge in self.edges}

    @property
    def entries(self) -> List[str]:
        return [name for name, node in self.nodes.items() if node.kind == "entry"]

    @property
    def exits(self) -> List[str]:
        return [name for name, node in self.nodes.items() if node.kind == "exit"]

    def node_names(self) -> List[str]:
        return list(self.nodes.keys())

    def edge_key(self, edge: Edge) -> Tuple[str, str]:
        return (edge.src, edge.dst)


def interval_overlaps(a0: int, a1: int, b0: int, b1: int) -> bool:
    return a0 < b1 and b0 < a1


def path_edges(instance: Instance, path: Iterable[str]) -> List[Edge]:
    names = list(path)
    result: List[Edge] = []
    for src, dst in zip(names, names[1:]):
        edge = instance.edge_between(src, dst)
        if edge is None:
            raise ValueError(f"no edge {src}->{dst}")
        result.append(edge)
    return result

