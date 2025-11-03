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


def verify_stakes_after_rounding(odds_a: float, odds_b: float, stake_a: float, stake_b: float) -> tuple:
    """
    Verify that rounded stakes still produce valid arbitrage.
    If rounding breaks the arbitrage, adjust stakes to restore it.

    Args:
        odds_a: Decimal odds for outcome A
        odds_b: Decimal odds for outcome B
        stake_a: Rounded stake for outcome A
        stake_b: Rounded stake for outcome B

    Returns:
        Tuple of (adjusted_stake_a, adjusted_stake_b, is_valid)
        is_valid: True if arbitrage is preserved after rounding (within 1 cent tolerance)
    """
    # Calculate potential returns
    return_a = stake_a * odds_a
    return_b = stake_b * odds_b

    # Check if returns are equal within 1 cent tolerance
    return_diff = abs(return_a - return_b)

    if return_diff <= 0.01:
        # Arbitrage is preserved
        return (stake_a, stake_b, True)

    # If returns don't match, adjust the larger stake down to equalize
    if return_a > return_b:
        # Reduce stake_a to match return_b
        adjusted_stake_a = return_b / odds_a
        adjusted_stake_a = round(adjusted_stake_a, 2)
        return (adjusted_stake_a, stake_b, True)
    else:
        # Reduce stake_b to match return_a
        adjusted_stake_b = return_a / odds_b
        adjusted_stake_b = round(adjusted_stake_b, 2)
        return (stake_a, adjusted_stake_b, True)


def calculate_stakes_with_validation(odds_a: float, odds_b: float, total_stake: float) -> Union[tuple, None]:
    """
    Calculate optimal stakes and validate that arbitrage survives rounding.

    Args:
        odds_a: Decimal odds for outcome A
        odds_b: Decimal odds for outcome B
        total_stake: Total investment amount

    Returns:
        Tuple of (stake_a, stake_b) if valid arbitrage after rounding, None otherwise
    """
    # Calculate ideal stakes
    denominator = (1 / odds_a) + (1 / odds_b)
    stake_a_ideal = total_stake * (1 / odds_a) / denominator
    stake_b_ideal = total_stake * (1 / odds_b) / denominator

    # Round to nearest cent
    stake_a_rounded = round(stake_a_ideal, 2)
    stake_b_rounded = round(stake_b_ideal, 2)

    # Adjust so total matches exactly
    stake_b_rounded = round(total_stake - stake_a_rounded, 2)

    # Verify arbitrage is preserved
    stake_a_final, stake_b_final, is_valid = verify_stakes_after_rounding(
        odds_a, odds_b, stake_a_rounded, stake_b_rounded
    )

    if is_valid:
        return (stake_a_final, stake_b_final)
    else:
        return None


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


def normalize_team_name(name: str) -> str:
    """
    Normalize team/player name for comparison across bookmakers.

    Args:
        name: Team/player name from API

    Returns:
        Normalized name (lowercase, stripped)
    """
    if not name:
        return ""

    # Convert to lowercase and strip whitespace
    normalized = name.lower().strip()

    # Remove common prefixes/suffixes that vary by bookmaker
    normalized = normalized.replace('fc ', '').replace(' fc', '')
    normalized = normalized.replace('team ', '').replace(' team', '')
    normalized = normalized.replace('united', 'utd')

    return normalized


def identify_outcome_type(outcome_name: str, home_team: str, away_team: str) -> str:
    """
    Identify if outcome is HOME, AWAY, DRAW, or OTHER.

    Args:
        outcome_name: The outcome name from the API
        home_team: Home team name
        away_team: Away team name

    Returns:
        One of: 'HOME', 'AWAY', 'DRAW', 'OTHER'
    """
    if not outcome_name:
        return 'OTHER'

    outcome_lower = outcome_name.lower()
    home_normalized = normalize_team_name(home_team)
    away_normalized = normalize_team_name(away_team)

    # Check for draw explicitly
    if 'draw' in outcome_lower or 'tie' in outcome_lower:
        return 'DRAW'

    # Check for home team
    if home_normalized and home_normalized in outcome_lower:
        return 'HOME'
    if 'home' in outcome_lower:
        return 'HOME'

    # Check for away team
    if away_normalized and away_normalized in outcome_lower:
        return 'AWAY'
    if 'away' in outcome_lower or 'road' in outcome_lower:
        return 'AWAY'

    # If we can't identify it, return the original name
    return 'OTHER'


def create_canonical_outcome_key(outcome_type: str, point: float = None, market_type: str = 'h2h') -> str:
    """
    Create a canonical outcome key for consistent matching.

    Args:
        outcome_type: One of HOME, AWAY, DRAW, or specific name
        point: Point value for spreads/totals (e.g., 3.5 for -3.5)
        market_type: Type of market (h2h, spreads, totals)

    Returns:
        Canonical key (e.g., "HOME", "AWAY_-3.5", "OVER_2.5")
    """
    if market_type == 'h2h' or point is None:
        return outcome_type
    elif outcome_type in ['HOME', 'AWAY']:
        return f"{outcome_type}_{point:+.1f}".replace('+', '')
    else:
        # For totals (OVER/UNDER)
        return f"{outcome_type}_{point:.1f}"

