import os
import sys
import pandas as pd
import requests
import time

# Add the current directory to the Python path
sys.path.insert(0, os.path.abspath('.'))

from board import create_app, db
from board.models import Movie

# TMDB API (free, no signup required for basic usage)
TMDB_BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w500"
# You can get a free API key at https://www.themoviedb.org/settings/api
TMDB_API_KEY = "8bf1d9bf0f43dcf73c7f196807c387dc"  # Replace with your key

def get_poster_from_tmdb(title, year, media_type="movie"):
    """
    Fetch poster URL from TMDB API.
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
            poster_path = data['results'][0].get('poster_path')
            if poster_path:
                return f"{TMDB_IMAGE_BASE}{poster_path}"
        return None
    except:
        return None

def update_posters():
    """
    Update poster URLs for all movies from netflix_titles.csv
    """
    print("=" * 60)
    print("Netflix Poster Updater")
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
    if TMDB_API_KEY == "YOUR_TMDB_API_KEY_HERE":
        print("\n✗ Please set your TMDB API key in this script")
        print("  Get free key at: https://www.themoviedb.org/settings/api")
        return
    
    # Initialize Flask app
    print("\n[Step 2] Connecting to database...")
    app = create_app()
    
    with app.app_context():
        # Get all movies from database
        movies = Movie.query.all()
        print(f"✓ Found {len(movies)} movies in database")
        
        # Create a mapping of title -> poster_url from Netflix data
        print("\n[Step 3] Fetching posters from TMDB...")
        print("This will take some time due to API rate limits...")
        print("-" * 60)
        
        updated_count = 0
        not_found_count = 0
        
        for idx, netflix_row in netflix_df.iterrows():
            title = netflix_row['title']
            year = netflix_row['release_year']
            media_type = "movie" if netflix_row['type'] == "Movie" else "tv"
            
            # Fetch poster from TMDB
            poster_url = get_poster_from_tmdb(title, year, media_type)
            
            if poster_url:
                # Find matching movie in database
                matching_movies = Movie.query.filter(
                    Movie.title == title,
                    Movie.release_year == year
                ).all()
                
                if matching_movies:
                    for movie in matching_movies:
                        if not movie.poster_url:  # Only update if no poster exists
                            movie.poster_url = poster_url
                            updated_count += 1
                            print(f"✓ Updated poster for: {title} ({year})")
                
                # Rate limiting (TMDB allows ~40 requests per 10 seconds)
                if (idx + 1) % 40 == 0:
                    time.sleep(1)
            else:
                not_found_count += 1
                if not_found_count <= 10:  # Show first 10 not found
                    print(f"✗ Poster not found: {title} ({year})")
        
        # Commit changes
        print("\n[Step 4] Saving to database...")
        db.session.commit()
        print(f"✓ Updated {updated_count} movie posters")
        print(f"✗ Could not find posters for {not_found_count} titles")
        
        print("\n" + "=" * 60)
        print("Update Complete!")
        print("=" * 60)

if __name__ == '__main__':
    print("\n📝 INSTRUCTIONS:")
    print("1. Get free TMDB API key: https://www.themoviedb.org/settings/api")
    print("2. Replace 'YOUR_TMDB_API_KEY_HERE' in this script")
    print("3. Run: python3 update_netflix_posters.py")
    print("4. Script will automatically fetch and update all posters")
    print("\n" + "=" * 60)
    update_posters()
