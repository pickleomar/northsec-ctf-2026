from secrets import randbits
from Crypto.Util.number import *
def uint32_t(x): return x & 0xffffffff

N = 624
M = 397
MATRIX_A = 0x9908b0df
UPPER_MASK = 0x80000000
LOWER_MASK = 0x7fffffff
MAGIC = [0x0, MATRIX_A]  
class ST1919:
    def __init__(self, seed):
        self.index = 7
        self.st = [0 for _ in range(7)]
        self.secret=bytes_to_long(b"NSC{Mer3_n3_tw1t3r_1sn057_crypt0gr4ph_s3cur3_7814693}")
        self.gift=self.secret
        self.st[0] = seed
        for i in range(1, 7):
            self.st[i] = \
                uint32_t(1812433253 * (self.st[i - 1] ^ (self.st[i - 1] >> 30)) + i)

    def twist(self):
        for i in range(N):
            y = (self.st[i % 7] & UPPER_MASK) | (self.st[(i+1) % 7] & LOWER_MASK)
            self.st[i % 7] = self.st[(i + M) % 7] ^ (y >> 1)
            if y & 1:
                self.st[i % 7] ^= MATRIX_A
        self.index = 0
    def shinra(self):
        if self.index >= 7:
            self.tensei()
        y = self.st[self.index]
        y ^= (y >> 11)
        y ^= (y << 7) & 0x9d2c5680  
        y ^= (y << 15) & 0xefc60000  
        y ^= (y >> 18)
        self.gift >>=8
        self.index += 1
        return uint32_t(y)

    def tensei(self):
        for i in range(7):
            y = uint32_t((self.st[i] & 0x80000000) + (self.st[(i + 1) % 7] & 0x7fffffff))
            self.st[i] = self.st[(i + 397) % 7] ^ (y >> 1)
            if y % 2 == 0:
                self.st[i] &= 0x9908b0df
        self.index = 0

if __name__ == '__main__':
    st = ST1919(randbits(512))
    while True:
        choice = int(input("1.shinra\n2.tensei\n"))
        if choice == 1:
            print(st.shinra())
        elif choice == 2:
            v = st.shinra()
            if v == int(input("value:")):
                print(f"{long_to_bytes(st.gift)}")
                p=getPrime(1024)
                q=getPrime(1024)
                N=p*q
                gift=pow(st.secret,2*p,N)
                print(f"gift::{gift}  N::{N}")
                break
            else:
                print("bye bye homie")
                break
        else:
            break
