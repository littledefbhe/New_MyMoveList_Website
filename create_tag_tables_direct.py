import os
import sys

# Add the current directory to the Python path
sys.path.insert(0, os.path.abspath('.'))

from board import create_app, db
from board.models import Tag
from sqlalchemy import text

def create_tag_tables():
    """Create the new tag tables using direct SQL."""
    print("=" * 60)
    print("Create Tag Tables (Direct SQL)")
    print("=" * 60)
    
    # Initialize Flask app
    print("\n[Step 1] Connecting to database...")
    app = create_app()
    
    with app.app_context():
        print("\n[Step 2] Creating tag tables...")
        try:
            # Create tags table
            db.session.execute(text("""
                CREATE TABLE IF NOT EXISTS tags (
                    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(100) NOT NULL,
                    tag_type VARCHAR(50) NOT NULL,
                    UNIQUE (name, tag_type)
                )
            """))
            
            # Create movie_tags association table
            db.session.execute(text("""
                CREATE TABLE IF NOT EXISTS movie_tags (
                    movie_id INTEGER NOT NULL,
                    tag_id INTEGER NOT NULL,
                    PRIMARY KEY (movie_id, tag_id),
                    FOREIGN KEY (movie_id) REFERENCES movies (id),
                    FOREIGN KEY (tag_id) REFERENCES tags (id)
                )
            """))
            
            # Create user_tag_preferences association table
            db.session.execute(text("""
                CREATE TABLE IF NOT EXISTS user_tag_preferences (
                    user_id INTEGER NOT NULL,
                    tag_id INTEGER NOT NULL,
                    PRIMARY KEY (user_id, tag_id),
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    FOREIGN KEY (tag_id) REFERENCES tags (id)
                )
            """))
            
            db.session.commit()
            print("✓ Created tag tables successfully")
        except Exception as e:
            print(f"✗ Error creating tables: {e}")
            db.session.rollback()
            return
        
        print("\n" + "=" * 60)
        print("Table Creation Complete!")
        print("=" * 60)

if __name__ == '__main__':
    create_tag_tables()
