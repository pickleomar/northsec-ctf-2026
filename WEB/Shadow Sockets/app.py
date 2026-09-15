#!/usr/bin/env python3
"""
Shadow Analytics - Enterprise Backend
Version: 2.1.4
Copyright (c) 2024 Shadow Analytics Inc.
"""

from flask import Flask, render_template, jsonify, send_file, request, session
from flask_sock import Sock
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import struct
import json
import time
import secrets
import io
from datetime import datetime
from PIL import Image, ImageDraw

# Internal Protocol Constants
_SYNC_MASK = 115  # Protocol sync byte (Player must discover this is 0x73)
_MAGIC_HEADER = 0x4D54524B

# Global State
WS_AUTHENTICATED_SESSIONS = set()
app = Flask(__name__)
app.secret_key = secrets.token_hex(32)
sock = Sock(app)

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["500 per day", "100 per hour"]
)

# Configuration
API_ACCESS_KEY = "mtrk_live_7f8a9b2c_d4e5f6a1_shadow_ops_backend_admin"
SYSTEM_SECRET = "NSC{T3rF_dy1_W3b50ck3t_S31B_fh4D_lw3Qt}"

# System Responses
SYSTEM_MESSAGES = [
    "NSC{brut3_f0rc3_w0nt_f1x_y0ur_sk1ll_1ssu3}",
    "NSC{p1z_st0p_cURLing_my_pr1v4t3_v4r14bl3s}",
    "NSC{4_b1t3_0f_s0ck3ts_1s_h4rd_t0_sw4ll0w_th3s3_d4ys}",
    "NSC{c0ngr4ts_y0u_pl4y3d_y0urs3lf_4nd_g0t_b4nn3d}"
]

security_log = {}
flagged_ips = set()

def monitor_traffic(ip, endpoint):
    key = f"{ip}:{endpoint}"
    if key not in security_log:
        security_log[key] = {"count": 0, "first": time.time()}
    security_log[key]["count"] += 1
    if security_log[key]["count"] > 10:
        flagged_ips.add(ip)

def generate_security_captcha():
    img = Image.new('RGB', (200, 80), color='white')
    draw = ImageDraw.Draw(img)
    for _ in range(100):
        x = secrets.randbelow(200)
        y = secrets.randbelow(80)
        draw.point((x, y), fill='lightgray')
    
    # Hints hidden in plain sight
    draw.text((150, 60), "0x73", fill='#f0f0f0')
    
    captcha_text = secrets.token_hex(3).upper()
    draw.text((20, 20), captcha_text, fill='black')
    
    img_io = io.BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)
    return img_io, captcha_text

@app.before_request
def session_manager():
    if 'session_id' not in session:
        session['session_id'] = secrets.token_hex(16)
        session['first_visit'] = time.time()
    if 'visited_endpoints' not in session:
        session['visited_endpoints'] = []
    session['visited_endpoints'].append(request.path)

@app.route('/')
@limiter.limit("60 per minute")
def dashboard():
    time.sleep(0.115) 
    return render_template('dashboard.html', 
                         timestamp=int(time.time()),
                         hint_timing=115,
                         session_id=session.get('session_id', 'unknown'))

@app.route('/admin')
@limiter.limit("10 per minute")
def admin_panel():
    monitor_traffic(request.remote_addr, '/admin')
    
    return render_template('fake_admin.html', 
                         message="Access Denied - Invalid Credentials")

@app.route('/admin/login', methods=['POST'])
@limiter.limit("5 per minute")
def admin_login():
    monitor_traffic(request.remote_addr, '/admin/login')
    username = request.form.get('username', '')
    password = request.form.get('password', '')
    
    defaults = [('admin', 'admin'), ('admin', 'password'), ('root', 'root')]
    
    if (username.lower(), password.lower()) in defaults:
        return jsonify({
            "success": False,
            "flag": SYSTEM_MESSAGES[0],
            "message": "Security Alert: Default credentials detected."
        })
    return jsonify({"success": False, "message": "Authentication failed."}), 401

