"""
Real-world constraints for arbitrage betting.
Accounts for practical limitations that affect arbitrage viability.
"""

from datetime import datetime, timedelta
from typing import Tuple, Dict, Optional
from src import config


class TimingConstraints:
    """Validates timing constraints for arbitrage opportunities."""

    @staticmethod
    def can_place_both_bets(commence_time: str) -> Tuple[bool, str]:
        """
        Verify that there's enough time to place both bets.

        Args:
            commence_time: ISO format event start time

        Returns:
            Tuple of (valid, reason)
        """
        try:
            event_time = datetime.fromisoformat(commence_time.replace('Z', '+00:00'))
            current_time = datetime.now(event_time.tzinfo)
            time_available_seconds = (event_time - current_time).total_seconds()

            # Minimum 5 minutes to place both bets with network delay
            min_time_required = 5 * 60  # 300 seconds

            if time_available_seconds < min_time_required:
                hours = time_available_seconds / 3600
                return (False, f"Only {hours:.2f} hours until event (need 5+ min to place bets)")

            return (True, f"Sufficient time: {time_available_seconds/60:.1f} min until event")

        except Exception as e:
            return (False, f"Could not parse event time: {e}")

    @staticmethod
    def validate_bookmaker_availability(bookmaker_a: str, bookmaker_b: str) -> Tuple[bool, str]:
        """
        Verify that bookmakers are available and accepting bets.

        Args:
            bookmaker_a: First bookmaker name
            bookmaker_b: Second bookmaker name

        Returns:
            Tuple of (valid, reason)
        """
        # Check if bookmakers are in our trusted list
        trusted_bookmakers = set(config.BOOKMAKER_TRUST_SCORES.keys())

        if bookmaker_a not in trusted_bookmakers:
            return (False, f"Bookmaker '{bookmaker_a}' not in trusted list")

        if bookmaker_b not in trusted_bookmakers:
            return (False, f"Bookmaker '{bookmaker_b}' not in trusted list")

        # In production, could check real-time API status here
        return (True, "Both bookmakers available and trusted")


class LineMovementConstraints:
    """Validates line movement and odds stability."""

    @staticmethod
    def validate_odds_not_stale(odds_timestamp: Optional[str], max_age_seconds: int = 60) -> Tuple[bool, str]:
        """
        Verify that odds are fresh.

        Args:
            odds_timestamp: When odds were fetched
            max_age_seconds: Maximum acceptable age in seconds

        Returns:
            Tuple of (valid, reason)
        """
        if odds_timestamp is None:
            # We don't have timestamp info; assume it's acceptable
            return (True, "Odds timestamp unavailable; using default assumption")

        try:
            timestamp = datetime.fromisoformat(odds_timestamp.replace('Z', '+00:00'))
            current_time = datetime.now(timestamp.tzinfo)
            age_seconds = (current_time - timestamp).total_seconds()

            if age_seconds > max_age_seconds:
                return (False, f"Odds are {age_seconds:.0f} seconds old (max: {max_age_seconds}s)")

            return (True, f"Odds are fresh ({age_seconds:.0f}s old)")

        except Exception as e:
            return (False, f"Could not validate odds age: {e}")

    @staticmethod
    def check_historical_movement(
        odds_a: float,
        odds_b: float,
        implied_prob_sum: float
    ) -> Tuple[bool, str]:
        """
        Check if odds seem reasonable (not extreme line movement).

        This detects if odds have moved so much that they're likely stale.

        Args:
            odds_a: Odds for outcome A
            odds_b: Odds for outcome B
            implied_prob_sum: Sum of implied probabilities

        Returns:
            Tuple of (valid, reason)
        """
        # Implied probability sum > 1.15 suggests very recent/stale data
        if implied_prob_sum > 1.15:
            return (False, f"Implied probability sum {implied_prob_sum:.3f} suggests stale odds")

        # Implied probability sum < 0.85 would be unusual
        if implied_prob_sum < 0.85:
            return (False, f"Implied probability sum {implied_prob_sum:.3f} seems incorrect")

        return (True, f"Odds seem reasonable (implied prob sum: {implied_prob_sum:.3f})")


