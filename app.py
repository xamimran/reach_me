

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_msearch import Search
from flask import Flask, render_template, redirect, url_for, send_from_directory
from flask_session import Session
from tempfile import mkdtemp
from flask_mail import Mail, Message
from models import db, users, uploads, comments
from auth.auth import auth_bp
from videos.videos import videos_bp

app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

STATUS = 'development'

if STATUS == 'development':
    app.config['DEBUG'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
else:
    app.debug = False
    app.config['SQLALCHEMY_DATABASE_URI'] = ''

# msearch configuration
# https://github.com/honmaple/flask-msearch
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['MSEARCH_INDEX_NAME'] = 'msearch'
app.config['MSEARCH_PRIMARY_KEY'] = 'id'
app.config['MSEARCH_ENABLE'] = True


db.init_app(app)
migrate = Migrate(app, db)
search = Search()
search.init_app(app)

# register blueprint
app.register_blueprint(auth_bp, url_prefix= '/')
app.register_blueprint(videos_bp, url_prefix= '/videos')


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure mail
# https://accounts.google.com/b/0/DisplayUnlockCaptcha
# app.config["MAIL_DEFAULT_SENDER"] = os.environ["MAIL_DEFAULT_SENDER"]
# app.config["MAIL_PASSWORD"] = os.environ["MAIL_PASSWORD"]
# app.config["MAIL_PORT"] = 587
# app.config["MAIL_SERVER"] = 'smtp.gmail.com'
# app.config["MAIL_USE_TLS"] = True
# app.config["MAIL_USE_SSL"] = False
# app.config["MAIL_USERNAME"] = os.environ["MAIL_USERNAME"]
# mail = Mail(app)






@app.route("/search", methods=["POST", "GET"])

def search():

    if request.method == "POST":

        keyword = request.form.get("search-field")
        # result = uploads.query.filter(uploads.title.like('%'+ tag +'%')).all()

        results = uploads.query.msearch(
            keyword, fields=['title', 'description', 'category'],limit=16).all()

        return render_template("search.html", files=results, srh=keyword)


@app.route("/video/<filename>", methods=["POST", "GET"])

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
        related = uploads.query.filter(uploads.vid != data.vid, uploads.category==data.category).limit(12)
        replays = comments.query.filter_by(vid_id=data.vid)

        return render_template("video.html", vidx=filename, data=data, comments=replays, files=related)


@app.route("/image/<filename>")

def image(filename):
    return send_from_directory(app.config["IMAGE_PATH"], filename)


@app.route("/link", methods=["POST", "GET"])
def link():

    if request.method == "POST":

        # Ensure title is submitted
        if not request.form.get("title"):
            return render_template("error.html", code=400, t1="Missing title")

        # Ensure description is submitted
        if not request.form.get("description"):
            return render_template("error.html", code=400, t1="Missing description")

        # Ensure the video has a link
        if not request.form.get("videoLink"):
            return render_template("error.html", code=400, t1="Video must have a link")

        if not request.form.get("imageLink"):
            return render_template("error.html", code=400, t1="Image must have a link")

        if request.form.get("category") not in GENRES:
            return render_template("error.html", code=400, t1="Invalid/missing category")

        the_id = id_generator()

        # Save uploaded to db
        entry = uploads(session["user_id"], request.form.get("title"), request.form.get("description"),
                request.form.get("category").lower(), the_id, request.form.get("videoLink"),
                the_id, request.form.get("imageLink"), 'link')

        db.session.add(entry)
        db.session.commit()
        flash('Uploaded')
        # session.pop('_flashes', None)
        return redirect(request.url)

    else:
        return render_template("link.html", genres=GENRES)


@app.route("/payment")

def payment():
    return "TODO"

# # Error 404 page
# @app.errorhandler(404)
# def page_not_found(e):
#     return render_template("error.html", code=404, t1="Page not found", t2="This may not mean anything."), 404

if __name__ == '__main__':
    app.run()
