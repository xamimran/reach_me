from flask import Flask, Blueprint, render_template, request, flash, redirect, session
from models import uploads, db
import os
import re
import string
import random

videos_bp = Blueprint('videos_bp', __name__, template_folder='templates', static_folder='static')

video_app = Flask(__name__)
# Upload genres
GENRES = [
        "Technology", "Art", "Animals", "Cars", "Music", "Lifestyle", "Gaming", "Funny", "Meme", "Other"
    ]


# Configure the location that videos will live in
video_app.config["VIDEO_PATH"] = "static/videos"

# Configure the location that images will live in
video_app.config["IMAGE_PATH"] = "static/images"

# List of img accepted extensions
video_app.config["ALLOWED_VIDEO_EXTENSIONS"] = ["MOV", "MP4", "OGG", "WEBM"]

# List of vids accepted extensions
video_app.config["ALLOWED_IMG_EXTENSIONS"] = ["PNG", "JPG", "JPEG"]
   
@videos_bp.route("/upload_method/<string:param>")
def upload_method(param):
    return render_template("videos/method.html", params= param)

@videos_bp.route("/upload", methods=["POST", "GET"])
def upload():

    if request.method == "POST":

        # Ensure title is submitted
        if not request.form.get("title"):
            return render_template("error.html", code=400, t1="Missing title")

        # Ensure description is submitted
        if not request.form.get("description"):
            return render_template("error.html", code=400, t1="Missing description")

        # Ensure category is provided
        if request.form.get("category") not in GENRES:
            return render_template("error.html", code=400, t1="Invalid/missing category")

        if request.files:

            video = request.files["file"]
            img = request.files["thumbnail"]

            # Ensure the video has a name
            if video.filename == "":
                return render_template("error.html", code=400, t1="Video must have a name")

            # Ensure the image has a name
            if img.filename == "":
                return render_template("error.html", code=400, t1="Image must have a name")

            the_id = id_generator()
            # Check the video extension
            if not check_vid(video.filename):
                return render_template("error.html", code=400, t1="Video extension not allowed")

            else:
                videoname = the_id + "." + check_vid(video.filename)

                video.save(os.path.join(video_app.config["VIDEO_PATH"], videoname))

            # Check the image extension
            if not check_img(img.filename):
                return render_template("error.css", code=400, t1="Image extension not allowed")

            else:
                imagename = the_id + "." + check_img(img.filename)

                img.save(os.path.join(video_app.config["IMAGE_PATH"], imagename))

            # Save uploaded to db
            entry = uploads(session["user_id"], request.form.get("title"), request.form.get("description"), 
                            request.form.get("category").lower(), videoname,
                             'N/A', imagename, 'N/A', 'upload') 

            db.session.add(entry)
            db.session.commit()
            flash('Uploaded')
            # session.pop('_flashes', None)
            return redirect(request.url)

    else:
        return render_template("videos/upload.html", genres=GENRES)


# Random number generator for file names
def id_generator(size=10, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

def check_vid(filename):

    if not "." in filename:
        return False

    extension = filename.rsplit(".", 1)[1]

    if extension.upper() in video_app.config["ALLOWED_VIDEO_EXTENSIONS"]:
        return extension
    else:
        return False

def check_img(filename):

    if not "." in filename:
        return False

    extension = filename.rsplit(".", 1)[1]

    if extension.upper() in video_app.config["ALLOWED_IMG_EXTENSIONS"]:
        return extension
    else:
        return False
 