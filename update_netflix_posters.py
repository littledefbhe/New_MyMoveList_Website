import os
import sys
import pandas as pd
import requests
import time

# Add the current directory to the Python path #
sys.path.insert(0, os.path.abspath('.'))

from board import create_app, db
from board.models import Movie

# TMDB API (free, no signup required for basic usage)
TMDB_BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w500"
# You can get a free API key at https://www.themoviedb.org/settings/api
TMDB_API_KEY = os.environ.get('TMDB_API_KEY')

def get_poster_and_rating_from_tmdb(title, year, media_type="movie"):
    """
    Fetch poster URL and rating from TMDB API.
    Returns tuple (poster_url, rating) or (None, None) if not found.
    """
    try:
        search_url = f"{TMDB_BASE_URL}/search/{media_type}"
        params = {
            'api_key': TMDB_API_KEY,
            'query': title,
        }
        if year:
            params['year'] = year
        
        response = requests.get(search_url, params=params, timeout=10)
        data = response.json()
        
        if data['results']:
            result = data['results'][0]
            poster_path = result.get('poster_path')
            rating = result.get('vote_average')
            
            poster_url = f"{TMDB_IMAGE_BASE}{poster_path}" if poster_path else None
            # Convert TMDB rating (0-10) to IMDB-style (0-10)
            imdb_rating = float(rating) if rating else None
            
            return poster_url, imdb_rating
        return None, None
    except:
        return None, None

def update_posters():
    """
    Update poster URLs and ratings for all movies from netflix_titles.csv
    """
    print("=" * 60)
    print("Netflix Poster & Rating Updater")
    print("=" * 60)
    
    # Load Netflix data
    print("\n[Step 1] Loading netflix_titles.csv...")
    try:
        netflix_df = pd.read_csv('netflix_titles.csv')
        print(f"✓ Loaded {len(netflix_df)} titles from Netflix")
    except:
        print("✗ Error: netflix_titles.csv not found")
        return
    
    # Check API key
    if not TMDB_API_KEY:
        print("\n✗ Please set TMDB_API_KEY environment variable")
        print("  Get free key at: https://www.themoviedb.org/settings/api")
        print("  Set it with: export TMDB_API_KEY='your-key-here'")
        return
    
    # Initialize Flask app
    print("\n[Step 2] Connecting to database...")
    app = create_app()
    
    with app.app_context():
        # Get all movies from database
        movies = Movie.query.all()
        print(f"✓ Found {len(movies)} movies in database")
        
        # Create a mapping of title -> poster_url from Netflix data
        print("\n[Step 3] Fetching posters and ratings from TMDB...")
        print("This will take some time due to API rate limits...")
        print("-" * 60)
        
        updated_posters_count = 0
        updated_ratings_count = 0
        not_found_count = 0
        
        for idx, netflix_row in netflix_df.iterrows():
            title = netflix_row['title']
            year = netflix_row['release_year']
            media_type = "movie" if netflix_row['type'] == "Movie" else "tv"
            
            # Fetch poster and rating from TMDB
            poster_url, rating = get_poster_and_rating_from_tmdb(title, year, media_type)
            
            if poster_url or rating:
                # Find matching movie in database
                matching_movies = Movie.query.filter(
                    Movie.title == title,
                    Movie.release_year == year
                ).all()
                
                if matching_movies:
                    for movie in matching_movies:
                        updated = False
                        if poster_url and not movie.poster_url:
                            movie.poster_url = poster_url
                            updated_posters_count += 1
                            updated = True
                        if rating and not movie.rating:
                            movie.rating = rating
                            updated_ratings_count += 1
                            updated = True
                        
                        if updated:
                            print(f"✓ Updated: {title} ({year}) - Poster: {'Yes' if poster_url else 'No'}, Rating: {'Yes' if rating else 'No'}")
                
                # Rate limiting (TMDB allows ~40 requests per 10 seconds)
                if (idx + 1) % 40 == 0:
                    time.sleep(1)
            else:
                not_found_count += 1
                if not_found_count <= 10:  # Show first 10 not found
                    print(f"✗ Not found in TMDB: {title} ({year})")
        
        # Commit changes
        print("\n[Step 4] Saving to database...")
        db.session.commit()
        print(f"✓ Updated {updated_posters_count} movie posters")
        print(f"✓ Updated {updated_ratings_count} movie ratings")
        print(f"✗ Could not find data for {not_found_count} titles")
        
        print("\n" + "=" * 60)
        print("Update Complete!")
        print("=" * 60)

if __name__ == '__main__':
    print("\n📝 INSTRUCTIONS:")
    print("1. Get free TMDB API key: https://www.themoviedb.org/settings/api")
    print("2. Set environment variable: export TMDB_API_KEY='your-key-here'")
    print("3. Run: python3 update_netflix_posters.py")
    print("4. Script will automatically fetch and update all posters and ratings")
    print("\n" + "=" * 60)
    update_posters()
