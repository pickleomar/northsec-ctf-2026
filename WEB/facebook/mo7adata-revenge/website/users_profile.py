from flask import Blueprint, render_template, request, flash, jsonify,abort,redirect,url_for,render_template_string  
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import json
from .models import Post
from . import db
from .models import User
from datetime import datetime
from flask import send_from_directory, request, abort


users_profile = Blueprint('users_profile', __name__)

@users_profile.route(f'/users/<int:id>')
@login_required
def index(id):

    user=User.query.filter_by(id=id).first()
    if not user:
        flash("User not found")
        return redirect(url_for('home.index'))
    posts=user.posts

    return  render_template("profile.html",user=current_user,posts=posts,user_profile=user)
