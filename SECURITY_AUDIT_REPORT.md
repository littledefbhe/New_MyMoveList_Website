# Security Audit Report

**Date:** June 14, 2026
**Auditor:** SWE-1.6 (Cascade)
**Scope:** MyMovieList Application Codebase

## Executive Summary

This security audit identified several vulnerabilities in the MyMovieList application codebase, ranging from hardcoded credentials to missing security configurations. The most critical issues involve hardcoded API keys and secret keys that should be stored in environment variables.

## Vulnerabilities Found

### 1. Hardcoded TMDB API Key (CRITICAL)
**Location:** `update_netflix_posters.py:17`
```python
TMDB_API_KEY = "8bf1d9bf0f43dcf73c7f196807c387dc"
```

**Risk Level:** CRITICAL
**OWASP Category:** A07:2021 - Identification and Authentication Failures
**Specific Vulnerability:** Hardcoded Credentials (CWE-798)

**Why This Line is Vulnerable:**
Line 17 contains a hardcoded API key as a string literal. This is vulnerable because:
- The API key is stored in plaintext in the source code
- Anyone with access to the repository can see the key
- The key will be committed to version control history
- The key can be extracted from the code even if the file is deleted
- There is no mechanism to rotate or revoke this key

**Description:** The TMDB API key is hardcoded directly in the source code. This exposes the API key to anyone with access to the codebase, including version control systems.

**Impact:**
- Unauthorized access to TMDB API
- Potential API abuse and quota exhaustion
- Exposure through version control history

**Recommendation:**
- Move API key to environment variable
- Use `os.environ.get('TMDB_API_KEY')`
- Add `.env` to `.gitignore`
- Document required environment variables

---

### 2. Hardcoded Flask Secret Key (HIGH)
**Location:** `board/__init__.py:15`
```python
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'your-secret-key-here'
```

**Risk Level:** HIGH
**OWASP Category:** A07:2021 - Identification and Authentication Failures
**Specific Vulnerability:** Hardcoded Cryptographic Key (CWE-321)

**Why This Line is Vulnerable:**
Line 15 contains a fallback secret key as a string literal. This is vulnerable because:
- The fallback key 'your-secret-key-here' is weak and predictable
- If the SECRET_KEY environment variable is not set, the app uses this weak key
- Attackers can use this known key to forge session cookies
- The fallback key is publicly known and can be found in documentation
- All cryptographic operations (CSRF tokens, session signing) become compromised

**Description:** The Flask application uses a fallback secret key that is hardcoded in the source code. If the environment variable is not set, the application uses a weak, predictable secret key.

**Impact:**
- Session hijacking vulnerabilities
- CSRF token compromise
- Ability to forge session cookies
- Cryptographic operations compromised

**Recommendation:**
- Remove the fallback secret key
- Make SECRET_KEY environment variable mandatory
- Generate a strong, random secret key for production
- Use secrets module or environment-specific configuration

---

### 3. Missing HTTPS Enforcement (MEDIUM)
**Location:** `board/__init__.py` (entire configuration section, lines 14-20)
```python
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'instance/movielist.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
```

**Risk Level:** MEDIUM
**OWASP Category:** A02:2021 - Cryptographic Failures
**Specific Vulnerability:** Missing Encryption in Transit (CWE-319)

**Why This Section is Vulnerable:**
The configuration section (lines 14-20) lacks HTTPS enforcement settings. This is vulnerable because:
- No `SESSION_COOKIE_SECURE = True` configuration to force HTTPS-only cookies
- No `PREFERRED_URL_SCHEME = 'https'` to enforce HTTPS
- No HSTS (HTTP Strict Transport Security) headers
- Application can run over HTTP in development and potentially production
- Session cookies can be transmitted over unencrypted connections
- Man-in-the-middle attacks can intercept sensitive data

**Description:** The application does not enforce HTTPS connections. This allows man-in-the-middle attacks and session hijacking over unencrypted connections.

**Impact:**
- Session hijacking over unencrypted connections
- Credential interception
- Data tampering in transit

**Recommendation:**
- Add `app.config['SESSION_COOKIE_SECURE'] = True`
- Add `app.config['SESSION_COOKIE_HTTPONLY'] = True`
- Add `app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'`
- Implement HSTS headers
- Use Flask-Talisman for security headers

---

### 4. Missing Secure Cookie Configuration (MEDIUM)
**Location:** `board/__init__.py` (configuration section, lines 14-20)
```python
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'instance/movielist.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
```

**Risk Level:** MEDIUM
**OWASP Category:** A05:2021 - Security Misconfiguration
**Specific Vulnerability:** Insecure Cookie Attributes (CWE-614)