class BookmakerConstraints:
    """Validates bookmaker-specific constraints."""

    @staticmethod
    def validate_bookmaker_trust(bookmaker_a: str, bookmaker_b: str, min_trust: int = 7) -> Tuple[bool, str]:
        """
        Verify bookmakers meet trust threshold.

        Args:
            bookmaker_a: First bookmaker
            bookmaker_b: Second bookmaker
            min_trust: Minimum trust score (0-10)

        Returns:
            Tuple of (valid, reason)
        """
        trust_a = config.BOOKMAKER_TRUST_SCORES.get(bookmaker_a, 5)
        trust_b = config.BOOKMAKER_TRUST_SCORES.get(bookmaker_b, 5)

        if trust_a < min_trust:
            return (False, f"Bookmaker '{bookmaker_a}' trust score {trust_a} below minimum {min_trust}")

        if trust_b < min_trust:
            return (False, f"Bookmaker '{bookmaker_b}' trust score {trust_b} below minimum {min_trust}")

        return (True, f"Both bookmakers trusted: {bookmaker_a} ({trust_a}/10), {bookmaker_b} ({trust_b}/10)")

    @staticmethod
    def check_account_limitations(bookmaker: str) -> Tuple[bool, str]:
        """
        Check if bookmaker has known account limitations.

        In production, this would check against a database of user accounts
        and their limits/restrictions.

        Args:
            bookmaker: Bookmaker name

        Returns:
            Tuple of (valid, reason)
        """
        # This is a placeholder for real-world implementation
        # In production, you'd check:
        # - Account limits per bet
        # - Account remaining balance
        # - Betting limits (e.g., sportsbooks close arbitrage accounts)
        # - Withdrawal restrictions

        return (True, f"Account limitations check skipped (implement with real user data)")

    @staticmethod
    def validate_maximum_bet_size(
        stake_a: float,
        stake_b: float,
        bookmaker_a: str,
        bookmaker_b: str
    ) -> Tuple[bool, str]:
        """
        Verify that bet sizes don't exceed bookmaker limits.

        Args:
            stake_a: Bet size for bookmaker A
            stake_b: Bet size for bookmaker B
            bookmaker_a: First bookmaker
            bookmaker_b: Second bookmaker

        Returns:
            Tuple of (valid, reason)
        """
        # Default limits (in production, pull from real data)
        default_max_bet = 5000.0  # $5000 per bet

        max_bets = {
            'DraftKings': 5000.0,
            'BetRivers': 5000.0,
            'FanDuel': 5000.0,
            'BetMGM': 5000.0,
            'Caesars': 5000.0,
            'PointsBet': 3000.0,
            'WynnBET': 3000.0,
        }

        max_a = max_bets.get(bookmaker_a, default_max_bet)
        max_b = max_bets.get(bookmaker_b, default_max_bet)

        if stake_a > max_a:
            return (False, f"Stake ${stake_a:.2f} exceeds {bookmaker_a} limit ${max_a:.2f}")

        if stake_b > max_b:
            return (False, f"Stake ${stake_b:.2f} exceeds {bookmaker_b} limit ${max_b:.2f}")

        return (True, f"Bet sizes within limits: ${stake_a:.2f} and ${stake_b:.2f}")


class RealWorldValidator:
    """Comprehensive real-world constraint validation."""

    def __init__(self):
        self.timing = TimingConstraints()
        self.line_movement = LineMovementConstraints()
        self.bookmaker = BookmakerConstraints()

    def validate_opportunity(
        self,
        opportunity: Dict,
        user_account_data: Optional[Dict] = None
    ) -> Tuple[bool, str, Dict]:
        """
        Validate an arbitrage opportunity against real-world constraints.

        Args:
            opportunity: Opportunity dictionary
            user_account_data: Optional user account info

        Returns:
            Tuple of (valid, primary_reason, detailed_results)
        """
        results = {
            'timing': None,
            'bookmakers': None,
            'odds_freshness': None,
            'bookmaker_trust': None,
            'bet_limits': None,
            'all_passed': True
        }

        # Check timing
        valid, reason = self.timing.can_place_both_bets(opportunity['commence_time'])
        results['timing'] = (valid, reason)
        if not valid:
            results['all_passed'] = False

        # Check bookmakers are available
        valid, reason = self.timing.validate_bookmaker_availability(
            opportunity['bookmaker_a'],
            opportunity['bookmaker_b']
        )
        results['bookmakers'] = (valid, reason)
        if not valid:
            results['all_passed'] = False

        # Check bookmaker trust
        valid, reason = self.bookmaker.validate_bookmaker_trust(
            opportunity['bookmaker_a'],
            opportunity['bookmaker_b'],
            min_trust=7
        )
        results['bookmaker_trust'] = (valid, reason)
        if not valid:
            results['all_passed'] = False

        # Check bet size limits
        valid, reason = self.bookmaker.validate_maximum_bet_size(
            opportunity['stake_a'],
            opportunity['stake_b'],
            opportunity['bookmaker_a'],
            opportunity['bookmaker_b']
        )
        results['bet_limits'] = (valid, reason)
        if not valid:
            results['all_passed'] = False

        # Determine primary reason for failure
        primary_reason = ""
        if not results['all_passed']:
            for check_name, (valid, reason) in [
                ('timing', results['timing']),
                ('bookmakers', results['bookmakers']),
                ('trust', results['bookmaker_trust']),
                ('limits', results['bet_limits'])
            ]:
                if not valid:
                    primary_reason = reason
                    break

        return (results['all_passed'], primary_reason, results)
