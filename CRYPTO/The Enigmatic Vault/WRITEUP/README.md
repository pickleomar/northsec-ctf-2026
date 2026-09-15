
# The Enigmatic Vault
## Author : Wiame5

`#crypto #xor #base64 #rot13 #primes`

## Challenge

We are given an encrypted message, a hint, a public key, and a strange binary blob.

The hint is ROT13:

```text
The answer is in the primes.
Look for the semi-prime numbers.
Use them wisly.
```

`strange_data.bin` is not a real PNG, but `strings` reveals the key:

```text
VIGENERE_KEY:CRYPTO
```

## Intended Path

Decode the Hint => Analyze Binary File => Vigenere Decryption => De-obfuscation => Base64 Decode => XOR with Prime Numbers

1. Decode `hint.txt` with ROT13.
2. Extract `CRYPTO` from `strange_data.bin`.
3. XOR `message.enc` with repeating key `CRYPTO`.
4. Reverse the Base64 body and decode it.
5. XOR the decoded bytes with the intended prime-derived key stream.

The first four final key bytes are forced by the flag format:

```text
decoded ^ NSC{ = 02 03 05 07
```

So the final layer clearly starts with prime numbers.

## PoC / Verification

The verified layers are implemented in `solve.py`:

With the provided artefacts, the deterministic path gives:

```text
repeating-key XOR output:
wlHNxBXa0JyY5R1NxN3elBnT/hjfx8WXmcWf4ZGfGBFT==

reversed Base64:
TFBGfGZ4fWcmXW8xfjh/TnBle3NxN1R5YyJ0aXBxNHlw

XOR with consecutive primes:
NSC{mult1@p...
```