**Why This Section is Vulnerable:**
The configuration section (lines 14-20) lacks secure cookie settings. This is vulnerable because:
- No `SESSION_COOKIE_SECURE = True` to enforce HTTPS-only cookies
- No `SESSION_COOKIE_HTTPONLY = True` to prevent JavaScript access to cookies
- No `SESSION_COOKIE_SAMESITE = 'Lax'` or `'Strict'` to prevent CSRF attacks
- Default Flask cookie settings are insecure for production
- Cookies can be accessed via JavaScript if XSS vulnerability exists
- Cookies can be transmitted over unencrypted HTTP connections

**Description:** Session cookies are not configured with security flags like Secure, HttpOnly, and SameSite.

**Impact:**
- Session cookies accessible via JavaScript (XSS risk)
- Session cookies transmitted over HTTP
- CSRF vulnerabilities

**Recommendation:**
```python
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
```

---

### 5. Unencrypted SQLite Database (LOW-MEDIUM)
**Location:** `board/__init__.py:19`
```python
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'instance/movielist.db')
```

**Risk Level:** LOW-MEDIUM
**OWASP Category:** A02:2021 - Cryptographic Failures
**Specific Vulnerability:** Missing Encryption of Sensitive Data (CWE-311)

**Why This Line is Vulnerable:**
Line 19 configures an unencrypted SQLite database file. This is vulnerable because:
- SQLite database file is stored in plaintext without encryption
- Anyone with file system access can read the entire database
- Database contains sensitive user data (email, username, password hashes)
- No encryption-at-rest mechanism protects the data
- Database backup files would also be unencrypted
- File system permissions may not be properly configured
- SQLite does not support built-in encryption without SQLCipher

**Description:** The SQLite database is stored as an unencrypted file. Anyone with file system access can read the database contents.

**Impact:**
- User data exposure if file system is compromised
- Password hashes accessible (though properly hashed)
- User PII accessible

**Recommendation:**
- Consider using SQLCipher for encrypted SQLite
- Implement proper file system permissions
- For production, consider PostgreSQL with SSL
- Regular database backups with encryption

---

## Security Strengths Found

### 1. SQL Injection Protection (GOOD)
**Status:** PROPERLY IMPLEMENTED
- Uses SQLAlchemy ORM with parameterized queries
- No raw SQL queries found
- All database queries use safe ORM methods (filter_by, get, etc.)

### 2. XSS Protection (GOOD)
**Status:** PROPERLY IMPLEMENTED
- Jinja2 auto-escaping enabled by default
- No `|safe` or `raw` filters found in templates
- User input properly escaped in all templates

### 3. Password Security (GOOD)
**Status:** PROPERLY IMPLEMENTED
- Uses werkzeug.security for password hashing
- `generate_password_hash()` and `check_password_hash()` properly implemented
- No plaintext password storage

### 4. CSRF Protection (GOOD)
**Status:** PROPERLY IMPLEMENTED
- Flask-WTF CSRFProtect enabled
- CSRF tokens injected in all forms
- CSRF token validation on POST requests

---

## Summary of Findings

| Category | Critical | High | Medium | Low | Total |
|----------|----------|------|--------|-----|-------|
| Hardcoded Secrets | 1 | 1 | 0 | 0 | 2 |
| Data Protection | 0 | 0 | 2 | 1 | 3 |
| Injection Attacks | 0 | 0 | 0 | 0 | 0 |
| XSS | 0 | 0 | 0 | 0 | 0 |
| **TOTAL** | **1** | **1** | **2** | **1** | **5** |

## Recommended Action Plan

### Priority 1 (Immediate - Critical/High)
1. Remove hardcoded TMDB API key and move to environment variable
2. Remove hardcoded Flask SECRET_KEY fallback
3. Generate and document proper SECRET_KEY for production

### Priority 2 (High - Medium)
4. Implement HTTPS enforcement and secure cookie configuration
5. Add security headers (HSTS, X-Frame-Options, etc.)
6. Consider database encryption for production

### Priority 3 (Medium - Low)
7. Implement file system permissions for database
8. Add security logging and monitoring
9. Regular security audits and dependency updates

---

## Additional Recommendations

1. **Environment Variables Management**
   - Use python-dotenv for development
   - Document all required environment variables
   - Create example .env.example file

2. **Security Headers**
   - Implement Content Security Policy (CSP)
   - Add X-Content-Type-Options: nosniff
   - Add X-Frame-Options: DENY or SAMEORIGIN

3. **Input Validation**
   - Add server-side validation for all user inputs
   - Implement rate limiting for API endpoints
   - Add length validation for text fields

4. **Error Handling**
   - Ensure error messages don't leak sensitive information
   - Implement proper logging without exposing secrets
   - Use generic error messages for users

5. **Dependencies**
   - Regularly update dependencies for security patches
   - Use `pip-audit` or `safety` to check for vulnerabilities
   - Pin dependency versions in requirements.txt

---

**Note:** This audit should be repeated after implementing fixes to verify that all vulnerabilities have been properly addressed.
