from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from os import path
from flask_cors import CORS


db = SQLAlchemy()
DB_NAME = "database.db"
UPLOAD_FOLDER = 'website/static/uploads'

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'AHSANPROJECTFL3ALAM'
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    app.config['DEBUG'] = True
    app.config['USE_RELOADER'] = False
    app.config["SERVER_NAME"] = "0.0.0.0:5000"  # Bind to all interfaces
    app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024
    app.debug = True
    CORS(app)
    db.init_app(app)

    from .views import views
    from .auth import auth
    from .users_profile import users_profile

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')
    app.register_blueprint(users_profile, url_prefix='/')

    from .models import User, Post, Like

    with app.app_context():
        db.create_all()

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)



    

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))

    return app

def create_database(app):
    if not path.exists('website/' + DB_NAME):
        db.create_all(app=app)
        print('Created Database!')