@app.route('/captcha.png')
def serve_captcha():
    img_io, captcha_text = generate_security_captcha()
    session['captcha'] = captcha_text
    return send_file(img_io, mimetype='image/png')

@app.route('/logo.png')
def serve_logo():
    img = Image.new('RGB', (200, 100), color='#1e3c72')
    draw = ImageDraw.Draw(img)
    draw.text((40, 35), "SHADOW METRICS", fill='white')
    img_io = io.BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)
    return send_file(img_io, mimetype='image/png')

@app.route('/api/status')
def system_status():
    return jsonify({
        "status": "operational",
        "version": "2.1.4",
        "rate_limit": {"limit": 500, "reset": int(time.time() + 3600)}
    })

@app.route('/api/internal/status')
@limiter.limit("20 per minute")
def internal_status():
    return jsonify({
        "status": "deprecated",
        "message": "Endpoint moved. Check archive for legacy configs.",
        "websocket_path": "/stream/metrics",
        "archive_years": ["2023", "2024"]
    })

@app.route('/api/internal/archive/<year_month>')
@limiter.limit("10 per minute")
def retrieve_archive(year_month):
    current_sid = session.get('session_id')
    time.sleep(0.5)
    
    if not current_sid or current_sid not in WS_AUTHENTICATED_SESSIONS:
        return jsonify({
            "error": "Unauthorized",
            "message": "Archive access requires active telemetry session",
            "hint": "Establish WebSocket connection first"
            }), 401
    
    if year_month == "2024-11":
        return jsonify({
            "archived_configs": [
                {"bot_id": "bot_001", "config": {"token_part_1": "mtrk_live_7f8a9b2c", "deployed": "2024-11-03", "status": "active"}},
                {"bot_id": "bot_002", "config": {"token_part_2": "d4e5f6a1", "deployed": "2024-11-08"}},
                {"bot_id": "bot_003", "config": {"token_part_3": "shadow_ops_backend_admin", "deployed": "2024-11-12", "classification": "CONFIDENTIAL"}}
            ],
            "validation_endpoint": "/api/validate"
        })
    return jsonify({"error": "Archive not found"}), 404

@app.route('/api/validate')
@limiter.limit("5 per minute")
def validate_key():
    token = request.args.get('token', '')
    time.sleep(1)
    
    if token == API_ACCESS_KEY:
        return jsonify({
            "valid": True,
            "flag": SYSTEM_SECRET,
            "message": "Identity Verified.",
            "user": "Delta_Killer"
        })
    monitor_traffic(request.remote_addr, '/api/validate')
    return jsonify({"valid": False, "message": "Invalid token"}), 401

@app.route('/robots.txt')
def robot_config():
    return """User-agent: *
Disallow: /admin/
Disallow: /api/internal/
Disallow: /.git/
Disallow: /backup/
Disallow: /config/
""", 200, {'Content-Type': 'text/plain'}

@app.route('/analytics-core.min.js')
def client_library():
    # This file contains the Clues for the player!
    js_code = """
/**
 * Shadow Analytics Core v2.1.4
 * (c) 2024 Shadow Analytics Inc.
 * Protocol: MTRK
 */
(function(window, undefined) {
    'use strict';
    var config = {
        ws: 'd3M6Ly9sb2NhbGhvc3Q6NTAwMC9zdHJlYW0vbWV0cmljcw==',
        magic: 'TUFHSUNfSEVBREVSOjB4NEQ1NDUyNEI=',
        protocol: 'UHJvdG9jb2xWZXJzaW9uOjF8WE9SX0tFWToweDcz',
        checksum: btoa('XOR_KEY_DECIMAL:115')
    };
    function decode(str) { try { return atob(str); } catch(e) { return str; } }
    function init() {
        var endpoint = decode(config.ws);
        console.log('[Analytics] Initializing telemetry stream...');
        if (window.location.search.includes('debug=1')) {
            console.log('[DEBUG] Config loaded');
        }
    }
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
    window.__analytics = {
        version: '2.1.4',
        debug: function() {
            console.log('WebSocket:', decode(config.ws));
            console.log('Magic Header:', decode(config.magic));
        }
    };
})(window);
"""
    return js_code, 200, {'Content-Type': 'application/javascript'}

