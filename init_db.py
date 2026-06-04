import os
import sys

# Add the current directory to the Python path
sys.path.insert(0, os.path.abspath('.'))

from board import create_app, db
from board.models import User

app = create_app()

with app.app_context():
    # This will create all database tables
    db.create_all()
    print("Database tables created successfully!!")