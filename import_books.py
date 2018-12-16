# DB Model
# Column 1: ISBN
# Column 2: Name
# Column 3: Author
# Column 4: Date Published

# INSERT INTO books (ISBN, title, author, year_published)
#                    VALUES(...)

import csv
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

if not os.getenv('DATABASE_URL'):
    raise RuntimeError("DATABASE_URL is not set")

# Set up database
engine = create_engine(os.getenv('DATABASE_URL'))
db = scoped_session(sessionmaker(bind=engine))

with open('data/books.csv') as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=',')
    for isbn, ttl, auth, year_pub in csv_reader:
        db.execute("INSERT INTO books (isbn, title, author, year_published) VALUES (:isbn, :title, :author, :year_published)",
                   { "isbn": isbn, "title": ttl, "author": auth, "year_published": int(year_pub)})
    db.commit()

