"""
Configuration module for the Arbitrage Finder system.
Loads environment variables and defines system constants.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
# Get the directory where this config.py file is located
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

# API Configuration
ODDS_API_KEY = os.getenv('ODDS_API_KEY')
BASE_API_URL = 'https://api.the-odds-api.com/v4'

# Sports to monitor
# Two-outcome sports (easier arbitrage - only 2 bets needed)
TWO_OUTCOME_SPORTS = ['mma_mixed_martial_arts', 'boxing_boxing']

# Three-outcome sports (3-way: Home/Draw/Away - requires 3 bets)
THREE_OUTCOME_SPORTS = [
    'soccer_epl',              # English Premier League
    'soccer_spain_la_liga',    # La Liga (Spain)
    'soccer_italy_serie_a',    # Serie A (Italy)
    'soccer_germany_bundesliga', # Bundesliga (Germany)
    'icehockey_nhl',           # NHL (North America)
    'icehockey_sweden_hockey_league',  # SHL (Sweden)
]

# All sports combined
SPORTS = TWO_OUTCOME_SPORTS + THREE_OUTCOME_SPORTS

# API Parameters
API_REGIONS = 'us'  # US sportsbooks
API_MARKETS = 'h2h,totals,spreads'  # Moneyline, totals (over/under), and spreads
ODDS_FORMAT = 'decimal'  # Decimal odds format for easier calculations

# Market type display names
MARKET_DISPLAY_NAMES = {
    'h2h': 'Moneyline',
    'totals': 'Total Points',
    'spreads': 'Point Spread'
}

# System Configuration
MINIMUM_PROFIT_THRESHOLD = 1.0  # Minimum profit percentage to trigger alert (1.0%)
DEFAULT_STAKE = 100  # Default total investment amount in dollars ($100)

# Output Configuration
SHOW_INDIVIDUAL_ALERTS = True  # Show individual alerts for each opportunity (default: True)
TOP_OPPORTUNITIES_COUNT = 5  # Number of top opportunities to display in summary (default: 5)

# Dynamic check intervals (minutes) based on time of day
PEAK_HOURS_START = 17  # 5pm
PEAK_HOURS_END = 23    # 11pm
PEAK_CHECK_INTERVAL = 10     # Check every 10 minutes during peak
OFF_PEAK_CHECK_INTERVAL = 30  # Check every 30 minutes during off-peak

# Alert Configuration
DUPLICATE_ALERT_WINDOW_SECONDS = 3600  # Don't re-alert same opportunity within 1 hour

# Database Configuration
DATABASE_PATH = 'arbitrage_data.db'  # SQLite database file
ENABLE_DATABASE_LOGGING = True  # Set to False to disable database logging

# Smart Filtering Configuration
# Bookmaker trust scores (1-10 scale, higher is more trustworthy)
BOOKMAKER_TRUST_SCORES = {
    'FanDuel': 10,
    'DraftKings': 10,
    'BetMGM': 9,
    'Caesars': 9,
    'PointsBet': 8,
    'BetRivers': 8,
    'Unibet': 8,
    'Bovada': 7,
    'MyBookie': 6,
    'BetOnline': 6,
}
MINIMUM_BOOKMAKER_TRUST = 7  # Only alert for books with trust >= 7

# Event timing filters
MINIMUM_EVENT_START_HOURS = 0.5  # Don't alert for events starting in < 30 minutes
MAXIMUM_EVENT_START_DAYS = 7     # Don't alert for events more than 7 days away

# Sport-specific minimum profit thresholds (override MINIMUM_PROFIT_THRESHOLD)
SPORT_PROFIT_THRESHOLDS = {
    'mma_mixed_martial_arts': 0.8,  # MMA: accept 0.8%+ (high volume)
    'boxing_boxing': 0.8,            # Boxing: accept 0.8%+ (high volume)
    'soccer_epl': 1.2,               # Soccer: need 1.2%+ (odds change faster)
    'soccer_spain_la_liga': 1.2,
    'soccer_italy_serie_a': 1.2,
    'soccer_germany_bundesliga': 1.2,
    'icehockey_nhl': 1.0,            # Hockey: need 1.0%+
    'icehockey_sweden_hockey_league': 1.0,
}

# Helper Functions
def get_check_interval() -> int:
    """
    Get the appropriate check interval based on current time of day.
    
    Returns:
        Check interval in minutes (10 during peak hours, 30 during off-peak)
    """
    from datetime import datetime
    current_hour = datetime.now().hour
    
    if PEAK_HOURS_START <= current_hour <= PEAK_HOURS_END:
        return PEAK_CHECK_INTERVAL
    else:
        return OFF_PEAK_CHECK_INTERVAL


def is_three_way_sport(sport_key: str) -> bool:
    """
    Check if a sport uses 3-way betting (Home/Draw/Away).
    
    Args:
        sport_key: API sport key
    
    Returns:
        True if sport is 3-way, False otherwise
    """
    return sport_key in THREE_OUTCOME_SPORTS

# Validation
if not ODDS_API_KEY or ODDS_API_KEY == 'your_api_key_here':
    raise ValueError(
        "ODDS_API_KEY not configured. "
        "Please copy .env.example to .env and add your API key from https://the-odds-api.com/"
    )

