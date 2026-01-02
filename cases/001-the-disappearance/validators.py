"""
Case 001: Challenge Validation Logic

Custom validators for Case 001 challenges.
These integrate with the main flag_engine to validate submissions.
"""

import hashlib
import re
from typing import Tuple, Optional
from datetime import datetime


# Semantic truth for Case 001
CASE_001_SEMANTIC_TRUTH = "d4ta.ex7ract@protonmail.ch"


def validate_001_preliminary(submission: str) -> Tuple[bool, str]:
    """
    Validate the preliminary challenge answer.
    Expected: internal-tools (the repository with the hidden email)
    """
    normalized = submission.lower().strip().replace(" ", "-")
    
    if normalized == "internal-tools":
        return True, "Correct! The internal-tools repository contains the evidence."
    
    # Partial credit hints
    if "tool" in normalized:
        return False, "Close! Check the exact repository name."
    
    if normalized in ["customer-portal", "api-gateway"]:
        return False, "This repository exists but doesn't contain the key evidence."
    
    if "fork" in normalized:
        return False, "The forks are red herrings. Look at the main repositories."
    
    return False, "Incorrect. Review the GitHub organization export more carefully."


def validate_001_timestamp(submission: str) -> Tuple[bool, str]:
    """
    Validate the timestamp challenge answer.
    Expected: 2024-11-14 23:48:12 (UTC)
    """
    # Clean up submission
    cleaned = submission.strip()
    
    # Try to parse various formats
    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%SZ",
    ]
    
    parsed_time = None
    for fmt in formats:
        try:
            parsed_time = datetime.strptime(cleaned.replace("Z", ""), fmt.replace("Z", ""))
            break
        except ValueError:
            continue
    
    if not parsed_time:
        return False, "Invalid timestamp format. Use YYYY-MM-DD HH:MM:SS"
    
    # Check if correct
    correct_time = datetime(2024, 11, 14, 23, 48, 12)
    
    if parsed_time == correct_time:
        return True, "Correct! This is when the encrypted burst to paste.sh occurred."
    
    # Check if close (within 5 minutes)
    delta = abs((parsed_time - correct_time).total_seconds())
    
    if delta <= 300:
        return False, "Very close! Check the exact seconds."
    
    if delta <= 3600:
        return False, "You're in the right hour. Look for the anomalous burst."
    
    if parsed_time.date() == correct_time.date():
        return False, "Correct date, but wrong time. Correlate with the Telegram message."
    
    return False, "Incorrect timestamp. Analyze the PCAP more carefully."


def validate_001_stego(submission: str) -> Tuple[bool, str]:
    """
    Validate the steganography challenge answer.
    Expected: nexus2024!
    """
    cleaned = submission.strip()
    
    if cleaned == "nexus2024!":
        return True, "Correct! This password was hidden using LSB steganography."
    
    # Case insensitive partial match
    if cleaned.lower() == "nexus2024!":
        return False, "Almost! Check the exact case."
    
    if "nexus" in cleaned.lower() and "2024" in cleaned:
        return False, "Close! Make sure you have the complete password including special characters."
    
    if cleaned == "bmV4dXMyMDI0IQ==":
        return False, "You found the encoded payload, but you need to decode it."
    
    return False, "Incorrect. Analyze wallpaper_abstract_047.png for steganographic content."


def validate_001_contact(submission: str) -> Tuple[bool, str]:
    """
    Validate the external contact challenge answer.
    Expected: DataHaven
    """
    cleaned = submission.strip().lower()
    
    # Remove @ prefix if present
    if cleaned.startswith("@"):
        cleaned = cleaned[1:]
    
    if cleaned == "datahaven":
        return True, "Correct! DataHaven was the contact who sent the forwarded message."
    
    # Check for common mistakes
    if "data" in cleaned and "haven" in cleaned:
        return False, "Check the exact spelling - no spaces or special characters."
    
    if cleaned in ["mchen__dev", "mchen-dev", "marcus"]:
        return False, "That's the subject, not the external contact."
    
    return False, "Incorrect. Look for forwarded messages in the Telegram export."


def validate_001_final(submission: str, user_flag: str) -> Tuple[bool, str]:
    """
    Validate the final flag challenge.
    The submission should match the user's personalized flag.
    
    The semantic truth is: d4ta.ex7ract@protonmail.ch
    But players submit their personalized HMAC flag.
    """
    # This validation is handled by the main flag_engine
    # which verifies the HMAC with the user's salt
    
    # Basic format check
    if not submission.startswith("FLAG{") or not submission.endswith("}"):
        return False, "Invalid flag format. Flags should be in the format FLAG{...}"
    
    # The actual HMAC verification happens in flag_engine.py
    # This function is called after HMAC verification succeeds
    return True, "🎉 Congratulations! You've solved The Disappearance case!"


def get_semantic_truth_hint(challenge_id: str) -> str:
    """
    Get a hint about the semantic truth for a challenge.
    Used when generating personalized flags.
    """
    hints = {
        "001-final": (
            "The semantic truth is an email address used for coordination. "
            "It appears encoded in a backup config file. "
            "ROT13 + Base64 decoding will reveal it."
        ),
    }
    
    return hints.get(challenge_id, "No hint available.")


# ============================================================================
# VALIDATION DISPATCHER
# ============================================================================

def validate_case_001_submission(
    challenge_id: str, 
    submission: str,
    user_flag: Optional[str] = None
) -> Tuple[bool, str]:
    """
    Dispatch validation to the appropriate handler.
    """
    validators = {
        "001-preliminary": validate_001_preliminary,
        "001-timestamp": validate_001_timestamp,
        "001-stego": validate_001_stego,
        "001-contact": validate_001_contact,
    }
    
    if challenge_id == "001-final":
        if not user_flag:
            return False, "Flag verification requires user context."
        return validate_001_final(submission, user_flag)
    
    validator = validators.get(challenge_id)
    if validator:
        return validator(submission)
    
    return False, f"Unknown challenge: {challenge_id}"


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    # Test validators
    test_cases = [
        ("001-preliminary", "internal-tools", True),
        ("001-preliminary", "Internal Tools", True),
        ("001-preliminary", "customer-portal", False),
        ("001-timestamp", "2024-11-14 23:48:12", True),
        ("001-timestamp", "2024-11-14T23:48:12Z", True),
        ("001-timestamp", "2024-11-14 23:48:00", False),
        ("001-stego", "nexus2024!", True),
        ("001-stego", "Nexus2024!", False),
        ("001-contact", "DataHaven", True),
        ("001-contact", "@datahaven", True),
        ("001-contact", "mchen-dev", False),
    ]
    
    print("Running validation tests...\n")
    
    for challenge_id, submission, expected in test_cases:
        result, message = validate_case_001_submission(challenge_id, submission)
        status = "✅" if result == expected else "❌"
        print(f"{status} {challenge_id}: '{submission}' -> {result}")
        if result != expected:
            print(f"   Expected: {expected}, Got: {result}")
            print(f"   Message: {message}")
    
    print("\nAll tests completed!")
