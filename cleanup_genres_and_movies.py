import os
import sys
import pandas as pd

# Add the current directory to the Python path
sys.path.insert(0, os.path.abspath('.'))

from board import create_app, db
from board.models import Movie, Genre, MovieStats, movie_genres
from sqlalchemy import text

def cleanup_genres_and_movies():
    """
    Comprehensive cleanup:
    1. Remove old movies not from Netflix
    2. Merge duplicate genres
    3. Remove orphaned genres
    """
    print("=" * 60)
    print("Comprehensive Genre and Movie Cleanup")
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
        
        # Delete old movies
        if len(movies_to_delete) > 0:
            print(f"\n[Step 4] Deleting {len(movies_to_delete)} old movies...")
            
            deleted_count = 0
            for movie in movies_to_delete:
                # Delete associated stats
                if movie.stats:
                    db.session.delete(movie.stats)
                
                # Delete the movie
                db.session.delete(movie)
                deleted_count += 1
                
                if deleted_count % 10 == 0:
                    print(f"  Deleted {deleted_count} movies...")
            
            db.session.commit()
            print(f"✓ Deleted {deleted_count} old movies")
        else:
            print("\n[Step 4] No old movies to delete")
        
        # Now merge duplicate genres
        print("\n[Step 5] Merging duplicate genres...")
        
        # Define genre mappings (singular -> plural/standard form)
        genre_mappings = {
            'Action': 'Action & Adventure',
            'Adventure': 'Action & Adventure',
            'Comedy': 'Comedies',
            'Drama': 'Dramas',
            'Sci-Fi': 'Sci-Fi & Fantasy',
            'Thriller': 'Thrillers',
            'Romance': 'Romantic Movies',
            'Crime': 'Crime TV Shows',
            'Horror': 'Horror Movies',
            'Mystery': 'TV Mysteries',
            'Music': 'Music & Musicals',
            'History': 'International Movies',
            'War': 'International Movies',
            'Western': 'International Movies',
            'Biography': 'International Movies',
            'Faith': 'Faith & Spirituality',
            'Kids': 'Kids\' TV',
            'Reality': 'Reality TV',
            'Sports': 'Sports Movies',
            'Anime': 'Anime Features',
            'Classic': 'Classic Movies',
            'Cult': 'Cult Movies',
            'Independent': 'Independent Movies',
            'LGBTQ': 'LGBTQ Movies',
            'Stand-Up': 'Stand-Up Comedy',
            'Science': 'Science & Nature TV',
            'Spanish': 'Spanish-Language TV Shows',
            'Teen': 'Teen TV Shows',
            'British': 'British TV Shows',
            'Korean': 'Korean TV Shows',
        }
        
        merged_count = 0
        for old_name, new_name in genre_mappings.items():
            # Find the old genre
            old_genre = Genre.query.filter_by(name=old_name).first()
            new_genre = Genre.query.filter_by(name=new_name).first()
            
            if old_genre and new_genre:
                # Get all movies with the old genre
                old_movie_ids = db.session.execute(
                    db.select(movie_genres.c.movie_id).where(movie_genres.c.genre_id == old_genre.id)
                ).scalars().all()
                
                # Reassign to new genre
                for movie_id in old_movie_ids:
                    # Check if movie already has the new genre
                    existing = db.session.execute(
                        db.select(movie_genres).where(
                            movie_genres.c.movie_id == movie_id,
                            movie_genres.c.genre_id == new_genre.id
                        )
                    ).first()
                    
                    if not existing:
                        # Add new genre association
                        db.session.execute(
                            movie_genres.insert().values(movie_id=movie_id, genre_id=new_genre.id)
                        )
                
                # Delete old genre associations
                db.session.execute(
                    movie_genres.delete().where(movie_genres.c.genre_id == old_genre.id)
                )
                
                # Delete the old genre
                db.session.delete(old_genre)
                merged_count += 1
                print(f"  Merged '{old_name}' -> '{new_name}'")
        
        db.session.commit()
        print(f"✓ Merged {merged_count} genre pairs")
        
        # Clean up orphaned genres (genres with no movies)
        print("\n[Step 6] Cleaning up orphaned genres...")
        orphaned_genres = db.session.execute(
            text("""
                SELECT id, name FROM genres 
                WHERE id NOT IN (SELECT DISTINCT genre_id FROM movie_genres)
            """)
        ).fetchall()
        
        if orphaned_genres:
            print(f"  Found {len(orphaned_genres)} orphaned genres:")
            for genre_id, genre_name in orphaned_genres:
                print(f"    - {genre_name}")
                db.session.execute(text(f"DELETE FROM genres WHERE id = {genre_id}"))
            db.session.commit()
            print(f"✓ Deleted {len(orphaned_genres)} orphaned genres")
        else:
            print("  No orphaned genres found")
        
        # Final summary
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
    cleanup_genres_and_movies()
