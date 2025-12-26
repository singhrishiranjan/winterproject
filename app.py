from flask import Flask, render_template, url_for, request, session, redirect, flash
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Confession 
from config import Config


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    return app

app = create_app()


@app.route("/")
def home():
    return render_template("index.html")

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
                return render_template("index.html")
            else:
                new_user = User(username=username, email=email, password_hash=generate_password_hash(password))
                db.session.add(new_user)
                db.session.commit()
                flash("Registration successful. Please log in.", 'success')
                return redirect(url_for('login'))
    else:
        return render_template("register.html")
        
@app.route("/login", methods=['GET', 'POST'])
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
            return render_template("dashboard.html", user=user)
        else:
            flash("Invalid credentials. Please try again.", 'error')
            return render_template("index.html")
    else:
        return render_template("index.html")
    
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
@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", 'success')
    return redirect(url_for('home'))


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True) 