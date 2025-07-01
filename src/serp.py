"""
SERP (Search Engine Results Page) fetching module with SerpApi and fallback scraping.
"""
import os
import time
import random
from typing import List, Dict, Optional
import requests
from bs4 import BeautifulSoup
from serpapi import GoogleSearch
import typer
from rich.progress import Progress, SpinnerColumn, TextColumn

# Import shared utilities to eliminate duplication
from utils.retry import retry_function


class SerpResult:
    """Container for a single search result."""
    
    def __init__(self, title: str, url: str, rank: int):
        self.title = title
        self.url = url
        self.rank = rank


class SerpFetcher:
    """Main class for fetching search engine results."""
    
    def __init__(self, api_key: str = None, engine: str = "google"):
        """
        Initialize SERP fetcher.
        
        Args:
            api_key: SerpApi API key (optional, falls back to scraping)
            engine: Search engine to use ("google" or "bing")
        """
        self.api_key = api_key
        self.engine = engine.lower()
        self.session = requests.Session()
        
        # Set user agent for web scraping fallback
        user_agents = [
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        ]
        self.session.headers.update({
            'User-Agent': random.choice(user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
    
    def fetch_serp_results(
        self, 
        keyword: str, 
        num_results: int = 20,
        max_retries: int = 3
    ) -> List[SerpResult]:
        """
        Fetch SERP results for a keyword.
        
        Args:
            keyword: Search keyword
            num_results: Number of results to fetch (max 20)
            max_retries: Maximum retry attempts
            
        Returns:
            List of SerpResult objects
        """
        # Try API first if available
        if self.api_key:
            try:
                return self._fetch_with_api(keyword, num_results, max_retries)
            except Exception as e:
                typer.echo(f"API fetch failed for '{keyword}': {e}")
                typer.echo("Falling back to web scraping...")
        
        # Fallback to web scraping
        return self._fetch_with_scraping(keyword, num_results, max_retries)
    
    def _fetch_with_api(
        self, 
        keyword: str, 
        num_results: int,
        max_retries: int
    ) -> List[SerpResult]:
        """Fetch results using SerpApi with shared retry logic."""
        def _api_call():
            search_params = {
                "engine": self.engine,
                "q": keyword,
                "api_key": self.api_key,
                "num": min(num_results, 20)
            }
            
            if self.engine == "google":
                search_params["pws"] = "0"  # Disable personalization
            
            search = GoogleSearch(search_params)
            results = search.get_dict()
            
            return self._parse_api_results(results)
        
        try:
            return retry_function(_api_call, max_retries=max_retries)
        except Exception:
            return []
    
    def _fetch_with_scraping(
        self, 
        keyword: str, 
        num_results: int,
        max_retries: int
    ) -> List[SerpResult]:
        """Fetch results using web scraping with shared retry logic."""
        if self.engine != "google":
            raise NotImplementedError("Web scraping only supports Google currently")
        
        def _scrape_call():
            # Google search URL
            url = f"https://www.google.com/search?q={requests.utils.quote(keyword)}&num={min(num_results, 20)}&pws=0"
            
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            return self._parse_google_html(response.text)
        
        try:
            return retry_function(_scrape_call, max_retries=max_retries, base_delay=2.0)
        except Exception:
            return []
    
    def _parse_api_results(self, results: Dict) -> List[SerpResult]:
        """Parse SerpApi JSON response."""
        serp_results = []
        
        # Both Google and Bing use "organic_results" key
        organic_results = results.get("organic_results", [])
        
        for i, result in enumerate(organic_results, 1):
            title = result.get("title", "")
            link = result.get("link", "")
            
            if title and link:
                serp_results.append(SerpResult(title, link, i))
        
        return serp_results
    
    def _parse_google_html(self, html: str) -> List[SerpResult]:
        """Parse Google search results HTML."""
        soup = BeautifulSoup(html, 'html.parser')
        serp_results = []
        
        # Find search result containers
        result_containers = soup.find_all('div', class_='g')
        
        for i, container in enumerate(result_containers, 1):
            # Find title and link
            title_elem = container.find('h3')
            link_elem = container.find('a')
            
            if title_elem and link_elem:
                title = title_elem.get_text(strip=True)
                link = link_elem.get('href', '')
                
                # Clean up Google redirect URLs
                if link.startswith('/url?q='):
                    link = link.split('/url?q=')[1].split('&')[0]
                
                if title and link and not link.startswith('#'):
                    serp_results.append(SerpResult(title, link, i))
        
        return serp_results
    
    def fetch_multiple_keywords(
        self, 
        keywords: List[str], 
        num_results: int = 20
    ) -> Dict[str, List[SerpResult]]:
        """
        Fetch SERP results for multiple keywords.
        
        Args:
            keywords: List of keywords to search
            num_results: Number of results per keyword
            
        Returns:
            Dictionary mapping keywords to their SERP results
        """
        results = {}
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            
            task = progress.add_task("Fetching SERP results...", total=len(keywords))
            
            for keyword in keywords:
                progress.update(task, description=f"Fetching: {keyword}")
                
                try:
                    keyword_results = self.fetch_serp_results(keyword, num_results)
                    results[keyword] = keyword_results
                    
                    typer.echo(f"✓ {keyword}: {len(keyword_results)} results")
                    
                    # Rate limiting - small delay between requests
                    if len(keywords) > 1:
                        time.sleep(random.uniform(0.5, 1.5))
                        
                except Exception as e:
                    typer.echo(f"✗ {keyword}: Failed - {str(e)}")
                    results[keyword] = []
                
                progress.advance(task)
        
        return results


def create_serp_fetcher() -> SerpFetcher:
    """
    Create SerpFetcher with API key from environment.
    
    Returns:
        Configured SerpFetcher instance
    """
    api_key = os.getenv('SERPAPI_KEY')
    engine = os.getenv('SEARCH_ENGINE', 'google')
    
    return SerpFetcher(api_key=api_key, engine=engine)