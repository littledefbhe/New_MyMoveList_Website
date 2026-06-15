# PythonAnywhere Deployment Guide

## Prerequisites
- PythonAnywhere account (free tier available)
- GitHub repository with your code: https://github.com/deanians1bae/New_MyMoveList_Website.git
- Application requirements documented

## Step 1: Set Up PythonAnywhere Account

1. Go to https://www.pythonanywhere.com/
2. Sign up for a free account
3. Verify your email address

## Step 2: Create a New Web App

1. Log in to PythonAnywhere
2. Go to the "Web" tab
3. Click "Add a new web app"
4. Choose:
   - **Python version:** Python 3.10 or later
   - **Web framework:** Flask
   - **PythonAnywhere username:** deanians1bae
5. Click "Next"

## Step 3: Configure Git Repository

1. In the "Web" tab, find your new web app
2. Click on the "Git" section
3. Enter your GitHub repository URL:
   ```
   https://github.com/deanians1bae/New_MyMoveList_Website.git
   ```
4. Click "Next"
5. PythonAnywhere will clone your repository to:
   ```
   /home/deanians1bae/New_MyMoveList_Website
   ```

## Step 4: Set Up Virtual Environment

1. In the "Web" tab, go to the "Virtualenv" section
2. Click "Enter virtualenv"
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Exit the virtualenv

## Step 5: Configure WSGI File

1. In the "Web" tab, go to the "Code" section
2. Click on the WSGI configuration file link
3. Replace the contents with:

```python
import sys
import os

# Add your project directory to the Python path
project_home = '/home/deanians1bae/New_MyMoveList_Website'
if project_home not in sys.path:
    sys.path = [project_home] + sys.path

# Change to the project directory
os.chdir(project_home)

# Set environment variables before importing
os.environ['SECRET_KEY'] = 'f0502786488ccea11030ff6c339d5c2d5be1934fa4bc8bd99a5e8f37d0e8c55e'
os.environ['TMDB_API_KEY'] = 'your-tmdb-api-key-here'
os.environ['FLASK_ENV'] = 'production'

# Import your Flask app using the factory pattern
from board import create_app
application = create_app()
```

## Step 6: Set Up Environment Variables

1. In the "Web" tab, go to the "Variables" section
2. Add the following environment variables:
   - **SECRET_KEY:** Generate a secure random key
   - **TMDB_API_KEY:** Your TMDB API key
   - **FLASK_ENV:** `production`

**Generate SECRET_KEY:**
```python
import secrets
print(secrets.token_hex(32))
```

## Step 7: Configure Database

1. In the "Databases" tab
2. Create a new MySQL or PostgreSQL database
3. Note the database name, username, and password
4. Update your `board/__init__.py` to use the production database:

```python
# Production database configuration
import os

if os.environ.get('FLASK_ENV') == 'production':
    # Use PythonAnywhere database
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://username:password@deanians1bae.mysql.pythonanywhere-services.com/deanians1bae$mymovelist'
else:
    # Development database
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///movielist.db'
```

**Important:** Replace with your actual database credentials from PythonAnywhere.

## Step 8: Initialize Database

1. In the "Consoles" tab, create a new Bash console
2. Navigate to your project directory:
   ```bash
   cd /home/deanians1bae/New_MyMoveList_Website
   ```
3. Activate the virtualenv:
   ```bash
   source /home/deanians1bae/.virtualenvs/New_MyMoveList_Website/bin/activate
   ```
4. Set environment variables:
   ```bash
   export SECRET_KEY='your-secret-key'
   export TMDB_API_KEY='your-tmdb-api-key'
   export FLASK_ENV='production'
   ```
5. Initialize the database:
   ```bash
   python3
   ```
   ```python
   from board import create_app, db
   app = create_app()
   with app.app_context():
       db.create_all()
   exit()
   ```

## Step 9: Run Database Migrations

Since you have existing data, export from SQLite and import to MySQL:

**Export from local SQLite:**
```bash
# On your local machine
sqlite3 movielist.db .dump > backup.sql
```

**Upload to PythonAnywhere:**
1. In the "Files" tab, navigate to `/home/deanians1bae/New_MyMoveList_Website`
2. Upload the `backup.sql` file

**Import to MySQL:**
```bash
# In PythonAnywhere Bash console
mysql -h deanians1bae.mysql.pythonanywhere-services.com -u deanians1bae -p deanians1bae$mymovelist < backup.sql
```

**Run recalculation script:**
```bash
python3 recalculate_stats.py
```

## Step 10: Reload Web App

1. In the "Web" tab
2. Click the "Reload" button
3. Check the error logs if there are any issues

## Step 11: Set Up Static Files

1. In the "Web" tab, go to the "Static files" section
2. Add:
   - **URL:** `/static/`
   - **Directory:** `/home/deanians1bae/New_MyMoveList_Website/board/static`

## Step 12: Test Your Application

1. Go to your web app URL: `https://deanians1bae.pythonanywhere.com/`
2. Test basic functionality:
   - Home page loads
   - Can sign up/login
   - Can view movies
   - Can add reviews

## Step 13: Set Up Automatic Git Pulls (Optional)

1. In the "Web" tab, go to the "Git" section
2. Enable automatic pulls (optional)
3. Or manually pull when you make changes:
   ```bash
   cd /home/deanians1bae/New_MyMoveList_Website
   git pull
   ```
4. Reload the web app after pulling

## Troubleshooting

### Application Won't Load
- Check error logs in the "Web" tab
- Verify all dependencies are installed
- Check database connection
- Verify environment variables are set

### Database Connection Issues
- Verify database credentials
- Check if database is created
- Test connection in console

### Static Files Not Loading
- Verify static files configuration
- Check file permissions
- Ensure static files directory exists

### Import Errors
- Verify virtualenv is activated
- Check if all dependencies are installed
- Verify Python path configuration

## Security Considerations

1. **HTTPS:** PythonAnywhere provides HTTPS automatically
2. **Environment Variables:** Never hardcode sensitive data
3. **Database:** Use production database, not SQLite
4. **Debug Mode:** Ensure debug mode is off in production
5. **Secret Key:** Use a strong, randomly generated SECRET_KEY

## Updating Your Application

When you make changes to your code:

1. Commit and push to GitHub:
   ```bash
   git add .
   git commit -m "Your changes"
   git push
   ```

2. Pull changes on PythonAnywhere:
   ```bash
   cd /home/deanians1bae/New_MyMoveList_Website
   git pull
   ```

3. Reload the web app in the "Web" tab

4. If you changed dependencies:
   ```bash
   source /home/deanians1bae/.virtualenvs/New_MyMoveList_Website/bin/activate
   pip install -r requirements.txt
   ```

## Cost Considerations

- **Free tier:** Limited resources, suitable for development/testing
- **Paid tiers:** More resources, better performance for production
- Consider upgrading if you have high traffic
