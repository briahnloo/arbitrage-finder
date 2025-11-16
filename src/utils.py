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

    DEPRECATED: Use calculate_three_way_stakes_balanced() instead for better rounding behavior.

    Args:
        odds_a: Decimal odds for outcome A (home win)
        odds_draw: Decimal odds for draw
        odds_b: Decimal odds for outcome B (away win)
        total_stake: Total amount to invest

    Returns:
        Tuple of (stake_a, stake_draw, stake_b) representing optimal bet amounts (unrounded)
    """
    # Calculate the denominator (sum of inverse odds)
    denominator = (1 / odds_a) + (1 / odds_draw) + (1 / odds_b)

    # Calculate stakes proportionally
    stake_a = total_stake * (1 / odds_a) / denominator
    stake_draw = total_stake * (1 / odds_draw) / denominator
    stake_b = total_stake * (1 / odds_b) / denominator

    return (stake_a, stake_draw, stake_b)


def calculate_three_way_stakes_balanced(odds_a: float, odds_draw: float, odds_b: float,
                                       total_stake: float = 100.0, max_iterations: int = 10) -> tuple:
    """
    Calculate 3-way stakes through iterative refinement to ensure returns are balanced.

    This function finds stakes [S_a, S_d, S_b] such that:
    1. S_a + S_d + S_b = total_stake (exactly, within cents)
    2. S_a * odds_a ≈ S_d * odds_draw ≈ S_b * odds_b (within tolerance)
    3. All values are valid money amounts (rounded to cents)

    The key difference from naive proportional allocation: this iteratively refines
    stakes to preserve return balance even after rounding to cents.

    Args:
        odds_a: Decimal odds for outcome A (home win)
        odds_draw: Decimal odds for draw
        odds_b: Decimal odds for outcome B (away win)
        total_stake: Total amount to invest (default $100)
        max_iterations: Maximum iterations for refinement (default 10)

    Returns:
        Tuple of (stake_a, stake_draw, stake_b) with exact total and balanced returns
    """
    # Start with theoretical optimal (unrounded)
    denominator = (1 / odds_a) + (1 / odds_draw) + (1 / odds_b)
    stake_a = total_stake * (1 / odds_a) / denominator
    stake_draw = total_stake * (1 / odds_draw) / denominator
    stake_b = total_stake * (1 / odds_b) / denominator

    # Iteratively refine by rounding and rebalancing
    for iteration in range(max_iterations):
        # Refine: scale stakes inversely to their returns
        # If an outcome has higher return than average, reduce its stake
        return_a = stake_a * odds_a
        return_draw = stake_draw * odds_draw
        return_b = stake_b * odds_b

        avg_return = (return_a + return_draw + return_b) / 3

        if return_a > avg_return + 0.005:  # Small epsilon to avoid oscillation
            scale_a = avg_return / return_a if return_a > 0 else 1.0
            stake_a *= scale_a
        if return_draw > avg_return + 0.005:
            scale_d = avg_return / return_draw if return_draw > 0 else 1.0
            stake_draw *= scale_d
        if return_b > avg_return + 0.005:
            scale_b = avg_return / return_b if return_b > 0 else 1.0
            stake_b *= scale_b

        # Re-normalize to total_stake
        current_total = stake_a + stake_draw + stake_b
        if current_total > 0:
            ratio = total_stake / current_total
            stake_a *= ratio
            stake_draw *= ratio
            stake_b *= ratio

        # NOW round to nearest cent (after normalization)
        stake_a = round(stake_a, 2)
        stake_draw = round(stake_draw, 2)
        stake_b = round(total_stake - stake_a - stake_draw, 2)  # Ensure exact total

        # Calculate returns for rounded stakes
        return_a = stake_a * odds_a
        return_draw = stake_draw * odds_draw
        return_b = stake_b * odds_b

        # Check if balanced (all returns within 1 cent tolerance)
        max_return = max(return_a, return_draw, return_b)
        min_return = min(return_a, return_draw, return_b)
        return_diff = max_return - min_return

        if return_diff < 0.01:  # Within 1 cent, we're done
            break

    return (stake_a, stake_draw, stake_b)


def verify_arbitrage_with_rounding(odds_a: float, odds_draw: float, odds_b: float,
                                  stake_a: float, stake_draw: float, stake_b: float,
                                  total_stake: float = 100.0) -> tuple:
    """
    Verify that arbitrage survives rounding and actual stake execution.

    Checks:
    1. Stakes sum to exactly total_stake (within 1 cent)
    2. Returns are balanced (within 5 cent tolerance)
    3. Calculates guaranteed profit based on actual returns

    Args:
        odds_a: Odds for outcome A
        odds_draw: Odds for draw
        odds_b: Odds for outcome B
        stake_a: Actual stake for A (should be rounded)
        stake_draw: Actual stake for draw (should be rounded)
        stake_b: Actual stake for B (should be rounded)
        total_stake: Expected total stake

    Returns:
        Tuple of (is_valid, guaranteed_profit, min_return, max_return)
        - is_valid: True if arbitrage survives rounding
        - guaranteed_profit: Minimum guaranteed profit (or loss if negative)
        - min_return: Minimum return across outcomes
        - max_return: Maximum return across outcomes
    """
    # Calculate returns
    return_a = stake_a * odds_a
    return_draw = stake_draw * odds_draw
    return_b = stake_b * odds_b

    # Check stake total
    actual_total = stake_a + stake_draw + stake_b
    if abs(actual_total - total_stake) > 0.01:
        return (False, 0, 0, 0)  # Invalid: stakes don't sum correctly

    # Check returns are balanced
    min_return = min(return_a, return_draw, return_b)
    max_return = max(return_a, return_draw, return_b)
    return_diff = max_return - min_return

    if return_diff > 0.05:  # More than 5 cents difference
        return (False, 0, min_return, max_return)

    # Arbitrage is valid
    guaranteed_profit = min_return - total_stake

    return (True, guaranteed_profit, min_return, max_return)


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


def calculate_market_confidence(market_type: str, odds_rank_a: int = 0, odds_rank_b: int = 0,
                                odds_rank_draw: int = 0) -> tuple:
    """
    Calculate confidence score based on market type and odds ranking.

    Args:
        market_type: Type of market ('h2h', 'spreads', 'totals', 'cross_market', 'h2h_moneyline')
        odds_rank_a: Rank of odds A (0=best, 1=2nd, 2=3rd)
        odds_rank_b: Rank of odds B
        odds_rank_draw: Rank of draw odds (for 3-way)

    Returns:
        Tuple of (confidence_percentage: float, confidence_label: str)
    """
    # Base confidence by market type
    # h2h is most liquid and tight (odds more likely correct)
    base_confidence = {
        'h2h': 90,
        'h2h_moneyline': 90,  # Same as h2h - pure moneyline bets
        'spreads': 75,
        'totals': 70,
        'cross_market': 80
    }

    market_confidence = base_confidence.get(market_type, 50)

    # Adjust for odds ranking (using alternative odds reduces confidence)
    max_rank = max(odds_rank_a, odds_rank_b, odds_rank_draw)

    if max_rank == 1:  # Using 2nd best odds
        market_confidence *= 0.95  # 5% reduction
    elif max_rank == 2:  # Using 3rd best odds
        market_confidence *= 0.85  # 15% reduction

    # Determine label
    if market_confidence >= 85:
        label = "HIGH"
    elif market_confidence >= 70:
        label = "MEDIUM"
    else:
        label = "LOW"

    return (round(market_confidence, 1), label)


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

