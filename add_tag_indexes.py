import sqlite3

def add_tag_indexes():
    """Add indexes to tag tables for better performance."""
    print("=" * 60)
    print("Add Tag Table Indexes")
    print("=" * 60)
    
    # Connect to the database
    print("\n[Step 1] Connecting to database...")
    try:
        conn = sqlite3.connect('instance/movielist.db')
        cursor = conn.cursor()
        print("✓ Connected to database")
    except Exception as e:
        print(f"✗ Error connecting to database: {e}")
        return
    
    print("\n[Step 2] Adding indexes...")
    try:
        # Index on tags.name for faster tag searches
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tags_name ON tags(name)")
        print("✓ Created index on tags.name")
        
        # Index on tags.tag_type for filtering by type
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tags_type ON tags(tag_type)")
        print("✓ Created index on tags.tag_type")
        
        # Index on movie_tags.movie_id for faster movie lookups
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_movie_tags_movie_id ON movie_tags(movie_id)")
        print("✓ Created index on movie_tags.movie_id")
        
        # Index on movie_tags.tag_id for faster tag lookups
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_movie_tags_tag_id ON movie_tags(tag_id)")
        print("✓ Created index on movie_tags.tag_id")
        
        # Index on user_tag_preferences.user_id for faster user preference lookups
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_prefs_user_id ON user_tag_preferences(user_id)")
        print("✓ Created index on user_tag_preferences.user_id")
        
        # Index on user_tag_preferences.tag_id for faster tag lookups
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_prefs_tag_id ON user_tag_preferences(tag_id)")
        print("✓ Created index on user_tag_preferences.tag_id")
        
        # Index on movies.overview for faster description searches
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_movies_overview ON movies(overview)")
        print("✓ Created index on movies.overview")
        
        conn.commit()
        print("✓ All indexes created successfully")
    except Exception as e:
        print(f"✗ Error creating indexes: {e}")
        conn.rollback()
        conn.close()
        return
    
    conn.close()
    
    print("\n" + "=" * 60)
    print("Index Creation Complete!")
    print("=" * 60)

if __name__ == '__main__':
    add_tag_indexes()
