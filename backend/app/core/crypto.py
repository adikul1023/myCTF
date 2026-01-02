"""
Cryptographic utilities for flag generation and verification.
Implements HMAC-based flag system with per-user, per-case uniqueness.

CRITICAL SECURITY NOTES:
- NO static flags are ever used
- Flags are computed dynamically using HMAC
- semantic_truth is never stored in plaintext
- All comparisons are constant-time
- Flags include time windows for automatic expiry
- User-specific salts prevent cross-user replay attacks
"""

import hashlib
import hmac
import base64
import time
from datetime import datetime, timezone
from typing import Optional, Tuple

from .config import settings


class CryptoService:
    """
    Cryptographic service for flag generation and verification.
    
    The flag system works as follows:
    1. Each case has a "semantic_truth" - the actual answer to the forensic question
    2. The semantic_truth is hashed before storage (never stored plaintext)
    3. Flags are generated per-user, per-case using HMAC:
       flag = HMAC(secret, user_id || case_id || semantic_truth_hash)
    4. Verification is always constant-time to prevent timing attacks
    """
    
    FLAG_PREFIX = "FORENSIC{"
    FLAG_SUFFIX = "}"
    
    def __init__(self, secret_key: Optional[str] = None):
        """
        Initialize the crypto service.
        
        Args:
            secret_key: The secret key for HMAC operations.
                       Defaults to FLAG_SECRET_KEY from settings.
        """
        self._secret_key = (secret_key or settings.FLAG_SECRET_KEY).encode("utf-8")
        self._flag_expiry_minutes = settings.FLAG_EXPIRY_MINUTES
    
    def _get_time_window(self) -> int:
        """
        Get the current time window for flag generation.
        
        Time is divided into windows of FLAG_EXPIRY_MINUTES.
        Flags generated in the same window will be identical.
        Once the window passes, old flags become invalid.
        
        Returns:
            Integer representing the current time window.
        """
        return int(time.time() // (self._flag_expiry_minutes * 60))
    
    def _get_adjacent_time_windows(self) -> Tuple[int, int, int]:
        """
        Get the current and adjacent time windows.
        
        For verification, we check current and previous window
        to handle submissions near window boundaries.
        
        Returns:
            Tuple of (previous_window, current_window, next_window)
        """
        current = self._get_time_window()
        return (current - 1, current, current + 1)
    
    def hash_semantic_truth(self, semantic_truth: str) -> str:
        """
        Hash the semantic truth for storage.
        The semantic truth (actual answer) is never stored in plaintext.
        
        Args:
            semantic_truth: The actual answer/truth for a case.
        
        Returns:
            SHA-256 hash of the semantic truth (hex encoded).
        """
        normalized = semantic_truth.strip().lower()
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    
    def generate_flag(
        self,
        user_id: str,
        case_id: str,
        semantic_truth_hash: str,
        user_flag_salt: str,
        time_window: Optional[int] = None,
    ) -> str:
        """
        Generate a unique, time-limited flag for a specific user and case.
        
        The flag is computed as:
        HMAC-SHA256(secret_key, user_id || case_id || semantic_truth_hash || user_salt || time_window)
        
        This ensures:
        - Each user gets a different flag for the same case
        - Flags cannot be shared between users (user_flag_salt binding)
        - Flags automatically expire after FLAG_EXPIRY_MINUTES
        - Replayed flags from other users always fail
        - Leaked flags become invalid after expiry
        
        Args:
            user_id: The user's unique identifier.
            case_id: The case's unique identifier.
            semantic_truth_hash: The hashed semantic truth for the case.
            user_flag_salt: The user's time-variant salt (rotates periodically).
            time_window: Optional time window override (for verification).
        
        Returns:
            The formatted flag string: FORENSIC{<hmac_value>}
        """
        if time_window is None:
            time_window = self._get_time_window()
        
        # Include user_flag_salt and time_window in the message
        # This makes flags:
        # 1. User-specific (can't replay other user's flags)
        # 2. Time-limited (automatically expire)
        message = f"{user_id}:{case_id}:{semantic_truth_hash}:{user_flag_salt}:{time_window}".encode("utf-8")
        
        hmac_digest = hmac.new(
            self._secret_key,
            message,
            hashlib.sha256,
        ).digest()
        
        # Use URL-safe base64 encoding, truncated for readability
        flag_value = base64.urlsafe_b64encode(hmac_digest)[:32].decode("utf-8")
        
        return f"{self.FLAG_PREFIX}{flag_value}{self.FLAG_SUFFIX}"
    
    def verify_flag(
        self,
        submitted_flag: str,
        user_id: str,
        case_id: str,
        semantic_truth_hash: str,
        user_flag_salt: str,
    ) -> Tuple[bool, str]:
        """
        Verify a submitted flag using constant-time comparison.
        
        Checks both current and previous time windows to handle
        submissions near window boundaries.
        
        SECURITY: This method uses hmac.compare_digest for timing-attack resistance.
        
        Args:
            submitted_flag: The flag submitted by the user.
            user_id: The user's unique identifier.
            case_id: The case's unique identifier.
            semantic_truth_hash: The hashed semantic truth for the case.
            user_flag_salt: The user's time-variant salt.
        
        Returns:
            Tuple of (is_valid, reason).
            Reasons: "valid", "expired", "invalid"
        """
        prev_window, curr_window, _ = self._get_adjacent_time_windows()
        
        # Check current time window first
        expected_current = self.generate_flag(
            user_id, case_id, semantic_truth_hash, user_flag_salt, curr_window
        )
        if hmac.compare_digest(
            submitted_flag.encode("utf-8"),
            expected_current.encode("utf-8"),
        ):
            return (True, "valid")
        
        # Check previous time window (for boundary cases)
        expected_previous = self.generate_flag(
            user_id, case_id, semantic_truth_hash, user_flag_salt, prev_window
        )
        if hmac.compare_digest(
            submitted_flag.encode("utf-8"),
            expected_previous.encode("utf-8"),
        ):
            return (True, "valid")
        
        # Flag doesn't match current or previous window
        # It could be expired or simply wrong/replayed from another user
        return (False, "invalid_or_expired")
    
    def verify_answer(
        self,
        submitted_answer: str,
        stored_semantic_truth_hash: str,
    ) -> bool:
        """
        Verify if a submitted answer matches the semantic truth.
        Uses constant-time comparison.
        
        Args:
            submitted_answer: The answer submitted by the user.
            stored_semantic_truth_hash: The stored hash of the semantic truth.
        
        Returns:
            True if the answer is correct, False otherwise.
        """
        submitted_hash = self.hash_semantic_truth(submitted_answer)
        
        # Constant-time comparison
        return hmac.compare_digest(
            submitted_hash.encode("utf-8"),
            stored_semantic_truth_hash.encode("utf-8"),
        )
    
    @staticmethod
    def generate_case_salt() -> str:
        """
        Generate a random salt for additional case-level entropy.
        
        Returns:
            A 32-byte hex-encoded random salt.
        """
        import secrets
        return secrets.token_hex(32)


# Global crypto service instance
crypto_service = CryptoService()
