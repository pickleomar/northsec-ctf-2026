# SHINRATENSEI
## Author : Scriptmagum

`#crypto #prng #mersenne-twister #state-recovery #coppersmith`

## Challenge

The service exposes a custom PRNG called `ST1919`.

Menu option `1` prints one PRNG output. Menu option `2` generates one more output and asks us to predict it. If the prediction is correct, the service prints:

- `st.gift`, which is the secret shifted right by one byte on every PRNG call
- `gift = secret^(2*p) mod N`, where `N = p*q`

The string hardcoded in the public file is a decoy. The exploit should recover the server-side `secret`; do not treat the public `3CI{...n0t_th3_fl4g...}` value as the final flag.

## Bug

`ST1919` uses the normal MT19937 tempering function:

```python
y ^= (y >> 11)
y ^= (y << 7) & 0x9d2c5680
y ^= (y << 15) & 0xefc60000
y ^= (y >> 18)
```

That tempering is reversible. The custom generator also has only 7 internal 32-bit state words, so 7 consecutive outputs are enough to recover the full state and predict the next output.

## Intended Path

1. Send option `1` seven times.
2. Untemper the 7 outputs to recover the 7 state words.
3. Clone the generator with `index = 7`.
4. Generate the next local output and submit it to option `2`.
5. Read the leaked prefix and the RSA-looking `gift, N` pair.
6. Recover the final 8 missing bytes with Coppersmith.

The byte shifting matters: after 7 leaks and the option `2` check, the printed `st.gift` is `secret >> 64`, so only the final 8 bytes are missing.

## PoC

The PRNG break is implemented in `solve.py`.

```bash
python3 solve.py --self-test
python3 solve.py --host HOST --port PORT
```

The socket mode prints the raw service response and, when possible, also prints the exact Sage command to run for the second stage.

If interacting manually, collect 7 outputs from option `1` and pass them directly:

```bash
python3 solve.py 123 456 789 111 222 333 444
```

Then send option `2` and the predicted value printed by the script.

For the final suffix, use the leaked bytes literal, `gift`, and `N`:

```bash
sage recover_suffix.sage "b'KNOWN_PREFIX_FROM_SERVICE'" GIFT N
```

Why this works: for the real secret `m`, `gift = m^(2*p) mod N`. Modulo `p`, Fermat gives `gift = m^2 mod p`, so:

```text
(known_prefix * 2^64 + x)^2 - gift = 0 mod p
```

The unknown `x` is only 64 bits, and `p` is about `N^0.5`, so Sage's `small_roots(..., beta=0.5)` recovers it. If this is run against the public source only, it recovers the decoy string containing `n0t_th3_fl4g`; the actual challenge flag comes from the live server's `secret`.
