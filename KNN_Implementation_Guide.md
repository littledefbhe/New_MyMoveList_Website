# KNN Model Implementation Guide for MyMovieList

## Overview

This guide outlines how to implement a K-Nearest Neighbors (KNN) model using scikit-learn for the MyMovieList application. KNN is ideal for this project because:

- **Movie Recommendations:** Find similar movies based on features (genre, rating, year, etc.)
- **User Collaborative Filtering:** Recommend movies based on similar users' preferences
- **Simple & Interpretable:** Easy to explain how recommendations work
- **No Training Required:** Lazy learning algorithm - computes on the fly
- **Works Well with Small-Medium Datasets:** Suitable for movie databases

---

## Data Structure Requirements

### Expected CSV Data Format

Your fake CSV data should contain the following columns:

```csv
movie_id,title,release_year,rating,runtime_minutes,genre1,genre2,genre3,watchlist_count,favorites_count,watched_count
1,The Shawshank Redemption,1994,9.3,142,Drama,Crime,,12500,8900,15000
2,The Godfather,1972,9.2,175,Crime,Drama,,11000,8200,14000
...
```

### Feature Engineering

**Numeric Features:**
- `release_year` - Normalize to 0-1 range
- `rating` - Already in good range (0-10)
- `runtime_minutes` - Normalize to 0-1 range
- `watchlist_count` - Log transform to handle skew
- `favorites_count` - Log transform to handle skew
- `watched_count` - Log transform to handle skew

**Categorical Features:**
- `genre1`, `genre2`, `genre3` - One-hot encode all unique genres

---

## Implementation Steps

### Step 1: Install Dependencies

Add to `requirements.txt`:
```
scikit-learn==1.3.0
pandas==2.0.3
numpy==1.24.3
joblib==1.3.1
```

Install:
```bash
pip install -r requirements.txt
```

### Step 2: Data Preparation Script

Create `prepare_movie_data.py`:

```python
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
import pickle
import os

def prepare_movie_features(csv_path='movies_data.csv'):
    """
    Load and preprocess movie data for KNN model.
    
    Args:
        csv_path: Path to CSV file containing movie data
        
    Returns:
        X: Feature matrix ready for KNN
        movie_ids: List of movie IDs in same order as features
        feature_names: List of feature column names
    """
    # Load data
    df = pd.read_csv(csv_path)
    
    # Handle missing values
    df = df.fillna({
        'rating': df['rating'].median(),
        'runtime_minutes': df['runtime_minutes'].median(),
        'watchlist_count': 0,
        'favorites_count': 0,
        'watched_count': 0
    })
    
    # Log transform count features to handle skew
    df['watchlist_count'] = np.log1p(df['watchlist_count'])
    df['favorites_count'] = np.log1p(df['favorites_count'])
    df['watched_count'] = np.log1p(df['watched_count'])
    
    # Combine genre columns into list
    genre_columns = ['genre1', 'genre2', 'genre3']
    df['genres'] = df[genre_columns].values.tolist()
    df['genres'] = df['genres'].apply(lambda x: [g for g in x if pd.notna(g)])
    
    # Define numeric features
    numeric_features = ['release_year', 'rating', 'runtime_minutes', 
                       'watchlist_count', 'favorites_count', 'watched_count']
    
    # Define categorical features
    categorical_features = ['genres']
    
    # Create preprocessing pipeline
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', StandardScaler(), numeric_features),
            ('cat', OneHotEncoder(handle_unknown='ignore'), categorical_features)
        ]
    )
    
    # Fit and transform
    X = preprocessor.fit_transform(df)
    
    # Save movie IDs and preprocessor
    movie_ids = df['movie_id'].values
    
    # Save preprocessor for later use
    with open('movie_preprocessor.pkl', 'wb') as f:
        pickle.dump(preprocessor, f)
    
    # Save feature names
    feature_names = preprocessor.get_feature_names_out()
    
    return X, movie_ids, feature_names

if __name__ == '__main__':
    X, movie_ids, feature_names = prepare_movie_features()
    print(f"Feature matrix shape: {X.shape}")
    print(f"Number of movies: {len(movie_ids)}")
    print(f"Number of features: {len(feature_names)}")
    
    # Save processed data
    np.save('movie_features.npy', X)
    np.save('movie_ids.npy', movie_ids)
    print("Data prepared and saved successfully!")
```

