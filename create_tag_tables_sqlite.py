import sqlite3

def create_tag_tables():
    """Create the new tag tables using direct SQLite connection."""
    print("=" * 60)
    print("Create Tag Tables (Direct SQLite)")
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
    
    print("\n[Step 2] Creating tag tables...")
    try:
        # Create tags table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tags (
                id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(100) NOT NULL,
                tag_type VARCHAR(50) NOT NULL,
                UNIQUE (name, tag_type)
            )
        """)
        print("✓ Created tags table")
        
        # Create movie_tags association table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS movie_tags (
                movie_id INTEGER NOT NULL,
                tag_id INTEGER NOT NULL,
                PRIMARY KEY (movie_id, tag_id),
                FOREIGN KEY (movie_id) REFERENCES movies (id),
                FOREIGN KEY (tag_id) REFERENCES tags (id)
            )
        """)
        print("✓ Created movie_tags table")
        
        # Create user_tag_preferences association table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_tag_preferences (
                user_id INTEGER NOT NULL,
                tag_id INTEGER NOT NULL,
                PRIMARY KEY (user_id, tag_id),
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (tag_id) REFERENCES tags (id)
            )
        """)
        print("✓ Created user_tag_preferences table")
        
        conn.commit()
        print("✓ All tables created successfully")
    except Exception as e:
        print(f"✗ Error creating tables: {e}")
        conn.rollback()
        conn.close()
        return
    
    conn.close()
    
    print("\n" + "=" * 60)
    print("Table Creation Complete!")
    print("=" * 60)

if __name__ == '__main__':
    create_tag_tables()
