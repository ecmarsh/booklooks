import csv
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Link database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


def main():
    """ Import book data from books.csv into books table """
    filename = "books.csv"
    with open(filename, "r", newline='') as file_obj:
        reader = csv.reader(file_obj, delimiter=',')
        # Skip the header
        next(reader)
        for isbn, title, author, year in reader:
            db.execute("INSERT INTO books (isbn, title, author, year) VALUES (:isbn, :title, :author, :year)",
                       {"isbn": isbn, "title": title, "author": author, "year": year})
    db.commit()


# Init
if __name__ == "__main__":
    main()