### Step 3: Train KNN Model

Create `train_knn_model.py`:

```python
import numpy as np
from sklearn.neighbors import NearestNeighbors
import pickle
import joblib

def train_knn_model(n_neighbors=10, algorithm='auto'):
    """
    Train KNN model for movie recommendations.
    
    Args:
        n_neighbors: Number of neighbors to find
        algorithm: Algorithm to use ('auto', 'ball_tree', 'kd_tree', 'brute')
        
    Returns:
        model: Trained KNN model
    """
    # Load prepared features
    X = np.load('movie_features.npy')
    movie_ids = np.load('movie_ids.npy')
    
    # Train KNN model
    # Using NearestNeighbors for recommendation (unsupervised)
    model = NearestNeighbors(
        n_neighbors=n_neighbors,
        algorithm=algorithm,
        metric='cosine',  # Cosine similarity works well for recommendations
        n_jobs=-1
    )
    
    model.fit(X)
    
    # Save model
    joblib.dump(model, 'movie_knn_model.pkl')
    
    # Save movie IDs mapping
    with open('movie_id_mapping.pkl', 'wb') as f:
        pickle.dump(movie_ids, f)
    
    print(f"KNN model trained with {n_neighbors} neighbors")
    print(f"Model saved to movie_knn_model.pkl")
    
    return model

if __name__ == '__main__':
    model = train_knn_model(n_neighbors=10)
    print("Model training complete!")
```

### Step 4: Create Prediction Service

Create `board/recommendation_service.py`:

```python
import numpy as np
import joblib
import pickle
import pandas as pd
from sqlalchemy.orm import joinedload
from .models import Movie, db

class MovieRecommendationService:
    """
    Service for movie recommendations using KNN model.
    """
    
    def __init__(self):
        """Load the trained KNN model and preprocessor."""
        try:
            self.model = joblib.load('movie_knn_model.pkl')
            self.preprocessor = pickle.load(open('movie_preprocessor.pkl', 'rb'))
            self.movie_ids = pickle.load(open('movie_id_mapping.pkl', 'rb'))
            self.movie_id_to_index = {mid: idx for idx, mid in enumerate(self.movie_ids)}
            self.loaded = True
        except Exception as e:
            print(f"Error loading model: {e}")
            self.loaded = False
    
    def get_similar_movies(self, movie_id, n=5):
        """
        Get similar movies based on KNN.
        
        Args:
            movie_id: ID of the reference movie
            n: Number of similar movies to return
            
        Returns:
            List of similar Movie objects
        """
        if not self.loaded:
            return []
        
        try:
            # Get index of the movie
            if movie_id not in self.movie_id_to_index:
                return []
            
            movie_index = self.movie_id_to_index[movie_id]
            
            # Load features
            X = np.load('movie_features.npy')
            
            # Find nearest neighbors
            distances, indices = self.model.kneighbors(
                X[movie_index].reshape(1, -1),
                n_neighbors=n+1  # +1 to exclude the movie itself
            )
            
            # Get neighbor movie IDs (exclude the movie itself)
            neighbor_indices = indices[0][1:]  # Skip first (itself)
            neighbor_movie_ids = [self.movie_ids[idx] for idx in neighbor_indices]
            
            # Fetch movie objects from database
            movies = Movie.query.filter(
                Movie.id.in_(neighbor_movie_ids)
            ).options(joinedload(Movie.stats)).all()
            
            # Sort by similarity (closer = more similar)
            movie_distance_map = {mid: dist for mid, dist in zip(neighbor_movie_ids, distances[0][1:])}
            movies.sort(key=lambda m: movie_distance_map.get(m.id, float('inf')))
            
            return movies
            
        except Exception as e:
            print(f"Error getting similar movies: {e}")
            return []
    
    def recommend_for_user(self, user_id, n=5):
        """
        Recommend movies based on user's watchlist/favorites.
        
        Args:
            user_id: ID of the user
            n: Number of recommendations to return
            
        Returns:
            List of recommended Movie objects
        """
        if not self.loaded:
            return []
        
        try:
            from .models import User
            
            # Get user's favorite/watched movies
            user = User.query.get(user_id)
            if not user:
                return []
            
            # Get user's favorite movies
            favorite_movies = user.favorite_movies.limit(5).all()
            
            if not favorite_movies:
                # If no favorites, return top-rated movies
                return Movie.query.options(joinedload(Movie.stats))\
                    .filter(Movie.rating.isnot(None))\
                    .order_by(Movie.rating.desc())\
                    .limit(n)\
                    .all()
            
            # Get similar movies for each favorite
            recommendations = []
            seen_ids = {m.id for m in favorite_movies}
            
            for movie in favorite_movies:
                similar = self.get_similar_movies(movie.id, n=n)
                for sim_movie in similar:
                    if sim_movie.id not in seen_ids:
                        recommendations.append(sim_movie)
                        seen_ids.add(sim_movie.id)
                        if len(recommendations) >= n:
                            break
                if len(recommendations) >= n:
                    break
            
            return recommendations[:n]
            
        except Exception as e:
            print(f"Error recommending for user: {e}")
            return []

# Create singleton instance
recommendation_service = MovieRecommendationService()
```

