# Implementation Plan for Part B: Secure Development, Automation & Deployment

## Phase Approach - Ordered from Easiest to Hardest

### Phase 1: Documentation & Code Quality (Easiest)
**Estimated Time: 1-2 hours**

#### Task 1.1: Update GitHub README.md (Section 10.3 - 1 mark)
- **Objective:** Provide clear instructions for accessing and using the app with security notes
- **Actions:**
  - Add installation instructions (pip install -r requirements.txt)
  - Add setup instructions (python init_db.py, python app.py)
  - Add usage instructions for key features
  - Add "Security Patch & Automation Notes" section summarizing:
    - Security patches implemented (SQLi prevention, CSRF protection, etc.)
    - Automation features (regression model integration)
- **Deliverable:** Updated README.md in repository root

#### Task 1.2: Code Standards & Cleanup (Section 9.2 - 2 marks)
- **Objective:** Ensure PEP 8 compliance and remove legacy code
- **Actions:**
  - Run `black` or `autopep8` on all Python files
  - Remove unused imports
  - Remove commented-out legacy code
  - Ensure consistent naming conventions
  - Check line lengths (max 79 characters)
- **Deliverable:** Clean, PEP 8 compliant codebase

#### Task 1.3: Code Readability & Comments (Section 9.1 - 3 marks)
- **Objective:** Add meaningful comments explaining security and ML logic
- **Actions:**
  - Add docstrings to all functions in pages.py
  - Add comments explaining security implementations (CSRF, SQLi prevention)
  - Add comments explaining database relationships in models.py
  - Add inline comments for complex logic
  - Document the purpose of each route in pages.py
- **Deliverable:** Well-commented code with clear explanations

---

### Phase 2: Security Testing & Documentation (Medium)
**Estimated Time: 2-3 hours**

#### Task 2.1: Security Testing Evidence (Section 8.2 - 2 marks)
- **Objective:** Document SAST/DAST testing conducted
- **Actions:**
  - Run bandit (SAST tool) on the codebase: `bandit -r .`
  - Document findings and fixes
  - Test for SQL injection vulnerabilities (manual testing or using sqlmap)
  - Test for XSS vulnerabilities
  - Test CSRF protection (try submitting forms without tokens)
  - Document all tests performed in code comments or a SECURITY.md file
  - Create GitHub commit messages referencing security fixes
- **Deliverable:** Documented evidence of security testing with commit references

#### Task 2.2: Security Patch Implementation (Section 8.1 - 3 marks)
- **Objective:** Patch identified vulnerabilities with OWASP mitigations
- **Actions:**
  - **SQL Injection Prevention:**
    - Verify all database queries use SQLAlchemy ORM (no raw SQL)
    - Ensure user input is properly parameterized
    - Add input validation on all forms
  - **CSRF Protection:**
    - Verify CSRFProtect is enabled (already in __init__.py)
    - Ensure all forms include CSRF tokens
    - Test that forms fail without valid tokens
  - **Input Validation:**
    - Validate all user inputs (length, type, format)
    - Sanitize user input before database operations
  - **Authentication Security:**
    - Ensure password hashing is implemented (already using werkzeug)
    - Verify session security (secure cookies, timeout)
  - **Error Handling:**
    - Ensure error messages don't leak sensitive information
    - Implement proper error pages
- **Deliverable:** Secured application with documented patches

---

### Phase 3: Web Integration (Medium-Hard)
**Estimated Time: 3-4 hours**

#### Task 3.1: Flask Routing & Data Handling (Section 7.1 - 3 marks)
- **Objective:** Create secure route handlers for ML automation
- **Actions:**
  - Design a new route for the ML prediction feature (e.g., `/predict` or `/recommend`)
  - Create form for user input (e.g., movie preferences, genre selection)
  - Implement GET request to display the form
  - Implement POST request to handle form submission
  - Validate and sanitize all input data
  - Pass data securely to ML model
  - Return predictions as JSON or render to template
  - Add error handling for invalid inputs
- **Deliverable:** New Flask route with proper GET/POST handling

