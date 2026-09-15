from itertools import product
import subprocess

key_hex = "4e53437bf9e9f4f0"
img = "Cartman.jpg"

key = bytes.fromhex(key_hex)

def set_des_parity(byte, parity):
    return (byte & 0xfe) | parity

for mask in product([0,1], repeat=8):
    new_key = bytes(set_des_parity(b, p) for b, p in zip(key, mask))
    try:
        s = new_key.decode("cp1251")
        if s.startswith("NSC{"):
            p = subprocess.run(
                ["steghide", "extract", "-sf", img, "-p", s],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            out = (p.stdout + p.stderr).decode(errors="ignore")
            if "criture des donn" in out or "writing extracted" in out.lower():
                print("[+] KEY FOUND:", s, new_key.hex())
                break
    except:
        pass
