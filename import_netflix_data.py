import os
import sys
import pandas as pd

# Add the current directory to the Python path
sys.path.insert(0, os.path.abspath('.'))

from board import create_app, db
from board.models import Movie, Genre, MovieStats

def parse_duration(duration_str):
    """Parse duration string to minutes."""
    if pd.isna(duration_str):
        return None
    
    if 'min' in str(duration_str):
        try:
            return int(duration_str.split(' ')[0])
        except:
            return None
    elif 'Season' in str(duration_str):
        return None
    return None

def parse_genres(genre_str):
    """Parse comma-separated genres."""
    if pd.isna(genre_str):
        return []
    genres = [g.strip() for g in genre_str.split(',')]
    return genres

def import_netflix_data():
    """Import Netflix titles into the database."""
    print("=" * 60)
    print("Netflix Data Importer")
    print("=" * 60)
    
    # Load Netflix data
    print("\n[Step 1] Loading netflix_titles.csv...")
    try:
        netflix_df = pd.read_csv('netflix_titles.csv')
        print(f"✓ Loaded {len(netflix_df)} titles from Netflix")
    except Exception as e:
        print(f"✗ Error loading CSV: {e}")
        return
    
    # Initialize Flask app
    print("\n[Step 2] Connecting to database...")
    app = create_app()
    
    with app.app_context():
        # Count existing movies
        existing_count = Movie.query.count()
        print(f"✓ Current database has {existing_count} movies")
        
        # Import data
        print("\n[Step 3] Importing Netflix titles...")
        print("-" * 60)
        
        imported_count = 0
        skipped_count = 0
        genre_count = 0
        
        for idx, row in netflix_df.iterrows():
            title = row['title']
            year = row['release_year']
            
            # Check if movie already exists
            existing = Movie.query.filter(
                Movie.title == title,
                Movie.release_year == year
            ).first()
            
            if existing:
                skipped_count += 1
                if skipped_count <= 5:
                    print(f"⊘ Skipped (exists): {title} ({year})")
                continue
            
            # Parse data
            runtime = parse_duration(row['duration'])
            genres = parse_genres(row['listed_in'])
            content_rating = row['rating'] if pd.notna(row['rating']) else None
            
            # Create movie
            movie = Movie(
                title=title,
                release_year=int(year) if pd.notna(year) else None,
                rating=None,
                certification=content_rating,
                runtime_minutes=runtime,
                poster_url=None,
                overview=row['description'] if pd.notna(row['description']) else None
            )
            
            db.session.add(movie)
            db.session.flush()
            
            # Create stats
            stats = MovieStats(
                movie_id=movie.id,
                ratings_count=0,
                reviews_count=0,
                watchlist_count=0,
                favorites_count=0,
                watched_count=0
            )
            db.session.add(stats)
            
            # Handle genres
            for genre_name in genres:
                genre = Genre.query.filter_by(name=genre_name).first()
                if not genre:
                    genre = Genre(name=genre_name)
                    db.session.add(genre)
                    db.session.flush()
                
                if genre not in movie.genres.all():
                    movie.genres.append(genre)
                    genre_count += 1
            
            imported_count += 1
            
            if imported_count <= 10:
                print(f"✓ Imported: {title} ({year}) - {len(genres)} genres")
            elif imported_count == 11:
                print("... (importing continues)")
            
            # Commit every 100 movies
            if imported_count % 100 == 0:
                db.session.commit()
                print(f"✓ Committed batch (total: {imported_count})")
        
        # Final commit
        db.session.commit()
        
        # Summary
        print("\n" + "=" * 60)
        print("Import Complete!")
        print("=" * 60)
        print(f"Total titles in CSV: {len(netflix_df)}")
        print(f"Imported: {imported_count}")
        print(f"Skipped (already exists): {skipped_count}")
        print(f"Total genres added: {genre_count}")
        print(f"New database total: {Movie.query.count()} movies")
        print("=" * 60)

if __name__ == '__main__':
    import_netflix_data()
