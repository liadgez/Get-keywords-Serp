"""
Domain extraction and competitor ranking logic.
"""
from typing import List, Dict, Tuple
from collections import Counter, defaultdict
from urllib.parse import urlparse
import tldextract
import re
from .serp import SerpResult


class CompetitorResult:
    """Container for competitor analysis results."""
    
    def __init__(self, domain: str, count: int, weighted_score: float):
        self.domain = domain
        self.count = count
        self.weighted_score = weighted_score
        self.keyword_appearances = {}  # keyword -> rank mapping
    
    def add_keyword_appearance(self, keyword: str, rank: int):
        """Add a keyword appearance for this domain."""
        self.keyword_appearances[keyword] = rank


class DomainParser:
    """Main class for parsing domains and calculating competitor rankings."""
    
    def __init__(self):
        """Initialize domain parser with filtering rules."""
        # Domains to exclude from competitor analysis
        self.excluded_domains = {
            'google.com', 'youtube.com', 'facebook.com', 'twitter.com',
            'linkedin.com', 'instagram.com', 'pinterest.com', 'reddit.com',
            'wikipedia.org', 'amazon.com', 'ebay.com', 'etsy.com',
            'shopify.com', 'wordpress.com', 'medium.com', 'quora.com'
        }
        
        # Additional patterns to exclude
        self.excluded_patterns = [
            r'.*\.google\..*',
            r'.*\.youtube\..*',
            r'.*\.facebook\..*',
            r'.*\.amazon\..*'
        ]
    
    def extract_domain(self, url: str) -> str:
        """
        Extract clean root domain from URL.
        
        Args:
            url: Full URL string
            
        Returns:
            Clean root domain (e.g., 'nike.com')
        """
        if not url or not isinstance(url, str):
            return ""
        
        try:
            # Handle URLs without protocol
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            # Use tldextract for accurate domain parsing
            extracted = tldextract.extract(url)
            
            if extracted.domain and extracted.suffix:
                return f"{extracted.domain}.{extracted.suffix}".lower()
            
            return ""
            
        except Exception:
            return ""
    
    def is_valid_competitor(self, domain: str) -> bool:
        """
        Check if domain should be considered as a valid competitor.
        
        Args:
            domain: Domain to validate
            
        Returns:
            True if domain is a valid competitor
        """
        if not domain:
            return False
        
        # Check excluded domains
        if domain in self.excluded_domains:
            return False
        
        # Check excluded patterns
        for pattern in self.excluded_patterns:
            if re.match(pattern, domain):
                return False
        
        # Additional validation
        if len(domain) < 4:  # Too short
            return False
        
        if domain.count('.') > 3:  # Too many subdomains
            return False
        
        return True
    
    def calculate_weighted_score(self, rank: int, max_rank: int = 20) -> float:
        """
        Calculate weighted score based on SERP rank.
        Higher ranks (1, 2, 3) get higher scores.
        
        Args:
            rank: SERP position (1-based)
            max_rank: Maximum rank to consider
            
        Returns:
            Weighted score
        """
        if rank < 1 or rank > max_rank:
            return 0.0
        
        return float(max_rank + 1 - rank)
    
    def parse_serp_results(
        self, 
        serp_data: Dict[str, List[SerpResult]],
        max_rank: int = 20
    ) -> List[CompetitorResult]:
        """
        Parse SERP results and calculate competitor rankings.
        
        Args:
            serp_data: Dictionary mapping keywords to SERP results
            max_rank: Maximum rank to consider for weighting
            
        Returns:
            List of CompetitorResult objects sorted by weighted score
        """
        domain_stats = defaultdict(lambda: {'count': 0, 'weighted_score': 0.0, 'keywords': {}})
        
        # Process each keyword's results
        for keyword, results in serp_data.items():
            for result in results:
                domain = self.extract_domain(result.url)
                
                if not self.is_valid_competitor(domain):
                    continue
                
                # Update domain statistics
                domain_stats[domain]['count'] += 1
                domain_stats[domain]['weighted_score'] += self.calculate_weighted_score(result.rank, max_rank)
                domain_stats[domain]['keywords'][keyword] = result.rank
        
        # Convert to CompetitorResult objects
        competitors = []
        for domain, stats in domain_stats.items():
            competitor = CompetitorResult(
                domain=domain,
                count=stats['count'],
                weighted_score=stats['weighted_score']
            )
            
            # Add keyword appearances
            for keyword, rank in stats['keywords'].items():
                competitor.add_keyword_appearance(keyword, rank)
            
            competitors.append(competitor)
        
        # Sort by weighted score (descending), then by count
        competitors.sort(key=lambda x: (-x.weighted_score, -x.count))
        
        return competitors
    
    def get_domain_summary(self, competitors: List[CompetitorResult]) -> Dict:
        """
        Generate summary statistics for competitor analysis.
        
        Args:
            competitors: List of CompetitorResult objects
            
        Returns:
            Dictionary with summary statistics
        """
        if not competitors:
            return {
                'total_competitors': 0,
                'top_competitor': None,
                'avg_weighted_score': 0.0,
                'domain_distribution': {}
            }
        
        total_score = sum(c.weighted_score for c in competitors)
        
        return {
            'total_competitors': len(competitors),
            'top_competitor': competitors[0].domain,
            'avg_weighted_score': total_score / len(competitors),
            'domain_distribution': {
                c.domain: c.count for c in competitors[:10]  # Top 10
            }
        }
    
    def filter_competitors(
        self, 
        competitors: List[CompetitorResult],
        min_appearances: int = 1,
        min_weighted_score: float = 0.0,
        max_results: int = 50
    ) -> List[CompetitorResult]:
        """
        Filter competitor results based on criteria.
        
        Args:
            competitors: List of CompetitorResult objects
            min_appearances: Minimum number of keyword appearances
            min_weighted_score: Minimum weighted score
            max_results: Maximum number of results to return
            
        Returns:
            Filtered list of competitors
        """
        filtered = [
            c for c in competitors
            if c.count >= min_appearances and c.weighted_score >= min_weighted_score
        ]
        
        return filtered[:max_results]


def create_domain_parser() -> DomainParser:
    """
    Create DomainParser instance.
    
    Returns:
        Configured DomainParser instance
    """
    return DomainParser()