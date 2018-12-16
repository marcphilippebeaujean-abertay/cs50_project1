import os

from flask import Flask, render_template, request, url_for, redirect
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
import re
import os
app = Flask(__name__)

if __name__ is "__main__":
    app.run(debug=True)

# Check for environment variable
if not os.getenv('DATABASE_URL'):
    raise RuntimeError("DATABASE_URL is not set")

email_regex = re.compile(r"^(?!.*[A-Z])(?!.*[\s])([\w]+)([.][\w]+)?[@][\w]+[.][a-z]+")
pw_regex = re.compile(r'(?=.*[a-z])(?=.*[A-Z])(?=.*[\d])(?!.*\s)(?=.{7,})')

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
    if not email_regex.match(email):
        return redirect(url_for('submission_error', message="Invalid email."))
    user_name = request.form.get("user-name")
    if len(user_name) < 4:
        return redirect(url_for('submission_error', message="Please enter a longer user name."))
    if re.match('\s', user_name):
        return redirect(url_for('submission_error', message="Please don't include whitespace in your user name."))
    password = request.form.get("pass")
    if not pw_regex.match(password):
        return redirect(url_for('submission_error', message="Please enter valid password (minimum specs: 6 characters, capital and lowercase letters, one digit and no white space."))
    if db.execute("SELECT * FROM users WHERE username =:username OR email =:email",
                  {'username': user_name, 'email': email}).rowcount > 0:
        return redirect(url_for('submission_error', message="User with username or email already registered."))
    db.execute("INSERT INTO users (username, email, password) VALUES (:username, :email, :password)",
        {"username": user_name, "email": email, "password": password})
    db.commit()
    return redirect(url_for('submission_success', message=f'User {user_name} has been registered!'))

@app.route("/submission_error/<string:message>")
def submission_error(message):
    return render_template("error.html", message=message)

@app.route("/submission_success/<string:message>")
def submission_success(message):
    return render_template("success.html", message=message)