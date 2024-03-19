import os

from flask import Flask, render_template, redirect
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Float
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests


MOVIE_URL = "http://www.omdbapi.com/?apiKey=5e4e2638"
FLASK_KEY = "'8BYkEfBA6O6donzWlSihBXox7C0sKR6b'"

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get(FLASK_KEY)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DB_URI", "sqlite:///posts.db")
bootstrap = Bootstrap5(app)


# CREATE DB


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)
db.init_app(app)


# CREATE TABLE


class Movies(db.Model):
    Id: Mapped[int] = mapped_column(Integer, primary_key=True)
    Title: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    Year: Mapped[int] = mapped_column(Integer, nullable=False)
    Description: Mapped[str] = mapped_column(String(500), nullable=False)
    Rating: Mapped[float] = mapped_column(Float, nullable=True)
    Ranking: Mapped[int] = mapped_column(Integer, nullable=True)
    Review: Mapped[str] = mapped_column(String(250), nullable=True)
    Image_Url: Mapped[str] = mapped_column(String(500), nullable=False)


with app.app_context():
    db.create_all()


# Creating WTForms

class EditRatingForm(FlaskForm):
    rating_field = StringField(label="Your Rating Out of 10 e.g 7.5", validators=[DataRequired()])
    review_field = StringField(label="Your Review", validators=[DataRequired()])
    submit_btn = SubmitField(label="Done")


@app.route("/")
def home():
    sorted_list = []
    movies_list = db.session.query(Movies).all()

    descending_order_movie_ratings = [movie.Rating for movie in movies_list]
    descending_order_movie_ratings.sort(reverse=True)

    for rating in descending_order_movie_ratings:
        for movie in movies_list:
            if rating == movie.Rating:
                movie_ranking = db.get_or_404(Movies, movie.Id)
                num = descending_order_movie_ratings.index(rating) + 1
                movie_ranking.Ranking = num
                db.session.commit()

    movie_list = db.session.query(Movies).all()
    ranking_list = [movie.Ranking for movie in movie_list]
    ranking_list.sort(reverse=True)

    for rank in ranking_list:
        movies_list = db.session.query(Movies).all()
        for movie in movies_list:
            if movie.Ranking == rank:
                sorted_list.append(movie)

    return render_template("index.html", all_movies=sorted_list, movies_list_length=len(sorted_list))


@app.route("/edit/id=<id_no>", methods=['GET', 'POST'])
def edit_rating(id_no):
    edit_form = EditRatingForm()
    if edit_form.validate_on_submit():
        edited_rating = edit_form.rating_field.data
        edited_review = edit_form.review_field.data

        with app.app_context():
            current_movie = db.get_or_404(Movies, id_no)
            current_movie.Rating = edited_rating
            current_movie.Review = edited_review
            db.session.commit()
        return redirect("/")
    else:
        return render_template("edit.html", form=edit_form, movie_id=id_no)


@app.route("/delete/id=<id_no>")
def delete_movie(id_no):
    with app.app_context():
        movie_to_delete = db.get_or_404(Movies, id_no)
        db.session.delete(movie_to_delete)
        db.session.commit()
    return redirect("/")


class AddMoviesForm(FlaskForm):
    movie_name = StringField(label="Movie Title", validators=[DataRequired()])
    add_button = SubmitField(label="Add Movie")


@app.route("/add", methods=['GET', 'POST'])
def add_movies():
    add_form = AddMoviesForm()

    if add_form.validate_on_submit():
        movie_title = add_form.movie_name.data

        parameters = {
            "s": movie_title,
            "type": "movie",
        }

        response = requests.get(url=MOVIE_URL, params=parameters)
        try:
            movies_data = response.json()['Search']
        except KeyError:
            output = "No Results Found. Please try again."
            return render_template("select.html", error=output)

        else:
            return render_template("select.html", all_movies=movies_data, all_movies_length=len(movies_data))
    else:
        return render_template("add.html", form=add_form)


@app.route("/update/id_no=<movie_id>")
def update(movie_id):
    parameter = {
        "i": movie_id,
        "plot": "short"
    }
    selected_movie = requests.get(url=MOVIE_URL, params=parameter)
    selected_movie_data = selected_movie.json()
    movie_title = selected_movie_data['Title']
    movie_year = selected_movie_data['Year']
    movie_description = selected_movie_data['Plot']
    movie_image = selected_movie_data['Poster']

    with app.app_context():
        new_movie = Movies(Title=movie_title, Year=movie_year,
                           Description=movie_description, Image_Url=movie_image)
        db.session.add(new_movie)
        db.session.commit()
        return redirect(f"/edit/id={new_movie.Id}")


if __name__ == '__main__':
    app.run(debug=False)
