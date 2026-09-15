from Crypto.Util.number import *
flag=b"NSC{REDACTED}"
p=random_prime(2^150)
q=random_prime(2^150)
n=p*q
assert bytes_to_long(flag) < p*q
tot=(p-1)*(q-1)
e=0x10001
c=pow(bytes_to_long(flag),e,n)
print(f"{n=}")
print(f"{c=}")