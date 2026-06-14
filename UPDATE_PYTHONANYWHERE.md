# Update Existing PythonAnywhere Deployment

## Quick Update Steps

### 1. Log in to PythonAnywhere
Go to https://www.pythonanywhere.com/ and log in

### 2. Open a Bash Console
1. Go to the "Consoles" tab
2. Click "Bash" to open a new console

### 3. Navigate to Your Project Directory
```bash
cd /home/littledefbhe/New_MyMoveList_Website
```

### 4. Pull Latest Changes from GitHub
```bash
git pull
```

### 5. Activate Virtual Environment
```bash
source /home/littledefbhe/.virtualenvs/New_MyMoveList_Website/bin/activate
```

### 6. Install/Update Dependencies
```bash
pip install -r requirements.txt
```

### 7. Set Environment Variables (if needed)
```bash
export SECRET_KEY='your-secret-key'
export TMDB_API_KEY='your-tmdb-api-key'
export FLASK_ENV='production'
```

### 8. Exit Console
```bash
exit
```

### 9. Reload Web App
1. Go to the "Web" tab
2. Find your web app
3. Click the "Reload" button

### 10. Test Your Application
Go to your web app URL and test the new features

## Database Updates (if needed)

If you've made database schema changes:

### Option 1: Recreate Database (WARNING: Deletes all data)
```bash
# In Bash console with virtualenv activated
python3
```
```python
from board import create_app, db
app = create_app()
with app.app_context():
    db.drop_all()
    db.create_all()
exit()
```

### Option 2: Run Migration Script
If you have migration scripts:
```bash
python3 migrate_movie_stats.py
python3 recalculate_stats.py
```

## Troubleshooting

### Pull Fails
```bash
# If you have local changes, stash them first
git stash
git pull
```

### Dependencies Fail to Install
```bash
# Upgrade pip first
pip install --upgrade pip
pip install -r requirements.txt
```

### App Won't Load After Reload
1. Check error logs in "Web" tab
2. Verify all dependencies are installed
3. Check database connection
4. Verify environment variables are set

### Database Issues
If you need to update the database schema:
1. Export your existing data
2. Drop and recreate tables
3. Import data back
4. Run recalculation scripts

## Quick Reference

**Most Common Update Commands:**
```bash
cd /home/littledefbhe/New_MyMoveList_Website
git pull
source /home/littledefbhe/.virtualenvs/New_MyMoveList_Website/bin/activate
pip install -r requirements.txt
exit
# Then reload web app in Web tab
```

**Check Current Git Status:**
```bash
git status
git log --oneline -5
```

**Check Installed Packages:**
```bash
pip list
```

## What Gets Updated

When you pull from GitHub, you'll get:
- Latest code changes
- New features
- Bug fixes
- Updated templates
- Updated database models

You'll need to:
- Install new dependencies
- Run database migrations (if schema changed)
- Recalculate statistics (if stats model changed)
- Reload the web app

## Automated Updates (Optional)

To set up automatic git pulls:
1. In "Web" tab → "Git" section
2. Enable automatic pulls
3. Set up a schedule (e.g., every hour)

Note: You'll still need to reload the web app manually after automatic pulls.
