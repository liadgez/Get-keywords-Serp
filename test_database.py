#!/usr/bin/env python3
"""
Test database functionality with mock data.
"""
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.serp import SerpResult
from src.parser import create_domain_parser, CompetitorResult
from src.db import create_database

def create_mock_competitors():
    """Create mock competitor data for testing."""
    competitors = [
        CompetitorResult("nike.com", 3, 60.0),
        CompetitorResult("adidas.com", 3, 57.0),
        CompetitorResult("newbalance.com", 1, 18.0),
        CompetitorResult("underarmour.com", 1, 18.0),
        CompetitorResult("footlocker.com", 1, 17.0),
    ]
    
    # Add keyword appearances
    competitors[0].add_keyword_appearance("nike shoes", 1)
    competitors[0].add_keyword_appearance("running shoes", 1)
    competitors[0].add_keyword_appearance("athletic footwear", 1)
    
    competitors[1].add_keyword_appearance("nike shoes", 2)
    competitors[1].add_keyword_appearance("running shoes", 2)
    competitors[1].add_keyword_appearance("athletic footwear", 2)
    
    competitors[2].add_keyword_appearance("running shoes", 3)
    competitors[3].add_keyword_appearance("athletic footwear", 3)
    competitors[4].add_keyword_appearance("nike shoes", 4)
    
    return competitors

def test_database():
    """Test database functionality."""
    print("🗄️  Testing Database Functionality")
    print("=" * 50)
    
    # Create database
    print("📊 Creating database...")
    db = create_database()
    
    # Create mock data
    keywords = ["nike shoes", "running shoes", "athletic footwear"]
    competitors = create_mock_competitors()
    
    print(f"✓ Created mock data: {len(keywords)} keywords, {len(competitors)} competitors")
    
    # Save analysis run
    print("\n💾 Saving analysis run...")
    run_id = db.save_analysis_run(
        keywords=keywords,
        competitors=competitors,
        engine="google",
        num_results=20,
        notes="Test run with mock data"
    )
    
    print(f"✓ Saved analysis run #{run_id}")
    
    # Get database stats
    print("\n📈 Database statistics:")
    stats = db.get_database_stats()
    for key, value in stats.items():
        print(f"  - {key}: {value}")
    
    # Get analysis runs
    print("\n📋 Recent analysis runs:")
    runs = db.get_analysis_runs(limit=5)
    for run in runs:
        print(f"  - Run #{run['id']}: {run['keywords'][:50]}... ({run['total_competitors']} competitors)")
    
    # Get competitors for the run
    print(f"\n🏆 Competitors from run #{run_id}:")
    competitors_from_db = db.get_competitors_by_run(run_id)
    for comp in competitors_from_db[:5]:
        keywords_str = ", ".join([f"{kw}({rank})" for kw, rank in comp['keyword_appearances'].items()])
        print(f"  - {comp['domain']}: {comp['weighted_score']:.1f} points | {keywords_str}")
    
    # Get domain history
    print(f"\n📊 Domain history for 'nike.com':")
    history = db.get_domain_history("nike.com", limit=3)
    for record in history:
        print(f"  - {record['created_at'][:16]}: {record['weighted_score']:.1f} points (rank {record['rank_position']})")
    
    print("\n✅ Database test completed successfully!")

if __name__ == "__main__":
    test_database()