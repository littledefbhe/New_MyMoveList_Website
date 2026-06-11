import os
import sys

# Add the current directory to the Python path
sys.path.insert(0, os.path.abspath('.'))

from board import create_app, db
from board.models import Movie, Genre, movie_genres
from sqlalchemy import text

def final_cleanup():
    """Remove low-count generic genres."""
    app = create_app()
    with app.app_context():
        print("=" * 60)
        print("Final Genre Cleanup")
        print("=" * 60)
        
        # Remove "Animation" genre (only 1 movie, also has Action & Adventure)
        animation_genre = Genre.query.filter_by(name='Animation').first()
        if animation_genre:
            print("\nRemoving 'Animation' genre...")
            # Get movies with this genre
            movie_ids = db.session.execute(
                db.select(movie_genres.c.movie_id).where(movie_genres.c.genre_id == animation_genre.id)
            ).scalars().all()
            
            print(f"  Found {len(movie_ids)} movies with 'Animation' genre")
            for movie_id in movie_ids:
                movie = Movie.query.get(movie_id)
                if movie:
                    all_genres = [g.name for g in movie.genres.all()]
                    print(f"    - {movie.title}: {', '.join(all_genres)}")
            
            # Delete the genre associations
            db.session.execute(
                movie_genres.delete().where(movie_genres.c.genre_id == animation_genre.id)
            )
            # Delete the genre
            db.session.delete(animation_genre)
            db.session.commit()
            print("  ✓ Removed 'Animation' genre")
        
        # Remove "TV Shows" genre (generic category with 16 movies)
        tv_shows_genre = Genre.query.filter_by(name='TV Shows').first()
        if tv_shows_genre:
            print("\nRemoving 'TV Shows' genre...")
            # Get movies with this genre
            movie_ids = db.session.execute(
                db.select(movie_genres.c.movie_id).where(movie_genres.c.genre_id == tv_shows_genre.id)
            ).scalars().all()
            
            print(f"  Found {len(movie_ids)} movies with 'TV Shows' genre")
            for movie_id in movie_ids:
                movie = Movie.query.get(movie_id)
                if movie:
                    all_genres = [g.name for g in movie.genres.all()]
                    print(f"    - {movie.title}: {', '.join(all_genres)}")
            
            # Delete the genre associations
            db.session.execute(
                movie_genres.delete().where(movie_genres.c.genre_id == tv_shows_genre.id)
            )
            # Delete the genre
            db.session.delete(tv_shows_genre)
            db.session.commit()
            print("  ✓ Removed 'TV Shows' genre")
        
        # Remove "Movies" genre (generic category with 57 movies)
        movies_genre = Genre.query.filter_by(name='Movies').first()
        if movies_genre:
            print("\nRemoving 'Movies' genre...")
            # Get movies with this genre
            movie_ids = db.session.execute(
                db.select(movie_genres.c.movie_id).where(movie_genres.c.genre_id == movies_genre.id)
            ).scalars().all()
            
            print(f"  Found {len(movie_ids)} movies with 'Movies' genre")
            
            # Delete the genre associations
            db.session.execute(
                movie_genres.delete().where(movie_genres.c.genre_id == movies_genre.id)
            )
            # Delete the genre
            db.session.delete(movies_genre)
            db.session.commit()
            print("  ✓ Removed 'Movies' genre")
        
        print("\n" + "=" * 60)
        print("Cleanup Complete!")
        print("=" * 60)
        print(f"Total movies: {Movie.query.count()}")
        print(f"Total genres: {Genre.query.count()}")
        
        # Show remaining genres
        print("\nRemaining genres:")
        genres = Genre.query.order_by(Genre.name).all()
        for genre in genres:
            movie_count = db.session.execute(
                db.select(db.func.count()).select_from(movie_genres).where(movie_genres.c.genre_id == genre.id)
            ).scalar()
            print(f"  - {genre.name}: {movie_count} movies")

if __name__ == '__main__':
    final_cleanup()
