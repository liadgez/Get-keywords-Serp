"""
SQLite database operations for storing competitor analysis results.
"""
import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path
from .parser import CompetitorResult


class CompetitorDatabase:
    """SQLite database manager for competitor analysis results."""
    
    def __init__(self, db_path: str = None):
        """
        Initialize database connection.
        
        Args:
            db_path: Path to SQLite database file
        """
        if db_path is None:
            db_path = os.getenv('DATABASE_PATH', './data/competitors.db')
        
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self._init_database()
    
    def _init_database(self):
        """Initialize database schema."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Analysis runs table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS analysis_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    keywords TEXT NOT NULL,
                    engine TEXT NOT NULL,
                    num_results INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    total_competitors INTEGER DEFAULT 0,
                    top_competitor TEXT,
                    notes TEXT
                )
            ''')
            
            # Competitor results table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS competitor_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id INTEGER NOT NULL,
                    domain TEXT NOT NULL,
                    count INTEGER NOT NULL,
                    weighted_score REAL NOT NULL,
                    rank_position INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (run_id) REFERENCES analysis_runs (id) ON DELETE CASCADE
                )
            ''')
            
            # Keyword appearances table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS keyword_appearances (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    competitor_id INTEGER NOT NULL,
                    keyword TEXT NOT NULL,
                    serp_rank INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (competitor_id) REFERENCES competitor_results (id) ON DELETE CASCADE
                )
            ''')
            
            # Create indexes for better performance
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_competitor_results_run_id 
                ON competitor_results (run_id)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_keyword_appearances_competitor_id 
                ON keyword_appearances (competitor_id)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_analysis_runs_created_at 
                ON analysis_runs (created_at)
            ''')
            
            conn.commit()
    
    def save_analysis_run(
        self,
        keywords: List[str],
        competitors: List[CompetitorResult],
        engine: str = "google",
        num_results: int = 20,
        notes: str = None
    ) -> int:
        """
        Save complete analysis run to database.
        
        Args:
            keywords: List of keywords analyzed
            competitors: List of competitor results
            engine: Search engine used
            num_results: Number of results fetched per keyword
            notes: Optional notes about the run
            
        Returns:
            Analysis run ID
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Insert analysis run
            cursor.execute('''
                INSERT INTO analysis_runs 
                (keywords, engine, num_results, total_competitors, top_competitor, notes)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                ','.join(keywords),
                engine,
                num_results,
                len(competitors),
                competitors[0].domain if competitors else None,
                notes
            ))
            
            run_id = cursor.lastrowid
            
            # Insert competitor results
            for rank, competitor in enumerate(competitors, 1):
                cursor.execute('''
                    INSERT INTO competitor_results 
                    (run_id, domain, count, weighted_score, rank_position)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    run_id,
                    competitor.domain,
                    competitor.count,
                    competitor.weighted_score,
                    rank
                ))
                
                competitor_id = cursor.lastrowid
                
                # Insert keyword appearances
                for keyword, serp_rank in competitor.keyword_appearances.items():
                    cursor.execute('''
                        INSERT INTO keyword_appearances 
                        (competitor_id, keyword, serp_rank)
                        VALUES (?, ?, ?)
                    ''', (competitor_id, keyword, serp_rank))
            
            conn.commit()
            return run_id
    
    def get_analysis_runs(self, limit: int = 10) -> List[Dict]:
        """
        Get recent analysis runs.
        
        Args:
            limit: Maximum number of runs to return
            
        Returns:
            List of analysis run dictionaries
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, keywords, engine, num_results, created_at, 
                       total_competitors, top_competitor, notes
                FROM analysis_runs 
                ORDER BY created_at DESC 
                LIMIT ?
            ''', (limit,))
            
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def get_competitors_by_run(self, run_id: int) -> List[Dict]:
        """
        Get competitor results for a specific run.
        
        Args:
            run_id: Analysis run ID
            
        Returns:
            List of competitor result dictionaries
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT cr.id, cr.domain, cr.count, cr.weighted_score, cr.rank_position,
                       GROUP_CONCAT(ka.keyword || ':' || ka.serp_rank) as keyword_ranks
                FROM competitor_results cr
                LEFT JOIN keyword_appearances ka ON cr.id = ka.competitor_id
                WHERE cr.run_id = ?
                GROUP BY cr.id, cr.domain, cr.count, cr.weighted_score, cr.rank_position
                ORDER BY cr.rank_position
            ''', (run_id,))
            
            competitors = []
            for row in cursor.fetchall():
                competitor = {
                    'id': row[0],
                    'domain': row[1],
                    'count': row[2],
                    'weighted_score': row[3],
                    'rank_position': row[4],
                    'keyword_appearances': {}
                }
                
                # Parse keyword appearances
                if row[5]:
                    for kw_rank in row[5].split(','):
                        if ':' in kw_rank:
                            keyword, rank = kw_rank.split(':', 1)
                            competitor['keyword_appearances'][keyword] = int(rank)
                
                competitors.append(competitor)
            
            return competitors
    
    def get_domain_history(self, domain: str, limit: int = 10) -> List[Dict]:
        """
        Get historical performance for a specific domain.
        
        Args:
            domain: Domain to analyze
            limit: Maximum number of records to return
            
        Returns:
            List of historical performance records
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT ar.created_at, ar.keywords, cr.count, cr.weighted_score, cr.rank_position
                FROM competitor_results cr
                JOIN analysis_runs ar ON cr.run_id = ar.id
                WHERE cr.domain = ?
                ORDER BY ar.created_at DESC
                LIMIT ?
            ''', (domain, limit))
            
            columns = ['created_at', 'keywords', 'count', 'weighted_score', 'rank_position']
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def delete_analysis_run(self, run_id: int) -> bool:
        """
        Delete an analysis run and all associated data.
        
        Args:
            run_id: Analysis run ID to delete
            
        Returns:
            True if deletion successful
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM analysis_runs WHERE id = ?', (run_id,))
            
            return cursor.rowcount > 0
    
    def get_database_stats(self) -> Dict:
        """
        Get database statistics.
        
        Returns:
            Dictionary with database statistics
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            stats = {}
            
            # Count analysis runs
            cursor.execute('SELECT COUNT(*) FROM analysis_runs')
            stats['total_runs'] = cursor.fetchone()[0]
            
            # Count competitor results
            cursor.execute('SELECT COUNT(*) FROM competitor_results')
            stats['total_competitors'] = cursor.fetchone()[0]
            
            # Count unique domains
            cursor.execute('SELECT COUNT(DISTINCT domain) FROM competitor_results')
            stats['unique_domains'] = cursor.fetchone()[0]
            
            # Latest run
            cursor.execute('SELECT MAX(created_at) FROM analysis_runs')
            stats['latest_run'] = cursor.fetchone()[0]
            
            # Database file size
            stats['db_size_mb'] = round(os.path.getsize(self.db_path) / (1024 * 1024), 2)
            
            return stats


def create_database(db_path: str = None) -> CompetitorDatabase:
    """
    Create CompetitorDatabase instance.
    
    Args:
        db_path: Optional path to database file
        
    Returns:
        Configured CompetitorDatabase instance
    """
    return CompetitorDatabase(db_path)