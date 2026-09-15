**Challenge:** GEAR 5 (MISC)  
**Author:** Fairalien
**Flag:** `NSC{G34R_F1V3_S0N_OF_The_5UN__N1K4}`

### Overview
The challenge title is a steganographic string that visually appears as `GEAR 5` but contains a hidden payload encoded with zero-width characters. An accompanying image of Luffy in Gear 5 form and a provided encoder script (`passphrase.py`) confirm the technique and theme (Nika / Sun God).

### Intended Path
1. Observe that the challenge title contains invisible characters (copy/paste or inspect the raw string).
2. Extract the sequence of Zero-Width Non-Joiner (`U+200C` → bit 0) and Zero-Width Joiner (`U+200D` → bit 1).
3. Group the recovered bits into 8-bit bytes and convert to ASCII.
4. The decoded payload is the passphrase `Nika_15_Th3_K1NG_Of_A11_The_Pirates`.
5. Combined with the Gear 5 / Nika thematic elements, this yields the flag in the expected leetspeak format.

### PoC (decoder)
```python
def decode_hidden(encoded: str) -> str:
    binary = []
    for c in encoded:
        if c == '\u200c':
            binary.append('0')
        elif c == '\u200d':
            binary.append('1')
    binstr = ''.join(binary)
    chars = []
    for i in range(0, len(binstr), 8):
        byte = binstr[i:i+8]
        if len(byte) == 8:
            chars.append(chr(int(byte, 2)))
    return ''.join(chars)

with open('challenge_tittle.txt', 'r', encoding='utf-8') as f:
    data = f.read().strip()

print(decode_hidden(data))
```

The recovered string matches the secret used in the supplied encoder, confirming the path.