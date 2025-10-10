"""
Password Handler
AI Match Simulation v3.0

Handles password hashing, verification, and strength validation.
Uses bcrypt for secure password hashing.
"""

import bcrypt
import re
from typing import Dict, Tuple
import logging

logger = logging.getLogger(__name__)


class PasswordHandler:
    """Password hashing and validation"""

    def __init__(self, rounds: int = 12):
        """
        Initialize password handler

        Args:
            rounds: bcrypt cost factor (default: 12)
                   Higher is more secure but slower
                   Recommended: 10-14
        """
        self.rounds = rounds

    def hash_password(self, password: str) -> str:
        """
        Hash password using bcrypt

        Args:
            password: Plain text password

        Returns:
            Hashed password string

        Raises:
            ValueError: If password is empty
        """
        if not password:
            raise ValueError("Password cannot be empty")

        try:
            # Generate salt and hash password
            salt = bcrypt.gensalt(rounds=self.rounds)
            hashed = bcrypt.hashpw(password.encode('utf-8'), salt)

            logger.debug("Password hashed successfully")

            return hashed.decode('utf-8')

        except Exception as e:
            logger.error(f"Password hashing failed: {e}")
            raise

    def verify_password(self, password: str, hashed: str) -> bool:
        """
        Verify password against hashed password

        Args:
            password: Plain text password
            hashed: Hashed password from database

        Returns:
            True if password matches, False otherwise
        """
        if not password or not hashed:
            return False

        try:
            result = bcrypt.checkpw(
                password.encode('utf-8'),
                hashed.encode('utf-8')
            )

            if result:
                logger.debug("Password verification successful")
            else:
                logger.debug("Password verification failed")

            return result

        except Exception as e:
            logger.error(f"Password verification error: {e}")
            return False

    def check_password_strength(
        self,
        password: str,
        min_length: int = 8,
        require_uppercase: bool = True,
        require_lowercase: bool = True,
        require_digit: bool = True,
        require_special: bool = False
    ) -> Tuple[bool, Dict, int]:
        """
        Check password strength against requirements

        Args:
            password: Password to check
            min_length: Minimum password length
            require_uppercase: Require at least one uppercase letter
            require_lowercase: Require at least one lowercase letter
            require_digit: Require at least one digit
            require_special: Require at least one special character

        Returns:
            Tuple of (is_valid, checks_dict, score)
            - is_valid: Whether password meets all requirements
            - checks_dict: Dict showing which checks passed
            - score: Password strength score (0-5)
        """
        checks = {
            'length': len(password) >= min_length,
            'uppercase': not require_uppercase or bool(re.search(r'[A-Z]', password)),
            'lowercase': not require_lowercase or bool(re.search(r'[a-z]', password)),
            'digit': not require_digit or bool(re.search(r'\d', password)),
            'special': not require_special or bool(re.search(r'[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]', password))
        }

        # Calculate score
        score = sum(checks.values())

        # Additional scoring for length
        if len(password) >= 12:
            score += 0.5
        if len(password) >= 16:
            score += 0.5

        # Check for common patterns (reduce score)
        common_patterns = [
            r'(.)\1{2,}',  # Repeated characters
            r'(012|123|234|345|456|567|678|789|890)',  # Sequential digits
            r'(abc|bcd|cde|def|efg|fgh|ghi|hij|ijk|jkl|klm|lmn|mno|nop|opq|pqr|qrs|rst|stu|tuv|uvw|vwx|wxy|xyz)',  # Sequential letters
        ]

        for pattern in common_patterns:
            if re.search(pattern, password.lower()):
                score -= 1
                break

        # Normalize score to 0-5
        score = max(0, min(5, int(score)))

        is_valid = all(checks.values())

        if is_valid:
            logger.debug(f"Password strength check passed (score: {score}/5)")
        else:
            logger.debug(f"Password strength check failed: {checks}")

        return is_valid, checks, score

    def generate_password_feedback(
        self,
        checks: Dict,
        score: int
    ) -> Dict[str, str]:
        """
        Generate user-friendly feedback for password

        Args:
            checks: Checks dict from check_password_strength
            score: Password strength score

        Returns:
            Dict with feedback message and suggestions
        """
        # Determine strength level
        if score >= 4:
            strength = "strong"
            message = "Password is strong"
        elif score >= 3:
            strength = "medium"
            message = "Password is acceptable but could be stronger"
        else:
            strength = "weak"
            message = "Password is too weak"

        # Generate suggestions
        suggestions = []

        if not checks.get('length'):
            suggestions.append("Use at least 8 characters")

        if not checks.get('uppercase'):
            suggestions.append("Include at least one uppercase letter")

        if not checks.get('lowercase'):
            suggestions.append("Include at least one lowercase letter")

        if not checks.get('digit'):
            suggestions.append("Include at least one number")

        if not checks.get('special'):
            suggestions.append("Consider adding special characters (!@#$%^&* etc.)")

        if score < 4:
            suggestions.append("Use a longer password (12+ characters)")
            suggestions.append("Avoid common patterns or repeated characters")

        return {
            'strength': strength,
            'message': message,
            'suggestions': suggestions,
            'score': score
        }

    @staticmethod
    def is_common_password(password: str) -> bool:
        """
        Check if password is in common passwords list

        Args:
            password: Password to check

        Returns:
            True if password is common, False otherwise
        """
        # Common passwords list (simplified)
        # In production, use a comprehensive list from a file
        common_passwords = {
            'password', 'password123', '12345678', '123456789', '12345',
            'qwerty', 'abc123', '111111', 'letmein', 'welcome',
            'monkey', '1234567890', 'admin', 'password1', 'passw0rd',
            'football', 'iloveyou', 'master', 'sunshine', 'princess'
        }

        return password.lower() in common_passwords


# ============================================================================
# Singleton Instance
# ============================================================================

_password_handler_instance = None


def get_password_handler():
    """Get singleton PasswordHandler instance."""
    global _password_handler_instance
    if _password_handler_instance is None:
        _password_handler_instance = PasswordHandler()
        logger.info("PasswordHandler singleton initialized")
    return _password_handler_instance
