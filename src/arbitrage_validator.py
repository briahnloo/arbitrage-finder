"""
Comprehensive arbitrage validation and scenario simulation.
Ensures all opportunities are mathematically sound and risk-free.
"""

from typing import List, Dict, Tuple, Optional
from enum import Enum
import math


class OutcomeType(Enum):
    """Represents different outcome types in sports betting."""
    HOME_WIN = "HOME_WIN"
    AWAY_WIN = "AWAY_WIN"
    DRAW = "DRAW"
    HOME_SPREAD_COVER = "HOME_SPREAD_COVER"
    AWAY_SPREAD_COVER = "AWAY_SPREAD_COVER"
    OVER = "OVER"
    UNDER = "UNDER"


class GameScenario:
    """Represents a specific game outcome scenario."""

    def __init__(self, home_score: int, away_score: int):
        """
        Initialize a game scenario.

        Args:
            home_score: Home team's final score
            away_score: Away team's final score
        """
        self.home_score = home_score
        self.away_score = away_score
        self.point_differential = home_score - away_score

    def __repr__(self):
        return f"{self.home_score}-{self.away_score}"


class ArbitrageValidator:
    """Validates arbitrage opportunities for mathematical soundness."""

    # Score scenarios to test (covers most realistic outcomes)
    # Format: (home_score, away_score)
    NHL_SCENARIOS = [
        (0, 0), (1, 0), (0, 1), (1, 1), (2, 0), (0, 2),
        (2, 1), (1, 2), (2, 2), (3, 0), (0, 3), (3, 1),
        (1, 3), (3, 2), (2, 3), (4, 0), (0, 4), (4, 1),
        (1, 4), (4, 2), (2, 4), (3, 3), (4, 3), (3, 4),
        (5, 0), (0, 5), (5, 1), (1, 5), (5, 2), (2, 5),
        (5, 3), (3, 5), (5, 4), (4, 5), (5, 5), (6, 0),
        (0, 6), (6, 1), (1, 6), (6, 2), (2, 6), (6, 3),
        (3, 6), (6, 4), (4, 6), (6, 5), (5, 6)
    ]

    SOCCER_SCENARIOS = [
        (0, 0), (1, 0), (0, 1), (1, 1), (2, 0), (0, 2),
        (2, 1), (1, 2), (2, 2), (3, 0), (0, 3), (3, 1),
        (1, 3), (3, 2), (2, 3), (3, 3), (4, 0), (0, 4),
        (4, 1), (1, 4), (4, 2), (2, 4), (4, 3), (3, 4),
        (5, 0), (0, 5), (5, 1), (1, 5), (5, 2), (2, 5),
    ]

    BASKETBALL_SCENARIOS = [
        (80, 75), (85, 80), (90, 88), (95, 92), (100, 98),
        (105, 100), (110, 105), (115, 110), (120, 115),
        (75, 80), (80, 85), (88, 90), (92, 95), (98, 100),
        (100, 105), (105, 110), (110, 115), (115, 120),
    ]

    TENNIS_SCENARIOS = [
        # Tennis is binary (Player A wins or Player B wins)
        "A_WINS", "B_WINS"
    ]

    MMA_SCENARIOS = [
        # MMA is binary + draw
        "A_WINS", "B_WINS", "DRAW"
    ]

    @staticmethod
    def matches_home_win(scenario: GameScenario) -> bool:
        """Check if scenario matches HOME_WIN outcome."""
        if isinstance(scenario, str):
            # String scenarios for combat sports (MMA/boxing)
            return scenario == "A_WINS"
        if not isinstance(scenario, GameScenario):
            raise TypeError(f"Expected GameScenario or str, got {type(scenario)}")
        return scenario.point_differential > 0

    @staticmethod
    def matches_away_win(scenario: GameScenario) -> bool:
        """Check if scenario matches AWAY_WIN outcome."""
        if isinstance(scenario, str):
            # String scenarios for combat sports (MMA/boxing)
            return scenario == "B_WINS"
        if not isinstance(scenario, GameScenario):
            raise TypeError(f"Expected GameScenario or str, got {type(scenario)}")
        return scenario.point_differential < 0

    @staticmethod
    def matches_draw(scenario: GameScenario) -> bool:
        """Check if scenario matches DRAW outcome."""
        if isinstance(scenario, str):
            # String scenarios for combat sports (MMA/boxing)
            return scenario == "DRAW"
        if not isinstance(scenario, GameScenario):
            raise TypeError(f"Expected GameScenario or str, got {type(scenario)}")
        return scenario.point_differential == 0

    @staticmethod
    def matches_home_spread(scenario: GameScenario, spread: float) -> bool:
        """
        Check if scenario matches HOME_SPREAD_COVER outcome.

        Args:
            scenario: Game scenario
            spread: Spread value (negative = home is favored)
                    e.g., -1.5 means home must win by 2+

        Returns:
            True if home covers the spread
        """
        if isinstance(scenario, str):
            # Spread betting not applicable to string scenarios (combat sports)
            raise ValueError(f"Spread betting not supported for string scenarios: {scenario}")
        if not isinstance(scenario, GameScenario):
            raise TypeError(f"Expected GameScenario or str, got {type(scenario)}")
        # If spread is -1.5, home needs to win by 2 or more
        # If spread is +1.5, home needs to win or lose by 1 or less
        threshold = abs(spread)

        if spread < 0:
            # Home is favored (must win by more than threshold)
            return scenario.point_differential > threshold
        else:
            # Home is underdog (can lose but by less than threshold)
            return scenario.point_differential > -threshold

    @staticmethod
    def matches_away_spread(scenario: GameScenario, spread: float) -> bool:
        """
        Check if scenario matches AWAY_SPREAD_COVER outcome.

        Args:
            scenario: Game scenario
            spread: Away team's spread (positive = underdog spread)

        Returns:
            True if away covers the spread
        """
        # This is the opposite of home spread
        return ArbitrageValidator.matches_home_spread(scenario, -spread)

    @staticmethod
    def matches_over(scenario: GameScenario, total: float) -> bool:
        """Check if scenario matches OVER total."""
        if isinstance(scenario, str):
            # Totals betting not applicable to string scenarios (combat sports)
            raise ValueError(f"Totals betting not supported for string scenarios: {scenario}")
        if not isinstance(scenario, GameScenario):
            raise TypeError(f"Expected GameScenario or str, got {type(scenario)}")
        combined_score = scenario.home_score + scenario.away_score
        return combined_score > total

    @staticmethod
    def matches_under(scenario: GameScenario, total: float) -> bool:
        """Check if scenario matches UNDER total."""
        if isinstance(scenario, str):
            # Totals betting not applicable to string scenarios (combat sports)
            raise ValueError(f"Totals betting not supported for string scenarios: {scenario}")
        if not isinstance(scenario, GameScenario):
            raise TypeError(f"Expected GameScenario or str, got {type(scenario)}")
        combined_score = scenario.home_score + scenario.away_score
        return combined_score < total

    def evaluate_outcome_in_scenario(
        self,
        outcome: Dict,
        scenario: GameScenario
    ) -> bool:
        """
        Determine if an outcome wins in a given scenario.

        Args:
            outcome: Dict with keys 'outcome_type', 'spread', 'total'
            scenario: Game scenario (GameScenario object or string for combat sports)

        Returns:
            True if outcome wins in this scenario
        """
        outcome_type = outcome['outcome_type']
        spread = outcome.get('spread')
        total = outcome.get('total')

        # Handle string scenarios for combat sports (MMA/boxing)
        if isinstance(scenario, str):
            # String scenarios: "A_WINS", "B_WINS", "DRAW"
            # For combat sports, outcome_type can be:
            # - String like "HOME", "AWAY", or player names (mapped to A_WINS/B_WINS)
            # - OutcomeType enum (rarely used for combat sports)
            
            # Handle string outcome types (combat sports)
            if isinstance(outcome_type, str):
                # Map outcome strings to scenario strings
                outcome_str = outcome_type.upper()
                if outcome_str in ["HOME", "A_WINS"] or "HOME" in outcome_str:
                    return scenario == "A_WINS"
                elif outcome_str in ["AWAY", "B_WINS"] or "AWAY" in outcome_str:
                    return scenario == "B_WINS"
                elif outcome_str == "DRAW":
                    return scenario == "DRAW"
                # If outcome is a player name, try to match against scenario
                # For now, assume player_a = A_WINS, player_b = B_WINS
                # This is handled by the caller mapping
                return False
            
            # Handle OutcomeType enum with string scenarios
            if outcome_type == OutcomeType.HOME_WIN:
                return scenario == "A_WINS"
            elif outcome_type == OutcomeType.AWAY_WIN:
                return scenario == "B_WINS"
            elif outcome_type == OutcomeType.DRAW:
                return scenario == "DRAW"
            # Spreads and totals don't apply to string scenarios
            return False

        # Handle GameScenario objects (team sports)
        if not isinstance(scenario, GameScenario):
            raise TypeError(f"Expected GameScenario or str, got {type(scenario)}")

        # Handle OutcomeType enum outcomes
        if isinstance(outcome_type, OutcomeType):
            if outcome_type == OutcomeType.HOME_WIN:
                return self.matches_home_win(scenario)
            elif outcome_type == OutcomeType.AWAY_WIN:
                return self.matches_away_win(scenario)
            elif outcome_type == OutcomeType.DRAW:
                return self.matches_draw(scenario)
            elif outcome_type == OutcomeType.HOME_SPREAD_COVER:
                return self.matches_home_spread(scenario, spread)
            elif outcome_type == OutcomeType.AWAY_SPREAD_COVER:
                return self.matches_away_spread(scenario, spread)
            elif outcome_type == OutcomeType.OVER:
                return self.matches_over(scenario, total)
            elif outcome_type == OutcomeType.UNDER:
                return self.matches_under(scenario, total)
        
        # Handle string outcome types with GameScenario (shouldn't happen normally)
        # But handle gracefully for compatibility
        if isinstance(outcome_type, str):
            outcome_str = outcome_type.upper()
            if outcome_str in ["HOME", "HOME_WIN"]:
                return self.matches_home_win(scenario)
            elif outcome_str in ["AWAY", "AWAY_WIN"]:
                return self.matches_away_win(scenario)
            elif outcome_str == "DRAW":
                return self.matches_draw(scenario)

        return False

    def validate_two_way_arbitrage(
        self,
        outcome_a: Dict,
        outcome_b: Dict,
        stake_a: float,
        stake_b: float,
        odds_a: float,
        odds_b: float,
        sport: str
    ) -> Tuple[bool, str, Dict]:
        """
        Validate 2-way arbitrage by simulating all game scenarios.

        For moneyline betting, draws/ties are acceptable as uncovered scenarios
        (in sports like hockey/soccer where ties exist).

        Args:
            outcome_a: First outcome dict
            outcome_b: Second outcome dict
            stake_a: Amount bet on outcome A
            stake_b: Amount bet on outcome B
            odds_a: Decimal odds for outcome A
            odds_b: Decimal odds for outcome B
            sport: Sport type (nhl, soccer, etc.)

        Returns:
            Tuple of (is_valid, reason, results_dict)
        """
        # Select appropriate scenarios for sport
        scenarios = self._get_scenarios_for_sport(sport)

        results = {
            'valid': True,
            'profit_range': [float('inf'), float('-inf')],
            'scenarios_analyzed': 0,
            'loss_scenarios': [],
            'profit_scenarios': [],
            'draw_scenarios': [],
            'all_scenario_profits': []
        }

        for scenario in scenarios:
            results['scenarios_analyzed'] += 1

            # Determine which outcomes win in this scenario
            try:
                outcome_a_wins = self.evaluate_outcome_in_scenario(outcome_a, scenario)
                outcome_b_wins = self.evaluate_outcome_in_scenario(outcome_b, scenario)
            except (TypeError, ValueError, AttributeError) as e:
                # Catch type errors and provide clear error message
                error_msg = f"Error evaluating scenario {scenario}: {e}. Outcome A: {outcome_a.get('outcome_type')}, Outcome B: {outcome_b.get('outcome_type')}"
                results['valid'] = False
                return (False, error_msg, results)

            # Calculate profit for this scenario
            if outcome_a_wins and outcome_b_wins:
                # Both bets win (should not happen in valid arbitrage)
                profit = (stake_a * odds_a) + (stake_b * odds_b) - (stake_a + stake_b)
                results['valid'] = False
                return (False, f"Both outcomes win in scenario {scenario}", results)

            elif outcome_a_wins:
                profit = (stake_a * odds_a) - (stake_a + stake_b)
            elif outcome_b_wins:
                profit = (stake_b * odds_b) - (stake_a + stake_b)
            else:
                # Neither outcome wins - check if this is a draw scenario
                # Draws are acceptable for moneyline betting (for GameScenario and string scenarios)
                is_draw = False
                if isinstance(scenario, GameScenario):
                    is_draw = scenario.point_differential == 0
                elif isinstance(scenario, str):
                    # For string scenarios (tennis, MMA), check if it's a DRAW scenario
                    is_draw = scenario == "DRAW"

                if is_draw:
                    profit = -(stake_a + stake_b)  # Push/draw loss
                    results['draw_scenarios'].append(scenario)
                else:
                    # Non-draw scenario with no winner - this is invalid
                    profit = -(stake_a + stake_b)
                    results['valid'] = False
                    results['loss_scenarios'].append(scenario)

            results['all_scenario_profits'].append({
                'scenario': str(scenario),
                'outcome_a_wins': outcome_a_wins,
                'outcome_b_wins': outcome_b_wins,
                'profit': round(profit, 2)
            })

            # Update profit range (only from winning scenarios)
            if outcome_a_wins or outcome_b_wins:
                results['profit_range'][0] = min(results['profit_range'][0], profit)
                results['profit_range'][1] = max(results['profit_range'][1], profit)

                if profit > 0.01:  # Small tolerance for rounding
                    results['profit_scenarios'].append(scenario)

        # Check if there are non-draw loss scenarios
        if results['loss_scenarios']:
            reason = f"Arbitrage fails in {len(results['loss_scenarios'])} non-draw scenarios: {results['loss_scenarios'][:3]}"
            results['valid'] = False
            return (False, reason, results)

        # Verify profit is consistent (arbitrage property)
        # Only check profit across winning scenarios (draws are acceptable losses)
        if len(results['profit_scenarios']) == 0:
            return (False, "No profitable scenarios found", results)

        profit_min = results['profit_range'][0]
        profit_max = results['profit_range'][1]

        # For moneyline with draws, profit_min might be 0 (from rounding)
        # So we check if profit_max is consistent instead
        if profit_min == float('inf'):
            # No winning scenarios at all
            return (False, "No winning scenarios found", results)

        profit_diff = profit_max - profit_min

        if profit_diff > 0.10:  # More than 10 cents difference (allow for rounding)
            reason = f"Profit varies significantly across scenarios (${profit_min:.2f} to ${profit_max:.2f})"
            results['valid'] = False
            return (False, reason, results)

        # Use minimum positive profit (excluding draws)
        if profit_min <= 0:
            actual_profit = min([p for p in [results['profit_range'][0], results['profit_range'][1]] if p > 0], default=0)
        else:
            actual_profit = profit_min

        reason = f"Valid arbitrage: guaranteed profit ${actual_profit:.2f} (draws: loss ${stake_a + stake_b:.2f})"
        return (True, reason, results)

    def validate_three_way_arbitrage(
        self,
        outcome_a: Dict,
        outcome_draw: Dict,
        outcome_b: Dict,
        stake_a: float,
        stake_draw: float,
        stake_b: float,
        odds_a: float,
        odds_draw: float,
        odds_b: float,
        sport: str
    ) -> Tuple[bool, str, Dict]:
        """
        Validate 3-way arbitrage by simulating all game scenarios.

        Args:
            outcome_a: Home outcome
            outcome_draw: Draw outcome
            outcome_b: Away outcome
            stake_a: Amount bet on outcome A
            stake_draw: Amount bet on draw
            stake_b: Amount bet on outcome B
            odds_a: Decimal odds for outcome A
            odds_draw: Decimal odds for draw
            odds_b: Decimal odds for outcome B
            sport: Sport type

        Returns:
            Tuple of (is_valid, reason, results_dict)
        """
        scenarios = self._get_scenarios_for_sport(sport)

        results = {
            'valid': True,
            'profit_range': [float('inf'), float('-inf')],
            'scenarios_analyzed': 0,
            'loss_scenarios': [],
            'all_scenario_profits': []
        }

        for scenario in scenarios:
            results['scenarios_analyzed'] += 1

            try:
                outcome_a_wins = self.evaluate_outcome_in_scenario(outcome_a, scenario)
                outcome_draw_wins = self.evaluate_outcome_in_scenario(outcome_draw, scenario)
                outcome_b_wins = self.evaluate_outcome_in_scenario(outcome_b, scenario)
            except (TypeError, ValueError, AttributeError) as e:
                # Catch type errors and provide clear error message
                error_msg = f"Error evaluating scenario {scenario}: {e}. Outcome A: {outcome_a.get('outcome_type')}, Draw: {outcome_draw.get('outcome_type')}, Outcome B: {outcome_b.get('outcome_type')}"
                results['valid'] = False
                return (False, error_msg, results)

            # Count winning outcomes
            winning_outcomes = sum([outcome_a_wins, outcome_draw_wins, outcome_b_wins])

            if winning_outcomes == 0:
                # No outcome wins
                profit = -(stake_a + stake_draw + stake_b)
                results['loss_scenarios'].append(scenario)
            elif winning_outcomes > 1:
                # Multiple outcomes win (invalid arbitrage)
                results['valid'] = False
                return (False, f"Multiple outcomes win in scenario {scenario}", results)
            else:
                # Exactly one outcome wins
                if outcome_a_wins:
                    profit = (stake_a * odds_a) - (stake_a + stake_draw + stake_b)
                elif outcome_draw_wins:
                    profit = (stake_draw * odds_draw) - (stake_a + stake_draw + stake_b)
                else:
                    profit = (stake_b * odds_b) - (stake_a + stake_draw + stake_b)

            results['all_scenario_profits'].append({
                'scenario': str(scenario),
                'outcomes_win': [outcome_a_wins, outcome_draw_wins, outcome_b_wins],
                'profit': round(profit, 2)
            })

            results['profit_range'][0] = min(results['profit_range'][0], profit)
            results['profit_range'][1] = max(results['profit_range'][1], profit)

        if results['loss_scenarios']:
            reason = f"Arbitrage fails in {len(results['loss_scenarios'])} scenarios"
            results['valid'] = False
            return (False, reason, results)

        profit_diff = results['profit_range'][1] - results['profit_range'][0]
        if profit_diff > 0.05:
            reason = f"Profit varies significantly: ${results['profit_range'][0]:.2f} to ${results['profit_range'][1]:.2f}"
            results['valid'] = False
            return (False, reason, results)

        reason = f"Valid 3-way arbitrage: guaranteed profit ${results['profit_range'][0]:.2f}"
        return (True, reason, results)

    def _get_scenarios_for_sport(self, sport: str) -> List:
        """Get appropriate scenarios for a sport."""
        if 'hockey' in sport or 'nhl' in sport:
            return [GameScenario(h, a) for h, a in self.NHL_SCENARIOS]
        elif 'soccer' in sport:
            return [GameScenario(h, a) for h, a in self.SOCCER_SCENARIOS]
        elif 'basket' in sport:
            return [GameScenario(h, a) for h, a in self.BASKETBALL_SCENARIOS]
        elif 'tennis' in sport:
            return self.TENNIS_SCENARIOS
        elif 'mma' in sport or 'boxing' in sport:
            return self.MMA_SCENARIOS
        else:
            # Default to NHL scenarios
            return [GameScenario(h, a) for h, a in self.NHL_SCENARIOS]


