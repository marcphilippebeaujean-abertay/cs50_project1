from flask import Flask, render_template, request, url_for, redirect, session, jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
import re
import os
import requests
app = Flask(__name__)

if __name__ is "__main__":
    app.run(debug=True)

# Check for environment variable
if not os.getenv('DATABASE_URL'):
    raise RuntimeError("DATABASE_URL is not set")

gr_dev_key = os.getenv('GOODREADS_DEV_KEY')


email_regex = re.compile(r"^(?!.*[A-Z])(?!.*[\s])([\w]+)([.][\w]+)?[@][\w]+[.][a-z]+")
pw_regex = re.compile(r'(?!.*\s)(?=.{7,})')

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

user=""

# Set up database
engine = create_engine(os.getenv('DATABASE_URL'))
db = scoped_session(sessionmaker(bind=engine))

def is_logged_in():
    if session.get('user') is None:
        session['user']=""
    return (len(session['user'])>0)

@app.route("/", methods=["GET", "POST"])
def index():
    return render_template("home.html", logged_in=is_logged_in())

@app.route("/register")
def register():
    return render_template("register.html")

@app.route("/handle-registration", methods=["POST"])
def register_user():
    if is_logged_in():
        return redirect(url_for('submission_error', message="Please log out first."))
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
        return redirect(url_for('submission_error', message="Please enter valid password (minimum specs: 6 characters, no white space."))
    if db.execute("SELECT * FROM users WHERE username =:username OR email =:email",
                  {'username': user_name, 'email': email}).rowcount > 0:
        return redirect(url_for('submission_error', message="User with username or email already registered."))
    db.execute("INSERT INTO users (username, email, password) VALUES (:username, :email, :password)",
        {"username": user_name, "email": email, "password": password})
    db.commit()
    session['user'] = user_name
    return redirect(url_for('submission_success', message=f'User {user_name} has been registered!'))

@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/login-user", methods=["POST"])
def login_user():
    if is_logged_in():
        return redirect(url_for('submission_error', message="Already logged in."))
    user_name = request.form.get("user")
    req_pw = request.form.get("pass")
    if db.execute("SELECT password FROM users WHERE username =:username AND password =:password",
                    {"username": user_name, "password": req_pw}).rowcount != 1:
        return redirect(url_for('submission_error', message="Login failed! Check your password and username."))
    else:
        session['user'] = user_name
        return redirect(url_for('submission_success', message=f'Logged in user {user_name}!'))

@app.route("/submission_error/<string:message>")
def submission_error(message):
    return render_template("error.html", message=message, logged_in=is_logged_in())

@app.route("/submission_success/<string:message>")
def submission_success(message):
    return render_template("success.html", message=message, logged_in=is_logged_in())

@app.route("/logout_user")
def logout_user():
    if not is_logged_in():
        return redirect(url_for('submission_error', message="Please log in to log out."))
    prev_user = session['user']
    session['user'] = ""
    return redirect(url_for('submission_success', message=f'Logged out user {prev_user}!'))

@app.route("/book_search", methods=["POST"])
def book_search():
    search_term = request.form.get("book-term").upper()
    if search_term is None:
        return redirect(url_for('submission_error', message="Couldn't process search."))
    # add sequel operator to search at beginning of string
    books = db.execute("SELECT * FROM books").fetchall()
    # search term and book title are transformed to uppercase
    books = [book for book in books if book.title.upper().startswith(search_term)]
    if len(books)<=0:
        return redirect(url_for('submission_error', message="Error 404: No books found."))
    return render_template("booklist.html", books=books, logged_in=True)

@app.route("/write_review/<string:isbn>")
def write_review(isbn):
    if not is_logged_in():
        return redirect(url_for('submission_error', message="Please log in to write reviews."))
    book = db.execute("SELECT * FROM books WHERE isbn =:isbn",
                      {"isbn": isbn}).fetchone()
    return render_template("review.html", book=book, logged_in=True)

@app.route("/view_reviews/<string:isbn>")
def view_reviews(isbn):
    gr_api_request = requests.get("https://www.goodreads.com/book/review_counts.json",
                        params={'isbns': isbn, 'key': gr_dev_key, 'format': 'json'})
    if gr_api_request.status_code!=200:
        raise Exception("ERROR: API request unsuccessful")
    gr_review_data = gr_api_request.json()['books'][0]
    if not is_logged_in():
        return redirect(url_for('submission_error', message="Please log in to view reviews."))
    reviews = db.execute("SELECT * FROM reviews WHERE isbn =:isbn",
                      {"isbn": isbn}).fetchall()
    book_title = db.execute("SELECT * FROM books WHERE isbn =:isbn",
                      {"isbn": isbn}).fetchone().title
    return render_template("reviewlist.html",
                           book_title=book_title,
                           review_count=gr_review_data["ratings_count"]+len(reviews),
                           avg_rating=gr_review_data["average_rating"],
                           reviews=reviews,
                           logged_in=True)

@app.route("/submit_review", methods=["POST"])
def submit_review():
    review_body = request.form.get("review-body")
    if len(review_body)<8:
        return redirect(url_for('submission_error', message=f'Review too short!'))
    if len(review_body)>300:
        return redirect(url_for('submission_error', message=f'Review too long!'))
    db.execute("INSERT INTO reviews (author, review, isbn, score) VALUES (:author, :review, :isbn, :score)",
               {"author": session['user'], "review": review_body, "isbn": request.form.get("isbn"), "score": request.form.get("score")})
    db.commit()
    return redirect(url_for('submission_success', message=f'Review submitted successfully!'))

@app.route("/api/<string:isbn>")
def review_api(isbn):
    book = db.execute("SELECT * FROM books WHERE isbn =:isbn",
                      {"isbn": isbn}).fetchone()
    if book is None:
        return jsonify({"error": "Invalid book isbn"}), 404
    gr_api_request = requests.get("https://www.goodreads.com/book/review_counts.json",
                                  params={'isbns': isbn, 'key': gr_dev_key, 'format': 'json'})
    gr_review_data = gr_api_request.json()['books'][0]
    return jsonify({
        "title": book.title,
        "author": book.author,
        "year": book.year_published,
        "review_count": gr_review_data["ratings_count"],
        "average_score": gr_review_data["average_rating"]
    })