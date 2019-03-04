import os
import secrets

from flask import Flask, flash, jsonify, make_response, redirect, render_template, request, session, url_for
from flask_session import Session
from flask_assets import Environment, Bundle

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import error, formatRating, lookup, login_required

# Config
app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False
app.jinja_env.line_statement_prefix = '#'
# Secret key
secret_key = secrets.token_urlsafe(16)
app.config['SECRET_KEY'] = secret_key

# Compile Sass
assets = Environment(app)
assets.url = app.static_url_path
scss = Bundle(
    'sass/main.scss',
    filters='pyscss',
    depends=('**/*.scss'),
    output='styles.css')
assets.register('scss_all', scss)


# Check for database env then connect
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


@app.route("/api/<isbn>", methods=["GET"])
def api(isbn):
    """ Endpoint for API requests given book isbn"""
    # Ensure valid isbn-10 format provided
    if len(isbn) != 10:
        response = make_response(
            jsonify("Please provide a valid ISBN-10"), 404)
        response.headers['X-Error'] = "Please provide a valid ISBN-10"
        return response

    # Ensure requested book is in our database
    isInDB = db.execute(
        "SELECT * from books "
        "WHERE isbn = :isbn ", {
            'isbn': isbn
        }).fetchone()
    if isInDB is None:
        response = make_response(
            jsonify("Book does not exist in database"), 404)
        response.headers['X-Error'] = "Book does not exist in database"
        return response

    # Query data for API response
    proxy = db.execute(
        "SELECT books.title, books.author, books.year, books.isbn, "
        "COUNT(reviews.*) AS review_count, CAST(AVG(reviews.rating) AS float) AS average_score "
        "FROM books LEFT JOIN reviews ON reviews.book_id=books.id "
        "WHERE books.isbn=:isbn "
        "GROUP BY books.id", {
            'isbn': isbn
        }).fetchone()

    # Return json data
    book_data = {
        "title": proxy.title,
        "author": proxy.author,
        "year": int(proxy.year),
        "isbn": proxy.isbn,
        "review_count": proxy.review_count,
        "average_score": proxy.average_score
    }

    # Send requested data
    return make_response(jsonify(book_data), 200)


@app.route("/book/<int:book_id>")
@login_required
def book(book_id):
    """ Shows book details """

    # Validate book id
    book = db.execute("SELECT * FROM books WHERE id = :id",
                      {"id": book_id}).fetchone()
    if book is None:
        return error("Can't seem to find that book!", 404)

    # Goodreads review data
    thirdparty_ratings = lookup(book.isbn)

    # Reviews to display from this site
    review_detail = db.execute(
        "SELECT CAST(reviews.stamp AS DATE), users.username, reviews.rating, reviews.text "
        "FROM reviews JOIN users ON reviews.user_id = users.id "
        "WHERE reviews.book_id = :book_id "
        "ORDER BY reviews.stamp DESC", {
            'book_id': book_id
        }).fetchall()

    # Summary of reviews on this site
    review_summary = db.execute(
        "SELECT CAST(COUNT(*) AS INT), CAST(AVG(rating) AS float) "
        "FROM reviews WHERE book_id=:book_id", {
            "book_id": book_id
        }).fetchall()

    # Query for any reviews current user has left
    users_review = db.execute(
        "SELECT rating "
        "FROM reviews "
        "WHERE book_id = :book_id "
        "AND user_id = :user_id ",
        {'book_id': book_id,
         'user_id': session["user_id"]
         }).fetchone()

    # Render page
    return render_template("book.html",
                           book=book,
                           formatRating=formatRating,
                           review_detail=review_detail,
                           review_summary=review_summary[0],
                           thirdparty_ratings=thirdparty_ratings,
                           users_review=users_review)


@app.route("/check")
def check():
    """
    Checks if requested username is available,
    returns JSON for client-side validation
    """
    username = request.args.get("user_name")
    users = db.execute("SELECT * FROM users WHERE username = :username",
                       {"username": username}).fetchone()
    if users is None:
        return jsonify(True)
    # Username is taken
    return jsonify(False)


