from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
import requests

app = Flask(__name__)

app.config["SECRET_KEY"] = "secretkey"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///books.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)


class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    isbn = db.Column(db.String(30), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(200))
    page_count = db.Column(db.Integer)
    average_rating = db.Column(db.Float)
    thumbnail = db.Column(db.String(500))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)


@app.route("/")
def index():
    if "user_id" not in session:
        return redirect(url_for("login"))

    books = Book.query.filter_by(user_id=session["user_id"]).all()

    return render_template("index.html", books=books)


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        user = User.query.filter_by(
            username=username,
            password=password
        ).first()

        if user:
            session["user_id"] = user.id
            return redirect(url_for("index"))

        flash("Invalid login")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/search", methods=["POST"])
def search():

    if "user_id" not in session:
        return redirect(url_for("login"))

    isbn = request.form["isbn"]

    url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}"

    response = requests.get(url)
    data = response.json()

    if data["totalItems"] == 0:
        flash("Book not found")
        return redirect(url_for("index"))

    volume_info = data["items"][0]["volumeInfo"]

    title = volume_info.get("title", "N/A")

    authors = volume_info.get("authors", ["N/A"])
    author = ", ".join(authors)

    page_count = volume_info.get("pageCount", 0)

    average_rating = volume_info.get("averageRating", 0)

    thumbnail = volume_info.get("imageLinks", {}).get("thumbnail", "")

    book = Book(
        isbn=isbn,
        title=title,
        author=author,
        page_count=page_count,
        average_rating=average_rating,
        thumbnail=thumbnail,
        user_id=session["user_id"]
    )

    db.session.add(book)
    db.session.commit()

    flash("Book added successfully")

    return redirect(url_for("index"))


@app.route("/delete/<int:book_id>", methods=["POST"])
def delete(book_id):

    book = Book.query.get_or_404(book_id)

    db.session.delete(book)
    db.session.commit()

    flash("Book deleted")

    return redirect(url_for("index"))


def create_database():
    with app.app_context():

        db.create_all()

        user_exists = User.query.filter_by(username="student").first()

        if not user_exists:
            user = User(
                username="student",
                password="password"
            )

            db.session.add(user)
            db.session.commit()


if __name__ == "__main__":
    create_database()
    app.run(debug=True)
