#!/usr/bin/env sage

from Crypto.Util.number import *
from secret import flag as _f, nonce as _k

PREC = 1363


def post_process(z, p):
    n1 = (z**3 - 3*z).n(p)
    n2 = (1 - 3*z**2).n(p)
    return (n1 / n2).n(p)
    

def core_transform(x, k, p):
    a = (20 * sin(x)**3 * cos(x)**3
         - 6 * sin(x) * cos(x) * (sin(x)**4 + cos(x)**4)).n(p)

    b = (1 - cos(6*x) - k * a).n(p)
    c = (sin(6*x) + k * (cos(6*x) + 1)).n(p)

    return (b / c).n(p)





m = bytes_to_long(_f)

stage1 = core_transform(m, _k, PREC)
stage2 = post_process(stage1, PREC)

print(f"out = {stage2}")