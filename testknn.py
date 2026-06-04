import pandas as pd
import numpy as np
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
import pickle

print("=" * 60)
print("KNN Movie Recommendation Test")
print("=" * 60)

# Step 1: Load data
print("\n[Step 1] Loading movie data from CSV...")
try:
    df = pd.read_csv('movies_data.csv')
    print(f"✓ Loaded {len(df)} movies")
except FileNotFoundError:
    print("✗ Error: movies_data.csv not found. Run export_movies.py first.")
    exit(1)

# Step 2: Handle missing values
print("\n[Step 2] Handling missing values...")
df = df.fillna({
    'rating': df['rating'].median(),
    'runtime_minutes': df['runtime_minutes'].median(),
    'watchlist_count': 0,
    'favorites_count': 0,
    'watched_count': 0,
    'genre1': 'Unknown',
    'genre2': 'Unknown',
    'genre3': 'Unknown'
})
print(f"✓ Missing values filled")

# Step 3: Feature engineering
print("\n[Step 3] Engineering features...")

# Log transform count features to handle skew
df['watchlist_count'] = np.log1p(df['watchlist_count'])
df['favorites_count'] = np.log1p(df['favorites_count'])
df['watched_count'] = np.log1p(df['watched_count'])
print(f"✓ Applied log transform to count features")

# Define features - use individual genre columns instead of combined list
numeric_features = ['release_year', 'rating', 'runtime_minutes', 
                   'watchlist_count', 'favorites_count', 'watched_count']
categorical_features = ['genre1', 'genre2', 'genre3']

print(f"Numeric features: {numeric_features}")
print(f"Categorical features: {categorical_features}")

# Step 4: Create preprocessing pipeline
print("\n[Step 4] Creating preprocessing pipeline...")
preprocessor = ColumnTransformer(
    transformers=[
        ('num', StandardScaler(), numeric_features),
        ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), categorical_features)
    ]
)

# Fit and transform
X = preprocessor.fit_transform(df)
print(f"✓ Feature matrix shape: {X.shape}")

# Save preprocessor
with open('movie_preprocessor.pkl', 'wb') as f:
    pickle.dump(preprocessor, f)
print(f"✓ Saved preprocessor to movie_preprocessor.pkl")

# Save movie IDs
movie_ids = df['movie_id'].values
np.save('movie_ids.npy', movie_ids)
print(f"✓ Saved movie IDs to movie_ids.npy")

# Save feature matrix
np.save('movie_features.npy', X)
print(f"✓ Saved feature matrix to movie_features.npy")

# Step 5: Train KNN model
print("\n[Step 5] Training KNN model...")
n_neighbors = 5
model = NearestNeighbors(
    n_neighbors=n_neighbors,
    algorithm='auto',
    metric='cosine',
    n_jobs=-1
)

model.fit(X)
print(f"✓ KNN model trained with {n_neighbors} neighbors")

# Save model
import joblib
joblib.dump(model, 'movie_knn_model.pkl')
print(f"✓ Saved model to movie_knn_model.pkl")

# Step 6: Test the model
print("\n[Step 6] Testing model with sample recommendations...")
print("=" * 60)

# Test with first few movies
test_movies = df.head(3)

for idx, row in test_movies.iterrows():
    movie_id = row['movie_id']
    movie_title = row['title']
    movie_rating = row['rating']
    
    print(f"\n📽️  Reference Movie: {movie_title} ({row['release_year']}) - Rating: {movie_rating}")
    print("-" * 60)
    
    # Get index of the movie
    movie_index = idx
    
    # Find nearest neighbors
    distances, indices = model.kneighbors(
        X[movie_index].reshape(1, -1),
        n_neighbors=n_neighbors + 1
    )
    
    # Get neighbor movie IDs (exclude the movie itself)
    neighbor_indices = indices[0][1:]  # Skip first (itself)
    neighbor_distances = distances[0][1:]
    
    print(f"Top {n_neighbors} similar movies:")
    for i, (neighbor_idx, distance) in enumerate(zip(neighbor_indices, neighbor_distances), 1):
        neighbor_movie = df.iloc[neighbor_idx]
        similarity_score = (1 - distance) * 100  # Convert cosine distance to similarity %
        print(f"  {i}. {neighbor_movie['title']} ({neighbor_movie['release_year']})")
        print(f"     Rating: {neighbor_movie['rating']} | Similarity: {similarity_score:.1f}%")

# Step 7: Summary
print("\n" + "=" * 60)
print("✓ KNN Model Test Complete!")
print("=" * 60)
print(f"\nModel Statistics:")
print(f"  - Total movies: {len(df)}")
print(f"  - Feature dimensions: {X.shape[1]}")
print(f"  - Number of neighbors: {n_neighbors}")
print(f"  - Distance metric: cosine")
print(f"\nGenerated Files:")
print(f"  - movies_data.csv (raw data)")
print(f"  - movie_features.npy (processed features)")
print(f"  - movie_ids.npy (movie ID mapping)")
print(f"  - movie_preprocessor.pkl (preprocessing pipeline)")
print(f"  - movie_knn_model.pkl (trained model)")
print("\nReady to integrate with Flask application!")
print("=" * 60)
