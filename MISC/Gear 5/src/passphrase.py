def encode_hidden(carrier: str, secret: str) -> str:
    """Hide a secret string inside a carrier string using zero-width characters."""
    # Convert secret to binary
    binary = ''.join(format(ord(c), '08b') for c in secret)
    
    # Map binary to zero-width characters
    # '0' -> Zero-Width Non-Joiner (U+200C)
    # '1' -> Zero-Width Joiner (U+200D)
    zero_width = {
        '0': '\u200C',
        '1': '\u200D'
    }
    
    hidden = ''.join(zero_width[bit] for bit in binary)
    
    # Embed hidden string after the first character of the carrier
    return carrier[0] + hidden + carrier[1:]



carrier = "GEAR 5"
secret  = "Nika_15_Th3_K1NG_Of_A11_The_Pirates"

encoded = encode_hidden(carrier, secret)

print("=== Encoding ===")
print(f"Carrier : {carrier!r}")
print(f"Secret  : {secret!r}")
print(f"Encoded : {encoded!r}")
print(f"Visible : {encoded}")          # looks like "Gear 5"
