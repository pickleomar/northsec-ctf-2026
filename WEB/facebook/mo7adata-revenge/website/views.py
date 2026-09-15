from flask import Blueprint, render_template, request, flash, jsonify,abort,redirect,url_for
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import json
from .models import Post,User,Comment,Like
from . import db
from datetime import datetime
from markupsafe import escape

views = Blueprint('views', __name__)

@views.route('/')
@views.route('/home')
@login_required
def index():
    posts=Post.query.order_by(Post.date.desc()).all()
    if posts is None:
        flash("There are no posts!")
        return redirect(url_for('views.index'))
    else:
        return render_template("home.html",user=current_user,posts=posts)
    return render_template("home.html",user=current_user)

@views.route('/posting', methods=['GET', 'POST'])
@login_required
def posting():
    if request.method == 'POST':
        post_title = escape(request.form.get('post_title'))
        post_content = escape(request.form.get('text_post'))
        theme = request.form.get('theme')
        id_user = current_user.id

        if not post_title:
            flash("Please Enter Your Posting Title", "error")
        elif not post_content:
            flash("Please Enter Your Posting Content", "error")
        else:
            #elif post_image:
            #secure_filename = secure_filename(post_image.filename)
            #image_data = post_image.read()
            new_post = Post(title=post_title, content=post_content,theme=theme , date=datetime.utcnow(),user_id=id_user)#, post_image=image_data)
            db.session.add(new_post)
            db.session.commit()
            flash("Your Post has been Posted", "success")
            return redirect(url_for('views.index'))
    return render_template("post_form.html", user=current_user)

@views.route('/delete-post/<int:post_id>', methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author.id == current_user.id:
        db.session.delete(post)
        db.session.commit()
        flash('Post has been deleted!', 'success')
    else:
        flash('You do not have permission to delete this post.', 'danger')
    return redirect(url_for('views.index'))

@views.route('/edit-post/<int:post_id>', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author.id == current_user.id:
        if request.method == 'POST':
            post_title = request.form.get('title')
            
            post_content = request.form.get('content')
            theme = request.form.get('theme')
            id_user = current_user.id
            if not post_title:
                flash("Please Enter Your Posting Title", "error")
                return redirect(url_for('views.index'))
            if not post_content:
                flash("Please Enter Your Posting Content", "error")
                return redirect(url_for('views.index'))
            else:
                post.title = post_title
                post.content = post_content
                post.theme = theme
                db.session.commit()
                flash("Your Post has been Edited!", "success")
                return redirect(url_for('views.index'))
        return render_template('edit_post.html', post=post, user=current_user)
    else:
        flash("you dont have permession to edit this post")
        return redirect(url_for('views.index'))


@views.route("/add-comment/<int:post_id>", methods=['POST'])
@login_required
def commenting(post_id):
    if request.method == 'POST':
        comment_content = request.form.get('comment_content')
        post = Post.query.get_or_404(post_id)
        if not comment_content:
            flash("Please Enter Your Commenting Content", "error")
            return redirect(url_for('views.index'))
        else:
            comment = Comment(content=comment_content, user_id=current_user.id, post_id=post.id)
            db.session.add(comment)
            db.session.commit()
            flash("Your Comment has been Posted!", "success")
            return redirect(url_for('views.index'))


@views.route('/delete_comment/<int:comment_id>', methods=['POST'])
@login_required
def delete_comment(comment_id):
    comment=Comment.query.get_or_404(comment_id)
    if comment.commentator.id == current_user.id:
        db.session.delete(comment)
        db.session.commit()
        flash('Comment has been deleted!', 'success')
    else:
        flash('You do not have permission to delete this post.', 'danger')
    return redirect(url_for('views.index'))

@views.route("/like_post/<int:post_id>",methods=['POST'])
@login_required
def like_post(post_id):
    post=Post.query.get_or_404(post_id)
    like=Like.query.filter_by(user_id=current_user.id, post_id=post_id).first()
    if not post:
        abort(404, "Post does not exist")
    else:
        if like:
            db.session.delete(like)
            db.session.commit()
            flash("You Unliked The Post", "success")
        else:
            liked=Like(user_id=current_user.id,post_id=post_id)
            db.session.add(liked)
            db.session.commit()
            flash("Your Like has been Liked!", "success")
    return redirect(url_for('views.index'))
