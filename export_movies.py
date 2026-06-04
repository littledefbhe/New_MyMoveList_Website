import os
import sys

# Add the current directory to the Python path
sys.path.insert(0, os.path.abspath('.'))

from board import create_app, db
from board.models import Movie, Genre
import pandas as pd

def export_movies():
    """Export movies from database to CSV for KNN training."""
    app = create_app()
    
    with app.app_context():
        # Query all movies with stats
        movies = Movie.query.all()
        
        print(f"Found {len(movies)} movies in database")
        
        # Prepare data
        data = []
        for movie in movies:
            # Get genres
            genres = [g.name for g in movie.genres.all()]
            
            # Get stats
            watchlist_count = movie.stats.watchlist_count if movie.stats else 0
            favorites_count = movie.stats.favorites_count if movie.stats else 0
            watched_count = movie.stats.watched_count if movie.stats else 0
            
            row = {
                'movie_id': movie.id,
                'title': movie.title,
                'release_year': movie.release_year,
                'rating': movie.rating if movie.rating else 0,
                'runtime_minutes': movie.runtime_minutes if movie.runtime_minutes else 0,
                'genre1': genres[0] if len(genres) > 0 else None,
                'genre2': genres[1] if len(genres) > 1 else None,
                'genre3': genres[2] if len(genres) > 2 else None,
                'watchlist_count': watchlist_count,
                'favorites_count': favorites_count,
                'watched_count': watched_count,
            }
            data.append(row)
        
        # Create DataFrame and save
        df = pd.DataFrame(data)
        df.to_csv('movies_data.csv', index=False)
        print(f"Exported {len(df)} movies to movies_data.csv")
        print(f"\nFirst few rows:")
        print(df.head())
        print(f"\nGenre distribution:")
        print(df['genre1'].value_counts())

if __name__ == '__main__':
    export_movies()