@app.route("/")
@login_required
def index():
    return render_template("/index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """ Log user in """
    session.clear()
    # Login form post request
    if request.method == "POST":
        # Ensure username, password were received
        try:
            username = request.form.get("username")
            password = request.form.get("hash")
        except ValueError:
            return error("must provide username and password", 403)

        # Validate credentials
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          {'username': username}).fetchone()
        if rows is None or not check_password_hash(rows["hash"], password):
            return error("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows["id"]

        # Render home page
        return redirect("/")

    # GET request
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out, redirect to login"""
    session.clear()
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    """ Register new user """

    # Registration form POST request
    if request.method == "POST":
        try:
            username = request.form.get("username")
            password = request.form.get("hash")
        except ValueError:
            return error("must provide username and password", 400)

        # Ensure confirmation matches password
        if not request.form.get("confirmation") or request.form.get("confirmation") != password:
            return error("password and confirmation must match", 400)

        # Server-side validation that username is available
        matches = db.execute("SELECT * FROM users WHERE (username = :username)",
                             {'username': username}).fetchone()
        if matches is not None:
            return error("sorry that username is taken", 400)

        # Insert new user
        db.execute(
            "INSERT INTO users (username, hash) "
            "VALUES (:username, :hash)",
            {'username': username,
             'hash': generate_password_hash(password,
                                            method='pbkdf2:sha256',
                                            salt_length=8)})
        db.commit()

        # Log user in with new session
        session_id = db.execute("SELECT id FROM users WHERE username = :username",
                                {'username': username}).fetchone()
        session["user_id"] = session_id["id"]

        return redirect("/")

    # GET request
    else:
        return render_template("register.html")


@app.route("/review/<book_id>", methods=["POST"])
@login_required
def review(book_id):
    """ Validate and insert a book review """

    # User id from current session
    user_id = session["user_id"]
    # Form data
    try:
        rating = request.form.get('rating')
        text = request.form.get('review-text')
    except ValueError:
        return error('Something went wrong with submission.', 400)

    # Has user already submitted a review for this book
    book_id_duplicates = db.execute(
        "SELECT user_id from reviews "
        "WHERE book_id = :book_id "
        "AND user_id = :user_id",
        {'book_id': book_id, 'user_id': user_id}).fetchone()
    if book_id_duplicates is not None:
        return error('Only one submission per book allowed!', 403)

    _review = {
        "user_id": user_id,
        "book_id": int(book_id),
        "rating": int(rating),
        "text": text.rstrip()  # Should user leave new line in textarea
    }

    # Save user review
    db.execute(
        "INSERT INTO reviews (user_id, book_id, rating, text)"
        "VALUES (:user_id, :book_id, :rating, :text)", _review)
    db.commit()

    # Reload the page, rendering their review
    return redirect(url_for("book", book_id=book_id))


@app.route("/search")
@login_required
def search():
    """ Renders books containing search query """
    try:
        query = request.args.get("q").lower()
    except AttributeError:
        query = request.args.get("q")

    # Adding browse functionality
    browse = request.args.get("browse")

    if browse is None:
        # Select all rows with a column value that includes query
        results = db.execute("SELECT * FROM books "
                             "WHERE LOWER(isbn) LIKE CONCAT('%', :q, '%')"
                             "OR LOWER(title) LIKE CONCAT('%', :q, '%') "
                             "OR LOWER(author) LIKE CONCAT('%', :q, '%') "
                             "ORDER BY title LIMIT 100", {'q': query}).fetchall()
    else:
        # Select titles starting with letter
        results = db.execute(
            "SELECT * FROM books "
            "WHERE LOWER(title) LIKE CONCAT(:q, '%') "
            "ORDER BY title", {'q': query}).fetchall()

    return render_template("search.html", browse=browse, query=query, results=results)
