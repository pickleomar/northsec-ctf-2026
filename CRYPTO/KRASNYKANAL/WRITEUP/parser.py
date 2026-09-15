import sys

with open(sys.argv[1], 'rb') as f:
    data = f.read()

# Trouver sha1 et extraire IV, c1, c2
sha1_offset = data.find(b'sha1')
iv = data[sha1_offset+5:sha1_offset+13]
c1 = data[sha1_offset+13:sha1_offset+21]
c2 = data[sha1_offset+21:sha1_offset+29]

# JPEG header (premiers 16 octets)
jpeg_header = bytes.fromhex("ffd8ffe000104a464946000101000001")

# Calculer les clairs
p1 = jpeg_header[:8]    # 8 premiers octets
p2 = jpeg_header[8:16]  # 8 suivants

# Calculer iv xor p1
iv_xor_p1 = bytes(a ^ b for a, b in zip(iv, p1))
c1_xor_p2 = bytes(a ^ b for a, b in zip(c1, p2))

hash1 = f"{c1.hex()}:{iv_xor_p1.hex()}"
hash2 = f"{c2.hex()}:{c1_xor_p2.hex()}"
print(iv.hex())
print("\nLes deux hashs:")
print(hash1)
print(hash2)