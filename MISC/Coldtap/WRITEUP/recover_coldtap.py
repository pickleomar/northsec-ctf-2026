#!/usr/bin/env python3
import argparse
import subprocess
from collections import defaultdict
from pathlib import Path


def frames_from_pcap(path):
    out = subprocess.check_output(
        ["tshark", "-r", str(path), "-T", "fields", "-e", "data"],
        stderr=subprocess.DEVNULL,
        text=True,
    )
    return [bytes.fromhex(line.strip()) for line in out.splitlines() if line.strip()]


def parse_tlvs(data):
    i = 0
    tlvs = []
    while i + 2 <= len(data):
        if data[i : i + 2] == b"\x90\x00":
            break
        tag = data[i]
        length = data[i + 1]
        value = data[i + 2 : i + 2 + length]
        if len(value) != length:
            raise ValueError(f"truncated TLV tag 0x{tag:02x}")
        tlvs.append((tag, value))
        i += 2 + length
    return tlvs


def parse_profile(frame):
    payload = frame[1:]
    fields = dict(parse_tlvs(payload))
    if not {0x81, 0x82, 0x83, 0x84}.issubset(fields):
        return None
    return {
        "chain_id": int.from_bytes(fields[0x81], "big"),
        "address": fields[0x82],
        "version": fields[0x83].decode(errors="replace"),
        "seed": fields[0x84],
    }


def parse_signature(frames, start_index):
    chunks = []
    for frame in frames[start_index:]:
        if not frame.startswith(b"\x02"):
            break
        chunks.append(frame[1:])
        if frame.endswith(b"\x90\x00"):
            break

    fields = dict(parse_tlvs(b"".join(chunks)))
    if not {0x71, 0x72, 0x73}.issubset(fields):
        return None
    return {"r": fields[0x71], "s": fields[0x72], "v": fields[0x73][0]}


def parse_sign_command(frame):
    if not frame.startswith(b"\x01\x80\x30"):
        return None
    return {"mode": frame[3], "lc": frame[5], "body": frame[6:]}


def recover_nonce(r, seed):
    return bytes(r[i] ^ seed[i % len(seed)] for i in range(len(r)))


def recover_digest(s, address):
    return bytes(s[i] ^ address[i % len(address)] for i in range(len(s)))


def load_captures(challenge_dir):
    sessions = []
    for pcap in sorted(challenge_dir.glob("hallway_*.pcapng")):
        frames = frames_from_pcap(pcap)
        session = {"file": pcap.name, "profile": None, "command": None, "signature": None}
        for i, frame in enumerate(frames):
            if frame.startswith(b"\x02\x81"):
                session["profile"] = parse_profile(frame)
            command = parse_sign_command(frame)
            if command:
                session["command"] = command
            if frame.startswith(b"\x02\x71"):
                session["signature"] = parse_signature(frames, i)
        sessions.append(session)
    return sessions


def main():
    ap = argparse.ArgumentParser(description="Recover ColdTap nonce reuse from NFC captures")
    ap.add_argument(
        "--challenge-dir",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "challenge",
    )
    args = ap.parse_args()

    sessions = load_captures(args.challenge_dir)
    profiles = [s["profile"] for s in sessions if s["profile"]]
    if not profiles:
        raise SystemExit("no badge profile TLV found")

    profile_by_version = {p["version"]: p for p in profiles}
    active_profile = profile_by_version.get("COLDTAP-1.7", profiles[-1])
    print(f"[+] Active badge version: {active_profile['version']}")
    print(f"[+] Chain ID: {active_profile['chain_id']}")
    print(f"[+] Badge address: 0x{active_profile['address'].hex()}")
    print(f"[+] 7-byte field seed: {active_profile['seed'].hex()}")

    signed = [s for s in sessions if s["signature"] and s["command"]]
    by_r = defaultdict(list)
    for session in signed:
        by_r[session["signature"]["r"]].append(session)

    reused = [(r, group) for r, group in by_r.items() if len(group) > 1]
    if not reused:
        raise SystemExit("no reused r value found")

    for r, group in reused:
        print(f"\n[+] Reused signature r: {r.hex()}")
        recovered = []
        for session in group:
            sig = session["signature"]
            command = session["command"]
            nonce = recover_nonce(sig["r"], active_profile["seed"])
            digest = recover_digest(sig["s"], active_profile["address"])
            recovered.append(nonce)
            print(f"    {session['file']}: mode={command['mode']} lc={command['lc']}")
            print(f"      v={sig['v']:02x}")
            print(f"      recovered nonce = {nonce.hex()}")
            print(f"      recovered digest = {digest.hex()}")

        if len(set(recovered)) == 1:
            print(f"[+] Confirmed reused field nonce: {recovered[0].hex()}")
        else:
            raise SystemExit("r collision did not recover a consistent nonce")

    meta = args.challenge_dir / "instance.json"
    if meta.exists():
        text = meta.read_text()
        marker = '"flagCiphertext": "'
        if marker in text:
            ciphertext = text.split(marker, 1)[1].split('"', 1)[0]
            print(f"\n[+] Offline flag ciphertext: {ciphertext}")


if __name__ == "__main__":
    main()