#### Task 3.2: Seamless UI Integration (Section 7.2 - 2 marks)
- **Objective:** Integrate ML predictions into the UI naturally
- **Actions:**
  - Create HTML template for the prediction/feature page
  - Style the form to match existing app design (Bootstrap)
  - Display model predictions/results dynamically
  - Add loading indicators for model processing
  - Ensure responsive design for mobile devices
  - Add the feature to navigation menu
  - Test user experience end-to-end
- **Deliverable:** Integrated UI feature that feels native to the app

---

### Phase 4: Machine Learning Implementation (Hard)
**Estimated Time: 4-6 hours**

#### Task 4.1: Regression Model Execution (Section 6.1 - 3 marks)
- **Objective:** Implement a regression model using scikit-learn
- **Actions:**
  - **Choose ML Use Case:**
    - Option A: Movie rating prediction based on features
    - Option B: Movie recommendation system (collaborative filtering)
    - Option C: Genre classification based on movie features
  - **Install Dependencies:**
    - Add scikit-learn to requirements.txt
    - Add pandas, numpy if needed
  - **Data Preparation:**
    - Extract training data from existing database
    - Create features (genre, year, runtime, etc.)
    - Create target variable (rating, popularity, etc.)
  - **Model Training:**
    - Split data into train/test sets
    - Train regression model (Linear, Logistic, or Polynomial)
    - Evaluate model performance (accuracy, MSE, etc.)
    - Save trained model (using joblib or pickle)
  - **Integration:**
    - Create prediction function in Python
    - Load model on app startup
    - Create API endpoint for predictions
- **Deliverable:** Working ML model integrated into the application

#### Task 4.2: Output Accuracy & Relevance (Section 6.2 - 2 marks)
- **Objective:** Ensure model generates useful predictions
- **Actions:**
  - Test model with various inputs
  - Validate predictions make logical sense
  - Tune hyperparameters for better accuracy
  - Add confidence scores to predictions
  - Handle edge cases (no data, outliers)
  - Display predictions in user-friendly format
  - Add explanation of how predictions work
- **Deliverable:** Accurate, relevant model outputs that enhance app utility

---

### Phase 5: Deployment & Presentation (Hardest)
**Estimated Time: 3-5 hours**

#### Task 5.1: Live Hosting on PythonAnywhere (Section 10.1 - 2 marks)
- **Objective:** Deploy app to PythonAnywhere
- **Actions:**
  - Create PythonAnywhere account
  - Create new web app (Flask template)
  - Upload code via Git or manual upload
  - Configure virtual environment
  - Install dependencies (pip install -r requirements.txt)
  - Configure WSGI file for Flask app
  - Set up database (SQLite or PostgreSQL)
  - Run database migrations
  - Configure static files serving
  - Set environment variables (SECRET_KEY)
  - Test all functionality on live server
  - Configure domain (if applicable)
- **Deliverable:** Fully functional live URL

#### Task 5.2: Digital and Printed Presentation (Section 10.2 - 2 marks)
- **Objective:** Create comprehensive project documentation
- **Actions:**
  - Create Word document with:
    - Table of contents
    - Header and footer
    - Headings and subheadings
    - Project overview
    - Screenshots of the application
    - Architecture diagrams
    - Security documentation
    - ML model documentation
    - Testing evidence
    - Deployment instructions
  - Perform spelling and grammar check
  - Format professionally
  - Save as PDF
  - Print and bind document
- **Deliverable:** Professional printed documentation

---

## Summary of Implementation Order

1. **Phase 1** (Easiest): Documentation & Code Quality
   - README.md update
   - PEP 8 cleanup
   - Add comments

2. **Phase 2** (Medium): Security Testing & Documentation
   - Security testing evidence
   - Security patch implementation

3. **Phase 3** (Medium-Hard): Web Integration
   - Flask routing for ML feature
   - UI integration

4. **Phase 4** (Hard): Machine Learning
   - Implement regression model
   - Ensure output accuracy

5. **Phase 5** (Hardest): Deployment & Presentation
   - Deploy to PythonAnywhere
   - Create printed documentation

**Total Estimated Time: 13-20 hours**

---

## Notes

- Each phase builds on the previous one
- Security patches should be tested thoroughly before ML integration
- ML model choice should align with app's purpose (movie recommendations/ratings)
- Keep GitHub commits descriptive for security evidence
- Test deployment on a staging environment first if possible
- Document everything as you go for the final presentation
