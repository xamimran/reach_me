from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
from werkzeug.security import check_password_hash, generate_password_hash

db = SQLAlchemy()

class users(db.Model):
    __tablename__ = 'users'
    # id,username,email,hash,timestamp,status,role
    uid = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    pwdhash = db.Column(db.String, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.now(timezone.utc), nullable=False)
    status = db.Column(db.String, default='notverified', nullable=False)
    role = db.Column(db.String, default='member', nullable=False)
    user_id = db.relationship('uploads', backref='user', lazy=True)

    def __init__(self, username, email, password):
        self.username = username
        self.email = email
        self.set_password(password)

    def set_password(self, password):
        self.pwdhash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.pwdhash, password)


class comments(db.Model):
    __tablename__ = 'comments'
    # vid_id,username,comment,date,time 
    cid = db.Column(db.Integer, primary_key=True, nullable=False)
    vid_id = db.Column(db.Integer, db.ForeignKey('uploads.vid'), nullable=False)
    username = db.Column(db.String, nullable=False)
    comment = db.Column(db.Text, nullable=False)
    date = db.Column(db.Date, default=datetime.now(timezone.utc), nullable=False)
    time = db.Column(db.Time, default=datetime.now(timezone.utc), nullable=False)

    def __init__(self, vid_id, username, comment):
        self.comment = comment
        self.vid_id = vid_id
        self.username = username

class uploads(db.Model):
    __tablename__ = 'uploads'
    __searchable__ = ['title', 'description', 'category']
    # vid_id,uploader,date,title,description,category,video,image
    vid = db.Column(db.Integer, primary_key=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.uid'), nullable=False)
    date = db.Column(db.Date, default=datetime.now(timezone.utc), nullable=False)
    title = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.Text, nullable=False)
    video = db.Column(db.String, nullable=False)
    video_link = db.Column(db.String)
    image = db.Column(db.String, nullable=False)
    image_link = db.Column(db.String)
    method = db.Column(db.String, nullable=False)
    video_id = db.relationship('comments', backref='vdetails', lazy=True)

    def __init__(self, user_id, title, description, category, video, video_link, image, image_link, method):
        self.user_id = user_id
        self.title = title
        self.description = description
        self.category = category
        self.video = video
        self.video_link = video_link
        self.image = image
        self.image_link = image_link
        self.method = method
