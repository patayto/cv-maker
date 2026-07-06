"""
HTTP Basic Authentication for CV Maker API

This module implements HTTP Basic authentication using passlib bcrypt for password hashing.
Username and password hash are configured via environment variables:
- AUTH_USERNAME: The username for authentication
- AUTH_PASSWORD_HASH: The bcrypt hash of the password
- DISABLE_AUTH: Set to "true" to disable authentication (for local development only)

To generate a password hash:
    from passlib.hash import bcrypt
    print(bcrypt.hash('your_password'))
"""

import os
from typing import Optional
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from passlib.hash import bcrypt

security = HTTPBasic(auto_error=False)  # Don't auto-reject when auth disabled


def verify_auth(credentials: Optional[HTTPBasicCredentials] = Depends(security)) -> str:
    """
    Verify HTTP Basic authentication credentials.

    Args:
        credentials: HTTP Basic credentials from the request (optional when auth disabled)

    Returns:
        The authenticated username (or "local" when auth disabled)

    Raises:
        HTTPException: 401 Unauthorized if credentials are invalid
    """
    # Check if auth is disabled for local development
    if os.getenv("DISABLE_AUTH", "").lower() == "true":
        return "local"  # Return dummy username for local dev

    # If auth is enabled, credentials are required
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Basic"},
        )

    # Get expected credentials from environment
    expected_username = os.getenv("AUTH_USERNAME")
    expected_password_hash = os.getenv("AUTH_PASSWORD_HASH")

    # If auth not configured, deny access (fail-safe)
    if not expected_username or not expected_password_hash:
        raise HTTPException(
            status_code=401,
            detail="Authentication not configured",
            headers={"WWW-Authenticate": "Basic"},
        )

    # Verify username
    if credentials.username != expected_username:
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )

    # Verify password hash
    if not bcrypt.verify(credentials.password, expected_password_hash):
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )

    return credentials.username
