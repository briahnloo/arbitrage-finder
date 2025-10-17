"""
Utility functions for odds conversion, formatting, and calculations.
"""

from datetime import datetime
from typing import Union


def convert_american_to_decimal(american_odds: int) -> float:
    """
    Convert American odds format to decimal odds format.
    
    Args:
        american_odds: American odds (e.g., +110 or -120)
    
    Returns:
        Decimal odds (e.g., 2.10)
    
    Examples:
        +110 -> 2.10
        -120 -> 1.833
    """
    if american_odds > 0:
        return (american_odds / 100) + 1
    else:
        return (100 / abs(american_odds)) + 1


def format_currency(amount: float) -> str:
    """
    Format a dollar amount as currency.
    
    Args:
        amount: Dollar amount
    
    Returns:
        Formatted string (e.g., "$100.00")
    """
    return f"${amount:.2f}"


def format_timestamp(iso_timestamp: str) -> str:
    """
    Format an ISO timestamp to a readable string.
    
    Args:
        iso_timestamp: ISO 8601 timestamp string
    
    Returns:
        Formatted datetime string
    """
    try:
        dt = datetime.fromisoformat(iso_timestamp.replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d %H:%M:%S UTC')
    except Exception:
        return iso_timestamp


def calculate_implied_probability(decimal_odds: float) -> float:
    """
    Calculate the implied probability from decimal odds.
    
    Args:
        decimal_odds: Odds in decimal format
    
    Returns:
        Implied probability as a percentage (0-100)
    
    Example:
        2.00 odds -> 50% implied probability
    """
    return (1 / decimal_odds) * 100


def calculate_arbitrage_profit(odds_a: float, odds_b: float) -> float:
    """
    Calculate the profit margin percentage for an arbitrage opportunity.
    
    Args:
        odds_a: Decimal odds for outcome A
        odds_b: Decimal odds for outcome B
    
    Returns:
        Profit margin as a percentage (e.g., 2.5 for 2.5% profit)
        Returns 0 if no arbitrage exists (sum >= 1.0)
    """
    implied_prob_sum = (1 / odds_a) + (1 / odds_b)
    
    if implied_prob_sum >= 1.0:
        return 0.0
    
    return (1 - implied_prob_sum) * 100


def calculate_stakes(odds_a: float, odds_b: float, total_stake: float) -> tuple:
    """
    Calculate optimal stake distribution for arbitrage betting.
    
    Args:
        odds_a: Decimal odds for outcome A
        odds_b: Decimal odds for outcome B
        total_stake: Total amount to invest
    
    Returns:
        Tuple of (stake_a, stake_b) representing optimal bet amounts
    """
    # Calculate the denominator (sum of inverse odds)
    denominator = (1 / odds_a) + (1 / odds_b)
    
    # Calculate stakes proportionally
    stake_a = total_stake * (1 / odds_a) / denominator
    stake_b = total_stake * (1 / odds_b) / denominator
    
    return (stake_a, stake_b)


def calculate_guaranteed_profit(odds_a: float, odds_b: float, stake_a: float, stake_b: float) -> float:
    """
    Calculate the guaranteed profit from an arbitrage bet.
    
    Args:
        odds_a: Decimal odds for outcome A
        odds_b: Decimal odds for outcome B
        stake_a: Amount bet on outcome A
        stake_b: Amount bet on outcome B
    
    Returns:
        Guaranteed profit amount
    """
    # Calculate potential returns from each outcome
    return_a = stake_a * odds_a
    return_b = stake_b * odds_b
    
    # Both should be equal (or very close) in a proper arbitrage
    # Return profit (return minus total investment)
    total_investment = stake_a + stake_b
    guaranteed_return = min(return_a, return_b)  # Use minimum for safety
    
    return guaranteed_return - total_investment


def calculate_three_way_arbitrage(odds_a: float, odds_draw: float, odds_b: float) -> float:
    """
    Calculate the profit margin percentage for a 3-way arbitrage opportunity.
    
    Args:
        odds_a: Decimal odds for outcome A (home win)
        odds_draw: Decimal odds for draw
        odds_b: Decimal odds for outcome B (away win)
    
    Returns:
        Profit margin as a percentage (e.g., 2.5 for 2.5% profit)
        Returns 0 if no arbitrage exists (sum >= 1.0)
    """
    implied_prob_sum = (1 / odds_a) + (1 / odds_draw) + (1 / odds_b)
    
    if implied_prob_sum >= 1.0:
        return 0.0
    
    return (1 - implied_prob_sum) * 100


def calculate_three_way_stakes(odds_a: float, odds_draw: float, odds_b: float, total_stake: float) -> tuple:
    """
    Calculate optimal stake distribution for 3-way arbitrage betting.
    
    Args:
        odds_a: Decimal odds for outcome A (home win)
        odds_draw: Decimal odds for draw
        odds_b: Decimal odds for outcome B (away win)
        total_stake: Total amount to invest
    
    Returns:
        Tuple of (stake_a, stake_draw, stake_b) representing optimal bet amounts
    """
    # Calculate the denominator (sum of inverse odds)
    denominator = (1 / odds_a) + (1 / odds_draw) + (1 / odds_b)
    
    # Calculate stakes proportionally
    stake_a = total_stake * (1 / odds_a) / denominator
    stake_draw = total_stake * (1 / odds_draw) / denominator
    stake_b = total_stake * (1 / odds_b) / denominator
    
    return (stake_a, stake_draw, stake_b)


def calculate_three_way_profit(odds_a: float, odds_draw: float, odds_b: float, 
                                stake_a: float, stake_draw: float, stake_b: float) -> float:
    """
    Calculate the guaranteed profit from a 3-way arbitrage bet.
    
    Args:
        odds_a: Decimal odds for outcome A
        odds_draw: Decimal odds for draw
        odds_b: Decimal odds for outcome B
        stake_a: Amount bet on outcome A
        stake_draw: Amount bet on draw
        stake_b: Amount bet on outcome B
    
    Returns:
        Guaranteed profit amount
    """
    # Calculate potential returns from each outcome
    return_a = stake_a * odds_a
    return_draw = stake_draw * odds_draw
    return_b = stake_b * odds_b
    
    # All should be equal (or very close) in a proper arbitrage
    # Return profit (return minus total investment)
    total_investment = stake_a + stake_draw + stake_b
    guaranteed_return = min(return_a, return_draw, return_b)  # Use minimum for safety
    
    return guaranteed_return - total_investment


def get_sport_display_name(sport_key: str) -> str:
    """
    Convert sport key to display-friendly name.
    
    Args:
        sport_key: API sport key (e.g., 'mma_mixed_martial_arts')
    
    Returns:
        Display name (e.g., 'MMA')
    """
    sport_names = {
        'tennis_atp': 'ATP Tennis',
        'tennis_wta': 'WTA Tennis',
        'mma_mixed_martial_arts': 'MMA',
        'boxing_boxing': 'Boxing',
        'soccer_epl': 'English Premier League',
        'soccer_spain_la_liga': 'La Liga (Spain)',
        'soccer_italy_serie_a': 'Serie A (Italy)',
        'soccer_germany_bundesliga': 'Bundesliga (Germany)',
        'icehockey_nhl': 'NHL',
        'icehockey_sweden_hockey_league': 'SHL (Sweden)',
    }
    return sport_names.get(sport_key, sport_key.replace('_', ' ').title())

