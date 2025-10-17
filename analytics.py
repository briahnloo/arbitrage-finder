"""
Analytics module for arbitrage opportunity statistics.
Provides functions to analyze historical data from the database.
"""

import sqlite3
from typing import Dict, List, Tuple
from collections import defaultdict
import config


def get_summary_stats() -> Dict:
    """
    Get overall summary statistics.
    
    Returns:
        Dictionary with summary statistics
    """
    try:
        conn = sqlite3.connect(config.DATABASE_PATH)
        cursor = conn.cursor()
        
        # Total opportunities found
        cursor.execute('SELECT COUNT(*) FROM opportunities')
        total_opps = cursor.fetchone()[0]
        
        # Total alerts sent
        cursor.execute('SELECT COUNT(*) FROM alerts_sent')
        total_alerts = cursor.fetchone()[0]
        
        # Total bets placed
        cursor.execute('SELECT COUNT(*) FROM bets_placed')
        total_bets = cursor.fetchone()[0]
        
        # Average profit margin
        cursor.execute('SELECT AVG(profit_margin) FROM opportunities')
        avg_profit = cursor.fetchone()[0] or 0
        
        # Best profit margin
        cursor.execute('SELECT MAX(profit_margin) FROM opportunities')
        best_profit = cursor.fetchone()[0] or 0
        
        # Total guaranteed profit if all taken
        cursor.execute('SELECT SUM(guaranteed_profit) FROM opportunities')
        total_potential_profit = cursor.fetchone()[0] or 0
        
        # Actual profit from placed bets
        cursor.execute('SELECT SUM(actual_profit) FROM bets_placed WHERE actual_profit IS NOT NULL')
        actual_profit = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return {
            'total_opportunities': total_opps,
            'total_alerts': total_alerts,
            'total_bets_placed': total_bets,
            'avg_profit_margin': avg_profit,
            'best_profit_margin': best_profit,
            'total_potential_profit': total_potential_profit,
            'actual_profit': actual_profit,
            'alert_rate': (total_alerts / total_opps * 100) if total_opps > 0 else 0,
            'bet_rate': (total_bets / total_alerts * 100) if total_alerts > 0 else 0
        }
    except sqlite3.Error as e:
        print(f"[ANALYTICS ERROR] {e}")
        return {}


def get_opportunities_by_sport() -> List[Tuple[str, int, float]]:
    """
    Get opportunity count and average profit by sport.
    
    Returns:
        List of tuples (sport, count, avg_profit)
    """
    try:
        conn = sqlite3.connect(config.DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT sport, COUNT(*) as count, AVG(profit_margin) as avg_profit
            FROM opportunities
            GROUP BY sport
            ORDER BY count DESC
        ''')
        
        results = cursor.fetchall()
        conn.close()
        
        return results
    except sqlite3.Error as e:
        print(f"[ANALYTICS ERROR] {e}")
        return []


def get_opportunities_by_bookmaker() -> List[Tuple[str, str, int]]:
    """
    Get most common bookmaker pairs for arbitrage.
    
    Returns:
        List of tuples (bookmaker_a, bookmaker_b, count)
    """
    try:
        conn = sqlite3.connect(config.DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT bookmaker_a, bookmaker_b, COUNT(*) as count
            FROM opportunities
            WHERE num_outcomes = 2
            GROUP BY bookmaker_a, bookmaker_b
            ORDER BY count DESC
            LIMIT 20
        ''')
        
        results = cursor.fetchall()
        conn.close()
        
        return results
    except sqlite3.Error as e:
        print(f"[ANALYTICS ERROR] {e}")
        return []


