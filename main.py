#!/usr/bin/env python3
"""
Keyword-Driven Competitor Discovery Tool
Main CLI interface for analyzing competitors based on keyword search results.
"""
import os
import sys
from pathlib import Path
from typing import Optional
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from dotenv import load_dotenv

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Import shared utilities to eliminate duplication
from src.utils.text import truncate_string
from src.utils.error_handling import handle_error_and_exit
from src.utils.console import print_success, print_error

from src.input import get_keywords_input
from src.serp import create_serp_fetcher
from src.parser import create_domain_parser
from src.db import create_database
from src.export import create_export_manager

# Load environment variables
load_dotenv()

app = typer.Typer(
    name="competitor-discovery",
    help="Discover competitors by analyzing keyword search results",
    add_completion=False
)
console = Console()


@app.command()
def analyze(
    keywords_file: Optional[str] = typer.Option(
        None, "--keywords-file", "-k", 
        help="Path to keywords file (CSV or text)"
    ),
    keywords_string: Optional[str] = typer.Option(
        None, "--keywords", "-s", 
        help="Comma-separated keywords string"
    ),
    engine: str = typer.Option(
        "google", "--engine", "-e", 
        help="Search engine (google or bing)"
    ),
    depth: int = typer.Option(
        20, "--depth", "-d", 
        help="Number of search results per keyword (max 20)"
    ),
    output_csv: Optional[str] = typer.Option(
        None, "--output-csv", "-o", 
        help="Output CSV file path"
    ),
    output_excel: Optional[str] = typer.Option(
        None, "--output-excel", "-x", 
        help="Output Excel file path"
    ),
    google_sheet_id: Optional[str] = typer.Option(
        None, "--sheet-id", 
        help="Google Sheets spreadsheet ID for export"
    ),
    min_appearances: int = typer.Option(
        1, "--min-appearances", 
        help="Minimum keyword appearances to include competitor"
    ),
    max_results: int = typer.Option(
        50, "--max-results", 
        help="Maximum number of competitors to return"
    ),
    save_to_db: bool = typer.Option(
        True, "--save-db/--no-save-db", 
        help="Save results to database"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", 
        help="Enable verbose output"
    )
):
    """
    Analyze competitors for given keywords.
    
    Example usage:
    python main.py analyze --keywords "nike shoes,running shoes,athletic footwear"
    python main.py analyze --keywords-file keywords.csv --output-csv results.csv
    """
    try:
        # Validate inputs
        if not keywords_file and not keywords_string:
            console.print("[red]Error: Please provide either --keywords-file or --keywords[/red]")
            raise typer.Exit(1)
        
        if depth > 20:
            console.print("[yellow]Warning: Depth limited to 20 results per keyword[/yellow]")
            depth = 20
        
        # Load keywords
        console.print("[blue]Loading keywords...[/blue]")
        keywords = get_keywords_input(keywords_file, keywords_string)
        
        print_success(f"Loaded {len(keywords)} keywords")
        if verbose:
            for i, kw in enumerate(keywords, 1):
                console.print(f"  {i}. {kw}")
        
        # Initialize components
        serp_fetcher = create_serp_fetcher()
        domain_parser = create_domain_parser()
        
        # Fetch SERP results
        console.print(f"[blue]Fetching SERP results using {engine.upper()}...[/blue]")
        serp_results = serp_fetcher.fetch_multiple_keywords(keywords, depth)
        
        # Check if we got results
        total_results = sum(len(results) for results in serp_results.values())
        if total_results == 0:
            console.print("[red]Error: No SERP results found. Check your keywords and try again.[/red]")
            raise typer.Exit(1)
        
        print_success(f"Fetched {total_results} total search results")
        
        # Parse and rank competitors
        console.print("[blue]Analyzing competitors...[/blue]")
        competitors = domain_parser.parse_serp_results(serp_results, depth)
        
        # Filter results
        competitors = domain_parser.filter_competitors(
            competitors, 
            min_appearances=min_appearances,
            max_results=max_results
        )
        
        if not competitors:
            console.print("[red]No competitors found matching your criteria.[/red]")
            raise typer.Exit(1)
        
        # Generate summary
        summary = domain_parser.get_domain_summary(competitors)
        
        # Display results
        _display_results(competitors[:20], keywords, summary, verbose)
        
        # Save to database
        if save_to_db:
            console.print("[blue]Saving to database...[/blue]")
            db = create_database()
            run_id = db.save_analysis_run(keywords, competitors, engine, depth)
            print_success(f"Saved analysis run #{run_id}")
        
        # Export results
        export_manager = create_export_manager()
        
        if output_csv:
            console.print(f"[blue]Exporting to CSV: {output_csv}[/blue]")
            csv_path = export_manager.export_to_csv(competitors, keywords, output_csv)
            print_success(f"CSV exported: {csv_path}")
        
        if output_excel:
            console.print(f"[blue]Exporting to Excel: {output_excel}[/blue]")
            excel_path = export_manager.create_excel_export(competitors, keywords, summary, output_excel)
            print_success(f"Excel exported: {excel_path}")
        
        if google_sheet_id:
            console.print("[blue]Exporting to Google Sheets...[/blue]")
            try:
                sheet_url = export_manager.export_to_google_sheets(
                    competitors, keywords, google_sheet_id
                )
                print_success(f"Google Sheet updated: {sheet_url}")
            except Exception as e:
                console.print(f"[red]Google Sheets export failed: {str(e)}[/red]")
        
        print_success("\nAnalysis complete!")
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Analysis cancelled by user[/yellow]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        if verbose:
            console.print_exception()
        raise typer.Exit(1)


