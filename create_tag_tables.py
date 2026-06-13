import os
import sys

# Add the current directory to the Python path
sys.path.insert(0, os.path.abspath('.'))

from board import create_app, db
from board.models import Tag

def create_tag_tables():
    """Create the new tag tables in the database."""
    print("=" * 60)
    print("Create Tag Tables")
    print("=" * 60)
    
    # Initialize Flask app
    print("\n[Step 1] Connecting to database...")
    app = create_app()
    
    with app.app_context():
        print("\n[Step 2] Creating tag tables...")
        try:
            # Create all tables (including new ones)
            db.create_all()
            print("✓ Created tag tables successfully")
        except Exception as e:
            print(f"✗ Error creating tables: {e}")
            return
        
        print("\n" + "=" * 60)
        print("Table Creation Complete!")
        print("=" * 60)

if __name__ == '__main__':
    create_tag_tables()
