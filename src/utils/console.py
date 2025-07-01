"""
Shared console utilities
=======================

Common console printing patterns extracted from multiple modules.
"""

from rich.console import Console

console = Console()


def print_success(message: str) -> None:
    """Print success message with consistent green formatting."""
    console.print(f"[green]✓ {message}[/green]")


def print_error(message: str) -> None:
    """Print error message with consistent red formatting.""" 
    console.print(f"[red]✗ {message}[/red]")


def print_info(message: str) -> None:
    """Print info message with consistent blue formatting."""
    console.print(f"[blue]ℹ {message}[/blue]")


def print_warning(message: str) -> None:
    """Print warning message with consistent yellow formatting."""
    console.print(f"[yellow]⚠ {message}[/yellow]")