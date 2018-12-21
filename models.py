from flask_sqlalchemy import SQLAlchemy

db=SQLAlchemy()

class Book(db.Model):
    __tablename__="books"
    isbn = db.Column(db.String, primary_key=True, nullable=False)
    title = db.Column(db.String, nullable=False)
    author = db.Column(db.String, nullable=False)
    year_published = db.Column(db.Integer, nullable=False)

class User(db.Model):
    __tablename__="users"
    username = db.Column(db.String, primary_key=True, nullable=False)
    email = db.Column(db.String, nullable=False)
    password = db.Column(db.String, nullable=False)

class Review(db.Model):
    __tablename__="reviews"
    id = db.Column(db.Integer, primary_key=True)
    author = db.Column(db.String, nullable=False)
    review = db.Column(db.String, nullable=False)
    isbn = db.Column(db.String, nullable=False)