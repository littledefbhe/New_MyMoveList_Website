# MyMoveList

A Flask-based movie tracking and recommendation web application with KNN-powered personalized suggestions.

## Features

- **User Authentication**: Sign up, login, logout with secure password hashing
- **Movie Browsing**: Browse movies by genre, search with filters
- **Personal Lists**: Add movies to watchlist, favorites, and mark as watched
- **Reviews & Ratings**: Write and edit movie reviews with star ratings
- **KNN Recommendations**: Personalized movie suggestions based on your preferences
- **Tag Preferences**: Customize recommendations by selecting preferred genres and movie types

## Access & Deployment

### Local Development

1. **Clone the repository:**
```bash
git clone https://github.com/littledefbhe/New_MyMoveList_Website.git
cd New_MyMoveList_Website
```

2. **Create virtual environment:**
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Set environment variables:**
```bash
export SECRET_KEY='your-secret-key-here'
export TMDB_API_KEY='your-tmdb-api-key-here'
export FLASK_ENV='development'
```

5. **Initialize database:**
```bash
python3 init_db.py
```

6. **Initialize KNN model:**
```bash
python3 init_knn.py
```

7. **Run the application:**
```bash
python3 app.py
```

Access the app at `http://localhost:8000`

### PythonAnywhere Deployment

The application is deployed at: `https://deanians1bae.pythonanywhere.com/`

**Note:** KNN recommendations are disabled on PythonAnywhere free tier due to disk space limitations for scipy/scikit-learn. Recommendations work in local development.

For detailed deployment instructions, see `PYTHONANYWHERE_DEPLOYMENT.md`

## Usage

### For New Users

1. Click "Sign Up" to create an account
2. Browse movies by genre or use the search function
3. Add movies to your watchlist, favorites, or mark as watched
4. Write reviews and rate movies you've watched
5. Set your tag preferences to get personalized recommendations

### For Existing Users

1. Log in with your credentials
2. View "Recommended for You" for personalized suggestions
3. Update your preferences in the profile section
4. Manage your watchlist, favorites, and watched movies
5. Edit or delete your reviews

## Security Patch & Automation Notes

### Implemented Security Measures

- **CSRF Protection**: All forms protected with Flask-WTF CSRF tokens
- **Password Hashing**: User passwords hashed using Flask-Login's secure hashing
- **SQL Injection Prevention**: SQLAlchemy ORM prevents SQL injection attacks
- **XSS Protection**: Jinja2 auto-escaping prevents XSS attacks
- **Session Security**: Secure session management with Flask-Login
- **Environment Variables**: Sensitive keys (SECRET_KEY, TMDB_API_KEY) stored in environment variables
- **Input Validation**: WTForms validates all user inputs

### Recent Security Fixes

- Fixed SQLAlchemy session conflicts in KNN recommendations
- Added email validation for user registration
- Implemented proper error handling for database operations
- Added secure file permissions for production deployment

### Automation Notes

- **KNN Model Initialization**: Automated on app startup (development only)
- **Database Statistics**: Auto-recalculated on review changes
- **Git Workflow**: Automated deployment via PythonAnywhere Git integration
- **Dependency Management**: Requirements.txt tracks all dependencies

### Known Limitations

- KNN recommendations disabled on PythonAnywhere free tier (disk space)
- TMDB API rate limits may affect movie data fetching
- SQLite database used in development (MySQL recommended for production)

## Project Structure

```
MyMoveList_Website/
├── app.py                      # Application entry point
├── board/
│   ├── __init__.py            # Flask app factory
│   ├── models.py              # SQLAlchemy models
│   ├── pages.py               # Flask routes
│   ├── forms.py               # WTForms
│   └── templates/             # HTML templates
├── knn_recommender.py         # KNN recommendation logic
├── init_db.py                 # Database initialization
├── init_knn.py                # KNN model initialization
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

## Technologies Used

- **Backend**: Flask, SQLAlchemy, Flask-Login, Flask-WTF
- **Frontend**: HTML, Jinja2 templates, Bootstrap
- **Database**: SQLite (development), MySQL (production)
- **Machine Learning**: scikit-learn, NumPy
- **API**: TMDB (The Movie Database)

## License

This project is for educational purposes.

## Support

For issues or questions, please refer to the deployment guides:
- `PYTHONANYWHERE_DEPLOYMENT.md` - PythonAnywhere deployment instructions
- `UPDATE_PYTHONANYWHERE.md` - Updating existing deployment
- `KNN_Implementation_Guide.md` - KNN recommendation system details