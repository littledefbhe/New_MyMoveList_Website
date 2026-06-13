import os
import sys
import numpy as np
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import MultiLabelBinarizer

# Add the current directory to the Python path
sys.path.insert(0, os.path.abspath('.'))

class KNNRecommender:
    """
    KNN-based movie recommendation system.
    
    Flow:
    1. User Input: User selects favorite genres and movie types
    2. User Preferences: Stored as tags in user_tag_preferences table
    3. KNN Model: Compares user preferences to movie tags
    4. Movie Database: Movies with their tags
    5. Recommendations: Returns movies matching user preferences
    """
    
    def __init__(self):
        self.mlb = MultiLabelBinarizer()
        self.knn_model = NearestNeighbors(n_neighbors=10, metric='jaccard')
        self.tag_to_index = {}
        self.index_to_tag = {}
        self.movie_features = None
        self.movie_ids = []
        self.is_fitted = False
    
    def fit(self):
        """Train the KNN model on existing movie tags."""
        print("Training KNN model on movie tags...")
        
        from board import create_app
        from board.models import Movie, Tag
        
        app = create_app()
        with app.app_context():
            # Get all movies with their tags
            movies = Movie.query.all()
            
            # Get all unique tags
            all_tags = Tag.query.order_by(Tag.name).all()
            self.tag_to_index = {tag.id: idx for idx, tag in enumerate(all_tags)}
            self.index_to_tag = {idx: tag.id for idx, tag in enumerate(all_tags)}
            
            # Create feature matrix
            movie_tag_lists = []
            self.movie_ids = []
            
            for movie in movies:
                # Get tag IDs for this movie
                tag_ids = [tag.id for tag in movie.tags]
                movie_tag_lists.append(tag_ids)
                self.movie_ids.append(movie.id)
            
            # Transform tag lists to binary feature matrix
            self.movie_features = self.mlb.fit_transform(movie_tag_lists)
            
            # Train KNN model
            self.knn_model.fit(self.movie_features)
            self.is_fitted = True
            
            print(f"✓ KNN model trained on {len(movies)} movies with {len(all_tags)} unique tags")
    
    def get_recommendations(self, user_preferences, n=10):
        """
        Get movie recommendations based on user preferences.
        
        Args:
            user_preferences: List of tag IDs that user prefers
            n: Number of recommendations to return
        
        Returns:
            List of movie IDs recommended for the user
        """
        if not self.is_fitted:
            self.fit()
        
        # Transform user preferences to feature vector
        user_features = self.mlb.transform([user_preferences])
        
        # Find nearest neighbors
        distances, indices = self.knn_model.kneighbors(user_features, n_neighbors=n)
        
        # Get movie IDs of recommendations
        recommended_movie_ids = [self.movie_ids[idx] for idx in indices[0]]
        
        return recommended_movie_ids
    
    def get_user_recommendations(self, user_id, n=10):
        """
        Get movie recommendations for a specific user based on their tag preferences.
        
        Args:
            user_id: User ID
            n: Number of recommendations to return
        
        Returns:
            List of movie objects recommended for the user
        """
        from board import create_app
        from board.models import Movie, User
        
        app = create_app()
        with app.app_context():
            # Get user's preferred tags
            user = User.query.get(user_id)
            if not user:
                return []
            
            preferred_tags = [tag.id for tag in user.preferred_tags.all()]
            
            if not preferred_tags:
                # If user has no preferences, return top-rated movies
                return Movie.query.order_by(Movie.rating.desc()).limit(n).all()
            
            # Get recommendations based on preferences
            recommended_movie_ids = self.get_recommendations(preferred_tags, n)
            
            # Get movie objects
            recommended_movies = Movie.query.filter(Movie.id.in_(recommended_movie_ids)).all()
            
            # Sort by recommendation order
            movie_order = {movie_id: idx for idx, movie_id in enumerate(recommended_movie_ids)}
            recommended_movies.sort(key=lambda x: movie_order.get(x.id, float('inf')))
            
            return recommended_movies[:n]

# Global recommender instance
recommender = KNNRecommender()

def get_user_recommendations(user_id, n=10):
    """Get recommendations for a user."""
    return recommender.get_user_recommendations(user_id, n)

if __name__ == '__main__':
    # Test the recommender
    print("Testing KNN Recommender...")
    
    # Fit the model
    recommender.fit()
    
    # Test with some sample preferences (Action, Adventure, Sci-Fi tags)
    from board import create_app
    from board.models import Tag, Movie
    
    app = create_app()
    with app.app_context():
        # Get some tag IDs for testing
        action_tag = Tag.query.filter_by(name='Action').first()
        adventure_tag = Tag.query.filter_by(name='Adventure').first()
        sci_fi_tag = Tag.query.filter_by(name='Sci-Fi').first()
        
        if action_tag and adventure_tag and sci_fi_tag:
            test_preferences = [action_tag.id, adventure_tag.id, sci_fi_tag.id]
            print(f"\nTest preferences: Action, Adventure, Sci-Fi")
            
            recommendations = recommender.get_recommendations(test_preferences, n=5)
            print(f"\nRecommended movie IDs: {recommendations}")
            
            # Get movie details
            movies = Movie.query.filter(Movie.id.in_(recommendations)).all()
            print("\nRecommended movies:")
            for movie in movies:
                tags = [tag.name for tag in movie.tags]
                print(f"  - {movie.title} ({movie.release_year}) - Tags: {', '.join(tags[:5])}")