def get_opportunities_by_hour() -> Dict[int, int]:
    """
    Get opportunity count by hour of day.
    
    Returns:
        Dictionary mapping hour (0-23) to count
    """
    try:
        conn = sqlite3.connect(config.DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                CAST(strftime('%H', timestamp) AS INTEGER) as hour,
                COUNT(*) as count
            FROM opportunities
            GROUP BY hour
            ORDER BY hour
        ''')
        
        results = {hour: count for hour, count in cursor.fetchall()}
        conn.close()
        
        return results
    except sqlite3.Error as e:
        print(f"[ANALYTICS ERROR] {e}")
        return {}


def get_profit_distribution() -> List[Tuple[str, int]]:
    """
    Get distribution of profit margins.
    
    Returns:
        List of tuples (profit_range, count)
    """
    try:
        conn = sqlite3.connect(config.DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                CASE 
                    WHEN profit_margin < 0.5 THEN '< 0.5%'
                    WHEN profit_margin < 1.0 THEN '0.5-1.0%'
                    WHEN profit_margin < 1.5 THEN '1.0-1.5%'
                    WHEN profit_margin < 2.0 THEN '1.5-2.0%'
                    WHEN profit_margin < 3.0 THEN '2.0-3.0%'
                    ELSE '> 3.0%'
                END as profit_range,
                COUNT(*) as count
            FROM opportunities
            GROUP BY profit_range
            ORDER BY 
                CASE profit_range
                    WHEN '< 0.5%' THEN 1
                    WHEN '0.5-1.0%' THEN 2
                    WHEN '1.0-1.5%' THEN 3
                    WHEN '1.5-2.0%' THEN 4
                    WHEN '2.0-3.0%' THEN 5
                    WHEN '> 3.0%' THEN 6
                END
        ''')
        
        results = cursor.fetchall()
        conn.close()
        
        return results
    except sqlite3.Error as e:
        print(f"[ANALYTICS ERROR] {e}")
        return []


def get_recent_opportunities(limit: int = 20) -> List[Dict]:
    """
    Get most recent opportunities.
    
    Args:
        limit: Number of opportunities to return
    
    Returns:
        List of opportunity dictionaries
    """
    try:
        conn = sqlite3.connect(config.DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                timestamp, sport, market, event_name, 
                profit_margin, guaranteed_profit,
                bookmaker_a, bookmaker_b
            FROM opportunities
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (limit,))
        
        columns = [desc[0] for desc in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        
        return results
    except sqlite3.Error as e:
        print(f"[ANALYTICS ERROR] {e}")
        return []


def calculate_roi_if_all_taken() -> Dict:
    """
    Calculate theoretical ROI if all opportunities were taken.
    
    Returns:
        Dictionary with ROI calculations
    """
    try:
        conn = sqlite3.connect(config.DATABASE_PATH)
        cursor = conn.cursor()
        
        # Total investment if all opportunities were taken
        cursor.execute('SELECT COUNT(*) * ? FROM opportunities', (config.DEFAULT_STAKE,))
        total_investment = cursor.fetchone()[0] or 0
        
        # Total profit
        cursor.execute('SELECT SUM(guaranteed_profit) FROM opportunities')
        total_profit = cursor.fetchone()[0] or 0
        
        # ROI percentage
        roi_pct = (total_profit / total_investment * 100) if total_investment > 0 else 0
        
        conn.close()
        
        return {
            'total_investment': total_investment,
            'total_profit': total_profit,
            'roi_percentage': roi_pct
        }
    except sqlite3.Error as e:
        print(f"[ANALYTICS ERROR] {e}")
        return {}


def get_opportunities_by_market() -> List[Tuple[str, int, float]]:
    """
    Get opportunity count and average profit by market type.
    
    Returns:
        List of tuples (market, count, avg_profit)
    """
    try:
        conn = sqlite3.connect(config.DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT market, COUNT(*) as count, AVG(profit_margin) as avg_profit
            FROM opportunities
            GROUP BY market
            ORDER BY count DESC
        ''')
        
        results = cursor.fetchall()
        conn.close()
        
        return results
    except sqlite3.Error as e:
        print(f"[ANALYTICS ERROR] {e}")
        return []

