"""
Shared retry utilities
=====================

Common retry logic extracted from multiple modules to eliminate duplication.
"""

import time
import random
from typing import Callable, Any, Optional
import functools


def retry_with_backoff(max_retries: int = 3, 
                      base_delay: float = 1.0,
                      exponential: bool = True,
                      jitter: bool = True) -> Callable:
    """
    Decorator for retrying functions with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Base delay between retries
        exponential: Use exponential backoff (2^attempt)
        jitter: Add random jitter to prevent thundering herd
        
    Returns:
        Decorated function with retry logic
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt < max_retries - 1:
                        # Calculate wait time
                        if exponential:
                            wait_time = base_delay * (2 ** attempt)
                        else:
                            wait_time = base_delay
                        
                        # Add jitter
                        if jitter:
                            wait_time += random.uniform(0, 1)
                        
                        time.sleep(wait_time)
                        continue
                    raise e
            return None
        return wrapper
    return decorator


def retry_function(func: Callable, max_retries: int = 3, 
                  base_delay: float = 1.0, *args, **kwargs) -> Any:
    """
    Retry a function call without using decorator.
    
    Args:
        func: Function to retry
        max_retries: Maximum number of retry attempts
        base_delay: Base delay between retries
        *args, **kwargs: Arguments to pass to function
        
    Returns:
        Function result or raises last exception
    """
    for attempt in range(max_retries):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = base_delay * (2 ** attempt) + random.uniform(0, 1)
                time.sleep(wait_time)
                continue
            raise e
    return None