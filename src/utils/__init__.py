"""
Shared utilities for Get-keywords-Serp
=====================================

Common functions extracted from multiple modules to eliminate duplication.
"""

from .retry import retry_with_backoff
from .text import truncate_string
from .error_handling import handle_error_and_exit
from .console import print_success, print_error

__all__ = [
    'retry_with_backoff',
    'truncate_string', 
    'handle_error_and_exit',
    'print_success',
    'print_error'
]