import os
import re
import string
import random

from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from flask_msearch import Search
from flask import Flask, flash, request, render_template, redirect, session, url_for, send_from_directory
from flask_session import Session
from tempfile import mkdtemp
from functools import wraps
from flask_mail import Mail, Message
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

STATUS = 'production'

if STATUS == 'development':
    app.config['DEBUG'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:3217123@localhost/dejahoe'
else:
    app.debug = False
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://fyvfhpiwnotsno:09910d2047f4a2c9649580fd6907b1e217176c25a91e6fc6b9218243a4d972ca@ec2-54-158-247-210.compute-1.amazonaws.com:5432/d771e7kahc8ss7'

# msearch configuration
# https://github.com/honmaple/flask-msearch
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['MSEARCH_INDEX_NAME'] = 'msearch'
app.config['MSEARCH_PRIMARY_KEY'] = 'id'
app.config['MSEARCH_ENABLE'] = True



db = SQLAlchemy(app)
search = Search()
search.init_app(app)

class users(db.Model):
    __tablename__ = 'users'
    # id,username,email,hash,timestamp,status,role
    uid = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    pwdhash = db.Column(db.String, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"), nullable=False)
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
    date = db.Column(db.Date, default=datetime.now(timezone.utc).strftime("%Y-%m-%d"), nullable=False)
    time = db.Column(db.Time, default=datetime.now(timezone.utc).strftime("%H:%M:%S"), nullable=False)

    def __init__(self, vid_id, username, comment):
        self.comment = comment
        self.vid_id = vid_id
        self.username = username

class uploads(db.Model):
    __tablename__ = 'uploads'
    __searchable__ = ['title', 'describtion', 'category']
    # vid_id,uploader,date,title,describtion,category,video,image
    vid = db.Column(db.Integer, primary_key=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.uid'), nullable=False)
    date = db.Column(db.Date, default=datetime.now(timezone.utc).strftime("%Y-%m-%d"), nullable=False)
    title = db.Column(db.String, nullable=False)
    describtion = db.Column(db.Text, nullable=False)
    category = db.Column(db.String, nullable=False)
    video = db.Column(db.String, nullable=False)
    image = db.Column(db.String, nullable=False)
    video_id = db.relationship('comments', backref='vdetails', lazy=True)

    def __init__(self, user_id, title, describtion, category, video, image):
        self.user_id = user_id
        self.title = title
        self.describtion = describtion
        self.category = category
        self.video = video
        self.image = image


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure mail
# https://accounts.google.com/b/0/DisplayUnlockCaptcha
app.config["MAIL_DEFAULT_SENDER"] = os.environ["MAIL_DEFAULT_SENDER"]
app.config["MAIL_PASSWORD"] = os.environ["MAIL_PASSWORD"]
app.config["MAIL_PORT"] = 587
app.config["MAIL_SERVER"] = 'smtp.gmail.com'
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USE_SSL"] = False
app.config["MAIL_USERNAME"] = os.environ["MAIL_USERNAME"]
mail = Mail(app)


def login_required(f):

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


@app.route("/")
# @app.route("/home")
@login_required
def index():
    # files = os.listdir(app.config["IMAGE_PATH"])
    # files = db.execute("SELECT * FROM uploads")
    page = request.args.get('page', 1, type=int)
    files = uploads.query.order_by(uploads.date.desc()).paginate(page=page, per_page=16)
    return render_template("index.html", files=files)

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        # Ensure username is submitted
        if not username:
            return render_template("error.html", code=400, t1="Username reqired")

        # Ensure password is submitted
        if not password or not confirmation:
            return render_template("error.html", code=400, t1="Missing password")

        # Ensure email is submitted
        if not email:
            return render_template("error.html", code=400, t1="Missing email")

        # Ensure passwords match
        if password != confirmation:
            return render_template("error.html", code=400, t1="Passwords don't match")

        # Ensure username and email are unique
        existu = users.query.filter_by(username=username).count()
        existe = users.query.filter_by(email=email).count()
        if existu != 0 or existe != 0:
            return render_template("error.html", code=400, t1="Username/email already exists")

        # Insert the user in the db
        newuser = users(username, email, password)
        db.session.add(newuser)
        db.session.commit()

        # Send email
        # message = Message("You are registered!", recipients=[email])
        # mail.send(message)

        # Redirect user to login page
        return redirect("/login")

    else:
        return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():

    # Forget any user_id
    session.clear()

    # User reached route via post
    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")

        # Query database for email

        auth = users.query.filter_by(username=username).first()

        if auth == None or not auth.check_password(password):
            return render_template("error.html", t1="Invaild username and/or password")

        # Remember which user has logged in
        session["user_id"] = auth.uid

        # Redirect user to home page
        return redirect("/")

    else:
        return render_template("login.html")


@app.route("/logout")
def logout():

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

@app.route("/profile")
@login_required
def profile():

    # Query the user info
    info = users.query.filter_by(uid=session["user_id"])
    return render_template("profile.html", info=info)

@app.route("/change_password", methods=["POST", "GET"])
@login_required
def reset():

    if request.method == "POST":

        old_password = request.form.get("old_password")
        new_password = request.form.get("new_password")
        confirmation = request.form.get("confirmation")

        # Query database for user
        auth = users.query.filter_by(uid=session["user_id"]).first()

        # Check if passwords match
        if not auth.check_password(old_password):
            return render_template("error.html", code=400, t1="Incorrect old password")

        # Check if passwords match
        elif new_password != confirmation:
            return render_template("error.html", code=400, t1="Unmatching new passwords")

        # Check if new password is the same as new
        elif auth.check_password(new_password):
            return render_template("error.html", code=400, t1="New password cant be same as old")

        else:

            # Save the new password to db 
            auth.set_password(new_password)
            db.session.commit()
            return redirect("/login")

    else:
        return render_template("change_password.html")

@app.route("/search", methods=["POST", "GET"])
@login_required
def search():

    if request.method == "POST":

        keyword = request.form.get("search-field")
        # result = uploads.query.filter(uploads.title.like('%'+ tag +'%')).all()

        results = uploads.query.msearch(
            keyword, fields=['title', 'describtion', 'category'],limit=16).all()

        return render_template("search.html", files=results, srh=keyword)


@app.route("/video/<filename>", methods=["POST", "GET"])
@login_required
def video(filename):

    if request.method == "POST":

        comment = request.form.get("comment")

        # Query the data
        vid_id = uploads.query.filter_by(video=filename).first()
        user_id = users.query.filter_by(uid=session["user_id"]).first()

        # Insert and commit the data
        newcomment = comments(vid_id.vid, user_id.username, comment)
        db.session.add(newcomment)
        db.session.commit()

        return redirect(request.url)
    else:

        data = uploads.query.filter_by(video=filename).first()
        related = uploads.query.filter_by(category=data.category).limit(12)
        replays = comments.query.filter_by(vid_id=data.vid)

        return render_template("video.html", vidx=filename, data=data, comments=replays, files=related)


@app.route("/image/<filename>")
@login_required
def image(filename):
    return send_from_directory(app.config["IMAGE_PATH"], filename)


# Configure the location that videos will live in
app.config["VIDEO_PATH"] = "C:/Users/I FIX/Desktop/dejahoe/static/videos"

# Configure the location that images will live in
app.config["IMAGE_PATH"] = "C:/Users/I FIX/Desktop/dejahoe/static/images"

# List of img accepted extensions
app.config["ALLOWED_VIDEO_EXTENSIONS"] = ["MOV", "MP4", "OGG", "WEBM"]

# List of vids accepted extensions
app.config["ALLOWED_IMG_EXTENSIONS"] = ["PNG", "JPG", "JPEG"]

# Upload genres
GENRES = [
        "Technology", "Art", "Animals", "Cars", "Music", "Lifestyle", "Gaming", "Funny", "Meme", "Other"
    ]

def check_vid(filename):

    if not "." in filename:
        return False

    extension = filename.rsplit(".", 1)[1]

    if extension.upper() in app.config["ALLOWED_VIDEO_EXTENSIONS"]:
        return extension
    else:
        return False

def check_img(filename):

    if not "." in filename:
        return False

    extension = filename.rsplit(".", 1)[1]

    if extension.upper() in app.config["ALLOWED_IMG_EXTENSIONS"]:
        return extension
    else:
        return False

# Random number generator for file names
def id_generator(size=10, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

@app.route("/upload", methods=["POST", "GET"])
@login_required
def upload():

    if request.method == "POST":

        # Ensure title is submitted
        if not request.form.get("title"):
            return render_template("error.html", code=400, t1="Missing title")

        # Ensure description is submitted
        if not request.form.get("describtion"):
            return render_template("error.html", code=400, t1="Missing description")


        if request.files:

            video = request.files["file"]
            img = request.files["thumbnail"]

            # Ensure the video has a name
            if video.filename == "":
                return render_template("error.css", code=400, t1="Video must have a name")

            # Ensure the image has a name
            if img.filename == "":
                return render_template("error.css", code=400, t1="Image must have a name")

            the_id = id_generator()
            # Check the video extension
            if not check_vid(video.filename):
                return render_template("error.css", code=400, t1="Video extension not allowed")

            else:
                videoname = the_id + "." + check_vid(video.filename)

                video.save(os.path.join(app.config["VIDEO_PATH"], videoname))

            # Check the image extension
            if not check_img(img.filename):
                return render_template("error.css", code=400, t1="Image extension not allowed")

            else:
                imagename = the_id + "." + check_img(img.filename)

                img.save(os.path.join(app.config["IMAGE_PATH"], imagename))

            # Save uploaded to db
            entry = uploads(session["user_id"], request.form.get("title"),
                            request.form.get("describtion"), 
                            request.form.get("category").lower(), videoname, imagename)
            db.session.add(entry)
            db.session.commit()
            flash('Uploaded')
            # session.pop('_flashes', None)
            return redirect(request.url)

    else:
        return render_template("upload.html", genres=GENRES)


@app.route("/payment")
@login_required
def payment():
    return "TODO"

# Error 404 page
@app.errorhandler(404)
def page_not_found(e):
    return render_template("error.html", code=404, t1="Page not found", t2="This may not mean anything."), 404

if __name__ == '__main__':
    app.run()
