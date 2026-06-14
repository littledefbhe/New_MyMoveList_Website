#!/usr/bin/env python3
"""
Script to recalculate all movie statistics from actual relationship tables.
This fixes incorrect statistics by counting from the actual database relationships.
"""

import sys
import os

# Add the current directory to the Python path
sys.path.insert(0, os.path.abspath('.'))

from board import create_app, db
from board.models import Movie, MovieStats, watchlist, favorites, watched

def recalculate_all_stats():
    """Recalculate all movie statistics from actual relationship tables."""
    print("=" * 60)
    print("Movie Statistics Recalculation")
    print("=" * 60)
    
    app = create_app()
    
    with app.app_context():
        # Get all movies
        movies = Movie.query.all()
        print(f"\nFound {len(movies)} movies in database")
        
        updated_count = 0
        errors_count = 0
        
        for movie in movies:
            try:
                # Count actual relationships using the association tables
                watchlist_count = db.session.execute(
                    db.select(db.func.count()).select_from(watchlist).where(watchlist.c.movie_id == movie.id)
                ).scalar() or 0
                
                favorites_count = db.session.execute(
                    db.select(db.func.count()).select_from(favorites).where(favorites.c.movie_id == movie.id)
                ).scalar() or 0
                
                watched_count = db.session.execute(
                    db.select(db.func.count()).select_from(watched).where(watched.c.movie_id == movie.id)
                ).scalar() or 0
                
                reviews_count = movie.reviews.count()
                
                # Get or create stats
                if not movie.stats:
                    movie.stats = MovieStats(movie_id=movie.id)
                
                # Update stats with actual counts
                movie.stats.watchlist_count = watchlist_count
                movie.stats.favorites_count = favorites_count
                movie.stats.watched_count = watched_count
                movie.stats.reviews_count = reviews_count
                
                # Keep ratings_count as is (or set to 0 if needed)
                if movie.stats.ratings_count is None:
                    movie.stats.ratings_count = 0
                
                updated_count += 1
                
                if updated_count <= 10:  # Show first 10 updates
                    print(f"✓ Updated: {movie.title} - Watchlist: {watchlist_count}, Favorites: {favorites_count}, Watched: {watched_count}, Reviews: {reviews_count}")
                
            except Exception as e:
                print(f"✗ Error updating {movie.title}: {str(e)}")
                errors_count += 1
        
        # Commit all changes
        print(f"\nCommitting changes to database...")
        db.session.commit()
        print(f"✓ Successfully updated {updated_count} movies")
        if errors_count > 0:
            print(f"✗ Encountered {errors_count} errors")
        
        print("\n" + "=" * 60)
        print("Recalculation Complete!")
        print("=" * 60)

if __name__ == '__main__':
    recalculate_all_stats()