### Step 5: Integrate with Flask Routes

Add to `board/pages.py`:

```python
from .recommendation_service import recommendation_service

@bp.route('/movie/<int:movie_id>/similar')
def similar_movies(movie_id):
    """Get similar movies using KNN recommendation."""
    movie = Movie.query.get_or_404(movie_id)
    
    # Get similar movies
    similar_movies = recommendation_service.get_similar_movies(movie_id, n=6)
    
    return render_template(
        'similar_movies.html',
        movie=movie,
        similar_movies=similar_movies,
        title=f"Movies Similar to {movie.title}"
    )

@bp.route('/recommendations')
@login_required
def recommendations():
    """Get personalized recommendations for current user."""
    recommendations = recommendation_service.recommend_for_user(
        current_user.id,
        n=10
    )
    
    return render_template(
        'recommendations.html',
        recommendations=recommendations,
        title='Recommended for You'
    )
```

### Step 6: Create UI Templates

Create `board/templates/recommendations.html`:

```html
{% extends "base.html" %}

{% block title %}{{ title }}{% endblock %}

{% block content %}
<div class="container mt-4">
    <h1 class="mb-4">Recommended for You</h1>
    
    {% if recommendations %}
    <div class="row">
        {% for movie in recommendations %}
        <div class="col-md-3 col-sm-6 mb-4">
            <div class="card movie-card">
                <img src="{{ movie.poster_url }}" class="card-img-top" alt="{{ movie.title }}">
                <div class="card-body">
                    <h5 class="card-title">{{ movie.title }}</h5>
                    <p class="card-text">{{ movie.release_year }}</p>
                    <p class="card-text">
                        <strong>Rating:</strong> {{ movie.rating }}/10
                    </p>
                    <a href="{{ url_for('pages.movie_detail', movie_id=movie.id) }}" 
                       class="btn btn-outline-light btn-sm">View Details</a>
                </div>
            </div>
        </div>
        {% endfor %}
    </div>
    {% else %}
    <div class="alert alert-info">
        <h4>No recommendations yet</h4>
        <p>Add some movies to your favorites to get personalized recommendations!</p>
        <a href="{{ url_for('pages.top_movies') }}" class="btn btn-primary">Browse Movies</a>
    </div>
    {% endif %}
</div>
{% endblock %}
```

