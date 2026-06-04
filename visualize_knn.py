import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.neighbors import NearestNeighbors
import joblib
import pickle

# Set style
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

print("=" * 70)
print("KNN Movie Recommendation Visualizer")
print("=" * 70)

# Load data
print("\n[Loading] Movie data...")
df = pd.read_csv('movies_data.csv')
print(f"✓ Loaded {len(df)} movies")

# Load model and preprocessor
print("\n[Loading] Trained KNN model...")
model = joblib.load('movie_knn_model.pkl')
preprocessor = pickle.load(open('movie_preprocessor.pkl', 'rb'))
X = np.load('movie_features.npy')
print("✓ Model and features loaded")

# Create figure with subplots
fig = plt.figure(figsize=(20, 12))
gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)

# 1. Genre Distribution
ax1 = fig.add_subplot(gs[0, 0])
genre_counts = df['genre1'].value_counts()
colors = plt.cm.Set3(range(len(genre_counts)))
ax1.bar(genre_counts.index, genre_counts.values, color=colors)
ax1.set_title('Genre Distribution', fontsize=14, fontweight='bold')
ax1.set_xlabel('Genre')
ax1.set_ylabel('Number of Movies')
ax1.tick_params(axis='x', rotation=45)
for i, v in enumerate(genre_counts.values):
    ax1.text(i, v + 0.5, str(v), ha='center', fontweight='bold')

# 2. Rating Distribution
ax2 = fig.add_subplot(gs[0, 1])
ax2.hist(df['rating'], bins=15, color='steelblue', edgecolor='black', alpha=0.7)
ax2.set_title('Rating Distribution', fontsize=14, fontweight='bold')
ax2.set_xlabel('Rating')
ax2.set_ylabel('Frequency')
ax2.axvline(df['rating'].mean(), color='red', linestyle='--', linewidth=2, label=f'Mean: {df["rating"].mean():.2f}')
ax2.legend()

# 3. Release Year Distribution
ax3 = fig.add_subplot(gs[0, 2])
ax3.hist(df['release_year'], bins=15, color='coral', edgecolor='black', alpha=0.7)
ax3.set_title('Release Year Distribution', fontsize=14, fontweight='bold')
ax3.set_xlabel('Year')
ax3.set_ylabel('Frequency')

# 4. Rating vs Release Year Scatter
ax4 = fig.add_subplot(gs[1, 0])
scatter = ax4.scatter(df['release_year'], df['rating'], 
                     c=df['rating'], cmap='RdYlGn', 
                     s=100, alpha=0.6, edgecolors='black')
ax4.set_title('Rating vs Release Year', fontsize=14, fontweight='bold')
ax4.set_xlabel('Release Year')
ax4.set_ylabel('Rating')
plt.colorbar(scatter, ax=ax4, label='Rating')

# 5. Top 10 Movies by Rating
ax5 = fig.add_subplot(gs[1, 1])
top_movies = df.nlargest(10, 'rating')
colors = plt.cm.RdYlGn(np.linspace(0.3, 1, 10))
ax5.barh(range(len(top_movies)), top_movies['rating'], color=colors)
ax5.set_yticks(range(len(top_movies)))
ax5.set_yticklabels(top_movies['title'], fontsize=8)
ax5.set_title('Top 10 Movies by Rating', fontsize=14, fontweight='bold')
ax5.set_xlabel('Rating')
ax5.invert_yaxis()

# 6. Movie Engagement (Watchlist Count - Log Transformed)
ax6 = fig.add_subplot(gs[1, 2])
ax6.scatter(df['rating'], np.log1p(df['watchlist_count']), 
           c=df['release_year'], cmap='viridis', 
           s=100, alpha=0.6, edgecolors='black')
ax6.set_title('Rating vs Watchlist Count (Log)', fontsize=14, fontweight='bold')
ax6.set_xlabel('Rating')
ax6.set_ylabel('Log Watchlist Count')
plt.colorbar(ax6.collections[0], ax=ax6, label='Year')

