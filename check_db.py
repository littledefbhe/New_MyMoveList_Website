from board import create_app, db
from board.models import Movie

def check_database():
    app = create_app()
    with app.app_context():
        # Check if we can connect to the database
        try:
            # Get count of movies
            movie_count = Movie.query.count()
            print(f"Found {movie_count} movies in the database")
            
            # Show first 5 movies
            print("\nFirst 5 movies:")
            for movie in Movie.query.limit(5).all():
                print(f"- {movie.title} ({movie.release_year}): Rating: {movie.rating}, Poster: {movie.poster_url}")
                
        except Exception as e:
            print(f"Error accessing database: {str(e)}")

if __name__ == '__main__':
    check_database()
