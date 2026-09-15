#!/usr/bin/env python3
import base64
import codecs
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1] / "CHALLENGE"


def xor_repeating(data, key):
    return bytes(byte ^ key[i % len(key)] for i, byte in enumerate(data))


def primes(count):
    out = []
    n = 2
    while len(out) < count:
        is_prime = True
        for p in out:
            if p * p > n:
                break
            if n % p == 0:
                is_prime = False
                break
        if is_prime:
            out.append(n)
        n += 1
    return out


def main():
    hint = (ROOT / "hint.txt").read_text().strip()
    decoded_hint = codecs.decode(hint, "rot_13")
    print(f"[+] ROT13 hint: {decoded_hint}", flush=True)

    strange = (ROOT / "strange_data.bin").read_bytes()
    marker = b"VIGENERE_KEY:"
    key_start = strange.index(marker) + len(marker)
    key = strange[key_start:strange.index(b"\x00", key_start)]
    print(f"[+] key from strange_data.bin: {key.decode()}", flush=True)

    message = (ROOT / "message.enc").read_bytes()
    stage1 = xor_repeating(message, key)
    print(f"[+] repeating-key XOR output: {stage1.decode()}", flush=True)

    body = stage1.rstrip(b"=")
    stage2_b64 = body[::-1] + b"=" * ((4 - len(body) % 4) % 4)
    stage2 = base64.b64decode(stage2_b64)
    print(f"[+] reversed Base64: {stage2_b64.decode()}", flush=True)
    print(f"[+] decoded bytes: {stage2.hex()}", flush=True)

    prime_key = primes(len(stage2))
    candidate = bytes(byte ^ prime_key[i] for i, byte in enumerate(stage2))
    print(f"[+] XOR with consecutive primes: {candidate!r}", flush=True)

    if candidate.startswith(b"NSC{") and candidate.endswith(b"}") and all(32 <= c < 127 for c in candidate):
        print(candidate.decode(), flush=True)
    else:
        print(
            "[-] provided artefacts do not produce a valid printable NSC{...} flag "
            "with the documented consecutive-prime final layer",
            flush=True,
        )
        raise SystemExit(1)


if __name__ == "__main__":
    main()
