#!/usr/bin/env python3
"""
Test script to verify the pipeline works with mock data.
"""
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.serp import SerpResult
from src.parser import create_domain_parser
from src.export import create_export_manager

def create_mock_serp_data():
    """Create mock SERP data for testing."""
    mock_data = {
        "nike shoes": [
            SerpResult("Nike Official - Running Shoes", "https://www.nike.com/running-shoes", 1),
            SerpResult("Adidas Running Shoes", "https://www.adidas.com/running", 2),
            SerpResult("Amazon Nike Shoes", "https://www.amazon.com/nike-shoes", 3),
            SerpResult("Foot Locker Nike", "https://www.footlocker.com/nike", 4),
            SerpResult("Zappos Nike Collection", "https://www.zappos.com/nike-shoes", 5),
        ],
        "running shoes": [
            SerpResult("Nike Running Shoes", "https://www.nike.com/running", 1),
            SerpResult("Adidas Ultra Boost", "https://www.adidas.com/ultraboost", 2),
            SerpResult("New Balance Running", "https://www.newbalance.com/running-shoes", 3),
            SerpResult("Brooks Running Shoes", "https://www.brooksrunning.com", 4),
            SerpResult("Amazon Running Shoes", "https://www.amazon.com/running-shoes", 5),
        ],
        "athletic footwear": [
            SerpResult("Nike Athletic Shoes", "https://www.nike.com/athletic-shoes", 1),
            SerpResult("Adidas Athletic Footwear", "https://www.adidas.com/athletic", 2),
            SerpResult("Under Armour Shoes", "https://www.underarmour.com/shoes", 3),
            SerpResult("Puma Athletic Shoes", "https://www.puma.com/athletic", 4),
            SerpResult("Reebok Fitness Shoes", "https://www.reebok.com/fitness", 5),
        ]
    }
    return mock_data

def test_pipeline():
    """Test the complete pipeline with mock data."""
    print("🧪 Testing Competitor Discovery Pipeline")
    print("=" * 50)
    
    # Create mock data
    print("📊 Creating mock SERP data...")
    serp_data = create_mock_serp_data()
    keywords = list(serp_data.keys())
    
    print(f"✓ Created mock data for {len(keywords)} keywords")
    for keyword, results in serp_data.items():
        print(f"  - {keyword}: {len(results)} results")
    
    # Parse and rank competitors
    print("\n🔍 Parsing domains and ranking competitors...")
    parser = create_domain_parser()
    competitors = parser.parse_serp_results(serp_data, max_rank=20)
    
    print(f"✓ Found {len(competitors)} competitors")
    
    # Generate summary
    summary = parser.get_domain_summary(competitors)
    print(f"✓ Top competitor: {summary['top_competitor']}")
    print(f"✓ Average weighted score: {summary['avg_weighted_score']:.1f}")
    
    # Display top 10 results
    print("\n🏆 Top 10 Competitors:")
    print("-" * 60)
    for i, competitor in enumerate(competitors[:10], 1):
        keyword_list = ", ".join([f"{kw}({rank})" for kw, rank in competitor.keyword_appearances.items()])
        print(f"{i:2d}. {competitor.domain:<25} | Score: {competitor.weighted_score:5.1f} | {keyword_list}")
    
    # Test export functionality
    print("\n📤 Testing export functionality...")
    export_manager = create_export_manager()
    
    # Export to CSV
    csv_path = export_manager.export_to_csv(competitors, keywords, "test_results.csv")
    print(f"✓ CSV exported to: {csv_path}")
    
    # Export summary
    summary_path = export_manager.export_summary_csv(competitors, keywords, summary, "test_summary.csv")
    print(f"✓ Summary exported to: {summary_path}")
    
    print("\n✅ Pipeline test completed successfully!")
    print("\nNext steps:")
    print("1. Set up SerpApi key in .env file for real SERP data")
    print("2. Test with: python main.py analyze --keywords 'your keywords here'")

if __name__ == "__main__":
    test_pipeline()