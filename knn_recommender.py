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
        self.knn_model = NearestNeighbors(n_neighbors=100, metric='jaccard')
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
    
    def get_recommendations(self, user_preferences, n=None):
        """
        Get movie recommendations based on user preferences.
        
        This approach finds movies that match ANY of the user's preferred genres,
        then ranks them by how many of their preferred genres they match,
        combined with IMDB rating and popularity.
        
        Args:
            user_preferences: List of tag IDs that user prefers
            n: Number of recommendations to return (None for unlimited)
        
        Returns:
            List of movie IDs recommended for the user
        """
        if not self.is_fitted:
            self.fit()
        
        from board import create_app, db
        from board.models import Movie, MovieStats
        
        app = create_app()
        with app.app_context():
            # Find all movies that have ANY of the user's preferred genres
            from board.models import movie_tags
            
            # Get movies that have at least one of the preferred tags
            matching_movies = db.session.query(movie_tags.c.movie_id)\
                .filter(movie_tags.c.tag_id.in_(user_preferences))\
                .distinct()\
                .all()
            
            movie_ids = [movie_id for movie_id, in matching_movies]
            
            if not movie_ids:
                return []
            
            # Get all movies with their tags, ratings, and stats
            movies = Movie.query.filter(Movie.id.in_(movie_ids)).all()
            
            # Get all movie stats for popularity
            stats_map = {stat.movie_id: stat for stat in MovieStats.query.all()}
            
            # Score each movie by combining multiple factors
            movie_scores = []
            for movie in movies:
                movie_tag_ids = [tag.id for tag in movie.tags]
                
                # 1. Tag matching score (0-1)
                matches = len(set(movie_tag_ids) & set(user_preferences))
                tag_score = matches / len(user_preferences) if user_preferences else 0
                
                # 2. Rating score (0-1, normalized to 0-10 scale)
                rating_score = (movie.rating / 10.0) if movie.rating else 0.5  # Default to 0.5 for unrated movies
                
                # 3. Popularity score (0-1, based on watched count)
                stats = stats_map.get(movie.id)
                popularity_score = 0.5  # Default to 0.5 for movies with no stats
                if stats and stats.watched_count:
                    # Normalize popularity (assuming 1000 watches is max for normalization)
                    popularity_score = min(stats.watched_count / 1000.0, 1.0)
                
                # Combined weighted score:
                # 50% tag matching, 30% rating, 20% popularity
                combined_score = (tag_score * 0.5) + (rating_score * 0.3) + (popularity_score * 0.2)
                
                movie_scores.append((movie.id, combined_score, tag_score, rating_score, popularity_score))
            
            # Sort by combined score (descending)
            movie_scores.sort(key=lambda x: x[1], reverse=True)
            
            # Return all or top n movie IDs
            if n is None:
                recommended_movie_ids = [movie_id for movie_id, _, _, _, _ in movie_scores]
            else:
                recommended_movie_ids = [movie_id for movie_id, _, _, _, _ in movie_scores[:n]]
            
            return recommended_movie_ids
    
    def get_user_recommendations(self, user_id, n=None):
        """
        Get movie recommendations for a specific user based on their tag preferences.
        
        Args:
            user_id: User ID
            n: Number of recommendations to return (None for unlimited)
        
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
                if n is None:
                    return Movie.query.order_by(Movie.rating.desc()).all()
                else:
                    return Movie.query.order_by(Movie.rating.desc()).limit(n).all()
            
            # Get recommendations based on preferences
            recommended_movie_ids = self.get_recommendations(preferred_tags, n)
            
            # Get movie objects
            recommended_movies = Movie.query.filter(Movie.id.in_(recommended_movie_ids)).all()
            
            # Sort by recommendation order
            movie_order = {movie_id: idx for idx, movie_id in enumerate(recommended_movie_ids)}
            recommended_movies.sort(key=lambda x: movie_order.get(x.id, float('inf')))
            
            if n is None:
                return recommended_movies
            else:
                return recommended_movies[:n]
    
    def get_library_based_recommendations(self, user_id, n=None):
        """
        Get movie recommendations based on user's library (watchlist, favorites, watched movies).
        
        This analyzes the user's library to infer their preferences and recommends similar movies.
        
        Args:
            user_id: User ID
            n: Number of recommendations to return (None for unlimited)
        
        Returns:
            List of movie objects recommended for the user
        """
        from board import create_app, db
        from board.models import Movie, User
        
        app = create_app()
        with app.app_context():
            # Get user
            user = User.query.get(user_id)
            if not user:
                return []
            
            # Get all movies from user's library
            library_movies = []
            library_movies.extend(user.watchlist.all())
            library_movies.extend(user.favorite_movies.all())
            library_movies.extend(user.watched_movies.all())
            
            # Remove duplicates
            library_movies = list(set(library_movies))
            
            if not library_movies:
                # If user has no library, return top-rated movies
                if n is None:
                    return Movie.query.order_by(Movie.rating.desc()).all()
                else:
                    return Movie.query.order_by(Movie.rating.desc()).limit(n).all()
            
            # Infer preferences from library movies by analyzing their tags
            tag_counts = {}
            for movie in library_movies:
                for tag in movie.tags:
                    tag_counts[tag.id] = tag_counts.get(tag.id, 0) + 1
            
            # Get top tags (most frequent in library)
            if not tag_counts:
                # If no tags found, return top-rated movies
                if n is None:
                    return Movie.query.order_by(Movie.rating.desc()).all()
                else:
                    return Movie.query.order_by(Movie.rating.desc()).limit(n).all()
            
            # Sort tags by frequency and get top 10
            sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
            inferred_preferences = [tag_id for tag_id, _ in sorted_tags[:10]]
            
            # Get recommendations based on inferred preferences
            recommended_movie_ids = self.get_recommendations(inferred_preferences, n)
            
            # Exclude movies already in library
            library_movie_ids = {movie.id for movie in library_movies}
            recommended_movie_ids = [mid for mid in recommended_movie_ids if mid not in library_movie_ids]
            
            if not recommended_movie_ids:
                # If no new recommendations, return top-rated movies not in library
                if n is None:
                    return Movie.query.filter(~Movie.id.in_(library_movie_ids))\
                        .order_by(Movie.rating.desc()).all()
                else:
                    return Movie.query.filter(~Movie.id.in_(library_movie_ids))\
                        .order_by(Movie.rating.desc()).limit(n).all()
            
            # Get movie objects
            recommended_movies = Movie.query.filter(Movie.id.in_(recommended_movie_ids)).all()
            
            # Sort by recommendation order
            movie_order = {movie_id: idx for idx, movie_id in enumerate(recommended_movie_ids)}
            recommended_movies.sort(key=lambda x: movie_order.get(x.id, float('inf')))
            
            if n is None:
                return recommended_movies
            else:
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
