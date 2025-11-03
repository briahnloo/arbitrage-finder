"""
Main arbitrage finder application.
Fetches odds from The Odds API, identifies arbitrage opportunities,
and displays alerts in the console.
"""

import requests
import schedule
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import sys

import config
from utils import (
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
    calculate_stakes_with_validation
)

# Import database if logging enabled
if config.ENABLE_DATABASE_LOGGING:
    from database import ArbitrageDatabase


class ArbitrageFinder:
    """Main class for finding and alerting arbitrage opportunities."""
    
    def __init__(self):
        """Initialize the arbitrage finder."""
        self.recent_alerts = {}  # Track recent alerts to avoid duplicates
        self.api_call_count = 0
        self.last_api_call_time = None
        
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

        For example: h2h odds + spread odds can create arbitrage.
        Team A moneyline 2.00 + Team B spread +3.5 at 2.05
        creates arbitrage if the outcomes don't overlap perfectly.

        Args:
            match_data: Single match data with multiple bookmakers

        Returns:
            List of cross-market arbitrage opportunities
        """
        cross_market_opps = []

        if not match_data.get('bookmakers'):
            return cross_market_opps

        home_team = match_data.get('home_team', 'Unknown')
        away_team = match_data.get('away_team', 'Unknown')
        commence_time = match_data.get('commence_time', '')

        # Build market data by outcome type
        # {outcome_type: {market_type: {point: [(odds, bookmaker)]}}}
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
                        continue  # Skip unidentifiable outcomes

                    # Create key for this outcome/market combination
                    if market_key == 'h2h':
                        combo_key = f"{outcome_type}"
                    else:
                        point = outcome.get('point')
                        combo_key = f"{outcome_type}_{point}"

                    # Store the odds option
                    if combo_key not in market_combinations:
                        market_combinations[combo_key] = []

                    market_combinations[combo_key].append({
                        'odds': odds,
                        'bookmaker': bookmaker_name,
                        'market': market_key,
                        'point': outcome.get('point'),
                        'raw_name': outcome.get('name')
                    })

        # Now try combinations across different market types
        # Look for HOME outcomes with different points/markets
        home_outcomes = {k: v for k, v in market_combinations.items() if k.startswith('HOME')}
        away_outcomes = {k: v for k, v in market_combinations.items() if k.startswith('AWAY')}

        # Try HOME from one market type with AWAY from another
        for home_key, home_options in home_outcomes.items():
            for away_key, away_options in away_outcomes.items():
                # Skip if they're from the same market and point (would be captured by 2-way)
                home_point = home_key.split('_')[1] if '_' in home_key else None
                away_point = away_key.split('_')[1] if '_' in away_key else None

                # Try top 2 odds for each
                for home_opt in home_options[:2]:
                    for away_opt in away_options[:2]:
                        odds_home = home_opt['odds']
                        odds_away = away_opt['odds']

                        # Calculate if this is valid arbitrage
                        profit_margin = calculate_arbitrage_profit(odds_home, odds_away)

                        if profit_margin >= config.MINIMUM_PROFIT_THRESHOLD:
                            # This is a cross-market arbitrage opportunity
                            stakes_result = calculate_stakes_with_validation(
                                odds_home, odds_away, config.DEFAULT_STAKE
                            )

                            if stakes_result is not None:
                                stake_a, stake_b = stakes_result
                                guaranteed_profit = calculate_guaranteed_profit(
                                    odds_home, odds_away, stake_a, stake_b
                                )

                                cross_market_opps.append({
                                    'sport': match_data.get('sport', 'Unknown'),
                                    'market': 'cross_market',  # Special marker
                                    'num_outcomes': 2,
                                    'player_a': home_key,
                                    'player_b': away_key,
                                    'odds_a': odds_home,
                                    'odds_b': odds_away,
                                    'bookmaker_a': home_opt['bookmaker'],
                                    'bookmaker_b': away_opt['bookmaker'],
                                    'market_a': home_opt['market'],
                                    'market_b': away_opt['market'],
                                    'point_a': home_opt.get('point'),
                                    'point_b': away_opt.get('point'),
                                    'profit_margin': profit_margin,
                                    'stake_a': stake_a,
                                    'stake_b': stake_b,
                                    'guaranteed_profit': guaranteed_profit,
                                    'total_stake': config.DEFAULT_STAKE,
                                    'is_cross_market': True,
                                    'commence_time': commence_time,
                                    'event_name': f"{home_team} vs {away_team}"
                                })

        return cross_market_opps

    def find_arbitrage_opportunities(self, matches: List[Dict]) -> List[Dict]:
        """
        Identify arbitrage opportunities from processed matches (2-way and 3-way).
        Uses validated stakes that survive rounding.

        Args:
            matches: List of processed match dictionaries

        Returns:
            List of arbitrage opportunities with verified profit calculations
        """
        opportunities = []

        for match in matches:
            num_outcomes = match.get('num_outcomes', 2)

            if num_outcomes == 2:
                # 2-way arbitrage (combat sports, totals, spreads)
                odds_a = match['odds_a']
                odds_b = match['odds_b']

                # Calculate profit margin
                profit_margin = calculate_arbitrage_profit(odds_a, odds_b)

                # Check if meets minimum threshold
                if profit_margin >= config.MINIMUM_PROFIT_THRESHOLD:
                    # Calculate and validate stakes (handles rounding)
                    stakes_result = calculate_stakes_with_validation(
                        odds_a, odds_b, config.DEFAULT_STAKE
                    )

                    if stakes_result is None:
                        # Arbitrage is broken by rounding, skip this opportunity
                        continue

                    stake_a, stake_b = stakes_result

                    # Calculate guaranteed profit
                    guaranteed_profit = calculate_guaranteed_profit(
                        odds_a, odds_b, stake_a, stake_b
                    )

                    # Create opportunity dict
                    opportunity = {
                        **match,
                        'profit_margin': profit_margin,
                        'stake_a': stake_a,
                        'stake_b': stake_b,
                        'guaranteed_profit': guaranteed_profit,
                        'total_stake': config.DEFAULT_STAKE,
                        'is_rounded': True  # Flag that stakes were validated after rounding
                    }

                    opportunities.append(opportunity)

            elif num_outcomes == 3:
                # 3-way arbitrage (soccer/hockey with draw)
                odds_a = match['odds_a']
                odds_draw = match['odds_draw']
                odds_b = match['odds_b']

                # Calculate profit margin
                profit_margin = calculate_three_way_arbitrage(odds_a, odds_draw, odds_b)

                # Check if meets minimum threshold
                if profit_margin >= config.MINIMUM_PROFIT_THRESHOLD:
                    # For 3-way, calculate stakes the traditional way then verify
                    denominator = (1 / odds_a) + (1 / odds_draw) + (1 / odds_b)
                    stake_a_ideal = config.DEFAULT_STAKE * (1 / odds_a) / denominator
                    stake_draw_ideal = config.DEFAULT_STAKE * (1 / odds_draw) / denominator
                    stake_b_ideal = config.DEFAULT_STAKE * (1 / odds_b) / denominator

                    # Round to cents
                    stake_a = round(stake_a_ideal, 2)
                    stake_draw = round(stake_draw_ideal, 2)
                    stake_b = round(config.DEFAULT_STAKE - stake_a - stake_draw, 2)

                    # Verify returns are equal within tolerance
                    return_a = stake_a * odds_a
                    return_draw = stake_draw * odds_draw
                    return_b = stake_b * odds_b

                    max_return = max(return_a, return_draw, return_b)
                    min_return = min(return_a, return_draw, return_b)

                    if max_return - min_return > 0.01:
                        # Rounding broke the arbitrage, skip
                        continue

                    # Calculate guaranteed profit
                    guaranteed_profit = calculate_three_way_profit(
                        odds_a, odds_draw, odds_b, stake_a, stake_draw, stake_b
                    )

                    # Create opportunity dict
                    opportunity = {
                        **match,
                        'profit_margin': profit_margin,
                        'stake_a': stake_a,
                        'stake_draw': stake_draw,
                        'stake_b': stake_b,
                        'guaranteed_profit': guaranteed_profit,
                        'total_stake': config.DEFAULT_STAKE,
                        'is_rounded': True
                    }

                    opportunities.append(opportunity)

        return opportunities
    
    def create_alert_key(self, opportunity: Dict) -> str:
        """
        Create a unique key for an opportunity to track duplicates.
        
        Args:
            opportunity: Opportunity dictionary
        
        Returns:
            Unique string key
        """
        return f"{opportunity['player_a']}_vs_{opportunity['player_b']}_{opportunity['bookmaker_a']}_{opportunity['bookmaker_b']}"
    
    def passes_filters(self, opportunity: Dict) -> tuple:
        """
        Check if opportunity passes all smart filters.
        
        Args:
            opportunity: Opportunity dictionary
        
        Returns:
            Tuple of (passes: bool, reason: str)
        """
        # Check bookmaker trust scores
        bookmakers = [opportunity['bookmaker_a'], opportunity['bookmaker_b']]
        if opportunity.get('num_outcomes') == 3:
            bookmakers.append(opportunity['bookmaker_draw'])
        
        for bookmaker in bookmakers:
            trust_score = config.BOOKMAKER_TRUST_SCORES.get(bookmaker, 5)  # Default 5 if unknown
            if trust_score < config.MINIMUM_BOOKMAKER_TRUST:
                return (False, f"Bookmaker {bookmaker} trust score ({trust_score}) below minimum ({config.MINIMUM_BOOKMAKER_TRUST})")
        
        # Check event timing
        try:
            event_time = datetime.fromisoformat(opportunity['commence_time'].replace('Z', '+00:00'))
            current_time = datetime.now(event_time.tzinfo)
            time_until_event = (event_time - current_time).total_seconds() / 3600  # Hours
            
            if time_until_event < config.MINIMUM_EVENT_START_HOURS:
                return (False, f"Event starts in {time_until_event:.1f} hours (minimum: {config.MINIMUM_EVENT_START_HOURS})")
            
            if time_until_event > (config.MAXIMUM_EVENT_START_DAYS * 24):
                return (False, f"Event too far in future ({time_until_event/24:.1f} days)")
        except Exception as e:
            # If we can't parse time, allow it through
            pass
        
        # Check sport-specific profit threshold
        sport = opportunity['sport']
        min_profit = config.SPORT_PROFIT_THRESHOLDS.get(sport, config.MINIMUM_PROFIT_THRESHOLD)
        if opportunity['profit_margin'] < min_profit:
            return (False, f"Profit {opportunity['profit_margin']:.2f}% below sport minimum {min_profit}%")
        
        return (True, "All filters passed")
    
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
        print()
        
        # Check if 2-way or 3-way arbitrage
        num_outcomes = opportunity.get('num_outcomes', 2)
        
        if num_outcomes == 2:
            # Display 2-way arbitrage (2 bets)
            print(f"{BOLD}BET 1:{RESET}")
            print(f"  Outcome: {opportunity['player_a']}")
            print(f"  Bookmaker: {opportunity['bookmaker_a']}")
            print(f"  Odds: {opportunity['odds_a']:.2f}")
            print(f"  Stake: {format_currency(opportunity['stake_a'])}")
            print()
            
            print(f"{BOLD}BET 2:{RESET}")
            print(f"  Outcome: {opportunity['player_b']}")
            print(f"  Bookmaker: {opportunity['bookmaker_b']}")
            print(f"  Odds: {opportunity['odds_b']:.2f}")
            print(f"  Stake: {format_currency(opportunity['stake_b'])}")
            print()
        
        elif num_outcomes == 3:
            # Display 3-way arbitrage (3 bets)
            print(f"{BOLD}BET 1 (Home/Win):{RESET}")
            print(f"  Outcome: {opportunity['player_a']}")
            print(f"  Bookmaker: {opportunity['bookmaker_a']}")
            print(f"  Odds: {opportunity['odds_a']:.2f}")
            print(f"  Stake: {format_currency(opportunity['stake_a'])}")
            print()
            
            print(f"{BOLD}BET 2 (Draw):{RESET}")
            print(f"  Outcome: {opportunity['player_draw']}")
            print(f"  Bookmaker: {opportunity['bookmaker_draw']}")
            print(f"  Odds: {opportunity['odds_draw']:.2f}")
            print(f"  Stake: {format_currency(opportunity['stake_draw'])}")
            print()
            
            print(f"{BOLD}BET 3 (Away/Loss):{RESET}")
            print(f"  Outcome: {opportunity['player_b']}")
            print(f"  Bookmaker: {opportunity['bookmaker_b']}")
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
        """
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"\n[{current_time}] Checking for arbitrage opportunities...")

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

        # Display alerts for new opportunities that pass filters
        new_opportunities = 0
        filtered_count = 0
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
                self.display_alert(opp)
                new_opportunities += 1

                # Log alert to database
                if self.db and opportunity_id:
                    self.db.log_alert(opportunity_id)

        if filtered_count > 0:
            print(f"[INFO] Filtered out {filtered_count} opportunities (trust/timing/profit threshold)")

        if cross_market_count > 0:
            print(f"[INFO] Cross-market opportunities detected: {cross_market_count}")

        if new_opportunities == 0 and len(all_opportunities) > 0:
            remaining = len(all_opportunities) - filtered_count
            if remaining > 0:
                print(f"[INFO] Found {remaining} opportunities, but all were recent duplicates")
            else:
                print("[INFO] No arbitrage opportunities found in this check")
        elif new_opportunities == 0:
            print("[INFO] No arbitrage opportunities found in this check")

        print(f"[INFO] Total API calls made: {self.api_call_count}")


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

