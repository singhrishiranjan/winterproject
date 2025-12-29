from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.sql import func


db = SQLAlchemy()


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    name = db.Column(db.String(100), nullable=True)
    bio = db.Column(db.Text, nullable=True)
    pfp = db.Column(db.String(255), nullable=True) #profile picture filename


    received_confessions = db.relationship('Confession', back_populates='receiver', lazy=True, foreign_keys='Confession.receiver_id')
    sent_confessions = db.relationship('Confession', back_populates='sender', lazy=True, foreign_keys='Confession.sender_id')  

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'
    
class Confession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=func.now(),  nullable=False)

    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

    receiver = db.relationship('User', foreign_keys=[receiver_id], back_populates='received_confessions')
    sender = db.relationship('User', foreign_keys=[sender_id], back_populates='sent_confessions')
    def __repr__(self):
        return f'<Confession {self.id}>'