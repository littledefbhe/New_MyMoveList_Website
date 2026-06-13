from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user, login_user, logout_user
from urllib.parse import urlparse as url_parse
from .models import db, User, Movie, Genre, MovieStats, Tag, watched, movie_genres, movie_tags
from .forms import LoginForm, RegistrationForm
from sqlalchemy import or_
from sqlalchemy.orm import joinedload
from thefuzz import fuzz

# Create a blueprint named "pages"
bp = Blueprint("pages", __name__)

# Define routes using the blueprint
@bp.route("/")
def home():
    # Use no_autoflush to prevent premature flushes
    with db.session.no_autoflush:
        # Get all genres that have at least one movie
        genres = db.session.query(Genre)\
            .join(movie_genres, Genre.id == movie_genres.c.genre_id)\
            .group_by(Genre.id)\
            .order_by(Genre.name)\
            .all()
        
        if not genres:
            return render_template("index.html", movies_by_genre={}, personalized_movies=[])
        
        # Get all movie stats in one query
        stats_map = {stat.movie_id: stat for stat in db.session.query(MovieStats).all()}
        
        # Get all movie-genre relationships
        genre_movies = {}
        for mg in db.session.query(movie_genres).all():
            if mg.genre_id not in genre_movies:
                genre_movies[mg.genre_id] = []
            genre_movies[mg.genre_id].append(mg.movie_id)
        
        movies_by_genre = {}
        
        # Process each genre
        for genre in genres:
            if genre.id not in genre_movies:
                continue
                
            # Get top 5 movies for this genre using ORM
            movies = db.session.query(Movie)\
                .filter(Movie.id.in_(genre_movies[genre.id]))\
                .order_by(db.desc(Movie.rating))\
                .limit(5)\
                .all()
            
            # Attach stats to movies
            for movie in movies:
                movie.stats = stats_map.get(movie.id)
                
            if movies:
                movies_by_genre[genre] = movies
        
        # Get personalized recommendations if user is authenticated
        personalized_movies = []
        if current_user.is_authenticated:
            try:
                import knn_recommender
                personalized_movies = knn_recommender.recommender.get_library_based_recommendations(current_user.id, n=10)
                
                # Attach stats to personalized movies
                for movie in personalized_movies:
                    movie.stats = stats_map.get(movie.id)
            except Exception as e:
                print(f"Error getting personalized recommendations: {str(e)}")
                personalized_movies = []
    
    return render_template("index.html", movies_by_genre=movies_by_genre, personalized_movies=personalized_movies)

@bp.route('/genre/<int:genre_id>')
def genre_movies(genre_id):
    # Get the genre by ID or return 404 if not found
    genre = Genre.query.get_or_404(genre_id)
    
    # Get all movies in this genre, ordered by rating (highest first)
    movies = Movie.query\
        .join(Movie.genres)\
        .filter(Genre.id == genre_id)\
        .options(joinedload(Movie.stats))\
        .order_by(Movie.rating.desc())\
        .all()
    
    return render_template(
        'genre_movies.html',
        genre=genre,
        movies=movies,
        title=f"{genre.name} Movies"
    )