@app.command()
def history(
    limit: int = typer.Option(10, "--limit", "-l", help="Number of recent runs to show")
):
    """Show analysis history from database."""
    try:
        db = create_database()
        runs = db.get_analysis_runs(limit)
        
        if not runs:
            console.print("[yellow]No analysis runs found in database[/yellow]")
            return
        
        table = Table(title="Analysis History")
        table.add_column("ID", style="cyan")
        table.add_column("Date", style="green")
        table.add_column("Keywords", style="blue")
        table.add_column("Engine", style="magenta")
        table.add_column("Competitors", style="yellow")
        table.add_column("Top Competitor", style="red")
        
        for run in runs:
            keywords_display = truncate_string(run['keywords'], 50)
            
            table.add_row(
                str(run['id']),
                run['created_at'][:16],  # Remove seconds
                keywords_display,
                run['engine'].upper(),
                str(run['total_competitors']),
                run['top_competitor'] or "N/A"
            )
        
        console.print(table)
        
    except Exception as e:
        handle_error_and_exit(e, "Error accessing database")


@app.command()
def show(run_id: int):
    """Show detailed results for a specific analysis run."""
    try:
        db = create_database()
        competitors = db.get_competitors_by_run(run_id)
        
        if not competitors:
            console.print(f"[red]No results found for run ID {run_id}[/red]")
            raise typer.Exit(1)
        
        table = Table(title=f"Analysis Run #{run_id} Results")
        table.add_column("Rank", style="cyan")
        table.add_column("Domain", style="green")
        table.add_column("Appearances", style="yellow")
        table.add_column("Weighted Score", style="magenta")
        table.add_column("Keywords", style="blue")
        
        for competitor in competitors[:20]:  # Show top 20
            keywords_str = ", ".join([
                f"{kw}({rank})" for kw, rank in competitor['keyword_appearances'].items()
            ])
            
            table.add_row(
                str(competitor['rank_position']),
                competitor['domain'],
                str(competitor['count']),
                f"{competitor['weighted_score']:.1f}",
                truncate_string(keywords_str, 50)
            )
        
        console.print(table)
        
    except Exception as e:
        handle_error_and_exit(e)


@app.command()
def stats():
    """Show database statistics."""
    try:
        db = create_database()
        stats = db.get_database_stats()
        
        panel_content = f"""
[cyan]Total Analysis Runs:[/cyan] {stats['total_runs']}
[green]Total Competitors Tracked:[/green] {stats['total_competitors']}
[yellow]Unique Domains:[/yellow] {stats['unique_domains']}
[blue]Latest Analysis:[/blue] {stats['latest_run'] or 'Never'}
[magenta]Database Size:[/magenta] {stats['db_size_mb']} MB
        """
        
        console.print(Panel(panel_content.strip(), title="Database Statistics"))
        
    except Exception as e:
        handle_error_and_exit(e)


def _display_results(competitors, keywords, summary, verbose=False):
    """Display analysis results in a formatted table."""
    
    # Summary panel
    summary_content = f"""
[cyan]Keywords Analyzed:[/cyan] {len(keywords)}
[green]Total Competitors:[/green] {summary['total_competitors']}
[yellow]Top Competitor:[/yellow] {summary['top_competitor'] or 'N/A'}
[blue]Avg Weighted Score:[/blue] {summary['avg_weighted_score']:.1f}
    """
    
    console.print(Panel(summary_content.strip(), title="Analysis Summary"))
    
    # Results table
    table = Table(title="Top Competitors")
    table.add_column("Rank", style="cyan", width=6)
    table.add_column("Domain", style="green", width=25)
    table.add_column("Appearances", style="yellow", width=12)
    table.add_column("Weighted Score", style="magenta", width=15)
    
    if verbose:
        table.add_column("Keywords", style="blue", width=30)
    
    for i, competitor in enumerate(competitors, 1):
        row = [
            str(i),
            competitor.domain,
            str(competitor.count),
            f"{competitor.weighted_score:.1f}"
        ]
        
        if verbose:
            keywords_str = ", ".join([
                f"{kw}({rank})" for kw, rank in competitor.keyword_appearances.items()
            ])
            row.append(truncate_string(keywords_str, 28))
        
        table.add_row(*row)
    
    console.print(table)


if __name__ == "__main__":
    app()