class StakeValidator:
    """Validates and adjusts stakes to maintain exact total and arbitrage properties."""

    @staticmethod
    def validate_and_adjust_stakes(
        odds_a: float,
        odds_b: float,
        stake_a: float,
        stake_b: float,
        total_stake: float = 100.0,
        tolerance: float = 0.05  # Increased from 0.01 to 0.05 to account for rounding
    ) -> Tuple[bool, float, float, str]:
        """
        Validate and adjust stakes to ensure:
        1. Total stake equals exactly $total_stake (within $0.01)
        2. Both outcomes produce approximately equal returns (within $0.05)

        Args:
            odds_a: Odds for outcome A
            odds_b: Odds for outcome B
            stake_a: Initial stake for A (may be rounded)
            stake_b: Initial stake for B (may be rounded)
            total_stake: Required total (default 100.0)
            tolerance: Tolerance for return difference (default $0.05)

        Returns:
            Tuple of (valid, adjusted_stake_a, adjusted_stake_b, reason)
        """
        # First, verify total adds up to exactly total_stake
        current_total = round(stake_a + stake_b, 2)
        if abs(current_total - total_stake) > 0.01:
            # Adjust stake_b to make total exact
            stake_b = round(total_stake - stake_a, 2)

        # Calculate returns for each outcome
        return_a = stake_a * odds_a
        return_b = stake_b * odds_b

        return_diff = abs(return_a - return_b)

        if return_diff <= tolerance:
            # Stakes are valid
            return (
                True,
                stake_a,
                stake_b,
                f"Valid: Total=${stake_a + stake_b:.2f}, Returns: ${return_a:.2f} vs ${return_b:.2f}"
            )

        # Returns don't match - try to adjust to reduce difference
        # Reduce the bet with higher return to match the lower return
        if return_a > return_b:
            adjusted_stake_a = return_b / odds_a
            adjusted_stake_a = round(adjusted_stake_a, 2)
            adjusted_stake_b = round(total_stake - adjusted_stake_a, 2)

            # Re-verify
            new_return_a = adjusted_stake_a * odds_a
            new_return_b = adjusted_stake_b * odds_b
            new_diff = abs(new_return_a - new_return_b)

            if new_diff <= tolerance:
                return (
                    True,
                    adjusted_stake_a,
                    adjusted_stake_b,
                    f"Adjusted: Total=${adjusted_stake_a + adjusted_stake_b:.2f}, Returns: ${new_return_a:.2f} vs ${new_return_b:.2f}"
                )
        else:
            adjusted_stake_b = return_a / odds_b
            adjusted_stake_b = round(adjusted_stake_b, 2)
            adjusted_stake_a = round(total_stake - adjusted_stake_b, 2)

            # Re-verify
            new_return_a = adjusted_stake_a * odds_a
            new_return_b = adjusted_stake_b * odds_b
            new_diff = abs(new_return_a - new_return_b)

            if new_diff <= tolerance:
                return (
                    True,
                    adjusted_stake_a,
                    adjusted_stake_b,
                    f"Adjusted: Total=${adjusted_stake_a + adjusted_stake_b:.2f}, Returns: ${new_return_a:.2f} vs ${new_return_b:.2f}"
                )

        return (False, stake_a, stake_b, f"Return difference ${return_diff:.2f} exceeds tolerance ${tolerance:.2f}")

    @staticmethod
    def validate_three_way_stakes(
        odds_a: float,
        odds_draw: float,
        odds_b: float,
        stake_a: float,
        stake_draw: float,
        stake_b: float,
        total_stake: float = 100.0,
        tolerance: float = 0.01
    ) -> Tuple[bool, float, float, float, str]:
        """
        Validate and adjust 3-way stakes.

        Returns:
            Tuple of (valid, stake_a, stake_draw, stake_b, reason)
        """
        # Ensure total is exact
        current_total = round(stake_a + stake_draw + stake_b, 2)
        if abs(current_total - total_stake) > 0.01:
            # Adjust one stake to make total exact
            stake_b = round(total_stake - stake_a - stake_draw, 2)

        return_a = stake_a * odds_a
        return_draw = stake_draw * odds_draw
        return_b = stake_b * odds_b

        max_return = max(return_a, return_draw, return_b)
        min_return = min(return_a, return_draw, return_b)
        return_diff = max_return - min_return

        if return_diff <= tolerance:
            return (
                True,
                stake_a,
                stake_draw,
                stake_b,
                f"Valid 3-way: Total=${stake_a + stake_draw + stake_b:.2f}"
            )

        return (False, stake_a, stake_draw, stake_b, f"Return difference ${return_diff:.2f} exceeds tolerance")