@bp.route('/search', methods=['GET'])
def search():
    query = request.args.get('q', '').strip()
    
    # Get filter parameters
    selected_genres = request.args.getlist('genre')
    selected_movie_types = request.args.getlist('movie_type')
    
    # Get all available genres and movie types for filters
    all_genres = Tag.query.filter_by(tag_type='genre').order_by(Tag.name).distinct().all()
    all_movie_types = Tag.query.filter_by(tag_type='movie_type').order_by(Tag.name).distinct().all()
    
    # Build base query
    movies_query = Movie.query
    
    # Apply genre filters
    if selected_genres:
        genre_tag_ids = [int(g) for g in selected_genres if g.isdigit()]
        if genre_tag_ids:
            movies_query = movies_query.filter(
                Movie.id.in_(
                    db.session.query(movie_tags.c.movie_id)
                    .filter(movie_tags.c.tag_id.in_(genre_tag_ids))
                )
            )
    
    # Apply movie type filters
    if selected_movie_types:
        movie_type_tag_ids = [int(t) for t in selected_movie_types if t.isdigit()]
        if movie_type_tag_ids:
            movies_query = movies_query.filter(
                Movie.id.in_(
                    db.session.query(movie_tags.c.movie_id)
                    .filter(movie_tags.c.tag_id.in_(movie_type_tag_ids))
                )
            )
    
    # Apply search query if provided (only if no filters are applied, or combine with filters)
    if query:
        search_term = f'%{query}%'
        movies_query = movies_query.filter(
            or_(
                Movie.title.ilike(search_term),
                db.and_(
                    Movie.overview.isnot(None),
                    Movie.overview.ilike(search_term)
                ),
                Movie.id.in_(
                    db.session.query(movie_tags.c.movie_id)
                    .join(Tag, Tag.id == movie_tags.c.tag_id)
                    .filter(Tag.name.ilike(search_term))
                )
            )
        )
    
    # Execute query
    movies = movies_query.distinct().order_by(Movie.rating.desc()).all()
    
    # If exact search returns few results and no filters are applied, try fuzzy matching
    if query and len(movies) < 5 and not selected_genres and not selected_movie_types:
        all_movies = Movie.query.limit(500).all()
        
        fuzzy_matches = []
        for movie in all_movies:
            title_score = fuzz.partial_ratio(query.lower(), movie.title.lower())
            tag_score = 0
            for tag in movie.tags:
                tag_score = max(tag_score, fuzz.partial_ratio(query.lower(), tag.name.lower()))
            
            best_score = max(title_score, tag_score)
            
            if best_score >= 70:
                fuzzy_matches.append((movie, best_score))
        
        fuzzy_matches.sort(key=lambda x: x[1], reverse=True)
        fuzzy_movies = [m[0] for m in fuzzy_matches[:20]]
        
        existing_ids = {m.id for m in movies}
        for movie in fuzzy_movies:
            if movie.id not in existing_ids:
                movies.append(movie)
                existing_ids.add(movie.id)
    
    return render_template(
        'search_results.html',
        query=query,
        movies=movies,
        all_genres=all_genres,
        all_movie_types=all_movie_types,
        selected_genres=selected_genres,
        selected_movie_types=selected_movie_types,
        title=f'Search: {query}' if query else 'Browse Movies'
    )

@bp.route('/movie/<int:movie_id>')
def movie_detail(movie_id):
    # Get the movie by ID or return 404 if not found
    movie = Movie.query.options(
        joinedload(Movie.stats)
    ).get_or_404(movie_id)
    
    # Check if movie is in user's watchlist (only for authenticated users)
    in_watchlist = current_user.is_in_watchlist(movie) if current_user.is_authenticated else False
    
    # Get similar movies (movies that share at least one genre, excluding the current movie)
    similar_movies = []
    if movie.genres:
        # Get the first 3 genre IDs for this movie
        genre_ids = [genre.id for genre in movie.genres][:3]
        
        # Find other movies that share these genres
        similar_movies = Movie.query\
            .join(Movie.genres)\
            .filter(
                Movie.id != movie_id,
                Genre.id.in_(genre_ids)
            )\
            .options(joinedload(Movie.stats))\
            .distinct()\
            .order_by(Movie.rating.desc())\
            .limit(4)\
            .all()
    
    # If we don't have enough similar movies, get some random popular movies
    if len(similar_movies) < 4:
        # Get additional random popular movies to fill the gap
        additional_count = 4 - len(similar_movies)
        additional_movies = Movie.query\
            .options(joinedload(Movie.stats))\
            .filter(Movie.id != movie_id)\
            .order_by(db.func.random())\
            .limit(additional_count)\
            .all()
        
        # Add to similar movies, avoiding duplicates
        existing_ids = {m.id for m in similar_movies}
        for m in additional_movies:
            if m.id not in existing_ids:
                similar_movies.append(m)
                existing_ids.add(m.id)
                if len(similar_movies) >= 4:
                    break
    
    return render_template(
        'movie_detail.html',
        movie=movie,
        similar_movies=similar_movies,
        in_watchlist=in_watchlist,
        title=f"{movie.title} ({movie.release_year})" if movie.release_year else movie.title
    )

@bp.route('/signin', methods=['GET', 'POST'])
def signin():
    if current_user.is_authenticated:
        return redirect(url_for('pages.home'))
        
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('pages.home'))
        flash('Invalid email or password', 'danger')
    return render_template('auth/signin.html', title='Sign In', form=form)

@bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('pages.home'))
        
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now registered!', 'success')
        return redirect(url_for('pages.signin'))
    return render_template('auth/signup.html', title='Sign Up', form=form)

