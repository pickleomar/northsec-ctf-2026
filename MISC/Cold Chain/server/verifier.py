from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Tuple

try:
    from .warehouse import Edge, Instance, interval_overlaps
except ImportError:  # pragma: no cover
    from warehouse import Edge, Instance, interval_overlaps


class VerificationError(Exception):
    pass


@dataclass
class Action:
    time: int
    kind: str
    args: Tuple[str, ...]
    order: int


@dataclass
class CrateState:
    node: Optional[str] = None
    ready: Optional[int] = None
    occupied_from: Optional[int] = None
    heat: int = 0
    cooling: int = 0
    done: bool = False


@dataclass
class Simulation:
    instance: Instance
    node_intervals: Dict[str, List[Tuple[int, int, int]]] = field(default_factory=dict)
    edge_intervals: Dict[Tuple[str, str], List[Tuple[int, int, int]]] = field(default_factory=dict)
    switch_commands: Dict[str, List[Tuple[int, str]]] = field(default_factory=dict)
    energy: int = 0
    cooling: int = 0


def parse_schedule(text: str) -> Tuple[int, List[Action]]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines or lines[0] != "BEGIN" or lines[-1] != "END":
        raise VerificationError("SCHEDULE FORMAT ERROR: expected BEGIN ... END")
    sync: Optional[int] = None
    actions: List[Action] = []
    for order, line in enumerate(lines[1:-1]):
        parts = line.split()
        if not parts:
            continue
        if parts[0] == "SYNC":
            if len(parts) != 2 or not parts[1].isdigit():
                raise VerificationError("SCHEDULE FORMAT ERROR: SYNC <phase>")
            sync = int(parts[1])
            continue
        if len(parts) < 3 or not parts[0].isdigit():
            raise VerificationError(f"SCHEDULE FORMAT ERROR near line: {line}")
        time = int(parts[0])
        if parts[1] == "SWITCH":
            if len(parts) != 4:
                raise VerificationError(f"SCHEDULE FORMAT ERROR near line: {line}")
            actions.append(Action(time, "SWITCH", (parts[2], parts[3]), order))
        elif parts[1] == "CRATE":
            if len(parts) != 5:
                raise VerificationError(f"SCHEDULE FORMAT ERROR near line: {line}")
            if not parts[2].isdigit():
                raise VerificationError(f"SCHEDULE FORMAT ERROR near line: {line}")
            actions.append(Action(time, parts[3], (parts[2], parts[4]), order))
        else:
            raise VerificationError(f"SCHEDULE FORMAT ERROR near line: {line}")
    if sync is None:
        raise VerificationError("SENSOR DESYNC: missing SYNC phase")
    return sync, sorted(actions, key=lambda action: (action.time, action.order))


def verify_schedule(instance: Instance, text: str) -> str:
    sync, actions = parse_schedule(text)
    if sync != instance.scanner_phase:
        raise VerificationError("SENSOR DESYNC: scanner epoch offset rejected")
    if any(action.time < 0 or action.time > instance.horizon for action in actions):
        raise VerificationError("SCHEDULE HORIZON VIOLATION")

    sim = Simulation(instance)
    states = {crate.cid: CrateState() for crate in instance.crates}

    for action in actions:
        if action.kind == "SWITCH":
            _apply_switch(sim, action)
        elif action.kind == "ENTER":
            _apply_enter(sim, states, action)
        elif action.kind == "MOVE":
            _apply_move(sim, states, action, sync)
        elif action.kind == "EXIT":
            _apply_exit(sim, states, action)
        else:
            raise VerificationError(f"SCHEDULE FORMAT ERROR: unknown action {action.kind}")

    for crate in instance.crates:
        state = states[crate.cid]
        if not state.done:
            raise VerificationError(f"CRATE {crate.cid} MISSING EXIT")
        if state.heat > crate.heat_budget:
            raise VerificationError(
                f"CRATE EXPIRED crate={crate.cid} heat={state.heat} limit={crate.heat_budget}"
            )
    _check_capacities(instance, sim)
    if sim.energy > instance.energy_budget:
        raise VerificationError(
            f"ENERGY LIMIT EXCEEDED used={sim.energy} limit={instance.energy_budget}"
        )
    if sim.cooling > instance.cooling_budget:
        raise VerificationError(
            f"COOLING LIMIT EXCEEDED used={sim.cooling} limit={instance.cooling_budget}"
        )
    return "ACCEPTED"


def _crate(instance: Instance, cid_text: str):
    cid = int(cid_text)
    if cid < 0 or cid >= len(instance.crates):
        raise VerificationError(f"UNKNOWN CRATE {cid}")
    return instance.crates[cid]


def _apply_switch(sim: Simulation, action: Action) -> None:
    junction, state = action.args
    if junction not in sim.instance.junctions:
        raise VerificationError(f"UNKNOWN SWITCH {junction}")
    meta = sim.instance.junctions[junction]
    if state not in meta.states:
        raise VerificationError(f"UNKNOWN SWITCH STATE {junction} {state}")
    commands = sim.switch_commands.setdefault(junction, [])
    for prior_time, _ in commands:
        if abs(action.time - prior_time) < meta.cooldown:
            raise VerificationError(
                f"SWITCH COOLDOWN VIOLATION junction={junction} t={action.time}"
            )
    commands.append((action.time, state))
    commands.sort()
    sim.energy += 1


