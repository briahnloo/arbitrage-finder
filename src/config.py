"""
Configuration module for the Arbitrage Finder system.
Loads environment variables and defines system constants.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
# Get the directory where this config.py file is located (project root)
env_path = Path(__file__).parent.parent / '.env'
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

# Sport rotation for optimization (stagger API calls)
# Each rotation checks 2 sports instead of all 8
# Cycles through every 4 cycles (every 40-50 minutes at peak, 2+ hours off-peak)
SPORT_ROTATION = [
    ['mma_mixed_martial_arts', 'boxing_boxing'],           # Group 1
    ['soccer_epl', 'soccer_spain_la_liga'],                # Group 2
    ['soccer_italy_serie_a', 'soccer_germany_bundesliga'], # Group 3
    ['icehockey_nhl', 'icehockey_sweden_hockey_league'],   # Group 4
]

# API Parameters
API_REGIONS = 'us'  # US sportsbooks
API_MARKETS = 'h2h,spreads,totals'  # All markets for maximum arbitrage detection
# Includes: moneyline (h2h), point spreads, and totals (over/under)
# 3 credits per request but finds more arbitrage opportunities across all market types
ODDS_FORMAT = 'decimal'  # Decimal odds format for easier calculations

# Market type display names
MARKET_DISPLAY_NAMES = {
    'h2h': 'Moneyline',
    'totals': 'Total Points',
    'spreads': 'Point Spread'
}

# System Configuration
MINIMUM_PROFIT_THRESHOLD = 0.5  # Minimum profit percentage to trigger alert (0.5%)
# Lowered from 1.0% to catch more arbitrage opportunities
# Still provides safety margin for execution risk
DEFAULT_STAKE = 100  # Default total investment amount in dollars ($100)

# Output Configuration
SHOW_INDIVIDUAL_ALERTS = True  # Show individual alerts for each opportunity (default: True)
TOP_OPPORTUNITIES_COUNT = 5  # Number of top opportunities to display in summary (default: 5)

# Dynamic check intervals (minutes) based on time of day
PEAK_HOURS_START = 14  # 2pm
PEAK_HOURS_END = 23    # 11pm
PEAK_CHECK_INTERVAL = 2      # Check every 2 minutes during peak
OFF_PEAK_CHECK_INTERVAL = 30  # Check every 30 minutes during off-peak

# Alert Configuration
DUPLICATE_ALERT_WINDOW_SECONDS = 3600  # Don't re-alert same opportunity within 1 hour

# Discord Configuration
DISCORD_PREMIUM_ALERTS_CHANNEL_ID = 1439531000303718491  # Premium subscriber alerts
DISCORD_FREE_PREVIEW_CHANNEL_ID = 1439540774864949268     # Free user preview alerts
DISCORD_ANNOUNCEMENTS_CHANNEL_ID = 1439530466200915978    # System announcements
DEFAULT_ALERT_CHANNEL_ID = DISCORD_FREE_PREVIEW_CHANNEL_ID  # Default to free if not specified

# Database Configuration
DATABASE_PATH = 'data/arbitrage_data.db'  # SQLite database file
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
MINIMUM_BOOKMAKER_TRUST = 6  # Only alert for books with trust >= 6 (LOWERED from 7 - Phase 1 optimization)

# Event timing filters
MINIMUM_EVENT_START_HOURS = 0.25  # Don't alert for events starting in < 15 minutes (LOWERED from 0.5 - Phase 1 optimization)
MAXIMUM_EVENT_START_DAYS = 7      # Don't alert for events more than 7 days away

# Sport-specific minimum profit thresholds (override MINIMUM_PROFIT_THRESHOLD)
# PHASE 1 OPTIMIZATION: Lowered soccer/hockey thresholds from 1.2% to 1.0% to account for 3-way complexity
SPORT_PROFIT_THRESHOLDS = {
    'mma_mixed_martial_arts': 0.8,  # MMA: accept 0.8%+ (high volume, 2-way easier)
    'boxing_boxing': 0.8,            # Boxing: accept 0.8%+ (high volume, 2-way easier)
    'soccer_epl': 1.0,               # Soccer: lowered from 1.2% to 1.0% (Phase 1 - 3-way is mathematically harder)
    'soccer_spain_la_liga': 1.0,     # La Liga: lowered from 1.2% to 1.0%
    'soccer_italy_serie_a': 1.0,     # Serie A: lowered from 1.2% to 1.0%
    'soccer_germany_bundesliga': 1.0, # Bundesliga: lowered from 1.2% to 1.0%
    'icehockey_nhl': 1.0,            # Hockey: keep at 1.0%
    'icehockey_sweden_hockey_league': 1.0,  # SHL: keep at 1.0%
}

# ═══════════════════════════════════════════════════════════════════════════════════
# PHASE 1 OPTIONAL ENHANCEMENTS (Low-Risk Detection Expansions)
# ═══════════════════════════════════════════════════════════════════════════════════

# Enable 2-way soccer/hockey arbitrage detection when draw odds are not available
# This is mathematically safe: if no bookmaker offers draw odds, 2-way is a complete partition
ALLOW_2WAY_SOCCER_HOCKEY_NO_DRAWS = True  # PHASE 1: New toggle

# Enable basic implied probability validation
# Validates that implied probability sum is reasonable (catches obvious misprices)
ENABLE_PROBABILITY_VALIDATION = True  # PHASE 1: New toggle

# Implied probability thresholds for sanity checks
# If implied prob sum exceeds this, odds are likely misconfigured or stale
MAXIMUM_IMPLIED_PROBABILITY = 1.15  # Allow up to 15% margin (suspicious but possible)
WARN_IMPLIED_PROBABILITY = 1.10     # Warn if probability sum exceeds 10% margin

# ═══════════════════════════════════════════════════════════════════════════════════
# DISCORD CONFIGURATION VALIDATION
# ═══════════════════════════════════════════════════════════════════════════════════

def _validate_discord_config():
    """
    Validate Discord channel IDs and alert user to configuration issues.
    Runs at module load time to catch errors early.
    """
    import logging
    logger = logging.getLogger(__name__)

    issues = []

    # Check if channel IDs look valid (Discord snowflakes are typically 18-19 digits)
    premium_id_str = str(DISCORD_PREMIUM_ALERTS_CHANNEL_ID)
    free_id_str = str(DISCORD_FREE_PREVIEW_CHANNEL_ID)

    if len(premium_id_str) < 17:
        issues.append(f'Premium channel ID looks invalid (too short): {DISCORD_PREMIUM_ALERTS_CHANNEL_ID}')

    if len(free_id_str) < 17:
        issues.append(f'Free preview channel ID looks invalid (too short): {DISCORD_FREE_PREVIEW_CHANNEL_ID}')

    # Check for known placeholder values
    placeholder_id = 123456789012345678
    if DISCORD_PREMIUM_ALERTS_CHANNEL_ID == placeholder_id:
        issues.append(f'Premium channel ID is placeholder value (not configured)')

    if DISCORD_FREE_PREVIEW_CHANNEL_ID == placeholder_id:
        issues.append(f'Free preview channel ID is placeholder value (not configured)')

    # Report findings
    if issues:
        logger.warning('=' * 80)
        logger.warning('[DISCORD CONFIG] ⚠️  Configuration Issues Detected:')
        for issue in issues:
            logger.warning(f'  - {issue}')
        logger.warning('[DISCORD CONFIG] 📋 Please verify channel IDs:')
        logger.warning(f'  1. In Discord, right-click channel → Copy Channel ID')
        logger.warning(f'  2. Update src/config.py or .env with correct IDs')
        logger.warning(f'  3. Alerts will NOT be sent until this is fixed')
        logger.warning('=' * 80)
        return False
    else:
        logger.info(f'[DISCORD CONFIG] ✓ Discord channel IDs validated')
        logger.info(f'  Premium channel: {DISCORD_PREMIUM_ALERTS_CHANNEL_ID}')
        logger.info(f'  Free preview channel: {DISCORD_FREE_PREVIEW_CHANNEL_ID}')
        return True

# Call validation at module load
try:
    _validate_discord_config()
except Exception as e:
    print(f'[ERROR] Discord config validation failed: {e}')

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

