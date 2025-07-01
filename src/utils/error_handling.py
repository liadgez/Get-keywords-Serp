"""
Shared error handling utilities
==============================

Common error handling patterns extracted from multiple modules.
"""

import typer
from rich.console import Console

console = Console()


def handle_error_and_exit(error: Exception, message: str = None) -> None:
    """
    Handle error with consistent formatting and exit.
    
    Args:
        error: Exception that occurred
        message: Optional custom error message
    """
    error_msg = message or f"Error: {str(error)}"
    console.print(f"[red]{error_msg}[/red]")
    raise typer.Exit(1)