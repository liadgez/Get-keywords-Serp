"""
Shared text processing utilities
===============================

Common text manipulation functions extracted from multiple modules.
"""


def truncate_string(text: str, max_length: int, suffix: str = "...") -> str:
    """
    Truncate string to maximum length with optional suffix.
    
    Args:
        text: String to truncate
        max_length: Maximum length before truncation
        suffix: Suffix to append when truncated
        
    Returns:
        Truncated string with suffix if needed
    """
    if not isinstance(text, str):
        text = str(text)
    
    if len(text) <= max_length:
        return text
    
    return text[:max_length] + suffix