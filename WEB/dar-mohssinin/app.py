#!/usr/bin/env python3
"""
Dar Mohssinin — AI Pitch Intelligence Platform
Series A SaaS for startup pitch deck analytics and investor matching.

Internal route namespace: /v1/api/*
Public SPA routes: everything else → index.html
"""

from flask import Flask, request, jsonify, session, Response, redirect
from urllib.parse import urljoin, urlparse, unquote
import sqlite3, hashlib, secrets, time, threading, json, os, mimetypes, re
from functools import wraps

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET', 'f0li0_s3cr3t_k3y_xK9mP2qR')

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, 'static')

app.config.update(
    SESSION_COOKIE_HTTPONLY = True,
    SESSION_COOKIE_SAMESITE = 'Lax',
    SESSION_COOKIE_SECURE   = False,
    SESSION_COOKIE_PATH     = '/',
    PERMANENT_SESSION_LIFETIME = 86400,
)

# Legacy compatibility: some older built frontend bundles call /x/* endpoints.
# Keep these working by redirecting to the canonical /v1/api/* namespace.
@app.before_request
def _legacy_api_alias():
    p = request.path
    if p == '/x' or p.startswith('/x/'):
        suffix = '' if p == '/x' else p[2:]
        target = f'/v1/api{suffix}'
        if request.query_string:
            target = f'{target}?{request.query_string.decode()}'
        return redirect(target, code=307)

# ─────────────────────────────────────────────────────────────────────────────
# 404 page (HTML, not JSON) — returned for traversal/scan attempts
# ─────────────────────────────────────────────────────────────────────────────
_404_HTML = b'''<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"/><title>404 - Dar Mohssinin</title>
<style>*{margin:0;padding:0;box-sizing:border-box}
body{background:#07090f;color:#e2e8f0;font-family:monospace;
     display:flex;align-items:center;justify-content:center;min-height:100vh}
.w{text-align:center;padding:2rem}
h1{font-size:5rem;font-weight:900;color:#6366f1;line-height:1}
p{color:#475569;margin-top:1rem;font-size:1rem}
img{margin-top:1.5rem;border-radius:8px;border:1px solid #1e293b;width:280px}
a{color:#6366f1;text-decoration:none;margin-top:1.5rem;display:inline-block;font-size:.875rem}
a:hover{text-decoration:underline}
.sub{font-size:.75rem;color:#334155;margin-top:.5rem}</style></head>
<body><div class="w">
  <h1>404</h1>
  <p>There is no spoon. Also no page.</p>
  <img src="https://c.tenor.com/fKIG2kiLVPgAAAAC/tenor.gif" alt="this is fine"/>
  <p class="sub">// nothing to see here, move along</p>
  <a href="/">Back to Dar Mohssinin</a>
</div></body></html>'''

def html_404():
    return Response(_404_HTML, status=404, mimetype='text/html')

# ─────────────────────────────────────────────────────────────────────────────
# SPA helper
# ─────────────────────────────────────────────────────────────────────────────
def _spa(path=''):
    low = path.lower()
    if '..' in path or '%2f' in low or '%2e' in low:
        return html_404()
    if re.match(r'^(admin|internal)(/|$)', path):
        return html_404()
    if path:
        candidate = os.path.realpath(os.path.join(STATIC_DIR, path.lstrip('/')))
        if candidate.startswith(STATIC_DIR) and os.path.isfile(candidate):
            mime = mimetypes.guess_type(candidate)[0] or 'application/octet-stream'
            with open(candidate, 'rb') as f:
                return Response(f.read(), mimetype=mime)
    index = os.path.join(STATIC_DIR, 'index.html')
    if os.path.isfile(index):
        with open(index, 'rb') as f:
            return Response(f.read(), mimetype='text/html')
    return Response(
        '<html><body style="font-family:monospace;padding:2rem">'
        '<h2>Frontend not built</h2>'
        '<p>Run: <code>cd frontend && npm install && npm run build</code></p>'
        '</body></html>', status=503, mimetype='text/html')

