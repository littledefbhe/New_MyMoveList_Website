import os
import sys

# Add the current directory to the Python path
sys.path.insert(0, os.path.abspath('.'))

from board import create_app
from knn_recommender import recommender

app = create_app()

with app.app_context():
    print("Fitting KNN model...")
    recommender.fit()
    print("KNN model fitted successfully!")
    print(f"Model can recommend from {len(recommender.movie_features)} movies")
