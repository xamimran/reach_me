import os
import re
import string
import random

from cs50 import SQL
from flask import Flask, flash, request, render_template, redirect, session, url_for, send_from_directory
from flask_session import Session
from tempfile import mkdtemp
from functools import wraps
from flask_mail import Mail, Message
from werkzeug.security import check_password_hash, generate_password_hash
# from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure mail
# https://accounts.google.com/b/0/DisplayUnlockCaptcha
app.config["MAIL_DEFAULT_SENDER"] = 'akajamesadam@gmail.com'
app.config["MAIL_PASSWORD"] = 'Youngmoneybunny69'
app.config["MAIL_PORT"] = 587
app.config["MAIL_SERVER"] = 'smtp.gmail.com'
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USE_SSL"] = False
app.config["MAIL_USERNAME"] = 'akajamesadam'
mail = Mail(app)

db = SQL("sqlite:///l2.db")

def login_required(f):

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


@app.route("/")
@login_required
def index():
    # files = os.listdir(app.config["IMAGE_PATH"])
    files = db.execute("SELECT * FROM uploads")
    return render_template("index.html", files=files)
    # return redirect("/video")

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
        # Ensure username is unique
        row = db.execute("SELECT * FROM users WHERE username = ? or email = ?", username, email)
        if len(row) != 0:
            return render_template("error.html", code=400, t1="Username/email already exists")

        # Insert the user in the db
        db.execute("INSERT INTO users (username, email, hash, timestamp) VALUES(?,?,?,date('now'))", username, email, generate_password_hash(password))

        # Send email
        message = Message("You are registered!", recipients=[email])
        mail.send(message)

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
        rows = db.execute("SELECT * FROM users WHERE username = ?", username)

        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], password):
            return render_template("error.html", t1="Invaild username and/or password")

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

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

    info = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])
    return render_template("profile.html", info=info)

@app.route("/change_password", methods=["POST", "GET"])
@login_required
def reset():

    if request.method == "POST":

        old_password = request.form.get("old_password")
        new_password = request.form.get("new_password")
        confirmation = request.form.get("confirmation")

        # Query database for user
        row = db.execute("SELECT hash FROM users where id = ?", session["user_id"])
        # Check if passwords match
        if not check_password_hash(row[0]["hash"], old_password):
            return render_template("error.html", code=400, t1="Incorrect old password")
        elif new_password != confirmation:
            return render_template("error.html", code=400, t1="Unmatching new passwords")
        elif check_password_hash(row[0]["hash"], new_password):
            return render_template("error.html", code=400, t1="New password cant be same as old")
        else:
            db.execute("UPDATE users SET hash = ? WHERE id = ?", generate_password_hash(new_password), session["user_id"])
            return redirect("/login")

    else:
        return render_template("change_password.html")


@app.route("/video/<filename>", methods=["POST", "GET"])
@login_required
def video(filename):

    if request.method == "POST":

        comment = request.form.get("comment")
        video = db.execute("SELECT vid_id FROM uploads WHERE video LIKE ?", filename)
        username = db.execute("SELECT username FROM users WHERE id = ?", session["user_id"])

        # db.execute("INSERT INTO comments (vid_id,username,comment,date,time) VALUES(1,'q',?,date('now'),time('now'))",
        #  comment)
        return redirect(request.url)
    else:

        data = db.execute("SELECT * FROM uploads WHERE video = ?", filename)
        related = db.execute("SELECT * FROM uploads WHERE category LIKE ?", data[0]["category"])
        replays = db.execute("SELECT * FROM comments WHERE vid_id = 2")
        return render_template("video.html", vidx=filename, data=data, comments=replays, files=related)


@app.route("/image/<filename>")
@login_required
def image(filename):
    return send_from_directory(app.config["IMAGE_PATH"], filename)

# Configure the location that videos will live in
app.config["VIDEO_PATH"] = "/home/ubuntu/x2/static/videos"

# Configure the location that images will live in
app.config["IMAGE_PATH"] = "/home/ubuntu/x2/static/images"

# List of img accepted extensions
app.config["ALLOWED_VIDEO_EXTENSIONS"] = ["MOV", "MP4", "OGG", "WEBM"]

# List of vids accepted extensions
app.config["ALLOWED_IMG_EXTENSIONS"] = ["PNG", "JPG", "JPEG"]

# Upload genres
GENRES = [
        "Amateur", "Anal", "Babe", "BBC", "Big ass", "Big dick", "Big tits", "Blonde", "Blowjob",
        "Brunette", "Creampie", "Cumshot", "Handjob", "Hardcore", "Lesbian", "Masturbation",
        "POV", "Public", "Rough", "Threesome"
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
            if img.filename =="":
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

            db.execute("INSERT INTO uploads (uploader,date,title,describtion,category,video,image) VALUES (?,date('now'),?,?,?,?,?)",
            session["user_id"], request.form.get("title"), request.form.get("describtion"), request.form.get("category"),
            videoname, imagename)

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
