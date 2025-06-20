# Node Service Security Documentation

## Overview
This document outlines the security vulnerabilities found in the Node Service codebase and provides detailed solutions for each issue. The vulnerabilities are categorized by severity level and include specific code examples for fixes.

## Security Vulnerabilities

### 1. SQL Injection Vulnerability (CRITICAL)
**Location**: `src/data/rds_service.py`

#### Issue
The codebase uses string formatting (`%s`) for SQL queries, making it vulnerable to SQL injection attacks. This could allow attackers to execute malicious SQL commands.

#### Current Implementation
```python
INSERT_MAILBOX = "INSERT INTO `mailbox`.`mailbox`(`username`,`password`,`name`,`maildir`,`quota`,`local_part`,`domain`,`created`,`modified`,`active`,`phone`,`email_other`,`token`,`token_validity`,`password_expiry`) VALUES ('%s', '%s', '%s', '%s', %d, '%s', '%s', '%s', '%s', %d, '%s', '%s', '%s', '%s', '%s');"
```

#### Fix
Use parameterized queries to prevent SQL injection:
```python
INSERT_MAILBOX = """INSERT INTO `mailbox`.`mailbox` 
    (`username`,`password`,`name`,`maildir`,`quota`,`local_part`,`domain`,`created`,`modified`,`active`,`phone`,`email_other`,`token`,`token_validity`,`password_expiry`) 
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""

# In the execute method:
cur.execute(INSERT_MAILBOX, (mailbox.email, mailbox.password, mailbox.name, ...))
```

### 2. Insecure Password Storage (HIGH)
**Location**: `src/data/rds_service.py`

#### Issue
The current implementation uses SHA-512 for password hashing without salt, making it vulnerable to rainbow table attacks.

#### Current Implementation
```python
def create_mailbox(self, email: str, password: str) -> Mailbox:
    return Mailbox(
        email = email, 
        password = HashUtil.sha512(password),
        name = email
    )
```

#### Fix
Implement secure password hashing using bcrypt:
```python
import bcrypt

def create_mailbox(self, email: str, password: str) -> Mailbox:
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    
    return Mailbox(
        email = email,
        password = hashed_password.decode('utf-8'),
        name = email
    )
```

### 3. Insecure Secret Management (HIGH)
**Location**: `src/secret.py`

#### Issue
The code relies on environment variables for sensitive configuration without proper validation or fallback mechanisms.

#### Current Implementation
```python
APP_SECRET = os.environ.get(app_constants.APP_SECRET)
DB_SECRET = os.environ.get(app_constants.DB_SECRET)
```

#### Fix
Implement proper environment variable validation:
```python
def get_required_env_var(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise ValueError(f"Required environment variable {name} is not set")
    return value

# Use the function for required variables
APP_SECRET = get_required_env_var(app_constants.APP_SECRET)
DB_SECRET = get_required_env_var(app_constants.DB_SECRET)
```

### 4. Weak Error Handling (MEDIUM)
**Location**: `src/authorize/authorize.py`

#### Issue
Insufficient error handling that could expose sensitive information and inadequate security event logging.

#### Fix
Implement comprehensive error handling:
```python
def authenticate_user(event: any) -> bool:
    try:
        headers = event.get("headers")
        if not headers:
            log.warning("No headers found in request")
            return None

        authorization = headers.get(app_constants.AUTH_HEADER)
        if not authorization:
            log.warning("No authorization header found")
            return None

        if not authorization.startswith("Basic "):
            log.warning("Invalid authorization format")
            return None

        try:
            value = base64Util.decode(authorization.replace("Basic ", ""))
            username, password = value.split(":")
        except Exception as e:
            log.error("Failed to decode authorization header", exc_info=True)
            return None

        username = username.lower()
        if not dataService.is_active_user(username):
            log.warning(f"User {username} is not active")
            return None

        account = set_password_by_env(username, password)
        if account and account.authentication():
            return account

        log.warning(f"Authentication failed for user {username}")
        return None

    except Exception as e:
        log.error("Authentication error", exc_info=True)
        return None
```

### 5. Missing Rate Limiting (MEDIUM)
**Location**: `src/authorize/authorize.py`

#### Issue
Authentication endpoints lack rate limiting, making them vulnerable to brute force attacks.

#### Fix
Implement rate limiting:
```python
from functools import wraps
import time
from collections import defaultdict

class RateLimiter:
    def __init__(self, max_attempts=5, window_seconds=300):
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self.attempts = defaultdict(list)

    def is_allowed(self, key: str) -> bool:
        now = time.time()
        self.attempts[key] = [t for t in self.attempts[key] if now - t < self.window_seconds]
        if len(self.attempts[key]) >= self.max_attempts:
            return False
        self.attempts[key].append(now)
        return True

rate_limiter = RateLimiter()

def rate_limit(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        key = kwargs.get('username', 'unknown')
        if not rate_limiter.is_allowed(key):
            log.warning(f"Rate limit exceeded for {key}")
            return None
        return f(*args, **kwargs)
    return decorated_function

@rate_limit
def authenticate_user(event: any) -> bool:
    # ... existing authentication code ...
```

## Prevention Strategies

1. **Database Security**
   - Use parameterized queries for all database operations
   - Implement proper input validation
   - Use prepared statements
   - Regular database security audits

2. **Password Security**
   - Use bcrypt or Argon2 for password hashing
   - Implement proper salt generation
   - Regular password policy reviews
   - Password strength requirements

3. **Secret Management**
   - Use AWS Secrets Manager or similar service
   - Implement proper environment variable validation
   - Regular secret rotation
   - Access control for secrets

4. **Error Handling**
   - Implement comprehensive error handling
   - Proper security event logging
   - No sensitive information in error messages
   - Regular log analysis

5. **Rate Limiting**
   - Implement rate limiting for authentication endpoints
   - Use Redis or similar for distributed rate limiting
   - Regular monitoring of failed attempts
   - IP-based blocking for suspicious activity

6. **General Security**
   - Use HTTPS for all API communications
   - Implement proper session management
   - Regular security audits
   - Penetration testing
   - Keep dependencies updated
   - Implement proper CORS policies
   - Use security headers
   - Regular code security reviews

## Implementation Timeline

1. **Immediate Actions** (1-2 weeks)
   - Fix SQL injection vulnerabilities
   - Implement secure password hashing
   - Add proper error handling

2. **Short-term Actions** (2-4 weeks)
   - Implement rate limiting
   - Set up proper secret management
   - Add comprehensive logging

3. **Long-term Actions** (1-3 months)
   - Regular security audits
   - Penetration testing
   - Security monitoring setup
   - Documentation updates

## Monitoring and Maintenance

1. **Regular Checks**
   - Security log analysis
   - Failed authentication attempts
   - Unusual access patterns
   - Database query performance

2. **Updates**
   - Regular dependency updates
   - Security patch implementation
   - Documentation maintenance
   - Security policy reviews

## Contact

For security-related issues or questions, please contact the security team at security@iomd.com.

## License

Copyright © 2024 IOMD USA. All rights reserved.