---

## Model Evaluation

### Evaluation Metrics

```python
def evaluate_model():
    """
    Evaluate KNN model performance.
    """
    # Load test data (split your CSV into train/test)
    # For recommendations, use:
    # - Precision@K: How many recommended movies are relevant?
    # - Recall@K: How many relevant movies were recommended?
    # - Coverage: Percentage of movies that can be recommended
    
    # Simple manual test
    test_movie_id = 1  # The Shawshank Redemption
    similar = recommendation_service.get_similar_movies(test_movie_id, n=5)
    
    print(f"Movies similar to movie {test_movie_id}:")
    for movie in similar:
        print(f"- {movie.title} ({movie.release_year}): {movie.rating}")
```

### Hyperparameter Tuning

Test different values for:
- **n_neighbors**: 5, 10, 15, 20 (more neighbors = more diverse recommendations)
- **metric**: 'cosine', 'euclidean', 'manhattan' (cosine works best for recommendations)
- **algorithm**: 'auto', 'ball_tree', 'kd_tree' (auto is usually best)

---

## Integration with Database

### Option 1: Export from Database to CSV

Create `export_movies_to_csv.py`:

```python
from board import create_app, db
from board.models import Movie, Genre, movie_genres
import pandas as pd

def export_movies():
    """Export movies from database to CSV for training."""
    app = create_app()
    
    with app.app_context():
        # Query all movies with stats
        movies = Movie.query.options(
            db.joinedload(Movie.stats)
        ).all()
        
        # Prepare data
        data = []
        for movie in movies:
            # Get genres
            genres = [g.name for g in movie.genres.all()]
            
            row = {
                'movie_id': movie.id,
                'title': movie.title,
                'release_year': movie.release_year,
                'rating': movie.rating or 0,
                'runtime_minutes': movie.runtime_minutes or 0,
                'genre1': genres[0] if len(genres) > 0 else None,
                'genre2': genres[1] if len(genres) > 1 else None,
                'genre3': genres[2] if len(genres) > 2 else None,
                'watchlist_count': movie.stats.watchlist_count if movie.stats else 0,
                'favorites_count': movie.stats.favorites_count if movie.stats else 0,
                'watched_count': movie.stats.watched_count if movie.stats else 0,
            }
            data.append(row)
        
        # Create DataFrame and save
        df = pd.DataFrame(data)
        df.to_csv('movies_data.csv', index=False)
        print(f"Exported {len(df)} movies to movies_data.csv")

if __name__ == '__main__':
    export_movies()
```

### Option 2: Train Directly from Database

Modify `prepare_movie_data.py` to query directly from SQLAlchemy instead of CSV.

---

## Usage Workflow

1. **Export Data:** Run `export_movies_to_csv.py` to get movies from database
2. **Prepare Features:** Run `prepare_movie_data.py` to process the CSV
3. **Train Model:** Run `train_knn_model.py` to train KNN
4. **Integrate:** Add routes and templates to Flask app
5. **Test:** Access `/recommendations` route to see recommendations

---

## Advantages of KNN for This Project

✅ **No Training Time**: Lazy learning - computes on the fly
✅ **Easy to Explain**: "Users who liked X also liked Y"
✅ **Works with Existing Data**: Uses movie features already in database
✅ **Personalized**: Can recommend based on user's favorites
✅ **Scalable**: For small-medium datasets (<10,000 movies)
✅ **Cold-Start Solution**: Can recommend based on movie features alone

---

## Potential Improvements

- **Hybrid Approach**: Combine KNN with content-based filtering
- **User-Based KNN**: Find similar users instead of similar movies
- **Weighted Features**: Give more importance to rating vs. genre
- **Dynamic K**: Adjust number of neighbors based on movie popularity
- **Cache Results**: Cache recommendations to improve performance
