#!/usr/bin/env python3
"""
Script to migrate the movie_stats table schema from ratings_count to average_rating.
"""

import sys
import os

# Add the current directory to the Python path
sys.path.insert(0, os.path.abspath('.'))

from board import create_app, db
from board.models import Movie, MovieStats

def migrate_movie_stats():
    """Migrate movie_stats table schema."""
    print("=" * 60)
    print("Movie Stats Schema Migration")
    print("=" * 60)
    
    app = create_app()
    
    with app.app_context():
        # Drop the existing movie_stats table
        print("Dropping existing movie_stats table...")
        db.session.execute(db.text("DROP TABLE IF EXISTS movie_stats"))
        db.session.commit()
        print("✓ Dropped movie_stats table")
        
        # Recreate the table with the new schema
        print("Recreating movie_stats table with new schema...")
        db.create_all()
        print("✓ Recreated movie_stats table")
        
        print("\n" + "=" * 60)
        print("Migration Complete!")
        print("=" * 60)

if __name__ == '__main__':
    migrate_movie_stats()
