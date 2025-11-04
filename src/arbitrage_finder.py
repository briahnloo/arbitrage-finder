"""
Main arbitrage finder application.
Fetches odds from The Odds API, identifies arbitrage opportunities,
and displays alerts in the console.
"""

import requests
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import sys
import logging

# Set up logging
logger = logging.getLogger(__name__)

from src import config
from src.utils import (
    format_currency,
    format_timestamp,
    calculate_arbitrage_profit,
    calculate_stakes,
    calculate_guaranteed_profit,
    calculate_three_way_arbitrage,
    calculate_three_way_stakes,
    calculate_three_way_profit,
    get_sport_display_name,
    normalize_team_name,
    identify_outcome_type,
    create_canonical_outcome_key,
    verify_stakes_after_rounding,
    calculate_stakes_with_validation,
    calculate_market_confidence
)
from src.arbitrage_validator import ArbitrageValidator, StakeValidator, OutcomePartition, OutcomeType
from src.realworld_constraints import RealWorldValidator

# Import database if logging enabled
if config.ENABLE_DATABASE_LOGGING:
    from src.database import ArbitrageDatabase


class ArbitrageFinder:
    """Main class for finding and alerting arbitrage opportunities."""
    
    def __init__(self):
        """Initialize the arbitrage finder."""
        self.recent_alerts = {}  # Track recent alerts to avoid duplicates
        self.api_call_count = 0
        self.last_api_call_time = None
        self.cycle_number = 0  # Track iteration cycles
        
        # Initialize database if enabled
        self.db = None
        if config.ENABLE_DATABASE_LOGGING:
            try:
                self.db = ArbitrageDatabase(config.DATABASE_PATH)
                print(f"[DATABASE] Initialized: {config.DATABASE_PATH}")
            except Exception as e:
                print(f"[DATABASE ERROR] Could not initialize database: {e}")
                self.db = None
        
    def fetch_odds(self, sport: str) -> Optional[Dict]:
        """
        Fetch odds data from The Odds API for a specific sport.
        
        Args:
            sport: Sport key (e.g., 'tennis_atp')
        
        Returns:
            JSON response dict or None if error occurs
        """
        url = f"{config.BASE_API_URL}/sports/{sport}/odds/"
        
        params = {
            'apiKey': config.ODDS_API_KEY,
            'regions': config.API_REGIONS,
            'markets': config.API_MARKETS,
            'oddsFormat': config.ODDS_FORMAT
        }
        
        try:
            self.api_call_count += 1
            self.last_api_call_time = datetime.now()
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            # Check remaining API quota
            remaining = response.headers.get('x-requests-remaining')
            if remaining:
                print(f"[API] Remaining requests: {remaining}")
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Failed to fetch odds for {sport}: {e}")
            return None
    
    def process_odds(self, odds_data: List[Dict], sport: str) -> List[Dict]:
        """
        Process odds data with improved outcome normalization and top 3 odds tracking.

        Args:
            odds_data: List of match data from API
            sport: Sport key for display purposes

        Returns:
            List of processed match dictionaries with top odds per market type
        """
        processed_matches = []

        for match in odds_data:
            if not match.get('bookmakers'):
                continue

            # Extract match info
            home_team = match.get('home_team', 'Unknown')
            away_team = match.get('away_team', 'Unknown')
            commence_time = match.get('commence_time', '')

            # Group odds by market type and normalized outcome
            # Format: {market_key: {canonical_outcome_key: [{'odds': x, 'bookmaker': y}, ...]}}
            markets_odds = {}

            for bookmaker in match['bookmakers']:
                bookmaker_name = bookmaker.get('title', 'Unknown')

                for market in bookmaker.get('markets', []):
                    market_key = market.get('key')
                    if not market_key:
                        continue

                    # Initialize market if not exists
                    if market_key not in markets_odds:
                        markets_odds[market_key] = {}

                    for outcome in market.get('outcomes', []):
                        odds = outcome.get('price')

                        # Skip invalid odds
                        if not odds or odds < 1.0 or odds > 1000:
                            continue

                        # Create canonical outcome key
                        if market_key == 'h2h':
                            # For h2h, identify if HOME/AWAY/DRAW
                            outcome_type = identify_outcome_type(outcome.get('name'), home_team, away_team)
                            canonical_key = create_canonical_outcome_key(outcome_type, point=None, market_type='h2h')
                        elif market_key == 'spreads':
                            # For spreads, identify team then add point
                            outcome_type = identify_outcome_type(outcome.get('name'), home_team, away_team)
                            point = outcome.get('point')
                            canonical_key = create_canonical_outcome_key(outcome_type, point=point, market_type='spreads')
                        elif market_key == 'totals':
                            # For totals, use OVER/UNDER
                            outcome_name = outcome.get('name', '').upper()
                            outcome_type = 'OVER' if 'OVER' in outcome_name else 'UNDER'
                            point = outcome.get('point')
                            canonical_key = create_canonical_outcome_key(outcome_type, point=point, market_type='totals')
                        else:
                            # Unknown market type, use raw name
                            canonical_key = outcome.get('name', 'UNKNOWN')

                        # Store odds (keep top 3 for each outcome)
                        if canonical_key not in markets_odds[market_key]:
                            markets_odds[market_key][canonical_key] = []

                        # Add this odds option
                        markets_odds[market_key][canonical_key].append({
                            'odds': odds,
                            'bookmaker': bookmaker_name,
                            'raw_name': outcome.get('name')  # Keep for reference
                        })

            # Sort each outcome's odds list by odds (best first)
            for market_key in markets_odds:
                for canonical_key in markets_odds[market_key]:
                    markets_odds[market_key][canonical_key].sort(
                        key=lambda x: x['odds'],
                        reverse=True
                    )

            # Process each market type separately
            for market_key, outcome_odds in markets_odds.items():
                # Filter to only outcomes with odds available
                outcome_keys = list(outcome_odds.keys())

                # Handle 2-way markets (combat sports, totals, spreads)
                if len(outcome_keys) == 2:
                    # CRITICAL FIX: Reject 2-way for sports that should be 3-way
                    # Soccer/Hockey with draws MUST be 3-way to avoid draw losses
                    if config.is_three_way_sport(sport) and market_key == 'h2h':
                        # This is soccer/hockey h2h but only has 2 outcomes (missing draw)
                        # Skip this - it's not safe arbitrage (draw would lose both bets)
                        logger.warning(f"Skipping 2-way {sport} h2h (missing draw outcome). Event: {home_team} vs {away_team}")
                        continue

                    outcome_a_key = outcome_keys[0]
                    outcome_b_key = outcome_keys[1]

                    outcome_a_list = outcome_odds[outcome_a_key]
                    outcome_b_list = outcome_odds[outcome_b_key]

                    # Generate opportunities for top 3 combinations
                    for i, odds_a_option in enumerate(outcome_a_list[:3]):
                        for j, odds_b_option in enumerate(outcome_b_list[:3]):
                            processed_matches.append({
                                'sport': sport,
                                'market': market_key,
                                'num_outcomes': 2,
                                'player_a': outcome_a_key,
                                'player_b': outcome_b_key,
                                'odds_a': odds_a_option['odds'],
                                'odds_b': odds_b_option['odds'],
                                'bookmaker_a': odds_a_option['bookmaker'],
                                'bookmaker_b': odds_b_option['bookmaker'],
                                'bookmaker_a_raw': odds_a_option.get('raw_name', outcome_a_key),
                                'bookmaker_b_raw': odds_b_option.get('raw_name', outcome_b_key),
                                'odds_rank_a': i,  # 0=best, 1=2nd, 2=3rd
                                'odds_rank_b': j,
                                'commence_time': commence_time,
                                'event_name': f"{home_team} vs {away_team}"
                            })

                # Handle 3-way markets (soccer/hockey h2h with draw)
                elif len(outcome_keys) == 3 and config.is_three_way_sport(sport) and market_key == 'h2h':
                    # Find HOME, AWAY, DRAW outcomes
                    home_outcome = next((k for k in outcome_keys if k == 'HOME'), None)
                    away_outcome = next((k for k in outcome_keys if k == 'AWAY'), None)
                    draw_outcome = next((k for k in outcome_keys if k == 'DRAW'), None)

                    if home_outcome and away_outcome and draw_outcome:
                        home_list = outcome_odds[home_outcome]
                        away_list = outcome_odds[away_outcome]
                        draw_list = outcome_odds[draw_outcome]

                        # Generate opportunities for top 3 combinations
                        for i, odds_home in enumerate(home_list[:3]):
                            for j, odds_draw in enumerate(draw_list[:3]):
                                for k, odds_away in enumerate(away_list[:3]):
                                    processed_matches.append({
                                        'sport': sport,
                                        'market': market_key,
                                        'num_outcomes': 3,
                                        'player_a': home_outcome,
                                        'player_draw': draw_outcome,
                                        'player_b': away_outcome,
                                        'odds_a': odds_home['odds'],
                                        'odds_draw': odds_draw['odds'],
                                        'odds_b': odds_away['odds'],
                                        'bookmaker_a': odds_home['bookmaker'],
                                        'bookmaker_draw': odds_draw['bookmaker'],
                                        'bookmaker_b': odds_away['bookmaker'],
                                        'odds_rank_a': i,
                                        'odds_rank_draw': j,
                                        'odds_rank_b': k,
                                        'commence_time': commence_time,
                                        'event_name': f"{home_team} vs {away_team}"
                                    })

        return processed_matches
    
    def find_cross_market_arbitrage(self, match_data: Dict) -> List[Dict]:
        """
        Find arbitrage opportunities by combining different market types.

        FIXED: Now validates that outcomes are truly mutually exclusive and partition
        the outcome space. Rejects combinations that don't cover all scenarios.

        Args:
            match_data: Single match data with multiple bookmakers

        Returns:
            List of valid cross-market arbitrage opportunities
        """
        cross_market_opps = []

        if not match_data.get('bookmakers'):
            return cross_market_opps

        home_team = match_data.get('home_team', 'Unknown')
        away_team = match_data.get('away_team', 'Unknown')
        commence_time = match_data.get('commence_time', '')
        sport = match_data.get('sport', 'Unknown')

        # Build comprehensive market data
        market_combinations = {}

        for bookmaker in match_data['bookmakers']:
            bookmaker_name = bookmaker.get('title', 'Unknown')

            for market in bookmaker.get('markets', []):
                market_key = market.get('key')

                for outcome in market.get('outcomes', []):
                    odds = outcome.get('price')

                    # Skip invalid odds
                    if not odds or odds < 1.0 or odds > 1000:
                        continue

                    # Identify outcome type
                    outcome_type = identify_outcome_type(outcome.get('name'), home_team, away_team)

                    if outcome_type == 'OTHER':
                        continue

                    # Create key for this outcome/market combination
                    if market_key == 'h2h':
                        combo_key = f"{outcome_type}"
                    else:
                        point = outcome.get('point')
                        combo_key = f"{outcome_type}_{point}"

                    if combo_key not in market_combinations:
                        market_combinations[combo_key] = []

                    market_combinations[combo_key].append({
                        'odds': odds,
                        'bookmaker': bookmaker_name,
                        'market': market_key,
                        'point': outcome.get('point'),
                        'raw_name': outcome.get('name')
                    })

        # FIXED: Only combine outcomes that are mutually exclusive and partition outcome space
        # Valid combinations:
        # 1. HOME (h2h) vs AWAY (h2h) - moneyline arbitrage
        # 2. HOME_X (spread) vs AWAY_Y (spread) - only if they partition outcomes
        # 3. HOME_X (spread) vs HOME (h2h) - ONLY if mutually exclusive (home spread vs away ml)
        #    Actually this is: home covers spread vs away wins (moneyline)

        validator = ArbitrageValidator()
        partition_validator = OutcomePartition()
        stake_validator = StakeValidator()

        # Strategy 1: H2H moneyline arbitrage (HOME vs AWAY)
        if 'HOME' in market_combinations and 'AWAY' in market_combinations:
            home_opts = market_combinations['HOME']
            away_opts = market_combinations['AWAY']

            # Build outcome dicts for validation
            outcome_home = {
                'outcome_type': OutcomeType.HOME_WIN,
                'spread': None,
                'total': None
            }
            outcome_away = {
                'outcome_type': OutcomeType.AWAY_WIN,
                'spread': None,
                'total': None
            }

            # Verify these outcomes partition the space
            is_valid_partition, partition_reason = partition_validator.validate_two_way_partition(
                outcome_home, outcome_away, sport
            )

            if is_valid_partition:
                for home_opt in home_opts[:2]:
                    for away_opt in away_opts[:2]:
                        odds_home = home_opt['odds']
                        odds_away = away_opt['odds']

                        profit_margin = calculate_arbitrage_profit(odds_home, odds_away)

                        if profit_margin >= config.MINIMUM_PROFIT_THRESHOLD:
                            stakes_result = calculate_stakes_with_validation(
                                odds_home, odds_away, config.DEFAULT_STAKE
                            )

                            if stakes_result is not None:
                                stake_a, stake_b = stakes_result

                                # Validate stakes preserve $100 total
                                is_valid, adj_stake_a, adj_stake_b, stake_reason = stake_validator.validate_and_adjust_stakes(
                                    odds_home, odds_away, stake_a, stake_b, config.DEFAULT_STAKE
                                )

                                if not is_valid:
                                    continue

                                # Scenario validate the opportunity
                                is_arb_valid, validation_reason, validation_results = validator.validate_two_way_arbitrage(
                                    outcome_home, outcome_away, adj_stake_a, adj_stake_b,
                                    odds_home, odds_away, sport
                                )

                                if is_arb_valid:
                                    guaranteed_profit = validation_results['profit_range'][0]

                                    cross_market_opps.append({
                                        'sport': sport,
                                        'market': 'h2h_moneyline',
                                        'num_outcomes': 2,
                                        'player_a': 'HOME',
                                        'player_b': 'AWAY',
                                        'odds_a': odds_home,
                                        'odds_b': odds_away,
                                        'bookmaker_a': home_opt['bookmaker'],
                                        'bookmaker_b': away_opt['bookmaker'],
                                        'market_a': home_opt['market'],
                                        'market_b': away_opt['market'],
                                        'profit_margin': profit_margin,
                                        'stake_a': adj_stake_a,
                                        'stake_b': adj_stake_b,
                                        'guaranteed_profit': guaranteed_profit,
                                        'total_stake': config.DEFAULT_STAKE,
                                        'is_cross_market': False,
                                        'is_validated': True,
                                        'commence_time': commence_time,
                                        'event_name': f"{home_team} vs {away_team}",
                                        'validation_notes': validation_reason
                                    })

        # Strategy 2: Spread + Moneyline (only valid specific combinations)
        # HOME -X (spread) vs AWAY (moneyline) is INVALID because:
        # - HOME -1.5 means home wins by 2+
        # - AWAY means away wins by any amount
        # - If away wins by 1, both lose (not arbitrage)
        # NOT IMPLEMENTING invalid cross-market combinations

        return cross_market_opps

    def find_arbitrage_opportunities(self, matches: List[Dict]) -> List[Dict]:
        """
        Identify arbitrage opportunities from processed matches (2-way and 3-way).
        Uses comprehensive validation: scenario simulation, partition validation, and stake validation.

        Args:
            matches: List of processed match dictionaries

        Returns:
            List of arbitrage opportunities with verified profit calculations
        """
        opportunities = []
        validator = ArbitrageValidator()
        stake_validator = StakeValidator()
        partition_validator = OutcomePartition()

        for match in matches:
            num_outcomes = match.get('num_outcomes', 2)

            if num_outcomes == 2:
                # 2-way arbitrage (combat sports, totals, spreads)
                odds_a = match['odds_a']
                odds_b = match['odds_b']
                sport = match.get('sport', 'Unknown')
                market = match.get('market', 'h2h')

                # SAFETY CHECK: Never show 2-way for sports with draws (soccer/hockey)
                # 2-way soccer is NOT risk-free (draw loses both bets)
                if config.is_three_way_sport(sport) and market == 'h2h':
                    logger.warning(f"REJECTED: 2-way {sport} h2h detected. This is not safe arbitrage. Event: {match.get('event_name')}")
                    continue

                # Calculate profit margin
                profit_margin = calculate_arbitrage_profit(odds_a, odds_b)

                # Check if meets minimum threshold
                if profit_margin >= config.MINIMUM_PROFIT_THRESHOLD:
                    # Calculate initial stakes
                    stakes_result = calculate_stakes_with_validation(
                        odds_a, odds_b, config.DEFAULT_STAKE
                    )

                    if stakes_result is None:
                        continue

                    stake_a, stake_b = stakes_result

                    # FIXED: Validate and adjust stakes to preserve $100 total
                    is_valid, adj_stake_a, adj_stake_b, stake_reason = stake_validator.validate_and_adjust_stakes(
                        odds_a, odds_b, stake_a, stake_b, config.DEFAULT_STAKE
                    )

                    if not is_valid:
                        continue

                    # Build outcome dicts for validation
                    # Map string outcome to OutcomeType enum or keep as string for combat sports
                    player_a_str = str(match['player_a'])
                    player_b_str = str(match['player_b'])
                    
                    # For combat sports (MMA/boxing), map HOME/AWAY to A_WINS/B_WINS
                    # For team sports, use OutcomeType enum or keep as string
                    is_combat_sport = 'mma' in sport.lower() or 'boxing' in sport.lower()
                    
                    if is_combat_sport:
                        # Map HOME -> A_WINS, AWAY -> B_WINS for combat sports
                        # For combat sports, HOME/AWAY represent player A/B respectively
                        # player_a is typically HOME (player A), player_b is typically AWAY (player B)
                        player_a_upper = player_a_str.upper()
                        player_b_upper = player_b_str.upper()
                        
                        # Map player_a to A_WINS (HOME = player A wins)
                        if player_a_upper in ["HOME", "A_WINS"]:
                            outcome_a_type = "A_WINS"
                        elif player_a_upper in ["AWAY", "B_WINS"]:
                            outcome_a_type = "B_WINS"
                        else:
                            # Default: player_a is player A (first fighter)
                            outcome_a_type = "A_WINS"
                        
                        # Map player_b to B_WINS (AWAY = player B wins)
                        if player_b_upper in ["AWAY", "B_WINS"]:
                            outcome_b_type = "B_WINS"
                        elif player_b_upper in ["HOME", "A_WINS"]:
                            outcome_b_type = "A_WINS"
                        else:
                            # Default: player_b is player B (second fighter)
                            outcome_b_type = "B_WINS"
                    else:
                        # For team sports, try to map to OutcomeType enum
                        player_a_upper = player_a_str.upper()
                        player_b_upper = player_b_str.upper()
                        
                        if player_a_upper == "HOME":
                            outcome_a_type = OutcomeType.HOME_WIN
                        elif player_a_upper == "AWAY":
                            outcome_a_type = OutcomeType.AWAY_WIN
                        else:
                            outcome_a_type = player_a_str
                            
                        if player_b_upper == "HOME":
                            outcome_b_type = OutcomeType.HOME_WIN
                        elif player_b_upper == "AWAY":
                            outcome_b_type = OutcomeType.AWAY_WIN
                        else:
                            outcome_b_type = player_b_str

                    outcome_a = {
                        'outcome_type': outcome_a_type,
                        'spread': match.get('point_a'),
                        'total': None
                    }
                    outcome_b = {
                        'outcome_type': outcome_b_type,
                        'spread': match.get('point_b'),
                        'total': None
                    }

                    # FIXED: Scenario validate the opportunity
                    is_arb_valid, validation_reason, validation_results = validator.validate_two_way_arbitrage(
                        outcome_a, outcome_b, adj_stake_a, adj_stake_b,
                        odds_a, odds_b, sport
                    )

                    if not is_arb_valid:
                        continue

                    guaranteed_profit = validation_results['profit_range'][0]

                    # Create opportunity dict
                    opportunity = {
                        **match,
                        'profit_margin': profit_margin,
                        'stake_a': adj_stake_a,
                        'stake_b': adj_stake_b,
                        'guaranteed_profit': guaranteed_profit,
                        'total_stake': config.DEFAULT_STAKE,
                        'is_validated': True,
                        'validation_reason': validation_reason
                    }

                    opportunities.append(opportunity)

            elif num_outcomes == 3:
                # 3-way arbitrage (soccer/hockey with draw)
                odds_a = match['odds_a']
                odds_draw = match['odds_draw']
                odds_b = match['odds_b']
                sport = match.get('sport', 'Unknown')

                # Calculate profit margin
                profit_margin = calculate_three_way_arbitrage(odds_a, odds_draw, odds_b)

                # Check if meets minimum threshold
                if profit_margin >= config.MINIMUM_PROFIT_THRESHOLD:
                    # Calculate initial stakes
                    denominator = (1 / odds_a) + (1 / odds_draw) + (1 / odds_b)
                    stake_a_ideal = config.DEFAULT_STAKE * (1 / odds_a) / denominator
                    stake_draw_ideal = config.DEFAULT_STAKE * (1 / odds_draw) / denominator
                    stake_b_ideal = config.DEFAULT_STAKE * (1 / odds_b) / denominator

                    stake_a = round(stake_a_ideal, 2)
                    stake_draw = round(stake_draw_ideal, 2)
                    stake_b = round(config.DEFAULT_STAKE - stake_a - stake_draw, 2)

                    # FIXED: Validate and adjust stakes for 3-way
                    is_valid, adj_stake_a, adj_stake_draw, adj_stake_b, stake_reason = stake_validator.validate_three_way_stakes(
                        odds_a, odds_draw, odds_b, stake_a, stake_draw, stake_b, config.DEFAULT_STAKE
                    )

                    if not is_valid:
                        continue

                    # Build outcome dicts for validation
                    outcome_a = {
                        'outcome_type': OutcomeType.HOME_WIN,
                        'spread': None,
                        'total': None
                    }
                    outcome_draw = {
                        'outcome_type': OutcomeType.DRAW,
                        'spread': None,
                        'total': None
                    }
                    outcome_b = {
                        'outcome_type': OutcomeType.AWAY_WIN,
                        'spread': None,
                        'total': None
                    }

                    # FIXED: Scenario validate 3-way opportunity
                    is_arb_valid, validation_reason, validation_results = validator.validate_three_way_arbitrage(
                        outcome_a, outcome_draw, outcome_b,
                        adj_stake_a, adj_stake_draw, adj_stake_b,
                        odds_a, odds_draw, odds_b, sport
                    )

                    if not is_arb_valid:
                        continue

                    guaranteed_profit = validation_results['profit_range'][0]

                    # Create opportunity dict
                    opportunity = {
                        **match,
                        'profit_margin': profit_margin,
                        'stake_a': adj_stake_a,
                        'stake_draw': adj_stake_draw,
                        'stake_b': adj_stake_b,
                        'guaranteed_profit': guaranteed_profit,
                        'total_stake': config.DEFAULT_STAKE,
                        'is_validated': True,
                        'validation_reason': validation_reason
                    }

                    opportunities.append(opportunity)

        return opportunities
    
    def create_alert_key(self, opportunity: Dict) -> str:
        """
        Create a unique key for an opportunity to track duplicates.
        Includes profit tier so different profit levels are treated as different opportunities.

        Args:
            opportunity: Opportunity dictionary

        Returns:
            Unique string key
        """
        # Group profit margins into tiers (0.5% ranges)
        # So 1.2% and 1.8% trigger new alerts, but 1.2% and 1.25% don't
        profit_tier = int(opportunity['profit_margin'] * 2) / 2  # Round to nearest 0.5%

        return f"{opportunity['player_a']}_vs_{opportunity['player_b']}_{opportunity['bookmaker_a']}_{opportunity['bookmaker_b']}_profit_{profit_tier:.1f}"
    
    def passes_filters(self, opportunity: Dict) -> tuple:
        """
        Check if opportunity passes all smart filters including real-world constraints.

        Args:
            opportunity: Opportunity dictionary

        Returns:
            Tuple of (passes: bool, reason: str)
        """
        # Check if opportunity has been validated
        if not opportunity.get('is_validated', False):
            return (False, "Opportunity failed mathematical validation (not scenario-verified)")

        # Check bookmaker trust scores
        bookmakers = [opportunity['bookmaker_a'], opportunity['bookmaker_b']]
        if opportunity.get('num_outcomes') == 3:
            bookmakers.append(opportunity['bookmaker_draw'])

        for bookmaker in bookmakers:
            trust_score = config.BOOKMAKER_TRUST_SCORES.get(bookmaker, 5)
            if trust_score < config.MINIMUM_BOOKMAKER_TRUST:
                return (False, f"Bookmaker {bookmaker} trust score ({trust_score}) below minimum ({config.MINIMUM_BOOKMAKER_TRUST})")

        # Check event timing
        try:
            event_time = datetime.fromisoformat(opportunity['commence_time'].replace('Z', '+00:00'))
            current_time = datetime.now(event_time.tzinfo)
            time_until_event = (event_time - current_time).total_seconds() / 3600  # Hours

            if time_until_event < config.MINIMUM_EVENT_START_HOURS:
                return (False, f"Event starts in {time_until_event:.1f} hours (minimum: {config.MINIMUM_EVENT_START_HOURS}h)")

            if time_until_event > (config.MAXIMUM_EVENT_START_DAYS * 24):
                return (False, f"Event too far in future ({time_until_event/24:.1f} days)")
        except Exception as e:
            pass

        # Check sport-specific profit threshold
        sport = opportunity['sport']
        min_profit = config.SPORT_PROFIT_THRESHOLDS.get(sport, config.MINIMUM_PROFIT_THRESHOLD)
        if opportunity['profit_margin'] < min_profit:
            return (False, f"Profit {opportunity['profit_margin']:.2f}% below sport minimum {min_profit}%")

        # ADDED: Check real-world constraints
        real_world_validator = RealWorldValidator()
        is_valid_realworld, primary_reason, constraint_results = real_world_validator.validate_opportunity(opportunity)

        if not is_valid_realworld:
            return (False, f"Real-world constraint failed: {primary_reason}")

        # ADDED: Verify stake totals are exact
        if opportunity.get('num_outcomes') == 2:
            total_stake = opportunity['stake_a'] + opportunity['stake_b']
        else:
            total_stake = opportunity['stake_a'] + opportunity.get('stake_draw', 0) + opportunity['stake_b']

        if abs(total_stake - config.DEFAULT_STAKE) > 0.01:
            return (False, f"Stake total ${total_stake:.2f} doesn't equal ${config.DEFAULT_STAKE:.2f}")

        return (True, "All filters and validations passed")
    
    def should_alert(self, opportunity: Dict) -> bool:
        """
        Check if we should alert for this opportunity (not a recent duplicate).
        
        Args:
            opportunity: Opportunity dictionary
        
        Returns:
            True if should alert, False otherwise
        """
        alert_key = self.create_alert_key(opportunity)
        current_time = datetime.now()
        
        # Check if we've alerted for this recently
        if alert_key in self.recent_alerts:
            last_alert_time = self.recent_alerts[alert_key]
            time_diff = (current_time - last_alert_time).total_seconds()
            
            if time_diff < config.DUPLICATE_ALERT_WINDOW_SECONDS:
                return False  # Too recent, don't alert again
        
        # Update the alert time
        self.recent_alerts[alert_key] = current_time
        
        # Clean up old entries (older than window)
        keys_to_remove = []
        for key, alert_time in self.recent_alerts.items():
            if (current_time - alert_time).total_seconds() > config.DUPLICATE_ALERT_WINDOW_SECONDS:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self.recent_alerts[key]
        
        return True
    
    def calculate_opportunity_score(self, opportunity: Dict) -> float:
        """
        Calculate composite score for ranking opportunities.
        
        Args:
            opportunity: Opportunity dictionary
            
        Returns:
            Composite score (higher is better)
        """
        profit_margin = opportunity.get('profit_margin', 0.0)
        guaranteed_profit = opportunity.get('guaranteed_profit', 0.0)
        
        # Get confidence score
        market_type = opportunity.get('market', 'h2h')
        odds_rank_a = opportunity.get('odds_rank_a', 0)
        odds_rank_b = opportunity.get('odds_rank_b', 0)
        odds_rank_draw = opportunity.get('odds_rank_draw', 0)
        
        confidence, _ = calculate_market_confidence(
            market_type,
            odds_rank_a=odds_rank_a,
            odds_rank_b=odds_rank_b,
            odds_rank_draw=odds_rank_draw
        )
        
        # Normalize profit to percentage (it's already in %)
        normalized_profit = guaranteed_profit / config.DEFAULT_STAKE * 100
        
        # Composite score: profit_margin (60%), confidence (30%), normalized_profit (10%)
        score = (profit_margin * 0.6) + (confidence * 0.3) + (normalized_profit * 0.1)
        
        return score
    
    def display_top_opportunities(self, opportunities: List[Dict], cycle_num: int):
        """
        Display top opportunities with detailed betting information.

        Args:
            opportunities: List of opportunity dictionaries (already ranked)
            cycle_num: Cycle number for display
        """
        if not opportunities:
            return

        # ANSI color codes
        GREEN = '\033[92m'
        YELLOW = '\033[93m'
        RED = '\033[91m'
        CYAN = '\033[96m'
        BOLD = '\033[1m'
        RESET = '\033[0m'

        print("\n" + "=" * 140)
        print(f"{BOLD}TOP {min(len(opportunities), config.TOP_OPPORTUNITIES_COUNT)} OPPORTUNITIES - Cycle #{cycle_num}{RESET}")
        print("=" * 140)

        # Quick reference table
        print(f"{BOLD}QUICK REFERENCE:{RESET}")
        print(f"{BOLD}{'Rank':<6} {'Event':<25} {'Sport':<18} {'Profit %':<10} {'Confidence':<15} {'Guaranteed':<12} {'Event Time':<20}{RESET}")
        print("-" * 140)

        # Display top opportunities summary
        for i, opp in enumerate(opportunities[:config.TOP_OPPORTUNITIES_COUNT], 1):
            # Get event name
            event_name = opp.get('event_name', f"{opp.get('player_a', 'Unknown')} vs {opp.get('player_b', 'Unknown')}")
            if len(event_name) > 24:
                event_name = event_name[:21] + "..."

            # Get sport name
            sport_name = get_sport_display_name(opp.get('sport', 'Unknown'))
            if len(sport_name) > 17:
                sport_name = sport_name[:14] + "..."

            # Get profit margin
            profit_margin = opp.get('profit_margin', 0.0)
            profit_str = f"{profit_margin:.2f}%"

            # Get confidence
            market_type = opp.get('market', 'h2h')
            odds_rank_a = opp.get('odds_rank_a', 0)
            odds_rank_b = opp.get('odds_rank_b', 0)
            odds_rank_draw = opp.get('odds_rank_draw', 0)

            confidence, confidence_label = calculate_market_confidence(
                market_type,
                odds_rank_a=odds_rank_a,
                odds_rank_b=odds_rank_b,
                odds_rank_draw=odds_rank_draw
            )

            # Color code confidence
            if confidence_label == "HIGH":
                conf_color = GREEN
            elif confidence_label == "MEDIUM":
                conf_color = YELLOW
            else:
                conf_color = RED

            # Format confidence string
            confidence_str = f"{conf_color}{confidence_label}{RESET} ({confidence:.0f}%)"

            # Get guaranteed profit
            guaranteed_profit = opp.get('guaranteed_profit', 0.0)
            profit_dollar_str = format_currency(guaranteed_profit)

            # Get event time
            try:
                event_time_str = format_timestamp(opp.get('commence_time', ''))
            except:
                event_time_str = "N/A"

            # Print summary row
            print(f"  {i:<4} {event_name:<25} {sport_name:<18} {profit_str:<10} {confidence_str:<25} {profit_dollar_str:<12} {event_time_str:<20}")

        print("-" * 140)

        # Detailed betting information for each opportunity
        print(f"\n{BOLD}DETAILED BETTING INFORMATION:{RESET}\n")

        for i, opp in enumerate(opportunities[:config.TOP_OPPORTUNITIES_COUNT], 1):
            # Get event information
            event_name = opp.get('event_name', f"{opp.get('player_a', 'Unknown')} vs {opp.get('player_b', 'Unknown')}")
            sport_name = get_sport_display_name(opp.get('sport', 'Unknown'))
            commence_time = format_timestamp(opp.get('commence_time', ''))

            # Get bet details
            player_a = opp.get('player_a', 'Unknown')
            player_b = opp.get('player_b', 'Unknown')
            odds_a = opp.get('odds_a', 0.0)
            odds_b = opp.get('odds_b', 0.0)
            stake_a = opp.get('stake_a', 0.0)
            stake_b = opp.get('stake_b', 0.0)
            bookmaker_a = opp.get('bookmaker_a', 'Unknown')
            bookmaker_b = opp.get('bookmaker_b', 'Unknown')
            guaranteed_profit = opp.get('guaranteed_profit', 0.0)
            profit_margin = opp.get('profit_margin', 0.0)
            total_stake = opp.get('total_stake', 100.0)

            # Get confidence
            market_type = opp.get('market', 'h2h')
            odds_rank_a = opp.get('odds_rank_a', 0)
            odds_rank_b = opp.get('odds_rank_b', 0)
            odds_rank_draw = opp.get('odds_rank_draw', 0)

            confidence, confidence_label = calculate_market_confidence(
                market_type,
                odds_rank_a=odds_rank_a,
                odds_rank_b=odds_rank_b,
                odds_rank_draw=odds_rank_draw
            )

            # Color code confidence
            if confidence_label == "HIGH":
                conf_color = GREEN
            elif confidence_label == "MEDIUM":
                conf_color = YELLOW
            else:
                conf_color = RED

            # Print detailed information
            print(f"{CYAN}╔{'═' * 136}╗{RESET}")
            print(f"{CYAN}║{RESET} {BOLD}Opportunity #{i}: {event_name}{RESET}")
            print(f"{CYAN}║{RESET} {BOLD}Sport:{RESET} {sport_name} | {BOLD}Event Time:{RESET} {commence_time}")
            print(f"{CYAN}║{RESET} {BOLD}Profit:{RESET} {profit_margin:.2f}% | {BOLD}Guaranteed Return:{RESET} {format_currency(guaranteed_profit)} | {BOLD}Confidence:{RESET} {conf_color}{confidence_label}{RESET} ({confidence:.0f}%)")
            print(f"{CYAN}╠{'═' * 136}╣{RESET}")

            # Bet 1 information
            return_a = stake_a * odds_a
            print(f"{CYAN}║{RESET} {BOLD}BET 1 - {player_a}:{RESET}")
            print(f"{CYAN}║{RESET}   {BOLD}Bookmaker:{RESET} {bookmaker_a:<20} {BOLD}Odds:{RESET} {odds_a:.2f}")
            print(f"{CYAN}║{RESET}   {BOLD}Stake:{RESET} {format_currency(stake_a):<15} {BOLD}If Wins, Returns:{RESET} {format_currency(return_a)}")

            # Bet 2 information
            return_b = stake_b * odds_b
            print(f"{CYAN}║{RESET} {BOLD}BET 2 - {player_b}:{RESET}")
            print(f"{CYAN}║{RESET}   {BOLD}Bookmaker:{RESET} {bookmaker_b:<20} {BOLD}Odds:{RESET} {odds_b:.2f}")
            print(f"{CYAN}║{RESET}   {BOLD}Stake:{RESET} {format_currency(stake_b):<15} {BOLD}If Wins, Returns:{RESET} {format_currency(return_b)}")

            print(f"{CYAN}╠{'═' * 136}╣{RESET}")
            print(f"{CYAN}║{RESET} {BOLD}SUMMARY:{RESET}")
            print(f"{CYAN}║{RESET}   {BOLD}Total Investment:{RESET} {format_currency(total_stake)}")
            print(f"{CYAN}║{RESET}   {BOLD}Minimum Return (Guaranteed):{RESET} {format_currency(min(return_a, return_b))}")
            print(f"{CYAN}║{RESET}   {BOLD}Guaranteed Profit:{RESET} {GREEN}{format_currency(guaranteed_profit)}{RESET}")
            print(f"{CYAN}║{RESET}   {BOLD}Return on Investment:{RESET} {GREEN}{(guaranteed_profit/total_stake)*100:.1f}%{RESET}")
            print(f"{CYAN}╚{'═' * 136}╝{RESET}")
            print()

        print("=" * 140)
        print()
    
    def display_alert(self, opportunity: Dict):
        """
        Display a formatted alert in the console for an arbitrage opportunity.
        
        Args:
            opportunity: Opportunity dictionary with all details
        """
        # ANSI color codes for better visibility
        GREEN = '\033[92m'
        YELLOW = '\033[93m'
        CYAN = '\033[96m'
        BOLD = '\033[1m'
        RESET = '\033[0m'
        
        print("\n" + "=" * 80)
        print(f"{GREEN}{BOLD}🎾 ARBITRAGE OPPORTUNITY FOUND! 🎾{RESET}")
        print("=" * 80)
        
        # Show event name if available, otherwise show player names
        if 'event_name' in opportunity:
            print(f"{CYAN}Event:{RESET} {opportunity['event_name']}")
        else:
            print(f"{CYAN}Match:{RESET} {opportunity['player_a']} vs {opportunity['player_b']}")
        
        print(f"{CYAN}Event Time:{RESET} {format_timestamp(opportunity['commence_time'])}")
        print(f"{CYAN}Sport:{RESET} {get_sport_display_name(opportunity['sport'])}")
        
        # Show market type
        market_type = opportunity.get('market', 'h2h')
        market_display = config.MARKET_DISPLAY_NAMES.get(market_type, market_type)
        print(f"{CYAN}Market:{RESET} {market_display}")
        print()

        print(f"{YELLOW}{BOLD}Profit Margin: {opportunity['profit_margin']:.2f}%{RESET}")

        # Calculate and display confidence
        odds_rank_a = opportunity.get('odds_rank_a', 0)
        odds_rank_b = opportunity.get('odds_rank_b', 0)
        odds_rank_draw = opportunity.get('odds_rank_draw', 0)
        is_cross_market = opportunity.get('is_cross_market', False)
        is_validated = opportunity.get('is_validated', False)

        confidence, confidence_label = calculate_market_confidence(
            market_type,
            odds_rank_a=odds_rank_a,
            odds_rank_b=odds_rank_b,
            odds_rank_draw=odds_rank_draw
        )

        confidence_color = GREEN if confidence_label == "HIGH" else YELLOW if confidence_label == "MEDIUM" else '\033[91m'
        print(f"Confidence: {confidence_color}{confidence_label}{RESET} ({confidence:.0f}%)")

        # ADDED: Show validation status
        if is_validated:
            validation_notes = opportunity.get('validation_reason', 'Scenario validated')
            print(f"{GREEN}✓ MATHEMATICALLY VERIFIED (Scenario Simulation){RESET}")
            print(f"{CYAN}Validation: {validation_notes}{RESET}")
        else:
            RED = '\033[91m'
            print(f"{RED}✗ NOT VALIDATED{RESET}")

        if is_cross_market:
            print(f"{CYAN}[CROSS-MARKET ARBITRAGE]{RESET}")

        if odds_rank_a > 0 or odds_rank_b > 0:
            confidence_note = "⚠️ Using alternative odds (not best available)"
            if odds_rank_a == 1 or odds_rank_b == 1:
                confidence_note = "⚠️ Using 2nd-best odds for one outcome"
            if odds_rank_a == 2 or odds_rank_b == 2:
                confidence_note = "⚠️ Using 3rd-best odds (lower confidence)"
            print(f"{YELLOW}{confidence_note}{RESET}")

        print()

        # Check if 2-way or 3-way arbitrage
        num_outcomes = opportunity.get('num_outcomes', 2)

        if num_outcomes == 2:
            # Display 2-way arbitrage (2 bets)
            rank_a_label = f" (#{odds_rank_a + 1})" if odds_rank_a > 0 else ""
            rank_b_label = f" (#{odds_rank_b + 1})" if odds_rank_b > 0 else ""

            print(f"{BOLD}BET 1:{RESET}")
            print(f"  Outcome: {opportunity['player_a']}")
            print(f"  Bookmaker: {opportunity['bookmaker_a']}{rank_a_label}")
            print(f"  Odds: {opportunity['odds_a']:.2f}")
            print(f"  Stake: {format_currency(opportunity['stake_a'])}")
            print()

            print(f"{BOLD}BET 2:{RESET}")
            print(f"  Outcome: {opportunity['player_b']}")
            print(f"  Bookmaker: {opportunity['bookmaker_b']}{rank_b_label}")
            print(f"  Odds: {opportunity['odds_b']:.2f}")
            print(f"  Stake: {format_currency(opportunity['stake_b'])}")
            print()

        elif num_outcomes == 3:
            # Display 3-way arbitrage (3 bets)
            odds_rank_draw = opportunity.get('odds_rank_draw', 0)
            rank_a_label = f" (#{odds_rank_a + 1})" if odds_rank_a > 0 else ""
            rank_draw_label = f" (#{odds_rank_draw + 1})" if odds_rank_draw > 0 else ""
            rank_b_label = f" (#{odds_rank_b + 1})" if odds_rank_b > 0 else ""

            print(f"{BOLD}BET 1 (Home/Win):{RESET}")
            print(f"  Outcome: {opportunity['player_a']}")
            print(f"  Bookmaker: {opportunity['bookmaker_a']}{rank_a_label}")
            print(f"  Odds: {opportunity['odds_a']:.2f}")
            print(f"  Stake: {format_currency(opportunity['stake_a'])}")
            print()

            print(f"{BOLD}BET 2 (Draw):{RESET}")
            print(f"  Outcome: {opportunity['player_draw']}")
            print(f"  Bookmaker: {opportunity['bookmaker_draw']}{rank_draw_label}")
            print(f"  Odds: {opportunity['odds_draw']:.2f}")
            print(f"  Stake: {format_currency(opportunity['stake_draw'])}")
            print()

            print(f"{BOLD}BET 3 (Away/Loss):{RESET}")
            print(f"  Outcome: {opportunity['player_b']}")
            print(f"  Bookmaker: {opportunity['bookmaker_b']}{rank_b_label}")
            print(f"  Odds: {opportunity['odds_b']:.2f}")
            print(f"  Stake: {format_currency(opportunity['stake_b'])}")
            print()
        
        print(f"{GREEN}TOTAL INVESTMENT: {format_currency(opportunity['total_stake'])}{RESET}")
        print(f"{GREEN}{BOLD}GUARANTEED PROFIT: {format_currency(opportunity['guaranteed_profit'])}{RESET}")
        print("=" * 80)
        print()
    
    def check_for_arbitrage(self):
        """
        Main function to check for arbitrage opportunities.
        Fetches odds, processes them (including cross-market), and alerts on opportunities.
        After each cycle, displays top 5 most profitable/confident opportunities.
        """
        self.cycle_number += 1
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"\n{'=' * 100}")
        print(f"[{current_time}] Cycle #{self.cycle_number} - Checking for arbitrage opportunities...")
        print(f"{'=' * 100}")

        all_opportunities = []
        cross_market_count = 0

        # Fetch and process odds for each sport
        for sport in config.SPORTS:
            print(f"[{sport}] Fetching odds...")
            odds_data = self.fetch_odds(sport)

            if odds_data:
                print(f"[{sport}] Found {len(odds_data)} matches")

                # Process odds (single market per match)
                processed_matches = self.process_odds(odds_data, sport)
                print(f"[{sport}] Processed {len(processed_matches)} single-market opportunities")

                # Find standard arbitrage opportunities
                opportunities = self.find_arbitrage_opportunities(processed_matches)

                if opportunities:
                    print(f"[{sport}] Found {len(opportunities)} standard arbitrage opportunities!")
                    all_opportunities.extend(opportunities)

                # Also check for cross-market arbitrage
                cross_market_opportunities = []
                for match_data in odds_data:
                    match_data['sport'] = sport  # Add sport to match data
                    cross_opps = self.find_cross_market_arbitrage(match_data)
                    cross_market_opportunities.extend(cross_opps)

                if cross_market_opportunities:
                    print(f"[{sport}] Found {len(cross_market_opportunities)} cross-market arbitrage opportunities!")
                    cross_market_count += len(cross_market_opportunities)
                    all_opportunities.extend(cross_market_opportunities)
                else:
                    print(f"[{sport}] No cross-market arbitrage opportunities found")
            else:
                print(f"[{sport}] Failed to fetch odds")

        # Collect all opportunities that pass filters and should alert
        valid_opportunities = []
        new_opportunities = 0
        filtered_count = 0
        duplicate_count = 0
        
        for opp in all_opportunities:
            # Log to database if enabled
            opportunity_id = None
            if self.db:
                opportunity_id = self.db.log_opportunity(opp)

            # Check if passes smart filters
            passes, reason = self.passes_filters(opp)
            if not passes:
                filtered_count += 1
                continue

            # Check if not a duplicate
            if self.should_alert(opp):
                # Calculate score for ranking
                score = self.calculate_opportunity_score(opp)
                opp['_score'] = score  # Store score temporarily
                valid_opportunities.append(opp)
                new_opportunities += 1

                # Display individual alert if enabled
                if config.SHOW_INDIVIDUAL_ALERTS:
                    self.display_alert(opp)

                # Log alert to database
                if self.db and opportunity_id:
                    self.db.log_alert(opportunity_id)
            else:
                duplicate_count += 1

        # Display summary statistics
        print(f"\n{'─' * 100}")
        print(f"Cycle #{self.cycle_number} Summary:")
        print(f"  • Total opportunities found: {len(all_opportunities)}")
        print(f"  • Filtered out: {filtered_count} (trust/timing/profit threshold)")
        print(f"  • Duplicates skipped: {duplicate_count}")
        print(f"  • New opportunities: {new_opportunities}")
        if cross_market_count > 0:
            print(f"  • Cross-market opportunities: {cross_market_count}")
        print(f"  • API calls made: {self.api_call_count}")
        print(f"{'─' * 100}")

        # Rank and display top opportunities
        if valid_opportunities:
            # Sort by score (descending)
            valid_opportunities.sort(key=lambda x: x.get('_score', 0), reverse=True)
            
            # Display top opportunities table
            self.display_top_opportunities(valid_opportunities, self.cycle_number)
            
            # Clean up temporary score field
            for opp in valid_opportunities:
                opp.pop('_score', None)
        else:
            print("\n[INFO] No new arbitrage opportunities found in this cycle.")
            print()


