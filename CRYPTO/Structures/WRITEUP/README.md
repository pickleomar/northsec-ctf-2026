
**Challenge**: STRUCTURES

**Tags**: RSA, factoring, Pollard Rho, msieve, yafu

**Author**: Zh3gh05t

**Summary**
- The challenge provides an RSA modulus `N`, public exponent `e=0x10001`, and ciphertext `C`.
- The goal is to recover the plaintext (the flag) by factoring `N`, computing the private exponent `d`, and decrypting `C`.

**Analysis / observations**
- The challenge materials include `plaintext.txt` containing `N`, `e`, and `C`.
- This is a classical RSA crypto problem: if we can factor `N = p * q` we compute phi(N) = (p-1)*(q-1), then `d = e^{-1} mod phi(N)` and `m = C^d mod N` gives the plaintext.
- The difficulty depends entirely on how `N` was generated. The challenge name `STRUCTURES` and hinting in other writeups suggests the primes may have a structural weakness (e.g., small factor, shared factor with other values, weak randomness). If simple methods fail, use general-purpose factoring tools (`msieve`, `yafu`, `ecm`).

**Practical approach**
1. Try simple checks: small prime factors, gcd with known values, check for squared primes, or extremely small prime factors.
2. Run Pollard's Rho (quick for certain composite shapes) and Pollard p-1.
3. If not successful, run `msieve`/`yafu`/`ecm` on `N`. These tools are optimized for large integer factorization and are the standard approach for contest RSA factoring.
4. Once `p` and `q` are found, compute `d = inverse(e, (p-1)*(q-1))` and decrypt `m = pow(C, d, N)`. Convert to bytes to get the flag.

**Exploit script**
The script below automates steps 1-3: it tries trial division and Pollard Rho, and if that fails will attempt to call `msieve` or `yafu` if they are installed. If factors are found it computes the plaintext.

```python
#!/usr/bin/env python3
import subprocess
from math import gcd

N = 18178315915112441606652118137376847977749807751714959768073319302982618515613188627423427373736536936056370105593574535221913040590260470724667288098724883147835192591673055200559634064239819534354916725160790855010091985561669414146945595967865770446068839587544982778404584005402974148740449071092346365929201871099257562938104449662727391683566023289091303633597605132019186179842296078685630597457382328431476802385584003012179288723097124888183822347263603985614266124758305217432156461897563853630612312128886602934349605545045051210075691601378648527061165901004910988981419757038837108789722770790710354378767
e = 0x10001
C = 7200697343804929335625399612648954430254980059794514325858960117858345358505061668141807696974747963882251938001354739772026667317157800149392945349583653438710855992222340938471094519483400749393772977755586430179017933918144217167746248964780522209147181528394986023559231930253051647569494599408687817575817221803179040243266134849057447280799672618842034755420422337837668841437737145237172922798734165013041243962214516423128071502117504569157602421638130500318086370436628342439695673328141295169816212427600370421733613271646081719796593901789562499671530495056236473261214545584035677516665365679664033136292

def is_probable_prime(n):
	# quick primality test using openssl if available, fallback to pow checks
	try:
		subprocess.run(['openssl','prime','-quick',str(n)], check=True, stdout=subprocess.DEVNULL)
		return True
	except Exception:
		# fallback Miller-Rabin with fixed bases for speed (not full-proof here)
		if n < 2:
			return False
		d = n-1
		s = 0
		while d % 2 == 0:
			d//=2; s+=1
		def check(a):
			x = pow(a, d, n)
			if x==1 or x==n-1: return True
			for _ in range(s-1):
				x = (x*x) % n
				if x==n-1: return True
			return False
		for a in [2,3,5,7,11,13,17,19]:
			if a >= n: break
			if not check(a): return False
		return True

def pollards_rho(n):
	if n%2==0: return 2
	import random
	while True:
		c = random.randrange(1, n-1)
		x = random.randrange(2, n-1)
		y = x
		d = 1
		while d==1:
			x = (pow(x,2,n) + c) % n
			y = (pow(y,2,n) + c) % n
			y = (pow(y,2,n) + c) % n
			d = gcd(abs(x-y), n)
			if d==n:
				break
		if d>1 and d<n:
			return d

def try_factor(n):
	# trial small primes
	smalls = [2,3,5,7,11,13,17,19,23,29,31,37,41,43,47,53,59,61,67,71,73,79,83,89,97]
	for p in smalls:
		if n % p == 0:
			return p
	# Pollard Rho attempt
	try:
		f = pollards_rho(n)
		if f and f!=n:
			return f
	except Exception:
		pass
	return None

def factor_with_external(n):
	# try msieve
	try:
		out = subprocess.check_output(['msieve','-v','-q',str(n)], text=True)
		for line in out.splitlines():
			if line.startswith('P') and ' ' in line:
				# msieve prints lines like 'P123  <factor>'
				parts = line.split()
				if len(parts)>=2:
					return int(parts[1])
	except Exception:
		pass
	# try yafu
	try:
		out = subprocess.check_output(['yafu','factor('+str(n)+')'], text=True)
		# yafu prints factors; attempt parse
		for token in out.split():
			if token.isdigit():
				return int(token)
	except Exception:
		pass
	return None

def main():
	print('Trying quick factor methods...')
	f = try_factor(N)
	if f is None:
		print('Quick methods failed, trying external tools (msieve/yafu)...')
		f = factor_with_external(N)
	if f is None:
		print('No factor found. Run msieve/yafu/ECM on N externally.')
		return
	p = f
	q = N//p
	print('Found factor p=', p)
	from Crypto.Util.number import inverse, long_to_bytes
	phi = (p-1)*(q-1)
	d = inverse(e, phi)
	m = pow(C, d, N)
	try:
		print('Plaintext:', long_to_bytes(m))
	except Exception:
		print('Plaintext (int):', m)

if __name__ == '__main__':
	main()

```

**Usage notes**
- If the script's quick methods fail, run an external factoring tool on `N`. Example commands:

```bash
# with msieve
msieve -v N

# with yafu (interactive)
yafu "factor(N)"

# with yafu (non-interactive)
yafu -v "factor(N)"
```

- After `p` and `q` are found the script will print the decrypted plaintext (the flag).