@bp.route('/signout')
@login_required
def signout():
    logout_user()
    return redirect(url_for('pages.home'))

@bp.route('/top-movies')
def top_movies():
    # Get top 50 movies by rating, ordered highest to lowest
    top_movies = Movie.query\
        .options(joinedload(Movie.stats))\
        .filter(Movie.rating.isnot(None))\
        .order_by(Movie.rating.desc())\
        .limit(50)\
        .all()
    
    # Add watchlist status for each movie (only for authenticated users)
    for movie in top_movies:
        movie.in_watchlist = current_user.is_in_watchlist(movie) if current_user.is_authenticated else False
    
    return render_template(
        'top_movies.html',
        movies=top_movies,
        title='Top Movies by IMDB Rating'
    )

@bp.route('/my-library')
@login_required
def my_library():
    # Get all movies in the user's watchlist, ordered by title
    watchlist_movies = current_user.watchlist\
        .options(joinedload(Movie.stats))\
        .order_by(Movie.title)\
        .all()
    
    # Get watched and favorited movies
    watched_movies = current_user.watched_movies\
        .options(joinedload(Movie.stats))\
        .order_by(Movie.title)\
        .all()
    
    favorite_movies = current_user.favorite_movies\
        .options(joinedload(Movie.stats))\
        .order_by(Movie.title)\
        .all()
    
    # Combine all movies and remove duplicates
    all_movies = {}
    for movie in watchlist_movies + watched_movies + favorite_movies:
        all_movies[movie.id] = movie
    all_movies = list(all_movies.values())
    all_movies.sort(key=lambda x: x.title)
    
    return render_template(
        'library.html',
        all_movies=all_movies,
        watchlist_movies=watchlist_movies,
        watched_movies=watched_movies,
        favorite_movies=favorite_movies,
        title='My Library',
        total_movies=len(all_movies),
        watchlist_count=len(watchlist_movies),
        watched_count=len(watched_movies),
        favorites_count=len(favorite_movies)
    )

@bp.route('/api/watchlist/toggle', methods=['POST'])
@login_required
def toggle_watchlist():
    try:
        data = request.get_json()
        movie_id = data.get('movie_id')
        
        if not movie_id:
            return jsonify({'error': 'Movie ID is required'}), 400
            
        movie = Movie.query.get(movie_id)
        if not movie:
            return jsonify({'error': 'Movie not found'}), 404
            
        # Toggle watchlist status
        in_watchlist = current_user.is_in_watchlist(movie)
        
        if in_watchlist:
            current_user.remove_from_watchlist(movie)
            status = 'removed from'
            button_text = 'Add to Watchlist'
        else:
            current_user.add_to_watchlist(movie)
            status = 'added to'
            button_text = 'Remove from Watchlist'
        
        db.session.commit()
        
        # Get updated watchlist count for the movie
        watchlist_count = movie.stats.watchlist_count if movie.stats and hasattr(movie.stats, 'watchlist_count') else 0
        
        return jsonify({
            'status': status,
            'button_text': button_text,
            'watchlist_count': watchlist_count,
            'movie_id': movie_id
        })
        
    except Exception as e:
        print(f"Error toggling watchlist: {str(e)}")
        return jsonify({'error': 'An error occurred while updating your watchlist'}), 500


@bp.route('/api/favorites/toggle', methods=['POST'])
@login_required
def toggle_favorite():
    try:
        data = request.get_json()
        movie_id = data.get('movie_id')
        
        if not movie_id:
            return jsonify({'error': 'Movie ID is required'}), 400
            
        movie = Movie.query.get(movie_id)
        if not movie:
            return jsonify({'error': 'Movie not found'}), 404
            
        # Toggle favorite status
        is_favorite = current_user.is_favorite(movie)
        
        if is_favorite:
            current_user.remove_from_favorites(movie)
            status = 'removed from'
            button_text = 'Add to Favorites'
        else:
            current_user.add_to_favorites(movie)
            status = 'added to'
            button_text = 'Remove from Favorites'
        
        db.session.commit()
        
        # Get updated favorites count for the movie
        favorites_count = movie.stats.favorites_count if movie.stats and hasattr(movie.stats, 'favorites_count') else 0
        
        return jsonify({
            'status': status,
            'button_text': button_text,
            'favorites_count': favorites_count,
            'movie_id': movie_id
        })
        
    except Exception as e:
        print(f"Error toggling favorite: {str(e)}")
        return jsonify({'error': 'An error occurred while updating your favorites'}), 500


