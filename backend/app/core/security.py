"""
Security service for authentication and authorization.
Implements Argon2 password hashing and JWT token management.
"""

import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, InvalidHashError
from jose import jwt, JWTError
from pydantic import BaseModel

from .config import settings


class TokenPayload(BaseModel):
    """JWT token payload structure."""
    sub: str  # user_id
    exp: datetime
    iat: datetime
    jti: str  # JWT ID for revocation
    type: str = "access"


class SecurityService:
    """
    Handles all security operations:
    - Password hashing with Argon2
    - JWT token creation and validation
    - Secure random generation
    """
    
    def __init__(self):
        self._hasher = PasswordHasher(
            time_cost=settings.ARGON2_TIME_COST,
            memory_cost=settings.ARGON2_MEMORY_COST,
            parallelism=settings.ARGON2_PARALLELISM,
            hash_len=settings.ARGON2_HASH_LEN,
            salt_len=settings.ARGON2_SALT_LEN,
        )
    
    def hash_password(self, password: str) -> str:
        """
        Hash a password using Argon2id.
        
        Args:
            password: The plaintext password to hash.
        
        Returns:
            The Argon2 hash string.
        """
        return self._hasher.hash(password)
    
    def verify_password(self, password: str, hash: str) -> bool:
        """
        Verify a password against an Argon2 hash.
        Uses constant-time comparison internally.
        
        Args:
            password: The plaintext password to verify.
            hash: The Argon2 hash to verify against.
        
        Returns:
            True if the password matches, False otherwise.
        """
        try:
            self._hasher.verify(hash, password)
            return True
        except (VerifyMismatchError, InvalidHashError):
            return False
    
    def needs_rehash(self, hash: str) -> bool:
        """
        Check if a password hash needs to be rehashed due to parameter changes.
        
        Args:
            hash: The Argon2 hash to check.
        
        Returns:
            True if the hash should be rehashed with current parameters.
        """
        return self._hasher.check_needs_rehash(hash)
    
    def create_access_token(
        self,
        user_id: str,
        expires_delta: Optional[timedelta] = None,
    ) -> str:
        """
        Create a JWT access token.
        
        Args:
            user_id: The user's unique identifier.
            expires_delta: Optional custom expiration time.
        
        Returns:
            Encoded JWT token string.
        """
        now = datetime.now(timezone.utc)
        
        if expires_delta:
            expire = now + expires_delta
        else:
            expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        # Generate unique token ID for potential revocation
        jti = secrets.token_urlsafe(16)
        
        payload = {
            "sub": str(user_id),
            "exp": expire,
            "iat": now,
            "jti": jti,  # JWT ID for revocation
            "type": "access",
        }
        
        return jwt.encode(
            payload,
            settings.SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM,
        )
    
    def decode_token(self, token: str) -> Optional[TokenPayload]:
        """
        Decode and validate a JWT token.
        
        Args:
            token: The JWT token string to decode.
        
        Returns:
            TokenPayload if valid, None if invalid or expired.
        """
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM],
            )
            return TokenPayload(**payload)
        except JWTError:
            return None
    
    @staticmethod
    def generate_invite_code(length: int = 16) -> str:
        """
        Generate a cryptographically secure invite code.
        
        Args:
            length: The length of the invite code.
        
        Returns:
            A secure random string suitable for use as an invite code.
        """
        return secrets.token_urlsafe(length)
    
    @staticmethod
    def generate_secure_token(length: int = 32) -> str:
        """
        Generate a cryptographically secure random token.
        
        Args:
            length: The number of random bytes.
        
        Returns:
            A hex-encoded secure random string.
        """
        return secrets.token_hex(length)


# Global security service instance
security_service = SecurityService()
