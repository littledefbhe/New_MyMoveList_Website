import os
from datetime import datetime
from flask import Flask, session
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect, generate_csrf
from .models import db, User
from board import pages  # Import the pages blueprint

def create_app():
    """Application factory function that creates and configures the Flask app"""
    # Create the Flask application instance
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
    if not app.config['SECRET_KEY']:
        raise ValueError("SECRET_KEY environment variable must be set for security. Please set it before running the application.")

    # Database configuration
    basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'instance/movielist.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize extensions
    db.init_app(app)
    csrf = CSRFProtect(app)
    
    # Initialize Flask-Login
    login_manager = LoginManager()
    login_manager.login_view = 'pages.signin'
    login_manager.login_message_category = 'info'
    login_manager.init_app(app)
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    # Register the pages blueprint with the application
    app.register_blueprint(pages.bp)
    
    # Add CSRF token to all templates
    @app.context_processor
    def inject_csrf_token():
        return dict(csrf_token=generate_csrf)
    
    # Custom Jinja filter for formatting relative time
    @app.template_filter('timesince')
    def timesince(dt, default="just now"):
        """
        Returns string representing "time since" e.g.
        3 days ago, 5 hours ago etc.
        """
        if dt is None:
            return ""
            
        now = datetime.utcnow()
        diff = now - dt
        
        periods = (
            (diff.days // 365, "year", "years"),
            (diff.days // 30, "month", "months"),
            (diff.days // 7, "week", "weeks"),
            (diff.days, "day", "days"),
            (diff.seconds // 3600, "hour", "hours"),
            (diff.seconds // 60, "minute", "minutes"),
            (diff.seconds, "second", "seconds"),
        )
        
        for period, singular, plural in periods:
            if period > 0:
                return f"{period} {singular if period == 1 else plural} ago"
                
        return default
    
    # Custom Jinja filter for formatting numbers
    @app.template_filter('format_number')
    def format_number(value):
        if not value:
            return '0'
        value = int(value)
        if value >= 1000000:
            return f'{value/1000000:.1f}M'.replace('.0', '')
        elif value >= 1000:
            return f'{value/1000:.1f}K'.replace('.0', '')
        return str(value)
    
    return app
