from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from .models import User
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from . import db
from flask_login import login_user, login_required, logout_user, current_user
import re
import os
import hashlib
from flask import send_from_directory, request, abort

auth = Blueprint('auth', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def is_valid_password(password):
    min_length = 8
    uppercase_pattern = re.compile(r'[A-Z]')
    lowercase_pattern = re.compile(r'[a-z]')
    digit_pattern = re.compile(r'\d')
    special_char_pattern = re.compile(r'[!@#$%^&*()]')

    if len(password) < min_length:
        return False, "Password must be at least 8 characters long."
    if not uppercase_pattern.search(password):
        return False, "Password must contain at least one uppercase letter."
    if not lowercase_pattern.search(password):
        return False, "Password must contain at least one lowercase letter."
    if not digit_pattern.search(password):
        return False, "Password must contain at least one digit."
    if not special_char_pattern.search(password):
        return False, "Password must contain at least one special character (e.g., !@#$%^&*())."

    return True, "Password is valid."

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user:
            if check_password_hash(user.password, password):
                flash("Your account successfully logged in!", "success")
                login_user(user, remember=True)
                return redirect(url_for('views.index'))
            else:
                flash("Login Failed", "error")
        else:
            flash("Login Failed", "error")
    return render_template("login.html", user=current_user)

@auth.route('/get_profile_pic')
def file():
	filename = request.args.get('pic')
	try:
		with open(filename, 'r') as f:
			return f.read()
	except:
		return 'error'

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')
        description = request.form.get('description')
        url=request.form.get('url')
        file = request.files['pic']

        if file.filename == '':
            flash('No selected file', category='error')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            # Get the original filename
            filename = secure_filename(file.filename)

            # Generate SHA1 hash of the email
            email_hash = hashlib.sha1(email.encode()).hexdigest()

            # Get the file extension from the original filename
            file_extension = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
            
            # Create a new filename using the SHA1 hash and the original file extension
            new_filename = f"{email_hash}.{file_extension}" if file_extension else email_hash

            upload_folder = current_app.config['UPLOAD_FOLDER']

            # Ensure the upload directory exists
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)

            # Save the file with the new filename
            file_path = os.path.join(upload_folder, new_filename)
            file.save(file_path)
        else:
            flash('Invalid file type', category='error')
            return redirect(request.url)

        if len(name) < 2:
            flash('First name must be greater than 1 character.', category='error')
        elif password1 != password2:
            flash('Passwords don\'t match.', category='error')
        else:
            valid, message = is_valid_password(password1)
            if not valid:
                flash(message, category='error')
            else:
                existing_user = User.query.filter_by(email=email).first()
                if existing_user:
                    flash('Email already exists.', category='error')
                else:
                    new_user = User(
                        email=email,
                        name=name,
                        description=description,
                        password=generate_password_hash(password1, method="pbkdf2:sha1"),
                        pic=new_filename,
                        url=url
                    )
                    db.session.add(new_user)
                    db.session.commit()
                    flash('Account created successfully!', category='success')
                    return redirect(url_for('views.index'))
    return render_template("register.html", user=current_user)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))