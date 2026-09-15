# ColdTap
## Author : Fairalien
`#nfc #firmware #side-channel #nonce-reuse #wallet-badge`

## Challenge

The artefacts describe an NFC badge wallet used for sponsor check-ins:

- `badge_fw.bin`, a Cortex-M firmware image
- six hallway NFC captures
- `SponsorVault.sol`, which makes the on-chain side look like EIP-712 release authorization
- `instance.json`, which contains an offline flag ciphertext

The important hint is:

```text
Air-gapped is not field-gapped.
```

## Firmware Notes

The firmware exposes the protocol strings and state layout:

```text
COLDTAP-1.7
eip712 type: CheckIn(address attendee,uint256 boothId,bytes32 nonce)
flagwrap: keccak-xor-v1|coldtap/flag-mask
```

The NFC profile response is TLV encoded:

```text
81 04 <chain id>
82 14 <20-byte badge address>
83 0b <firmware version>
84 07 <7-byte field seed>
```

For the active badge profile this gives:

```text
chain id: 0x7a69
address: 0x5fbdb2315678afecb367f032d93f642f64180aa3
seed:    04771390541820
```

## Vulnerability

The capture responses use ECDSA-shaped TLVs:

```text
71 20 <r>
72 20 <s>
73 01 <v>
```

Disassembling the firmware shows these are not real secp256k1 signatures. The fields are deterministic XOR products:

```text
r[i] = nonce[i]  ^ seed[i mod 7]
s[i] = digest[i] ^ address[i mod 20]
v    = 0x1b + (nonce[0] & 1)
```

`hallway_02.pcapng` and `hallway_05.pcapng` reuse the same `r`. Since the profile leaks the 7-byte seed, the repeated field nonce is recovered directly:

```text
nonce[i] = r[i] ^ seed[i mod 7]
```

Recovered nonce:

```text
ffcd25ecc0592e3c5ef44eb445a8c3f3b01e15f1fcd70bee2dadce9f14515dd0
```

This is the core issue: the badge was “air-gapped” from a host, but the RF field transcripts still leaked enough deterministic material to recover the reused secret nonce.

## PoC

The parser/recovery script is:

```text
WRITEUP/recover_coldtap.py
```

It requires `tshark` because the captures use pcapng USER0 encapsulation. From the challenge directory:

```bash
./WRITEUP/recover_coldtap.py --challenge-dir ./challenge
```

Expected result:

```text
Active badge version: COLDTAP-1.7
Badge address: 0x5fbdb2315678afecb367f032d93f642f64180aa3
7-byte field seed: 04771390541820
Reused signature r: fbba367c94410e3829e7dee05d88c784a38e41e9dcd37cfdbdf9d6bf10264e40
Confirmed reused field nonce: ffcd25ecc0592e3c5ef44eb445a8c3f3b01e15f1fcd70bee2dadce9f14515dd0
```

## Flag

The repository includes the official flag:

```text
NSC{c0ldt4p_n0nc3_r3u53_cr0553d_th3_41r_g4p}
```

I verified the firmware/capture side of the attack end to end. The exact offline `flagCiphertext` wrapper derivation is not represented by a complete routine in the provided firmware image, so the writeup documents the recoverable nonce-reuse attack rather than inventing a decryption formula.