@bp.route('/api/user/movie-statuses')
@login_required
def get_user_movie_statuses():
    """Get the current user's watchlist, favorites, and watched movie IDs"""
    try:
        watchlist_ids = [movie.id for movie in current_user.watchlist.all()]
        favorite_ids = [movie.id for movie in current_user.favorite_movies.all()]
        watched_ids = [movie.id for movie in current_user.watched_movies.all()]
        
        return jsonify({
            'success': True,
            'watchlist': watchlist_ids,
            'favorites': favorite_ids,
            'watched': watched_ids
        })
    except Exception as e:
        print(f"Error getting user movie statuses: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to get user movie statuses'}), 500

@bp.route('/api/movie/remove', methods=['POST'])
@login_required
def remove_movie():
    try:
        data = request.get_json()
        movie_id = data.get('movie_id')
        
        if not movie_id:
            return jsonify({'error': 'Movie ID is required'}), 400
            
        movie = Movie.query.get(movie_id)
        if not movie:
            return jsonify({'error': 'Movie not found'}), 404
            
        # Remove from all lists
        removed = False
        if current_user.is_in_watchlist(movie):
            current_user.remove_from_watchlist(movie)
            removed = True
            
        if current_user.is_favorite(movie):
            current_user.favorite_movies.remove(movie)
            removed = True
            
        if current_user.has_watched(movie):
            current_user.watched_movies.remove(movie)
            removed = True
            
        if removed:
            db.session.commit()
            return jsonify({
                'success': True,
                'message': 'Movie removed from your library'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Movie not found in any of your lists'
            }), 404
            
    except Exception as e:
        print(f"Error removing movie: {str(e)}")
        return jsonify({'error': 'An error occurred while removing the movie'}), 500


@bp.route('/api/watched/toggle', methods=['POST'])
@login_required
def toggle_watched():
    try:
        data = request.get_json()
        movie_id = data.get('movie_id')
        
        if not movie_id:
            return jsonify({'error': 'Movie ID is required'}), 400
            
        movie = Movie.query.get(movie_id)
        if not movie:
            return jsonify({'error': 'Movie not found'}), 404
            
        # Toggle watched status
        has_watched = current_user.has_watched(movie)
        
        if has_watched:
            current_user.unmark_as_watched(movie)
            status = 'marked as not watched'
            button_text = 'Mark as Watched'
        else:
            current_user.mark_as_watched(movie)
            status = 'marked as watched'
            button_text = 'Watched'
        
        db.session.commit()
        
        # Get updated watched count for the movie
        watched_count = movie.stats.watched_count if movie.stats and hasattr(movie.stats, 'watched_count') else 0
        
        return jsonify({
            'status': status,
            'button_text': button_text,
            'watched_count': watched_count,
            'movie_id': movie_id,
            'is_watched': not has_watched  # Return the new state
        })
        
    except Exception as e:
        print(f"Error toggling watched status: {str(e)}")
        return jsonify({'error': 'An error occurred while updating watched status'}), 500

@bp.route('/profile')
@bp.route('/profile/<int:user_id>')
def profile(user_id=None):
    # If no user_id is provided and user is authenticated, show their own profile
    if user_id is None:
        if current_user.is_authenticated:
            return redirect(url_for('pages.profile', user_id=current_user.id))
        else:
            return redirect(url_for('pages.signin', next=request.url))
    
    # Get the user whose profile we're viewing
    user = User.query.get_or_404(user_id)
    is_own_profile = current_user.is_authenticated and (current_user.id == user_id)
    
    # Get user's movie stats
    stats = {
        'watchlist_count': user.watchlist.count(),
        'watched_count': user.watched_movies.count(),
        'favorites_count': user.favorite_movies.count()
    }
    
    # Get recently watched movies (last 6)
    recent_movies = db.session.query(Movie)\
        .join(watched, Movie.id == watched.c.movie_id)\
        .filter(watched.c.user_id == user_id)\
        .order_by(watched.c.watched_at.desc())\
        .limit(6)\
        .all()
    
    # Get all watched movies for the user, ordered by watch date (newest first)
    watched_movies = db.session.query(Movie)\
        .join(watched, Movie.id == watched.c.movie_id)\
        .filter(watched.c.user_id == user_id)\
        .order_by(watched.c.watched_at.desc())\
        .all()
    
    return render_template(
        'profile.html',
        user=user,
        stats=stats,
        recent_movies=recent_movies,
        watched_movies=watched_movies,
        is_own_profile=is_own_profile
    )

@bp.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    try:
        # Update username if changed
        new_username = request.form.get('username')
        if new_username and new_username != current_user.username:
            # Check if username is already taken
            existing_user = User.query.filter_by(username=new_username).first()
            if existing_user and existing_user.id != current_user.id:
                flash('Username already taken. Please choose another one.', 'danger')
                return redirect(url_for('pages.profile'))
            current_user.username = new_username
        
        # Update email if changed
        new_email = request.form.get('email')
        if new_email and new_email != current_user.email:
            # Check if email is already in use
            existing_email = User.query.filter_by(email=new_email).first()
            if existing_email and existing_email.id != current_user.id:
                flash('Email already in use. Please use another email.', 'danger')
                return redirect(url_for('pages.profile'))
            current_user.email = new_email
        
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while updating your profile. Please try again.', 'danger')
        print(f"Error updating profile: {str(e)}")
    
    return redirect(url_for('pages.profile'))

@bp.route('/community')
def community():
    """Community page showing user profiles and activity"""
    # Get all active users, ordered by most recently active
    users = User.query.filter_by(is_active=True)\
                    .order_by(User.last_login.desc())\
                    .limit(50).all()  # Limit to 50 most recent users
    
    # Add stats to each user
    for user in users:
        user.stats = {
            'watchlist_count': user.watchlist.count(),
            'watched_count': user.watched_movies.count(),
            'favorites_count': user.favorite_movies.count()
        }
    
    return render_template('community.html', users=users)

@bp.route('/api/recommendations')
@login_required
def get_recommendations():
    """Get personalized movie recommendations for the current user using KNN."""
    try:
        import knn_recommender
        n = request.args.get('n', 20, type=int)
        recommendations = knn_recommender.get_user_recommendations(current_user.id, n)
        
        # Format recommendations for JSON response
        rec_data = []
        for movie in recommendations:
            rec_data.append({
                'id': movie.id,
                'title': movie.title,
                'release_year': movie.release_year,
                'rating': movie.rating,
                'poster_url': movie.poster_url,
                'tags': [tag.name for tag in movie.tags]
            })
        
        return jsonify({
            'success': True,
            'recommendations': rec_data
        })
    except Exception as e:
        print(f"Error getting recommendations: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to get recommendations'
        }), 500

