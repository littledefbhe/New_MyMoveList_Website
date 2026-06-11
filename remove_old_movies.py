import os
import sys
import pandas as pd

# Add the current directory to the Python path
sys.path.insert(0, os.path.abspath('.'))

from board import create_app, db
from board.models import Movie, Genre, MovieStats

def remove_old_movies():
    """
    Remove movies that were not imported from Netflix CSV.
    Only keeps movies that match title + year from netflix_titles.csv
    """
    print("=" * 60)
    print("Remove Old Movie Data")
    print("=" * 60)
    
    # Load Netflix data
    print("\n[Step 1] Loading netflix_titles.csv...")
    try:
        netflix_df = pd.read_csv('netflix_titles.csv')
        print(f"✓ Loaded {len(netflix_df)} titles from Netflix")
    except Exception as e:
        print(f"✗ Error loading CSV: {e}")
        return
    
    # Create a set of (title, year) tuples from Netflix data
    netflix_movies = set()
    for idx, row in netflix_df.iterrows():
        title = row['title']
        year = row['release_year']
        netflix_movies.add((title, int(year)))
    
    print(f"✓ Created reference set with {len(netflix_movies)} unique (title, year) pairs")
    
    # Initialize Flask app
    print("\n[Step 2] Connecting to database...")
    app = create_app()
    
    with app.app_context():
        # Get all movies from database
        all_movies = Movie.query.all()
        print(f"✓ Found {len(all_movies)} movies in database")
        
        # Identify movies to keep (from Netflix) and to delete (old data)
        movies_to_delete = []
        movies_to_keep = []
        
        for movie in all_movies:
            key = (movie.title, movie.release_year)
            if key in netflix_movies:
                movies_to_keep.append(movie)
            else:
                movies_to_delete.append(movie)
        
        print(f"\n[Step 3] Analysis:")
        print(f"  Movies to KEEP (from Netflix): {len(movies_to_keep)}")
        print(f"  Movies to DELETE (old data): {len(movies_to_delete)}")
        
        if len(movies_to_delete) == 0:
            print("\n✓ No old movies to remove. Database only contains Netflix data.")
            return
        
        # Show sample of movies to be deleted
        print(f"\n[Step 4] Sample of movies to be deleted (first 10):")
        for movie in movies_to_delete[:10]:
            print(f"  - {movie.title} ({movie.release_year})")
        
        if len(movies_to_delete) > 10:
            print(f"  ... and {len(movies_to_delete) - 10} more")
        
        # Confirm deletion
        print("\n" + "=" * 60)
        response = input("Do you want to proceed with deletion? (yes/no): ")
        
        if response.lower() != 'yes':
            print("✗ Deletion cancelled.")
            return
        
        # Delete movies
        print("\n[Step 5] Deleting old movies...")
        
        deleted_count = 0
        for movie in movies_to_delete:
            # Delete associated stats
            if movie.stats:
                db.session.delete(movie.stats)
            
            # Delete the movie (genres will be handled by cascade)
            db.session.delete(movie)
            deleted_count += 1
            
            if deleted_count % 100 == 0:
                print(f"  Deleted {deleted_count} movies...")
        
        # Commit changes
        print("\n[Step 6] Saving to database...")
        db.session.commit()
        
        print(f"\n✓ Successfully deleted {deleted_count} old movies")
        print(f"✓ Kept {len(movies_to_keep)} Netflix movies")
        
        # Clean up orphaned genres
        print("\n[Step 7] Cleaning up orphaned genres...")
        from sqlalchemy import text
        # Delete genres that are not associated with any movies
        db.session.execute(text("""
            DELETE FROM genres 
            WHERE id NOT IN (SELECT DISTINCT genre_id FROM movie_genres)
        """))
        db.session.commit()
        print("✓ Cleaned up orphaned genres")
        
        print("\n" + "=" * 60)
        print("Cleanup Complete!")
        print("=" * 60)
        print(f"New database total: {Movie.query.count()} movies")

if __name__ == '__main__':
    remove_old_movies()