@sock.route('/stream/metrics')
def telemetry_stream(ws):
    try:
        data = ws.receive(timeout=10)
        
        if not data or len(data) < 6:
            return
        
        magic = struct.unpack('>I', data[:4])[0]
        version = struct.unpack('>H', data[4:6])[0]
        
        if magic != _MAGIC_HEADER or version != 0x0001:
            ws.send(json.dumps({"error": "Protocol Mismatch"}))
            return
        
        # Implicit XOR Decryption (The Player must figure this out from JS file)
        payload_encrypted = data[6:]
        payload_decrypted = bytes([b ^ _SYNC_MASK for b in payload_encrypted])
        
        try:
            json.loads(payload_decrypted)
        except:
            ws.send(json.dumps({"error": "Payload Corrupted"}))
            return
        
        current_sid = session.get('session_id')
        if current_sid:
            WS_AUTHENTICATED_SESSIONS.add(current_sid)
            
        session['ws_connected_at'] = time.time()        
        
        ws.send(json.dumps({
            "status": "authenticated",
            "session_id": current_sid,
            "protocol": "1.0"
        }))
        
        ws.send(json.dumps({
            "event": "metrics",
            "active_bots": 47,
            "timestamp": datetime.now().isoformat()
        }))
        
        time.sleep(0.5)
        
        ws.send(json.dumps({
            "event": "system_notice",
            "legacy_systems": {
                "archive_location": "/api/internal/archive/2024-11",
                "access": "Restricted to active sessions"
            }
        }))
        
        while True:
            msg = ws.receive(timeout=30)
            if msg is None: break
            ws.send(json.dumps({"echo": msg}))
                
    except Exception:
        pass

@app.route('/.git/config')
def git_leak():
    return """[core]
    repositoryformatversion = 0
    filemode = true
    bare = false
    logallrefupdates = true
[remote "origin"]
    url = git@github.com:shadow-ops/metrics-dashboard.git
    fetch = +refs/heads/*:refs/remotes/origin/*
[branch "main"]
    remote = origin
    merge = refs/heads/main
[user]
    name = DevOps Bot
    email = devops@shadow-analytics.tech
""", 200, {'Content-Type': 'text/plain'}

@app.route('/.git/HEAD')
def git_head():
    return "ref: refs/heads/main\n", 200, {'Content-Type': 'text/plain'}

@app.route('/backup/')
def backup_dir():
    return jsonify({"error": "Forbidden"}), 403

@app.errorhandler(429)
def ratelimit_handler(e):
    return jsonify({"error": "Rate limit exceeded", "retry_after": "60 seconds","YALAH HAK LFLAG GHA MATYEHCH SIRVOR": "NSC{c0ngr4ts_y0u_pl4y3d_y0urs3lf_4nd_g0t_b4nn3d}"}), 429

@app.errorhandler(404)
def not_found(e):
    time.sleep(0.115)
    return jsonify({
        "error": "Not found",
        "path": request.path,
    }), 404

@app.route('/admin/godmode/reset_bans')
def reset_all_bans():
    # SECURITY: Only allow this from localhost (your machine)
    if request.remote_addr != "127.0.0.1":
        return jsonify({"error": "Access Denied"}), 403
        
    # Clear the global variables
    global flagged_ips, security_log
    flagged_ips.clear()
    security_log.clear()
    
    print(f"[ADMIN] All bans cleared by {request.remote_addr}")
    return jsonify({"status": "success", "message": "All bans have been wiped."})
    
if __name__ == '__main__':
    print(">> Shadow Analytics Engine Starting...")
    print(">> Environment: Production")
    print(">> Listening on 0.0.0.0:5000")
    app.run(debug=True, host='127.0.0.1', port=5000)