@bp.route('/api/preferences', methods=['POST'])
@login_required
def update_preferences():
    """Update user's tag preferences."""
    try:
        data = request.get_json()
        tag_ids = data.get('tag_ids', [])
        
        # Clear existing preferences by removing each one
        for tag in list(current_user.preferred_tags.all()):
            current_user.remove_tag_preference(tag)
        
        # Add new preferences
        for tag_id in tag_ids:
            tag = Tag.query.get(tag_id)
            if tag:
                current_user.add_tag_preference(tag)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Preferences updated successfully'
        })
    except Exception as e:
        print(f"Error updating preferences: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Failed to update preferences'
        }), 500

@bp.route('/api/preferences', methods=['GET'])
@login_required
def get_preferences():
    """Get user's current tag preferences."""
    try:
        preferences = current_user.preferred_tags.all()
        pref_data = [{
            'id': tag.id,
            'name': tag.name,
            'tag_type': tag.tag_type
        } for tag in preferences]
        
        return jsonify({
            'success': True,
            'preferences': pref_data
        })
    except Exception as e:
        print(f"Error getting preferences: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to get preferences'
        }), 500

@bp.route('/preferences')
@login_required
def preferences():
    """Preferences page for users to select their favorite genres and movie types."""
    all_genres = Tag.query.filter_by(tag_type='genre').order_by(Tag.name).all()
    all_movie_types = Tag.query.filter_by(tag_type='movie_type').order_by(Tag.name).all()
    
    # Get user's current preferences
    user_preferences = current_user.preferred_tags.all()
    selected_tag_ids = {tag.id for tag in user_preferences}
    
    return render_template(
        'preferences.html',
        all_genres=all_genres,
        all_movie_types=all_movie_types,
        selected_tag_ids=selected_tag_ids,
        title='My Preferences'
    )
