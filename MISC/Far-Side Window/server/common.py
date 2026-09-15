from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import struct

SYNC_MARKER = bytes.fromhex("1ACFFC1D")
DEFAULT_FLAG = "NSC{4R73M15_11_F4R_51D3_W1ND0W}"


@dataclass(frozen=True)
class ChallengeState:
    spacecraft_id: int
    safe_latch: int
    last_counter: int
    auth_seed: int


def crc16_ccitt_false(data: bytes) -> int:
    crc = 0xFFFF
    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ 0x1021) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    return crc


def crc16_x25(data: bytes) -> int:
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 1:
                crc = ((crc >> 1) ^ 0x8408) & 0xFFFF
            else:
                crc = (crc >> 1) & 0xFFFF
    return (~crc) & 0xFFFF


def infer_frame_size(blob: bytes) -> int:
    positions = []
    start = 0
    while True:
        index = blob.find(SYNC_MARKER, start)
        if index < 0:
            break
        positions.append(index)
        start = index + 1
    gaps = [b - a for a, b in zip(positions, positions[1:])]
    if not gaps:
        raise ValueError("could not infer frame size from sync marker")
    return max(set(gaps), key=gaps.count)


def recover_state(downlink_path: Path) -> ChallengeState:
    blob = downlink_path.read_bytes()
    frame_size = infer_frame_size(blob)
    spacecraft_id = safe_latch = last_counter = auth_seed = None

    for offset in range(0, len(blob), frame_size):
        frame = blob[offset:offset + frame_size]
        if len(frame) != frame_size or frame[:4] != SYNC_MARKER:
            continue

        primary_word = struct.unpack(">H", frame[4:6])[0]
        spacecraft_id = (primary_word >> 6) & 0x03FF

        packet_zone = frame[10:58]
        packet_id = struct.unpack(">H", packet_zone[:2])[0]
        packet_length = struct.unpack(">H", packet_zone[4:6])[0] + 7
        payload = packet_zone[12:packet_length]
        apid = packet_id & 0x07FF

        if apid == 0x121 and len(payload) >= 6:
            safe_latch = int.from_bytes(payload[2:4], "big")
            last_counter = int.from_bytes(payload[4:6], "big")
        elif apid == 0x1A1 and len(payload) >= 3:
            auth_seed = int.from_bytes(payload[1:3], "big")

    if None in (spacecraft_id, safe_latch, last_counter, auth_seed):
        raise ValueError("failed to recover challenge state from downlink")

    return ChallengeState(
        spacecraft_id=spacecraft_id,
        safe_latch=safe_latch,
        last_counter=last_counter,
        auth_seed=auth_seed,
    )


def validate_command(frame: bytes, state: ChallengeState, nonce: int) -> str | None:
    if len(frame) != 12:
        return "BAD LENGTH"

    if struct.unpack(">H", frame[10:12])[0] != crc16_ccitt_false(frame[:10]):
        return "BAD CRC"

    primary_word, tc_counter, segment_header, opcode, argument, auth_tag = struct.unpack(">HHBBHH", frame[:10])
    spacecraft_id = (primary_word >> 6) & 0x03FF
    vcid = (primary_word >> 3) & 0x07
    frame_type = (primary_word >> 1) & 0x03
    bypass = primary_word & 0x01

    if spacecraft_id != state.spacecraft_id or vcid != 0 or frame_type != 2 or bypass != 1:
        return "BAD FORMAT"
    if tc_counter != ((state.last_counter + 1) & 0xFFFF):
        return "BAD COUNTER"
    if segment_header != 0xC1:
        return "BAD FORMAT"
    if opcode != 0x52:
        return "BAD OPCODE"
    if argument != state.safe_latch:
        return "BAD ARG"

    expected_tag = crc16_x25(struct.pack(">I", nonce) + frame[:8] + struct.pack(">H", state.auth_seed))
    if auth_tag != expected_tag:
        return "BAD TAG"

    return None