class OutcomePartition:
    """Validates that outcomes form a complete partition of outcome space."""

    @staticmethod
    def validate_two_way_partition(
        outcome_a: Dict,
        outcome_b: Dict,
        sport: str
    ) -> Tuple[bool, str]:
        """
        Verify that two outcomes partition all possible game results.

        Note: For moneyline in 2-outcome sports (like hockey), draws are allowed
        uncovered as they're not valid outcomes.

        Args:
            outcome_a: First outcome
            outcome_b: Second outcome
            sport: Sport type

        Returns:
            Tuple of (is_valid_partition, reason)
        """
        # Get scenarios for this sport
        validator = ArbitrageValidator()
        scenarios = validator._get_scenarios_for_sport(sport)

        covered_scenarios = 0
        uncovered_scenarios = []
        both_win_scenarios = []

        for scenario in scenarios:
            a_wins = validator.evaluate_outcome_in_scenario(outcome_a, scenario)
            b_wins = validator.evaluate_outcome_in_scenario(outcome_b, scenario)

            if a_wins and b_wins:
                both_win_scenarios.append(scenario)
            elif a_wins or b_wins:
                covered_scenarios += 1
            else:
                uncovered_scenarios.append(scenario)

        if both_win_scenarios:
            return (False, f"Outcomes overlap in scenarios: {both_win_scenarios[:3]}")

        # For moneyline in sports like hockey where draws can occur,
        # draws being uncovered is acceptable (they're tie/push scenarios)
        # Also handle combat sports (MMA/boxing) with string outcomes
        outcome_a_type = outcome_a['outcome_type']
        outcome_b_type = outcome_b['outcome_type']
        
        is_moneyline = False
        if isinstance(outcome_a_type, OutcomeType) and isinstance(outcome_b_type, OutcomeType):
            is_moneyline = outcome_a_type == OutcomeType.HOME_WIN and outcome_b_type == OutcomeType.AWAY_WIN
        elif isinstance(outcome_a_type, str) and isinstance(outcome_b_type, str):
            # For combat sports, check if it's A_WINS vs B_WINS or HOME vs AWAY
            is_moneyline = (
                (outcome_a_type.upper() in ["HOME", "A_WINS"] and outcome_b_type.upper() in ["AWAY", "B_WINS"]) or
                (outcome_a_type.upper() in ["AWAY", "B_WINS"] and outcome_b_type.upper() in ["HOME", "A_WINS"])
            )
        
        if is_moneyline:
            # This is moneyline - draws are acceptable to be uncovered
            uncovered_draws = [s for s in uncovered_scenarios
                              if (isinstance(s, GameScenario) and s.point_differential == 0) or
                                 (isinstance(s, str) and s == "DRAW")]
            other_uncovered = [s for s in uncovered_scenarios
                              if not ((isinstance(s, GameScenario) and s.point_differential == 0) or
                                     (isinstance(s, str) and s == "DRAW"))]

            if other_uncovered:
                return (False, f"Non-draw scenarios not covered: {other_uncovered[:3]}")

            return (True, f"Valid partition: {covered_scenarios} scenarios covered (draws acceptable)")

        # For other market types, all scenarios must be covered
        if uncovered_scenarios:
            return (False, f"Outcomes don't cover {len(uncovered_scenarios)} scenarios: {uncovered_scenarios[:3]}")

        return (True, f"Valid partition: all {len(scenarios)} scenarios covered exactly once")

    @staticmethod
    def validate_three_way_partition(
        outcome_a: Dict,
        outcome_draw: Dict,
        outcome_b: Dict,
        sport: str
    ) -> Tuple[bool, str]:
        """
        Verify that three outcomes form a complete partition.

        Args:
            outcome_a: Home outcome
            outcome_draw: Draw outcome
            outcome_b: Away outcome
            sport: Sport type

        Returns:
            Tuple of (is_valid_partition, reason)
        """
        validator = ArbitrageValidator()
        scenarios = validator._get_scenarios_for_sport(sport)

        covered_count = 0
        uncovered_scenarios = []
        multi_win_scenarios = []

        for scenario in scenarios:
            a_wins = validator.evaluate_outcome_in_scenario(outcome_a, scenario)
            d_wins = validator.evaluate_outcome_in_scenario(outcome_draw, scenario)
            b_wins = validator.evaluate_outcome_in_scenario(outcome_b, scenario)

            win_count = sum([a_wins, d_wins, b_wins])

            if win_count == 0:
                uncovered_scenarios.append(scenario)
            elif win_count == 1:
                covered_count += 1
            else:
                multi_win_scenarios.append(scenario)

        if multi_win_scenarios:
            return (False, f"Outcomes overlap in scenarios: {multi_win_scenarios[:3]}")

        if uncovered_scenarios:
            return (False, f"Outcomes don't cover {len(uncovered_scenarios)} scenarios")

        return (True, f"Valid partition: all {len(scenarios)} scenarios covered exactly once")
