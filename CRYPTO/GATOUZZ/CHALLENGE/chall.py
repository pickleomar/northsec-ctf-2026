from Crypto.Util.number import *
flag=b'NSC{REDACTED}'

a ,b= (getPrime(1024), getPrime(1024))
p,s= (a*b, a+b)

c ,d= (pow(bytes_to_long(flag), 65537, p),int(pow(65537, -1, a*b-a-b+1)) )  

x,y =( int(int(pow(d, -1, p)) >> 567),(int((s)>> 567)))

print(f'{p=}')
print(f'{x=}')
print(f'{y=}')
print(f'{c=}')

