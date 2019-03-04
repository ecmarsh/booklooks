import requests

from flask import redirect, render_template, request, session
from functools import wraps


def error(message, code=400):
    """Render message as an error to user."""
    def escape(s):
        """
        Escape special characters.
        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("error.html", top=code, bottom=escape(message)), code


def login_required(f):
    """
    Decorate routes to require login.
    http://flask.pocoo.org/docs/1.0/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


def lookup(isbn):
    """
    Get book results from goodreads API.
    https://www.goodreads.com/api/index
    """

    # Request config
    url = "https://www.goodreads.com/book/review_counts.json"
    key = 'wFjwok88x2qelijJiSgVgA'

    try:
        res = requests.get(url, params={"key": key, "isbns": isbn})
        res.raise_for_status()
    except requests.RequestException:
        return None

    # Parse response
    try:
        books = res.json()
        response = {
            "avg": float(books['books'][0]["average_rating"]),
            "count": "{:,}".format(books['books'][0]["work_ratings_count"])
        }
        return response
    except (KeyError, TypeError, ValueError):
        return None


def formatRating(value):
    """Format rating to 100th"""
    if value is None:
        return ""

    return f"{value:,.2f}"
