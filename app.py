import os

from flask import Flask, render_template, request, url_for, redirect
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
import re
import os
app = Flask(__name__)

# Check for environment variable
if not os.getenv('DATABASE_URL'):
    raise RuntimeError("DATABASE_URL is not set")

EMAIL_REGEX = re.compile(r"[^@]+@[^@]+\.[^@]+")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv('DATABASE_URL'))
db = scoped_session(sessionmaker(bind=engine))

@app.route("/")
def index():
    return render_template("home.html")

@app.route("/register")
def register():
    return render_template("register.html")

@app.route("/handle-registration", methods=["POST"])
def register_user():
    email = request.form.get("email")
    if not EMAIL_REGEX.match(email):
        return redirect(url_for('submission_error', message="Invalid email!"))
    user_name = request.form.get("user-name")
    password = request.form.get("pass")
    return render_template("home.html")

@app.route("/submission_error/<string:message>")
def submission_error(message):
    return render_template("error.html", message=message)