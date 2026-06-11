import os
import sys

# Add the current directory to the Python path
sys.path.insert(0, os.path.abspath('.'))

from board import create_app, db
from board.models import Movie, Genre, movie_genres

def investigate_low_count_genres():
    """Investigate genres with very low movie counts."""
    app = create_app()
    with app.app_context():
        genres = Genre.query.order_by(Genre.name).all()
        
        print("Genres with low movie counts (< 20):")
        print("-" * 60)
        
        for genre in genres:
            movie_count = db.session.execute(
                db.select(db.func.count()).select_from(movie_genres).where(movie_genres.c.genre_id == genre.id)
            ).scalar()
            
            if movie_count < 20:
                print(f"\n{genre.name}: {movie_count} movies")
                
                # Show the movies
                movie_ids = db.session.execute(
                    db.select(movie_genres.c.movie_id).where(movie_genres.c.genre_id == genre.id)
                ).scalars().all()
                
                for movie_id in movie_ids:
                    movie = Movie.query.get(movie_id)
                    if movie:
                        # Show all genres for this movie
                        all_genres = [g.name for g in movie.genres.all()]
                        print(f"  - {movie.title} ({movie.release_year}): {', '.join(all_genres)}")

if __name__ == '__main__':
    investigate_low_count_genres()
