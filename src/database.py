"""
Database module for tracking arbitrage opportunities.
Uses SQLite to store historical data for analytics.
"""

import sqlite3
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path


class ArbitrageDatabase:
    """Database manager for arbitrage opportunities."""
    
    def __init__(self, db_path: str):
        """
        Initialize database connection.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.conn = None
        self.init_database()
    
    def init_database(self):
        """Create database tables if they don't exist."""
        try:
            self.conn = sqlite3.connect(self.db_path)
            cursor = self.conn.cursor()
            
            # Opportunities table - stores all found arbitrage opportunities
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS opportunities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    sport TEXT NOT NULL,
                    market TEXT NOT NULL,
                    event_name TEXT NOT NULL,
                    num_outcomes INTEGER NOT NULL,
                    player_a TEXT NOT NULL,
                    player_b TEXT,
                    player_draw TEXT,
                    odds_a REAL NOT NULL,
                    odds_b REAL,
                    odds_draw REAL,
                    bookmaker_a TEXT NOT NULL,
                    bookmaker_b TEXT,
                    bookmaker_draw TEXT,
                    profit_margin REAL NOT NULL,
                    stake_a REAL NOT NULL,
                    stake_b REAL,
                    stake_draw REAL,
                    guaranteed_profit REAL NOT NULL,
                    total_stake REAL NOT NULL,
                    commence_time TEXT NOT NULL
                )
            ''')
            
            # Alerts sent table - tracks which opportunities were alerted
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS alerts_sent (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    opportunity_id INTEGER NOT NULL,
                    timestamp TEXT NOT NULL,
                    FOREIGN KEY (opportunity_id) REFERENCES opportunities(id)
                )
            ''')
            
            # Bets placed table - user can manually record bets taken
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS bets_placed (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    opportunity_id INTEGER NOT NULL,
                    timestamp TEXT NOT NULL,
                    actual_profit REAL,
                    notes TEXT,
                    FOREIGN KEY (opportunity_id) REFERENCES opportunities(id)
                )
            ''')
            
            self.conn.commit()
            
        except sqlite3.Error as e:
            print(f"[DATABASE ERROR] Failed to initialize database: {e}")
    
    def log_opportunity(self, opportunity: Dict) -> Optional[int]:
        """
        Log a found arbitrage opportunity to the database.
        
        Args:
            opportunity: Dictionary containing opportunity details
        
        Returns:
            Opportunity ID if successful, None otherwise
        """
        try:
            cursor = self.conn.cursor()
            
            # Extract values with defaults
            num_outcomes = opportunity.get('num_outcomes', 2)
            timestamp = datetime.now().isoformat()
            
            if num_outcomes == 2:
                cursor.execute('''
                    INSERT INTO opportunities (
                        timestamp, sport, market, event_name, num_outcomes,
                        player_a, player_b, player_draw,
                        odds_a, odds_b, odds_draw,
                        bookmaker_a, bookmaker_b, bookmaker_draw,
                        profit_margin, stake_a, stake_b, stake_draw,
                        guaranteed_profit, total_stake, commence_time
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    timestamp,
                    opportunity['sport'],
                    opportunity.get('market', 'h2h'),
                    opportunity.get('event_name', f"{opportunity['player_a']} vs {opportunity['player_b']}"),
                    num_outcomes,
                    opportunity['player_a'],
                    opportunity['player_b'],
                    None,  # no draw
                    opportunity['odds_a'],
                    opportunity['odds_b'],
                    None,  # no draw odds
                    opportunity['bookmaker_a'],
                    opportunity['bookmaker_b'],
                    None,  # no draw bookmaker
                    opportunity['profit_margin'],
                    opportunity['stake_a'],
                    opportunity['stake_b'],
                    None,  # no draw stake
                    opportunity['guaranteed_profit'],
                    opportunity['total_stake'],
                    opportunity['commence_time']
                ))
            else:  # 3-way
                cursor.execute('''
                    INSERT INTO opportunities (
                        timestamp, sport, market, event_name, num_outcomes,
                        player_a, player_b, player_draw,
                        odds_a, odds_b, odds_draw,
                        bookmaker_a, bookmaker_b, bookmaker_draw,
                        profit_margin, stake_a, stake_b, stake_draw,
                        guaranteed_profit, total_stake, commence_time
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    timestamp,
                    opportunity['sport'],
                    opportunity.get('market', 'h2h'),
                    opportunity.get('event_name', ''),
                    num_outcomes,
                    opportunity['player_a'],
                    opportunity['player_b'],
                    opportunity['player_draw'],
                    opportunity['odds_a'],
                    opportunity['odds_b'],
                    opportunity['odds_draw'],
                    opportunity['bookmaker_a'],
                    opportunity['bookmaker_b'],
                    opportunity['bookmaker_draw'],
                    opportunity['profit_margin'],
                    opportunity['stake_a'],
                    opportunity['stake_b'],
                    opportunity['stake_draw'],
                    opportunity['guaranteed_profit'],
                    opportunity['total_stake'],
                    opportunity['commence_time']
                ))
            
            self.conn.commit()
            return cursor.lastrowid
            
        except sqlite3.Error as e:
            print(f"[DATABASE ERROR] Failed to log opportunity: {e}")
            return None
    
    def log_alert(self, opportunity_id: int):
        """
        Log that an alert was sent for an opportunity.
        
        Args:
            opportunity_id: ID of the opportunity from opportunities table
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO alerts_sent (opportunity_id, timestamp)
                VALUES (?, ?)
            ''', (opportunity_id, datetime.now().isoformat()))
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"[DATABASE ERROR] Failed to log alert: {e}")
    
    def mark_bet_placed(self, opportunity_id: int, actual_profit: Optional[float] = None, notes: str = ""):
        """
        Mark that user placed bets for an opportunity.
        
        Args:
            opportunity_id: ID of the opportunity
            actual_profit: Actual profit realized (if known)
            notes: Optional notes about the bet
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO bets_placed (opportunity_id, timestamp, actual_profit, notes)
                VALUES (?, ?, ?, ?)
            ''', (opportunity_id, datetime.now().isoformat(), actual_profit, notes))
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"[DATABASE ERROR] Failed to mark bet placed: {e}")
    
    def get_opportunities(self, limit: int = 100, sport: Optional[str] = None) -> List[Dict]:
        """
        Retrieve opportunities from database with optional filtering.
        
        Args:
            limit: Maximum number of opportunities to return
            sport: Optional sport filter
        
        Returns:
            List of opportunity dictionaries
        """
        try:
            cursor = self.conn.cursor()
            
            if sport:
                cursor.execute('''
                    SELECT * FROM opportunities
                    WHERE sport = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                ''', (sport, limit))
            else:
                cursor.execute('''
                    SELECT * FROM opportunities
                    ORDER BY timestamp DESC
                    LIMIT ?
                ''', (limit,))
            
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
            
        except sqlite3.Error as e:
            print(f"[DATABASE ERROR] Failed to retrieve opportunities: {e}")
            return []
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()

