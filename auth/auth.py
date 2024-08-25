from flask import Blueprint, render_template, request, session, redirect
from functools import wraps
from models import users, uploads, db

auth_bp = Blueprint('auth_bp', __name__, template_folder='templates')



def login_required(f):

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

@auth_bp.route("/")
# @app.route("/home")
@login_required
def index():
    # files = os.listdir(app.config["IMAGE_PATH"])
    # files = db.execute("SELECT * FROM uploads")
    page = request.args.get('page', 1, type=int)
    files = uploads.query.order_by(uploads.date.desc()).paginate(page=page, per_page=16)
    return render_template("auth/index.html", files=files)


@auth_bp.route("/login", methods=["GET", "POST"])
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

        print("Helooe", session)
        # Redirect user to home page
        return redirect("/")

    else:
        return render_template("auth/login.html")
    
@auth_bp.route("/register", methods=["GET", "POST"])
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
        return render_template("auth/register.html")


@auth_bp.route("/logout")
def logout():

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

@auth_bp.route("/profile")
def profile():

    # Query the user info
    info = users.query.filter_by(uid=session["user_id"])
    return render_template("auth/profile.html", info=info)

@auth_bp.route("/change_password", methods=["POST", "GET"])

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