def main():
    """Main entry point for the application."""
    current_interval = config.get_check_interval()
    
    print("=" * 80)
    print("Sports Betting Arbitrage Finder - MVP")
    print("=" * 80)
    print(f"Monitoring: {', '.join([get_sport_display_name(s) for s in config.SPORTS])}")
    print(f"Minimum Profit Threshold: {config.MINIMUM_PROFIT_THRESHOLD}%")
    print(f"Check Interval: Dynamic (Peak: {config.PEAK_CHECK_INTERVAL}min, Off-Peak: {config.OFF_PEAK_CHECK_INTERVAL}min)")
    print(f"Current Interval: Every {current_interval} minutes")
    print(f"Default Stake: {format_currency(config.DEFAULT_STAKE)}")
    print("=" * 80)
    print("\nPress Ctrl+C to stop\n")
    
    # Create finder instance
    finder = ArbitrageFinder()
    
    # Run immediately on start
    try:
        finder.check_for_arbitrage()
    except Exception as e:
        print(f"[ERROR] Exception during check: {e}")
    
    # Dynamic scheduling with interval updates
    last_interval = current_interval
    next_check_time = datetime.now() + timedelta(minutes=current_interval)
    
    # Run the scheduler
    try:
        while True:
            current_time = datetime.now()
            
            # Check if it's time for next check
            if current_time >= next_check_time:
                # Update interval if time of day changed
                current_interval = config.get_check_interval()
                if current_interval != last_interval:
                    print(f"\n[INFO] Check interval changed to {current_interval} minutes")
                    last_interval = current_interval
                
                # Run the check
                safe_check(finder)
                
                # Schedule next check
                next_check_time = current_time + timedelta(minutes=current_interval)
            
            time.sleep(30)  # Check every 30 seconds if we need to run
            
    except KeyboardInterrupt:
        print("\n\nStopping arbitrage finder...")
        print(f"Total API calls made: {finder.api_call_count}")
        print("Goodbye!")
        sys.exit(0)


def safe_check(finder):
    """Wrapper to safely run checks with error handling."""
    try:
        finder.check_for_arbitrage()
    except Exception as e:
        print(f"[ERROR] Exception during check: {e}")


if __name__ == "__main__":
    main()