def _apply_enter(sim: Simulation, states: Dict[int, CrateState], action: Action) -> None:
    crate = _crate(sim.instance, action.args[0])
    node = action.args[1]
    state = states[crate.cid]
    if state.node is not None or state.done:
        raise VerificationError(f"CRATE {crate.cid} DOUBLE ENTER")
    if node != crate.entry or sim.instance.nodes[node].kind != "entry":
        raise VerificationError(f"CRATE {crate.cid} WRONG ENTRY {node}")
    if action.time < crate.release:
        raise VerificationError(f"CRATE {crate.cid} RELEASE VIOLATION")
    state.node = node
    state.ready = action.time
    state.occupied_from = action.time


def _apply_move(
    sim: Simulation, states: Dict[int, CrateState], action: Action, sync: int
) -> None:
    crate = _crate(sim.instance, action.args[0])
    dst = action.args[1]
    state = states[crate.cid]
    if state.node is None or state.ready is None or state.occupied_from is None or state.done:
        raise VerificationError(f"CRATE {crate.cid} NOT ACTIVE")
    src = state.node
    if action.time < state.ready:
        raise VerificationError(
            f"CRATE {crate.cid} NOT AT {src} UNTIL T={state.ready}"
        )
    edge = sim.instance.edge_between(src, dst)
    if edge is None:
        raise VerificationError(f"NO CONVEYOR EDGE {src}->{dst}")
    if edge.state is not None:
        if not _switch_allows(sim, src, edge.state, action.time):
            active = _active_switch_state(sim, src, action.time)
            raise VerificationError(
                f"SWITCH STATE VIOLATION junction={src} need={edge.state} have={active} t={action.time}"
            )
    arrival = action.time + edge.travel
    tick = (arrival + sync + edge.scan_lag) % sim.instance.scanner_cycle
    if tick >= sim.instance.scanner_window:
        raise VerificationError(
            f"SENSOR DESYNC sensor={edge.sensor} crate={crate.cid} tick={tick} t={arrival}"
        )
    _charge_wait(sim, crate.cid, state, action.time)
    sim.node_intervals.setdefault(src, []).append((state.occupied_from, action.time, crate.cid))
    sim.edge_intervals.setdefault((src, dst), []).append((action.time, arrival, crate.cid))
    state.heat += edge.travel * edge.heat_rate * crate.sensitivity
    state.cooling += edge.travel * edge.cooling_rate * crate.sensitivity
    sim.energy += edge.energy
    sim.cooling += edge.travel * edge.cooling_rate * crate.sensitivity
    state.node = dst
    state.ready = arrival
    state.occupied_from = arrival


def _apply_exit(sim: Simulation, states: Dict[int, CrateState], action: Action) -> None:
    crate = _crate(sim.instance, action.args[0])
    node = action.args[1]
    state = states[crate.cid]
    if state.node is None or state.ready is None or state.occupied_from is None:
        raise VerificationError(f"CRATE {crate.cid} NOT ACTIVE")
    if node != crate.exit or state.node != crate.exit:
        raise VerificationError(f"CRATE {crate.cid} WRONG EXIT {node}")
    if action.time < state.ready:
        raise VerificationError(
            f"CRATE {crate.cid} NOT AT EXIT UNTIL T={state.ready}"
        )
    _charge_wait(sim, crate.cid, state, action.time)
    sim.node_intervals.setdefault(state.node, []).append((state.occupied_from, action.time, crate.cid))
    if action.time > crate.deadline:
        raise VerificationError(
            f"CRATE EXPIRED crate={crate.cid} exit_t={action.time} deadline={crate.deadline}"
        )
    state.node = None
    state.done = True


def _charge_wait(sim: Simulation, cid: int, state: CrateState, until: int) -> None:
    if state.ready is None or state.node is None:
        return
    duration = until - state.ready
    if duration <= 0:
        return
    crate = sim.instance.crates[cid]
    node = sim.instance.nodes[state.node]
    heat = duration * node.heat_rate * crate.sensitivity
    cooling = duration * node.cooling_rate * crate.sensitivity
    state.heat += heat
    state.cooling += cooling
    sim.cooling += cooling


def _active_switch_state(sim: Simulation, junction: str, t: int) -> str:
    meta = sim.instance.junctions[junction]
    active_time = -10**9
    active_state = meta.initial
    for command_time, state in sim.switch_commands.get(junction, []):
        ready = command_time + meta.response
        if ready <= t and ready >= active_time:
            active_time = ready
            active_state = state
    return active_state


def _switch_allows(sim: Simulation, junction: str, required: str, t: int) -> bool:
    meta = sim.instance.junctions[junction]
    if _active_switch_state(sim, junction, t) == required:
        return True
    hold = meta.cooldown + 8
    for command_time, state in sim.switch_commands.get(junction, []):
        ready = command_time + meta.response
        if state == required and ready <= t and t - ready <= hold:
            return True
    return False


def _check_capacities(instance: Instance, sim: Simulation) -> None:
    for node, intervals in sim.node_intervals.items():
        capacity = instance.nodes[node].capacity
        points = sorted({point for start, end, _ in intervals for point in (start, end)})
        for start, end, cid in intervals:
            if end < start:
                raise VerificationError(f"NEGATIVE NODE INTERVAL crate={cid} node={node}")
        for t in points:
            load = sum(1 for start, end, _ in intervals if start <= t < end)
            if load > capacity:
                raise VerificationError(f"COLLISION AT T={t} node={node} load={load} cap={capacity}")
    for (src, dst), intervals in sim.edge_intervals.items():
        for index, (a0, a1, ca) in enumerate(intervals):
            if a1 <= a0:
                raise VerificationError(f"BAD EDGE INTERVAL crate={ca} edge={src}->{dst}")
            for b0, b1, cb in intervals[index + 1 :]:
                if interval_overlaps(a0, a1, b0, b1):
                    t = max(a0, b0)
                    raise VerificationError(
                        f"COLLISION AT T={t} edge={src}->{dst} crates={ca},{cb}"
                    )