# ─────────────────────────────────────────────────────────────────────────────
# DATABASE
# ─────────────────────────────────────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect('folio.db', check_same_thread=False)
    conn.execute('PRAGMA journal_mode=WAL')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        username      TEXT UNIQUE NOT NULL,
        email         TEXT UNIQUE NOT NULL,
        notify_email  TEXT,
        password_hash TEXT NOT NULL,
        role          TEXT DEFAULT 'founder',
        display_name  TEXT DEFAULT '',
        bio           TEXT DEFAULT '',
        csrf_token    TEXT NOT NULL DEFAULT ''
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS projects (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        owner_id      INTEGER NOT NULL,
        name          TEXT NOT NULL,
        description   TEXT DEFAULT '',
        preview_slug  TEXT NOT NULL,
        status        TEXT DEFAULT 'pending',
        feedback      TEXT DEFAULT '',
        score         INTEGER DEFAULT 0,
        created_at    INTEGER
    )''')
    # Backward-compatible schema migration for older challenge instances.
    # Adds review audit timestamp used by frontend "bot reviewed" activity cues.
    try:
        c.execute('ALTER TABLE projects ADD COLUMN reviewed_at INTEGER')
    except sqlite3.OperationalError:
        pass
    c.execute(
        "UPDATE projects SET reviewed_at=created_at "
        "WHERE status='reviewed' AND reviewed_at IS NULL"
    )
    # Password recovery tokens
    c.execute('''CREATE TABLE IF NOT EXISTS recovery_tokens (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id    INTEGER NOT NULL,
        token      TEXT NOT NULL,
        created_at INTEGER NOT NULL,
        used       INTEGER DEFAULT 0
    )''')
    # Legacy operational magic links (internal admin workflow convenience)
    c.execute('''CREATE TABLE IF NOT EXISTS magic_links (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id    INTEGER NOT NULL,
        token      TEXT NOT NULL,
        purpose    TEXT NOT NULL,
        created_at INTEGER NOT NULL,
        used       INTEGER DEFAULT 0
    )''')
    # Internal notification queue (for @dar-lmohsinin.ma delivery)
    c.execute('''CREATE TABLE IF NOT EXISTS internal_queue (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        recipient   TEXT NOT NULL,
        payload     TEXT NOT NULL,
        created_at  INTEGER NOT NULL,
        retrieved   INTEGER DEFAULT 0
    )''')

    admin_hash = hashlib.sha256('Adm1n_F0l10_S3cr3t!'.encode()).hexdigest()
    admin_csrf = secrets.token_hex(16)
    c.execute('''INSERT OR IGNORE INTO users
                 (username, email, notify_email, password_hash, role, display_name, csrf_token)
                 VALUES (?,?,?,?,?,?,?)''',
              ('admin', 'admin@dar-lmohsinin.ma', 'admin@dar-lmohsinin.ma',
               admin_hash, 'admin', 'Dar Mohssinin Admin', admin_csrf))
    # Keep admin branding/mailbox aligned on existing databases too.
    c.execute(
        """UPDATE users
           SET email='admin@dar-lmohsinin.ma',
               notify_email='admin@dar-lmohsinin.ma',
               display_name='Dar Mohssinin Admin'
           WHERE username='admin'"""
    )
    conn.commit()
    conn.close()

# ─────────────────────────────────────────────────────────────────────────────
# DECORATORS
# ─────────────────────────────────────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def wrap(*a, **kw):
        if 'user_id' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*a, **kw)
    return wrap

def admin_required(f):
    @wraps(f)
    def wrap(*a, **kw):
        if session.get('role') != 'admin':
            return jsonify({'error': 'Forbidden'}), 403
        return f(*a, **kw)
    return wrap

def require_csrf(f):
    """Validates X-CSRF-Token header against DB-stored token for the session user."""
    @wraps(f)
    def wrap(*a, **kw):
        token = request.headers.get('X-CSRF-Token', '')
        conn = get_db()
        row = conn.execute(
            'SELECT csrf_token FROM users WHERE id=?', (session.get('user_id'),)
        ).fetchone()
        conn.close()
        if not row or not secrets.compare_digest(row['csrf_token'], token):
            return jsonify({'error': 'Invalid CSRF token'}), 403
        return f(*a, **kw)
    return wrap

def is_reserved_admin_mailbox(candidate_addr: str, actor_user_id: int | None) -> bool:
    """
    Prevent non-admin users from binding their notify_email to admin's mailbox.
    This closes trivial account-takeover by self-setting notify_email=admin@...
    while preserving the intended bot-driven chain.
    """
    addr = (candidate_addr or '').strip().lower()
    if not addr:
        return False
    conn = get_db()
    admin = conn.execute(
        "SELECT id, email, notify_email FROM users WHERE username='admin'"
    ).fetchone()
    conn.close()
    if not admin:
        return False
    if actor_user_id == admin['id']:
        return False
    admin_email = (admin['email'] or '').strip().lower()
    admin_notify = (admin['notify_email'] or '').strip().lower()
    return addr == admin_email or addr == admin_notify

def _deliver_notification(notify_addr: str, payload: dict):
    """
    Deliver non-security operational notifications to notify_email.
    Internal addresses are routed to in-app internal_queue.
    External addresses are logged as SMTP no-op in this challenge environment.
    """
    addr = (notify_addr or '').strip().lower()
    if not addr:
        return
    if addr.endswith('@dar-lmohsinin.ma'):
        recipient = addr.split('@')[0]
        conn = get_db()
        conn.execute(
            'INSERT INTO internal_queue (recipient, payload, created_at) VALUES (?,?,?)',
            (recipient, json.dumps(payload), int(time.time()))
        )
        conn.commit()
        conn.close()
    else:
        app.logger.info(f'[Mailer] Would send notification email to {addr} payload={payload.get("type", "system")}')

def _issue_magic_link(user_id: int, purpose: str, ttl_hint_sec: int = 900) -> str:
    """
    Create a single-use magic link token for internal operational workflows.
    ttl_hint_sec is only advisory for docs/logging; server-side TTL enforced at use.
    """
    token = secrets.token_urlsafe(32)
    conn = get_db()
    conn.execute(
        'INSERT INTO magic_links (user_id, token, purpose, created_at) VALUES (?,?,?,?)',
        (user_id, token, purpose, int(time.time()))
    )
    conn.commit()
    conn.close()
    return token

def _emit_review_notifications(project_id: int, owner_id: int, project_name: str, score: int):
    """
    Emit two operational notifications after bot review:
    - Deck review result to project owner (notify_email)
    - Admin compliance queue update with legacy one-click magic link
    """
    conn = get_db()
    owner = conn.execute(
        'SELECT username, notify_email FROM users WHERE id=?', (owner_id,)
    ).fetchone()
    admin = conn.execute(
        "SELECT id, notify_email FROM users WHERE username='admin'"
    ).fetchone()
    conn.close()

    if owner:
        _deliver_notification(owner['notify_email'], {
            'type': 'deck_reviewed',
            'project_id': project_id,
            'project_name': project_name,
            'score': score,
            'message': f"Your deck '{project_name}' was reviewed by the compliance bot.",
        })

    if admin:
        token = _issue_magic_link(admin['id'], 'admin_ops')
        _deliver_notification(admin['notify_email'], {
            'type': 'admin_ops',
            'project_id': project_id,
            'project_name': project_name,
            'score': score,
            'link': f'/v1/api/auth/magic/{token}',
            'message': f"Compliance queue update: '{project_name}' requires admin sign-off.",
        })

# ─────────────────────────────────────────────────────────────────────────────
# ADMIN REVIEW BOT
#
# Simulates the admin's browser visiting submitted project preview links.
# Maintains a real authenticated session via requests.Session().
#
# The bot fetches: urljoin(PREVIEW_BASE, unquote(preview_slug))
#   PREVIEW_BASE = 'http://127.0.0.1:<port>/v1/api/projects/preview/'
#
# Subtle flaw: unquote() is called before urljoin() to "handle encoded slugs",
# turning %2e%2e/ into ../ — which urljoin then resolves as a path traversal.
# ─────────────────────────────────────────────────────────────────────────────
_BOT_PORT = int(os.environ.get('PORT', 5000))
_PREVIEW_BASE = f'http://127.0.0.1:{_BOT_PORT}/v1/api/projects/preview/'

def _bot_session():
    """Creates an authenticated requests.Session for the admin account."""
    import requests as req_lib
    s = req_lib.Session()
    s.headers.update({'User-Agent': 'DarMohssinin-ReviewBot/2.1 (internal)'})
    r = s.post(
        f'http://127.0.0.1:{_BOT_PORT}/v1/api/auth/signin',
        json={'username': 'admin', 'password': 'Adm1n_F0l10_S3cr3t!'},
        timeout=10,
    )
    if r.status_code != 200:
        raise RuntimeError('Bot could not authenticate')
    return s

def _bot_review(project_id: int):
    time.sleep(2)
    owner_id = None
    project_name = 'project'
    try:
        conn = get_db()
        row = conn.execute(
            'SELECT preview_slug, owner_id, name FROM projects WHERE id=?', (project_id,)
        ).fetchone()
        conn.close()
        if not row:
            return

        slug = row['preview_slug']
        owner_id = row['owner_id']
        project_name = row['name'] or 'project'

        # Decode slug to handle any percent-encoded characters in stored values.
        # This ensures compatibility with slugs submitted from different clients.
        decoded_slug = unquote(slug)

        # Resolve against the preview catalog base — mirrors browser fetch() behaviour
        target_url = urljoin(_PREVIEW_BASE, decoded_slug)

        app.logger.info(f'[ReviewBot] project={project_id} slug={slug!r} -> {target_url}')

        bot = _bot_session()
        bot.get(target_url, timeout=10, allow_redirects=True)

    except Exception as e:
        app.logger.warning(f'[ReviewBot] error on project {project_id}: {e}')
    finally:
        try:
            conn = get_db()
            reviewed_score = __import__('random').randint(60, 95)
            conn.execute(
                "UPDATE projects SET status='reviewed', "
                "feedback='Sme7lina had floss lmohsinin kamlin liya', "
                "score=?, reviewed_at=? WHERE id=?",
                (reviewed_score, int(time.time()), project_id),
            )
            conn.commit()
            conn.close()
            if owner_id:
                _emit_review_notifications(project_id, owner_id, project_name, reviewed_score)
        except Exception:
            pass

def kick_bot(project_id: int):
    threading.Thread(target=_bot_review, args=(project_id,), daemon=True).start()

# ─────────────────────────────────────────────────────────────────────────────
# AUTH  /v1/api/auth/*
# ─────────────────────────────────────────────────────────────────────────────
@app.route('/v1/api/auth/signup', methods=['POST'])
def signup():
    d = request.get_json() or {}
    username = (d.get('username') or '').strip().lower()
    email    = (d.get('email') or '').strip().lower()
    password = d.get('password') or ''

    if len(username) < 3 or not re.match(r'^[a-z0-9_]+$', username):
        return jsonify({'error': 'Username must be 3+ alphanumeric/underscore chars'}), 400
    if '@' not in email:
        return jsonify({'error': 'Valid email required'}), 400
    if len(password) < 8:
        return jsonify({'error': 'Password must be at least 8 characters'}), 400
    if username == 'admin':
        return jsonify({'error': 'Username not available'}), 409

    ph   = hashlib.sha256(password.encode()).hexdigest()
    csrf = secrets.token_hex(16)
    try:
        conn = get_db()
        conn.execute(
            'INSERT INTO users (username, email, notify_email, password_hash, csrf_token) VALUES (?,?,?,?,?)',
            (username, email, email, ph, csrf)
        )
        conn.commit()
        conn.close()
        return jsonify({'message': 'Account created. Welcome to Dar Mohssinin!'}), 201
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Username or email already registered'}), 409

@app.route('/v1/api/auth/signin', methods=['POST'])
def signin():
    d = request.get_json() or {}
    username = (d.get('username') or '').strip().lower()
    password = d.get('password') or ''
    ph = hashlib.sha256(password.encode()).hexdigest()
    conn = get_db()
    row = conn.execute(
        'SELECT id, username, role, csrf_token FROM users WHERE username=? AND password_hash=?',
        (username, ph)
    ).fetchone()
    conn.close()
    if not row:
        return jsonify({'error': 'Invalid credentials'}), 401
    session.clear()
    session['user_id']  = row['id']
    session['username'] = row['username']
    session['role']     = row['role']
    session.permanent   = True
    return jsonify({
        'username':   row['username'],
        'role':       row['role'],
        'csrf_token': row['csrf_token'],
    })

@app.route('/v1/api/auth/signout', methods=['POST'])
def signout():
    session.clear()
    return jsonify({'message': 'Signed out'})

@app.route('/v1/api/auth/whoami', methods=['GET'])
@login_required
def whoami():
    conn = get_db()
    row = conn.execute(
        'SELECT username, email, notify_email, role, display_name, bio, csrf_token FROM users WHERE id=?',
        (session['user_id'],)
    ).fetchone()
    conn.close()
    if not row:
        session.clear()
        return jsonify({'error': 'Unauthorized'}), 401
    return jsonify(dict(row))

# ─────────────────────────────────────────────────────────────────────────────
# PASSWORD RECOVERY  /v1/api/auth/recover*
#
# Recovery is sent to PRIMARY account email (security channel), not notify_email.
# notify_email is operational-only (deck reviews, admin workflow updates, etc.).
# ─────────────────────────────────────────────────────────────────────────────
@app.route('/v1/api/auth/recover', methods=['POST'])
def request_recovery():
    d = request.get_json() or {}
    username = (d.get('username') or '').strip().lower()
    if not username:
        return jsonify({'error': 'username required'}), 400

    conn = get_db()
    user = conn.execute(
        'SELECT id, email FROM users WHERE username=?', (username,)
    ).fetchone()

    if user:
        token = secrets.token_urlsafe(32)
        conn.execute(
            'INSERT INTO recovery_tokens (user_id, token, created_at) VALUES (?,?,?)',
            (user['id'], token, int(time.time()))
        )
        conn.commit()

        primary_addr = (user['email'] or '').strip().lower()
        app.logger.info(f'[SecureMailer] Would send password recovery token to primary email: {primary_addr}')

    conn.close()
    # Always return same response — don't leak whether username exists
    return jsonify({'message': 'If that account exists, recovery instructions were sent to the primary account email.'}), 200

@app.route('/v1/api/auth/recover/confirm', methods=['POST'])
def confirm_recovery():
    d = request.get_json() or {}
    token    = (d.get('token') or '').strip()
    new_pass = d.get('password') or ''

    if not token or len(new_pass) < 8:
        return jsonify({'error': 'token and password (min 8 chars) required'}), 400

    conn = get_db()
    row = conn.execute(
        '''SELECT rt.user_id FROM recovery_tokens rt
           WHERE rt.token=? AND rt.used=0 AND rt.created_at > ?''',
        (token, int(time.time()) - 3600)
    ).fetchone()

    if not row:
        conn.close()
        return jsonify({'error': 'Invalid or expired recovery token'}), 400

    ph = hashlib.sha256(new_pass.encode()).hexdigest()
    conn.execute('UPDATE users SET password_hash=? WHERE id=?', (ph, row['user_id']))
    conn.execute('UPDATE recovery_tokens SET used=1 WHERE token=?', (token,))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Password updated successfully. You can now sign in.'})

@app.route('/v1/api/auth/magic/<token>', methods=['GET'])
def redeem_magic_link(token):
    """
    Legacy internal workflow convenience link.
    Single-use token that authenticates the corresponding user session.
    Used by admin operations notifications.
    """
    token = (token or '').strip()
    if not token:
        return jsonify({'error': 'token required'}), 400

    conn = get_db()
    row = conn.execute(
        '''SELECT ml.id, ml.user_id, ml.purpose, u.username, u.role, u.csrf_token
           FROM magic_links ml
           JOIN users u ON u.id = ml.user_id
           WHERE ml.token=? AND ml.used=0 AND ml.created_at > ?''',
        (token, int(time.time()) - 900)
    ).fetchone()

    if not row:
        conn.close()
        return jsonify({'error': 'Invalid or expired magic link'}), 400

    conn.execute('UPDATE magic_links SET used=1 WHERE id=?', (row['id'],))
    conn.commit()
    conn.close()

    session.clear()
    session['user_id'] = row['user_id']
    session['username'] = row['username']
    session['role'] = row['role']
    session.permanent = True

    return jsonify({
        'message': 'Magic link accepted',
        'username': row['username'],
        'role': row['role'],
        'purpose': row['purpose'],
    }), 200

# ─────────────────────────────────────────────────────────────────────────────
# ACCOUNT SETTINGS  /v1/api/account/*
# ─────────────────────────────────────────────────────────────────────────────
@app.route('/v1/api/account/profile', methods=['GET'])
@login_required
def get_profile():
    conn = get_db()
    row = conn.execute(
        'SELECT username, email, notify_email, display_name, bio, role FROM users WHERE id=?',
        (session['user_id'],)
    ).fetchone()
    conn.close()
    return jsonify(dict(row))

@app.route('/v1/api/account/profile', methods=['PATCH'])
@login_required
@require_csrf
def update_profile():
    d = request.get_json() or {}
    display_name = (d.get('display_name') or '').strip()[:80]
    bio          = (d.get('bio') or '').strip()[:500]
    conn = get_db()
    conn.execute(
        'UPDATE users SET display_name=?, bio=? WHERE id=?',
        (display_name, bio, session['user_id'])
    )
    conn.commit()
    conn.close()
    return jsonify({'message': 'Profile updated'})

@app.route('/v1/api/account/security', methods=['POST'])
@login_required
@require_csrf
def update_security():
    """Change password — POST + JSON + CSRF. No query params accepted."""
    d = request.get_json() or {}
    current  = d.get('current_password') or ''
    new_pass = d.get('new_password') or ''
    if len(new_pass) < 8:
        return jsonify({'error': 'New password must be at least 8 characters'}), 400
    curr_hash = hashlib.sha256(current.encode()).hexdigest()
    conn = get_db()
    row = conn.execute(
        'SELECT id FROM users WHERE id=? AND password_hash=?',
        (session['user_id'], curr_hash)
    ).fetchone()
    if not row:
        conn.close()
        return jsonify({'error': 'Current password incorrect'}), 401
    new_hash = hashlib.sha256(new_pass.encode()).hexdigest()
    conn.execute('UPDATE users SET password_hash=? WHERE id=?', (new_hash, session['user_id']))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Password updated'})

# ─────────────────────────────────────────────────────────────────────────────
# NOTIFICATION PREFERENCES  /v1/api/account/notifications/*
#
# One-click unsubscribe endpoint — accepts GET so email clients can invoke it
# directly without JavaScript. Session cookie is still validated.
#
# Flaw: updates notify_email based on query param. Reachable by bot via CSPT.
# ─────────────────────────────────────────────────────────────────────────────
@app.route('/v1/api/account/notifications/unsubscribe', methods=['GET'])
@login_required
def notification_unsubscribe():
    """
    One-click notification management.
    Designed for unsubscribe links embedded in outgoing emails.
    Updates the notification delivery address for the authenticated user.
    """
    new_addr = request.args.get('email', '').strip()
    if not new_addr:
        return jsonify({'error': 'email parameter required'}), 400
    if is_reserved_admin_mailbox(new_addr, session.get('user_id')):
        return jsonify({'error': 'That mailbox is reserved'}), 403
    conn = get_db()
    conn.execute('UPDATE users SET notify_email=? WHERE id=?', (new_addr, session['user_id']))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Notification preferences updated'})

@app.route('/v1/api/account/notifications', methods=['GET'])
@login_required
def get_notification_prefs():
    conn = get_db()
    row = conn.execute(
        'SELECT notify_email FROM users WHERE id=?', (session['user_id'],)
    ).fetchone()
    conn.close()
    return jsonify({'notify_email': row['notify_email']})

@app.route('/v1/api/account/notifications', methods=['PATCH'])
@login_required
@require_csrf
def update_notification_prefs():
    d = request.get_json() or {}
    new_addr = (d.get('notify_email') or '').strip()
    if not new_addr or '@' not in new_addr:
        return jsonify({'error': 'Valid notify_email required'}), 400
    if is_reserved_admin_mailbox(new_addr, session.get('user_id')):
        return jsonify({'error': 'That mailbox is reserved'}), 403
    conn = get_db()
    conn.execute('UPDATE users SET notify_email=? WHERE id=?', (new_addr, session['user_id']))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Notification address updated'})

# ─────────────────────────────────────────────────────────────────────────────
# PROJECTS  /v1/api/projects/*
# ─────────────────────────────────────────────────────────────────────────────
@app.route('/v1/api/projects', methods=['GET'])
@login_required
def list_projects():
    conn = get_db()
    rows = conn.execute(
        '''SELECT id, name, description, preview_slug, status, feedback, score, created_at, reviewed_at
           FROM projects WHERE owner_id=? ORDER BY id DESC''',
        (session['user_id'],)
    ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route('/v1/api/projects', methods=['POST'])
@login_required
def create_project():
    """
    POST /v1/api/projects
    { name, description, preview_slug }

    preview_slug: a URL path segment identifying the live deck preview page.
    Stored verbatim. Admin bot resolves it against the preview catalog base.

    Validation: rejects obvious traversal strings (../), but percent-encoded
    variants are treated as valid slugs and stored without normalization.
    """
    d    = request.get_json() or {}
    name = (d.get('name') or '').strip()[:120]
    desc = (d.get('description') or '').strip()[:500]
    slug = (d.get('preview_slug') or '').strip()

    if not name:
        return jsonify({'error': 'Project name is required'}), 400
    if not slug:
        return jsonify({'error': 'preview_slug is required'}), 400

    # Basic traversal guard — prevents obvious ../ patterns
    if '../' in slug:
        return jsonify({'error': 'Invalid preview slug: path traversal not permitted'}), 400

    conn = get_db()
    cur = conn.execute(
        'INSERT INTO projects (owner_id, name, description, preview_slug, created_at) VALUES (?,?,?,?,?)',
        (session['user_id'], name, desc, slug, int(time.time()))
    )
    project_id = cur.lastrowid
    conn.commit()
    conn.close()

    kick_bot(project_id)

    return jsonify({
        'message': 'Project submitted. Our team will review your deck shortly.',
        'id': project_id,
    }), 201

@app.route('/v1/api/projects/<int:project_id>', methods=['GET'])
@login_required
def get_project(project_id):
    conn = get_db()
    row = conn.execute(
        '''SELECT id, name, description, preview_slug, status, feedback, score, created_at, reviewed_at
           FROM projects WHERE id=? AND owner_id=?''',
        (project_id, session['user_id'])
    ).fetchone()
    conn.close()
    if not row:
        return jsonify({'error': 'Not found'}), 404
    return jsonify(dict(row))

@app.route('/v1/api/projects/preview/<path:slug>', methods=['GET'])
@login_required
def project_preview(slug):
    """
    GET /v1/api/projects/preview/<slug>
    Returns metadata for a project identified by its preview slug.
    Normal use: admin bot fetches this to confirm the preview is reachable.
    CSPT payloads resolve AWAY from this route to other endpoints.
    """
    conn = get_db()
    row = conn.execute(
        'SELECT name, description, preview_slug, status FROM projects WHERE preview_slug=? AND owner_id=?',
        (slug, session['user_id'])
    ).fetchone()
    conn.close()
    if not row:
        return jsonify({'error': 'Preview not found'}), 404
    return jsonify(dict(row))

# ─────────────────────────────────────────────────────────────────────────────
# ANALYTICS  /v1/api/analytics/*  (admin only, decoy surface)
# ─────────────────────────────────────────────────────────────────────────────
@app.route('/v1/api/analytics/overview', methods=['GET'])
@login_required
@admin_required
def analytics_overview():
    conn = get_db()
    total_projects = conn.execute('SELECT COUNT(*) FROM projects').fetchone()[0]
    total_users    = conn.execute('SELECT COUNT(*) FROM users').fetchone()[0]
    conn.close()
    return jsonify({
        'total_projects': total_projects,
        'total_users':    total_users,
        'arr':            '2.4M',
        'nps':            72,
    })

# ─────────────────────────────────────────────────────────────────────────────
# NOTIFICATIONS FEED  /v1/api/notifications/feed
#
# Returns recent system notifications for the current user's notify_email inbox.
# Drives the in-app notification bell. Polls every 5s from the frontend.
# ─────────────────────────────────────────────────────────────────────────────
@app.route('/v1/api/notifications/feed', methods=['GET'])
@login_required
def notifications_feed():
    conn = get_db()
    user = conn.execute(
        'SELECT notify_email FROM users WHERE id=?', (session['user_id'],)
    ).fetchone()

    if not user:
        conn.close()
        return jsonify({'notifications': []})

    notify_addr = user['notify_email'] or ''

    # For @dar-lmohsinin.ma addresses, pull from internal queue
    if notify_addr.endswith('@dar-lmohsinin.ma'):
        recipient = notify_addr.split('@')[0]
        rows = conn.execute(
            '''SELECT id, payload, created_at, retrieved FROM internal_queue
               WHERE recipient=? ORDER BY created_at DESC LIMIT 20''',
            (recipient,)
        ).fetchall()
        conn.close()
        items = []
        for r in rows:
            try:
                data = json.loads(r['payload'])
                item = {
                    'id':         r['id'],
                    'type':       data.get('type', 'system'),
                    'title':      _notif_title(data.get('type', '')),
                    'body':       _notif_body(data),
                    'created_at': r['created_at'],
                    'read':       bool(r['retrieved']),
                }
                if data.get('type') == 'admin_ops':
                    item['link'] = data.get('link')
                    item['project_name'] = data.get('project_name')
                items.append(item)
            except Exception:
                pass
        return jsonify({'notifications': items, 'address': notify_addr})

    conn.close()
    # External address — no in-app delivery (would go to SMTP in production)
    return jsonify({
        'notifications': [],
        'address': notify_addr,
        'note': 'Notifications for external addresses are delivered via email only.',
    })

def _notif_title(ntype):
    return {
        'deck_reviewed':     'Your Deck Was Reviewed',
        'admin_ops':         'Compliance Queue Update',
        'investor_match':    'New Investor Match',
    }.get(ntype, 'System Notification')

def _notif_body(data):
    ntype = data.get('type', '')
    if ntype == 'deck_reviewed':
        return f'Your deck scored {data.get("score", "—")}/100.'
    if ntype == 'admin_ops':
        return data.get('message', 'A reviewed project requires admin compliance sign-off.')
    return data.get('message', 'New notification from Dar Mohssinin.')

# ─────────────────────────────────────────────────────────────────────────────
# INTERNAL NOTIFICATION QUEUE  /v1/api/internal/notify/*
#
# Retrieves queued messages for the CURRENT user's internal mailbox only.
# This endpoint is session-authenticated and mailbox-scoped.
# ─────────────────────────────────────────────────────────────────────────────
@app.route('/v1/api/internal/notify/<recipient>', methods=['GET'])
@login_required
def internal_notify_get(recipient):
    conn = get_db()
    user = conn.execute(
        'SELECT notify_email FROM users WHERE id=?', (session['user_id'],)
    ).fetchone()
    notify_addr = (user['notify_email'] if user else '') or ''
    if not notify_addr.endswith('@dar-lmohsinin.ma'):
        conn.close()
        return jsonify({'error': 'Internal mailbox not enabled for this account'}), 403

    owner_recipient = notify_addr.split('@')[0].strip().lower()
    if recipient.strip().lower() != owner_recipient:
        conn.close()
        return jsonify({'error': 'Forbidden: mailbox ownership check failed'}), 403

    rows = conn.execute(
        '''SELECT id, payload, created_at FROM internal_queue
           WHERE recipient=? AND retrieved=0 ORDER BY created_at DESC''',
        (owner_recipient,)
    ).fetchall()
    if rows:
        ids = [r['id'] for r in rows]
        conn.execute(
            f'UPDATE internal_queue SET retrieved=1 WHERE id IN ({",".join("?" for _ in ids)})',
            ids
        )
        conn.commit()
    conn.close()
    messages = []
    for r in rows:
        try:
            messages.append(json.loads(r['payload']))
        except Exception:
            pass
    return jsonify({'messages': messages})

# ─────────────────────────────────────────────────────────────────────────────
# INVESTOR MESSAGES  /v1/api/messages/*
# ─────────────────────────────────────────────────────────────────────────────
@app.route('/v1/api/messages', methods=['GET'])
@login_required
def get_messages():
    import random
    auto_replies = [
        "Compelling narrative. Is the preview link live? Our bot doesn't like 404s, it gets emotional.",
        "Interesting TAM. Submit a project and our bot will fetch it. The bot always fetches. Always.",
        "Love the founder story. Make sure your deck preview is reachable — the bot is watching.",
        "Strong metrics. Have you noticed that after review your project status changes in about 2 seconds? Weird right.",
        "Good timing for this market. Drop your preview link. The bot is hungry.",
    ]
    return jsonify({
        'messages': [
            {'from': 'Dar Mohssinin Team', 'body': random.choice(auto_replies), 'ts': int(time.time()) - 3600}
        ]
    })

# ─────────────────────────────────────────────────────────────────────────────
# FLAG  /v1/api/capture  (admin only)
# ─────────────────────────────────────────────────────────────────────────────
@app.route('/v1/api/capture', methods=['GET'])
@login_required
@admin_required
def capture_flag():
    return jsonify({
        'flag':    'NSC{14h_yd3w3mh4_n34m4_lfl4g_0lm4_fl0s_lm0hss1n_k4m1n_l1ya}',
        'meme': 'https://c.tenor.com/TbTe1Nc6j34AAAAC/tenor.gif',
    })

# ─────────────────────────────────────────────────────────────────────────────
# SPA CATCH-ALL — must be last
# ─────────────────────────────────────────────────────────────────────────────
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_spa(path):
    return _spa(path)

# ─────────────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    init_db()
    print('\n[*] Dar Mohssinin dev server starting')
    print(f'[*] STATIC_DIR  : {STATIC_DIR}')
    print(f'[*] index.html  : {os.path.isfile(os.path.join(STATIC_DIR, "index.html"))}\n')
    app.run(host='127.0.0.1', port=_BOT_PORT, debug=False)
