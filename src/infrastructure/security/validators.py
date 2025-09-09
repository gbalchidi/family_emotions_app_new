"""Security validators for input sanitization."""
from __future__ import annotations

import html
import re
from typing import Optional


class InputValidator:
    """Input validation and sanitization."""
    
    # Patterns for dangerous content
    SCRIPT_PATTERN = re.compile(r'<script[^>]*>.*?</script>', re.IGNORECASE | re.DOTALL)
    HTML_TAG_PATTERN = re.compile(r'<[^>]+>')
    SQL_KEYWORDS = re.compile(
        r'\b(DROP|DELETE|INSERT|UPDATE|CREATE|ALTER|EXEC|EXECUTE|UNION|SELECT)\b',
        re.IGNORECASE
    )
    
    @classmethod
    def sanitize_text(cls, text: str, max_length: Optional[int] = None) -> str:
        """Sanitize text input from potential XSS and injection attacks."""
        if not text:
            return ""
        
        # Remove script tags
        text = cls.SCRIPT_PATTERN.sub("", text)
        
        # Remove all HTML tags
        text = cls.HTML_TAG_PATTERN.sub("", text)
        
        # Escape HTML entities
        text = html.escape(text)
        
        # Remove excessive whitespace
        text = " ".join(text.split())
        
        # Limit length if specified
        if max_length and len(text) > max_length:
            text = text[:max_length]
        
        return text.strip()
    
    @classmethod
    def validate_name(cls, name: str) -> str:
        """Validate and sanitize name input."""
        if not name:
            raise ValueError("Name cannot be empty")
        
        # Allow only letters, spaces, hyphens, and apostrophes
        if not re.match(r"^[a-zA-Zа-яА-ЯёЁ\s\-']+$", name):
            raise ValueError("Name contains invalid characters")
        
        name = cls.sanitize_text(name, max_length=100)
        
        if len(name) < 2:
            raise ValueError("Name must be at least 2 characters long")
        
        return name
    
    @classmethod
    def validate_username(cls, username: Optional[str]) -> Optional[str]:
        """Validate telegram username."""
        if not username:
            return None
        
        # Telegram username pattern
        if not re.match(r"^[a-zA-Z0-9_]{5,32}$", username):
            return None
        
        return username
    
    @classmethod
    def check_sql_injection(cls, text: str) -> bool:
        """Check if text contains potential SQL injection patterns."""
        return bool(cls.SQL_KEYWORDS.search(text))