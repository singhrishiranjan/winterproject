from flask import Flask, render_template, url_for, request, session, redirect, flash
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from models import db, User, Confession 
from config import Config
from datetime import datetime
import os

PFP_UPLOAD_FOLDER = 'static/uploads/'
PFP_ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.config['PFP_UPLOAD_FOLDER'] = PFP_UPLOAD_FOLDER
    app.config['MAX_CONTENT_LENGTH'] = 1 * 1024 * 1024 
    db.init_app(app)
    return app

app = create_app()


def save_uploaded_file(file, allowed_extensions, upload_folder):
    if not file or file.filename == '':
        return None
    
    ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
    if ext not in allowed_extensions:
        return None
    
    original_name = secure_filename(file.filename)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_filename = f"{timestamp}_{original_name}"

    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)

    file_path = os.path.join(upload_folder, unique_filename)
    file.save(file_path)

    return unique_filename

def delete_old_file(filename, upload_folder):
    if filename:
        file_path = os.path.join(upload_folder, filename)
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            print(f"Error deleting file {file_path}: {e}")

@app.errorhandler(413)
def request_entity_too_large(error):
    flash("File is too large! Maximum size allowed is 2MB.", 'error')
    return redirect(url_for('home'))

@app.route("/", methods=['GET'])
def home():
    if session.get('user_id'):
        user = User.query.filter_by(id=session.get('user_id')).first()
        return redirect(url_for('dashboard', username=user.username))
    return render_template("index.html")

@app.route("/<username>/dashboard", methods=['GET'])
def dashboard(username):
    user = User.query.filter_by(username=username).first()
    confessions = Confession.query.filter_by(receiver_id=user.id).all()
    if not user or user.id != session.get('user_id'):
        flash("Unauthorized access.", 'error')
        return redirect(url_for('home'))
    return render_template("dashboard.html", user=user, confessions=confessions)
@app.route("/register", methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        if user:
            flash("User exists already with this email. Either use another email id or log in.", 'error')
            return redirect(url_for('register'))
        else:
            existing_username = User.query.filter_by(username=username).first()
            if existing_username:
                flash("Username already taken. Please choose another.", 'error')
                return redirect(url_for('register'))
            else:
                new_user = User(username=username, email=email, password_hash=generate_password_hash(password))
                db.session.add(new_user)
                db.session.commit()
                flash("Registration successful. Please log in.", 'success')
                return redirect(url_for('login'))
    else:
        return render_template("register.html")
        
@app.route("/login", methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        if not username and not email:
            flash("Please enter either username or email.", 'error')
            return render_template("index.html")
        if email:
            user = User.query.filter_by(email=email).first()
        if username:
            user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            return redirect(url_for('dashboard', username=user.username))
        else:
            flash("Invalid credentials. Please try again.", 'error')
            return redirect(url_for('login'))
    return redirect(url_for('home'))
    
@app.route("/<receiver>/confess", methods=['GET', 'POST'])
def confess(receiver):
    receiver = User.query.filter_by(username=receiver).first()
    sender = User.query.filter_by(id=session.get('user_id')).first()
    if request.method == 'POST':
        confession = request.form.get('confession')
        anonymous = request.form.get('anonymous') == 'on'
        if anonymous or not session.get('user_id'):
            new_confession = Confession(receiver_id=receiver.id, content=confession)
            db.session.add(new_confession)
            db.session.commit()
            flash("Your confession has been sent anonymously!", 'success')
            return render_template('confess.html', receiver=receiver.username, sender=sender.username if anonymous else None)
        else:
            new_confession = Confession(receiver_id=receiver.id, sender_id=sender.id, content=confession)
            db.session.add(new_confession)
            db.session.commit()
            flash("Your confession has been sent!", 'success')
            return render_template('confess.html', receiver=receiver.username, sender=sender.username)
    else:
        return render_template("confess.html", receiver=receiver.username, sender=sender.username if sender else None)

@app.route("/<username>/profile", methods=['GET'])
def profile(username):
    user = User.query.filter_by(username=username).first()
    is_visitor = session.get('user_id') != user.id if user else True
    if not user:
        flash("User not found.", 'error')
        return redirect(url_for('home'))
    if request.method == 'GET':
        return render_template('profile.html', is_visitor = is_visitor, username=username, name=user.name if user.name else None, bio=user.bio if user.bio else None, pfp=user.pfp if user.pfp else None)
    return redirect(url_for('home'))


@app.route("/<username>/profile/update", methods=['GET', 'POST'])
def update_profile(username):
    user = User.query.filter_by(username=username).first()
    
    if not user or user.id != session.get('user_id'):
        flash("Unauthorized access.", 'error')
        return redirect(url_for('home'))
    if request.method == 'GET':
        return render_template('update_profile.html', username=username, name=user.name if user.name else None, bio=user.bio if user.bio else None, pfp=user.pfp if user.pfp else None)
    changes_made = False

    new_name = request.form.get('name')
    new_bio = request.form.get('bio')

    if new_name and new_name != user.name:
        user.name = new_name
        changes_made = True
    if new_bio and new_bio != user.bio:
        user.bio = new_bio
        changes_made = True

    if 'pfp' in request.files:
        saved_name = save_uploaded_file(
            request.files['pfp'], 
            PFP_ALLOWED_EXTENSIONS,
            app.config['PFP_UPLOAD_FOLDER']
            
        )
        if saved_name:
            delete_old_file(user.pfp, app.config['PFP_UPLOAD_FOLDER'])
            user.pfp = saved_name
            changes_made = True

    if changes_made:
        db.session.commit()
        flash("Profile updated successfully!")
    else:
        flash("No changes were made.")
    return redirect(url_for('profile', username=user.username))
        

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", 'success')
    return redirect(url_for('home'))


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True) 