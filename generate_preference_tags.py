import os
import sys
import pandas as pd

# Add the current directory to the Python path
sys.path.insert(0, os.path.abspath('.'))

from board import create_app, db
from board.models import Movie, Tag, movie_tags

def generate_preference_tags():
    """
    Generate tags for movies based on Netflix data.
    Tags are focused on genres and movie types for user preference matching.
    """
    print("=" * 60)
    print("Generate Preference Tags (Genres + Movie Types)")
    print("=" * 60)
    
    # Load Netflix data
    print("\n[Step 1] Loading netflix_titles.csv...")
    try:
        netflix_df = pd.read_csv('netflix_titles.csv')
        print(f"✓ Loaded {len(netflix_df)} titles from Netflix")
    except Exception as e:
        print(f"✗ Error loading CSV: {e}")
        return
    
    # Create a dictionary mapping (title, year) to Netflix data
    netflix_data = {}
    for idx, row in netflix_df.iterrows():
        title = row['title']
        year = row['release_year']
        netflix_data[(title, int(year))] = row
    
    print(f"✓ Created mapping for {len(netflix_data)} titles")
    
    # Initialize Flask app
    print("\n[Step 2] Connecting to database...")
    app = create_app()
    
    with app.app_context():
        # Clear existing tags
        print("\n[Step 3] Clearing existing tags...")
        Tag.query.delete()
        db.session.execute(movie_tags.delete())
        db.session.commit()
        print("✓ Cleared existing tags")
        
        # Get all movies
        movies = Movie.query.all()
        print(f"\n[Step 4] Processing {len(movies)} movies...")
        
        tag_stats = {'genre': set(), 'movie_type': set()}
        total_tags_added = 0
        
        for idx, movie in enumerate(movies):
            key = (movie.title, movie.release_year)
            
            if key not in netflix_data:
                continue
            
            netflix_row = netflix_data[key]
            movie_tags_list = []
            
            # 1. Add Netflix genres as genre tags
            if pd.notna(netflix_row['listed_in']):
                genres = [g.strip() for g in netflix_row['listed_in'].split(',')]
                for genre in genres:
                    # Clean up genre name for consistency
                    clean_genre = genre.strip()
                    movie_tags_list.append(('genre', clean_genre))
                    tag_stats['genre'].add(clean_genre)
            
            # 2. Add movie type as movie_type tag
            if pd.notna(netflix_row['type']):
                movie_type = netflix_row['type'].strip()
                movie_tags_list.append(('movie_type', movie_type))
                tag_stats['movie_type'].add(movie_type)
            
            # Create tags and associate with movie
            for tag_type, tag_name in movie_tags_list:
                # Get or create tag
                tag = Tag.query.filter_by(name=tag_name, tag_type=tag_type).first()
                if not tag:
                    tag = Tag(name=tag_name, tag_type=tag_type)
                    db.session.add(tag)
                    db.session.flush()
                
                # Associate tag with movie
                if tag not in movie.tags.all():
                    movie.tags.append(tag)
                    total_tags_added += 1
            
            # Progress update
            if (idx + 1) % 1000 == 0:
                print(f"  Processed {idx + 1}/{len(movies)} movies...")
        
        # Commit all changes
        print("\n[Step 5] Saving tags to database...")
        db.session.commit()
        print(f"✓ Added {total_tags_added} tag associations")
        
        # Show tag statistics
        print("\n[Step 6] Tag Statistics:")
        print("-" * 60)
        print(f"Genre tags: {len(tag_stats['genre'])} unique genres")
        for genre in sorted(tag_stats['genre']):
            print(f"  - {genre}")
        
        print(f"\nMovie type tags: {len(tag_stats['movie_type'])} unique types")
        for movie_type in sorted(tag_stats['movie_type']):
            print(f"  - {movie_type}")
        
        # Total unique tags
        total_unique_tags = Tag.query.count()
        print(f"\nTotal unique tags: {total_unique_tags}")
        
        # Show sample movies with tags
        print("\n[Step 7] Sample movies with tags:")
        sample_movies = Movie.query.limit(3).all()
        for movie in sample_movies:
            tags = movie.tags.all()
            tag_names = [f"{t.name} ({t.tag_type})" for t in tags]
            print(f"  {movie.title}: {', '.join(tag_names)}")
        
        print("\n" + "=" * 60)
        print("Tag Generation Complete!")
        print("=" * 60)
        print("\nThese tags align with your ML model:")
        print("- Users can select favorite genres and movie types")
        print("- Movies are tagged with genres and movie types")
        print("- KNN model will match user preferences to movie tags")

if __name__ == '__main__':
    generate_preference_tags()