# 7. Sample KNN Recommendations - Movie 1
ax7 = fig.add_subplot(gs[2, 0])
test_movie_idx = 0
test_movie = df.iloc[test_movie_idx]
distances, indices = model.kneighbors(X[test_movie_idx].reshape(1, -1), n_neighbors=6)
neighbor_indices = indices[0][1:]  # Exclude self
neighbor_distances = distances[0][1:]

similar_movies = df.iloc[neighbor_indices]
similarity_scores = (1 - neighbor_distances) * 100

colors_rec = plt.cm.Greens(np.linspace(0.4, 1, 5))
ax7.barh(range(len(similar_movies)), similarity_scores, color=colors_rec)
ax7.set_yticks(range(len(similar_movies)))
ax7.set_yticklabels(similar_movies['title'], fontsize=8)
ax7.set_title(f'Similar to: {test_movie["title"][:30]}...', fontsize=12, fontweight='bold')
ax7.set_xlabel('Similarity Score (%)')
ax7.invert_yaxis()
for i, v in enumerate(similarity_scores):
    ax7.text(v + 1, i, f'{v:.1f}%', va='center', fontweight='bold')

# 8. Sample KNN Recommendations - Movie 2
ax8 = fig.add_subplot(gs[2, 1])
test_movie_idx = 1
test_movie = df.iloc[test_movie_idx]
distances, indices = model.kneighbors(X[test_movie_idx].reshape(1, -1), n_neighbors=6)
neighbor_indices = indices[0][1:]
neighbor_distances = distances[0][1:]

similar_movies = df.iloc[neighbor_indices]
similarity_scores = (1 - neighbor_distances) * 100

colors_rec = plt.cm.Blues(np.linspace(0.4, 1, 5))
ax8.barh(range(len(similar_movies)), similarity_scores, color=colors_rec)
ax8.set_yticks(range(len(similar_movies)))
ax8.set_yticklabels(similar_movies['title'], fontsize=8)
ax8.set_title(f'Similar to: {test_movie["title"][:30]}...', fontsize=12, fontweight='bold')
ax8.set_xlabel('Similarity Score (%)')
ax8.invert_yaxis()
for i, v in enumerate(similarity_scores):
    ax8.text(v + 1, i, f'{v:.1f}%', va='center', fontweight='bold')

# 9. Sample KNN Recommendations - Movie 3
ax9 = fig.add_subplot(gs[2, 2])
test_movie_idx = 2
test_movie = df.iloc[test_movie_idx]
distances, indices = model.kneighbors(X[test_movie_idx].reshape(1, -1), n_neighbors=6)
neighbor_indices = indices[0][1:]
neighbor_distances = distances[0][1:]

similar_movies = df.iloc[neighbor_indices]
similarity_scores = (1 - neighbor_distances) * 100

colors_rec = plt.cm.Purples(np.linspace(0.4, 1, 5))
ax9.barh(range(len(similar_movies)), similarity_scores, color=colors_rec)
ax9.set_yticks(range(len(similar_movies)))
ax9.set_yticklabels(similar_movies['title'], fontsize=8)
ax9.set_title(f'Similar to: {test_movie["title"][:30]}...', fontsize=12, fontweight='bold')
ax9.set_xlabel('Similarity Score (%)')
ax9.invert_yaxis()
for i, v in enumerate(similarity_scores):
    ax9.text(v + 1, i, f'{v:.1f}%', va='center', fontweight='bold')

# Main title
fig.suptitle('KNN Movie Recommendation System - Data Visualization', 
             fontsize=16, fontweight='bold', y=0.995)

# Save the figure
plt.savefig('knn_visualization.png', dpi=300, bbox_inches='tight')
print("\n✓ Visualization saved to 'knn_visualization.png'")

# Show the plot
plt.show()

print("\n" + "=" * 70)
print("Visualization Summary")
print("=" * 70)
print(f"Total Movies: {len(df)}")
print(f"Genre Categories: {len(genre_counts)}")
print(f"Rating Range: {df['rating'].min():.1f} - {df['rating'].max():.1f}")
print(f"Year Range: {df['release_year'].min()} - {df['release_year'].max()}")
print(f"Average Rating: {df['rating'].mean():.2f}")
print("=" * 70)
