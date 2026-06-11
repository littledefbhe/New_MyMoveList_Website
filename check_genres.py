import os
import sys

# Add the current directory to the Python path
sys.path.insert(0, os.path.abspath('.'))

from board import create_app, db
from board.models import Genre, Movie, movie_genres

def check_genres():
    """Check current genres in the database."""
    app = create_app()
    with app.app_context():
        genres = Genre.query.order_by(Genre.name).all()
        print(f"Found {len(genres)} genres in database:")
        print("-" * 60)
        for genre in genres:
            # Count movies with this genre
            movie_count = db.session.execute(
                db.select(db.func.count()).select_from(movie_genres).where(movie_genres.c.genre_id == genre.id)
            ).scalar()
            print(f"  - {genre.name}: {movie_count} movies")
        
        print("\n" + "=" * 60)
        print("Checking for potential duplicates/similar genres...")
        print("-" * 60)
        
        # Group by first word to find potential duplicates
        genre_dict = {}
        for genre in genres:
            first_word = genre.name.split()[0].lower()
            if first_word not in genre_dict:
                genre_dict[first_word] = []
            genre_dict[first_word].append(genre.name)
        
        for first_word, names in genre_dict.items():
            if len(names) > 1:
                print(f"\n  '{first_word}' variations:")
                for name in names:
                    print(f"    - {name}")

if __name__ == '__main__':
    check_genres()
