from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

# Association tables
watchlist = db.Table('watchlist',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('movie_id', db.Integer, db.ForeignKey('movies.id'), primary_key=True)
)

favorites = db.Table('favorites',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('movie_id', db.Integer, db.ForeignKey('movies.id'), primary_key=True),
    db.Column('added_at', db.DateTime, default=datetime.utcnow)
)

watched = db.Table('watched',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('movie_id', db.Integer, db.ForeignKey('movies.id'), primary_key=True),
    db.Column('watched_at', db.DateTime, default=datetime.utcnow)
)

# Association table for many-to-many relationship between movies and genres
movie_genres = db.Table('movie_genres',
    db.Column('movie_id', db.Integer, db.ForeignKey('movies.id'), primary_key=True),
    db.Column('genre_id', db.Integer, db.ForeignKey('genres.id'), primary_key=True)
)

# Association table for many-to-many relationship between movies and tags
movie_tags = db.Table('movie_tags',
    db.Column('movie_id', db.Integer, db.ForeignKey('movies.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tags.id'), primary_key=True)
)

# Association table for user tag preferences
user_tag_preferences = db.Table('user_tag_preferences',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tags.id'), primary_key=True)
)


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    watchlist = db.relationship(
        'Movie',
        secondary=watchlist,
        lazy='dynamic',
        backref=db.backref('watchers', lazy='dynamic')
    )

    favorite_movies = db.relationship(
        'Movie',
        secondary=favorites,
        lazy='dynamic',
        backref=db.backref('favorited_by', lazy='dynamic')
    )

    watched_movies = db.relationship(
        'Movie',
        secondary=watched,
        lazy='dynamic',
        backref=db.backref('watched_by', lazy='dynamic')
    )

    preferred_tags = db.relationship(
        'Tag',
        secondary=user_tag_preferences,
        lazy='dynamic',
        backref=db.backref('preferred_by', lazy='dynamic')
    )
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def add_to_watchlist(self, movie):
        """Add a movie to the user's watchlist if not already present."""
        if not self.is_in_watchlist(movie):
            self.watchlist.append(movie)
            if movie.stats:
                movie.stats.watchlist_count += 1
            db.session.commit()
            return True
        return False
        
    def remove_from_watchlist(self, movie):
        """Remove a movie from the user's watchlist if present."""
        if self.is_in_watchlist(movie):
            self.watchlist.remove(movie)
            if movie.stats and movie.stats.watchlist_count > 0:
                movie.stats.watchlist_count -= 1
            db.session.commit()
            return True
        return False
        
    def is_in_watchlist(self, movie):
        """Check if a movie is in the user's watchlist."""
        return self.watchlist.filter(watchlist.c.movie_id == movie.id).count() > 0
        
    def is_favorite(self, movie):
        """Check if a movie is in the user's favorites."""
        return self.favorite_movies.filter(favorites.c.movie_id == movie.id).count() > 0
        
    def has_watched(self, movie):
        """Check if a movie is in the user's watched list."""
        return self.watched_movies.filter(watched.c.movie_id == movie.id).count() > 0
        
    def add_to_favorites(self, movie):
        """Add a movie to the user's favorites if not already present."""
        if not self.is_favorite(movie):
            self.favorite_movies.append(movie)
            if movie.stats:
                movie.stats.favorites_count = (movie.stats.favorites_count or 0) + 1
            db.session.commit()
            return True
        return False
        
    def remove_from_favorites(self, movie):
        """Remove a movie from the user's favorites if present."""
        if self.is_favorite(movie):
            self.favorite_movies.remove(movie)
            if movie.stats and (movie.stats.favorites_count or 0) > 0:
                movie.stats.favorites_count -= 1
            db.session.commit()
            return True
        return False
        
    def mark_as_watched(self, movie):
        """Add a movie to the user's watched list if not already present."""
        if not self.has_watched(movie):
            self.watched_movies.append(movie)
            if movie.stats:
                movie.stats.watched_count = (movie.stats.watched_count or 0) + 1
            db.session.commit()
            return True
        return False
        
    def unmark_as_watched(self, movie):
        """Remove a movie from the user's watched list if present."""
        if self.has_watched(movie):
            self.watched_movies.remove(movie)
            if movie.stats and (movie.stats.watched_count or 0) > 0:
                movie.stats.watched_count -= 1
            db.session.commit()
            return True
        return False

    def add_tag_preference(self, tag):
        """Add a tag to the user's preferences if not already present."""
        if tag not in self.preferred_tags.all():
            self.preferred_tags.append(tag)
            return True
        return False

    def remove_tag_preference(self, tag):
        """Remove a tag from the user's preferences if present."""
        if tag in self.preferred_tags.all():
            self.preferred_tags.remove(tag)
            return True
        return False

    def has_tag_preference(self, tag):
        """Check if a tag is in the user's preferences."""
        return self.preferred_tags.filter(user_tag_preferences.c.tag_id == tag.id).count() > 0
        
    def __repr__(self):
        return f'<User {self.username}>'


class Movie(db.Model):
    __tablename__ = 'movies'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    release_year = db.Column(db.Integer, nullable=False)
    rating = db.Column(db.Float)
    certification = db.Column(db.String(10))
    runtime_minutes = db.Column(db.Integer)
    poster_url = db.Column(db.String(500))
    overview = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    genres = db.relationship('Genre', secondary=movie_genres, lazy='dynamic',
                           backref=db.backref('movies', lazy='dynamic'))
    tags = db.relationship('Tag', secondary=movie_tags, lazy='dynamic',
                          backref=db.backref('movies', lazy='dynamic'))
    stats = db.relationship('MovieStats', backref='movie', uselist=False, lazy=True)
    
    def __repr__(self):
        return f'<Movie {self.title} ({self.release_year})>'

class Genre(db.Model):
    __tablename__ = 'genres'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

    def __repr__(self):
        return f'<Genre {self.name}>'

class Tag(db.Model):
    __tablename__ = 'tags'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    tag_type = db.Column(db.String(50), nullable=False)  # 'genre' or 'movie_type'

    def __repr__(self):
        return f'<Tag {self.name} ({self.tag_type})>'

class MovieStats(db.Model):
    __tablename__ = 'movie_stats'

    movie_id = db.Column(db.Integer, db.ForeignKey('movies.id'), primary_key=True)
    ratings_count = db.Column(db.Integer, default=0)
    reviews_count = db.Column(db.Integer, default=0)
    watchlist_count = db.Column(db.Integer, default=0)
    favorites_count = db.Column(db.Integer, default=0)
    watched_count = db.Column(db.Integer, default=0)
    
    def __repr__(self):
        return f'<MovieStats for movie {self.movie_id}>'
