import os
import pickle
import base64
import logging
from flask import Flask, request, render_template_string, Response
from datetime import datetime, timedelta
import hashlib

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-key-unsafe-for-production'

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SESSION_COOKIE_NAME = 'enterprise_session'
SESSION_TIMEOUT = 3600


class UserProfile:
    def __init__(self, user_id, username, role, metadata=None):
        self.user_id = user_id
        self.username = username
        self.role = role
        self.metadata = metadata or {}
        self.created_at = datetime.now()
        self.last_accessed = datetime.now()
    
    def update_access(self):
        self.last_accessed = datetime.now()


def serialize_session(user_profile):
    try:
        pickled = pickle.dumps(user_profile, protocol=pickle.HIGHEST_PROTOCOL)
        encoded = base64.b64encode(pickled).decode('utf-8')
        return encoded
    except Exception as e:
        logger.error(f"Serialization error: {str(e)}")
        return None


def deserialize_session(encoded_session):
    try:
        decoded = base64.b64decode(encoded_session.encode('utf-8'))
        user_profile = pickle.loads(decoded)
        return user_profile
    except Exception as e:
        logger.error(f"Deserialization error: {type(e).__name__}: {str(e)}")
        return None


def get_user_session():
    session_cookie = request.cookies.get(SESSION_COOKIE_NAME)
    
    if not session_cookie:
        return None
    
    user_profile = deserialize_session(session_cookie)
    return user_profile


@app.before_request
def log_request():
    logger.info(f"{request.method} {request.path} from {request.remote_addr}")


@app.route('/')
def index():
    user_profile = get_user_session()
    
    if not user_profile:
        new_user = UserProfile(
            user_id=hashlib.md5(request.remote_addr.encode()).hexdigest()[:8],
            username=f"user_{datetime.now().strftime('%s')}",
            role='visitor',
            metadata={'ip': request.remote_addr, 'first_visit': True}
        )
        session_data = serialize_session(new_user)
        
        html = '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Enterprise Portal</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
                .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 5px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                h1 { color: #333; }
                .info { background: #e8f4f8; padding: 15px; border-left: 4px solid #0078d4; margin: 20px 0; }
                .session-id { font-family: monospace; background: #f0f0f0; padding: 10px; border-radius: 3px; word-break: break-all; margin: 10px 0; font-size: 11px; }
                .status { color: #666; font-size: 14px; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Enterprise Portal v2.3.1</h1>
                <p>Welcome to our enterprise portal. Your session has been initialized.</p>
                <div class="info">
                    <strong>Session Information:</strong>
                    <div class="session-id">''' + session_data + '''</div>
                    <p class="status">Session active. Refresh to continue.</p>
                </div>
                <p>Please refresh the page to access your profile.</p>
            </div>
        </body>
        </html>
        '''
        
        response = Response(html, content_type='text/html')
        response.set_cookie(SESSION_COOKIE_NAME, session_data, max_age=SESSION_TIMEOUT, httponly=True)
        return response
    
    user_profile.update_access()
    
    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Enterprise Portal</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
            .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 5px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1 { color: #333; }
            .profile { background: #f0f8ff; padding: 20px; border-radius: 5px; margin: 20px 0; }
            .field { margin: 10px 0; }
            label { font-weight: bold; color: #0078d4; }
            .session-id { font-family: monospace; background: #f0f0f0; padding: 10px; border-radius: 3px; word-break: break-all; margin: 10px 0; font-size: 10px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Enterprise Portal v2.3.1</h1>
            <h2>User Profile</h2>
            <div class="profile">
                <div class="field"><label>User ID:</label> ''' + user_profile.user_id + '''</div>
                <div class="field"><label>Username:</label> ''' + user_profile.username + '''</div>
                <div class="field"><label>Role:</label> ''' + user_profile.role + '''</div>
                <div class="field"><label>Last Accessed:</label> ''' + str(user_profile.last_accessed) + '''</div>
            </div>
            <p style="color: #999; font-size: 12px; margin-top: 30px;">Session ID logged. Enterprise tracking enabled.</p>
        </div>
    </body>
    </html>
    '''
    
    response = Response(html, content_type='text/html')
    response.set_cookie(SESSION_COOKIE_NAME, serialize_session(user_profile), max_age=SESSION_TIMEOUT, httponly=True)
    return response


@app.route('/api/profile', methods=['GET'])
def api_profile():
    user_profile = get_user_session()
    
    if not user_profile:
        return {'error': 'Invalid session'}, 401
    
    return {
        'user_id': user_profile.user_id,
        'username': user_profile.username,
        'role': user_profile.role,
        'metadata': user_profile.metadata
    }


@app.route('/api/health', methods=['GET'])
def health():
    return {'status': 'ok', 'timestamp': datetime.now().isoformat()}


@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {str(error)}")
    return {'error': 'Internal server error'}, 500


@app.errorhandler(404)
def not_found(error):
    return {'error': 'Not found'}, 404


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
