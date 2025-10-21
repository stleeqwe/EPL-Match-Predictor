"""
Rating Calculator Domain Service
Calculates weighted ratings based on position
"""
from typing import Dict, List, Tuple
from backend.core.domain.value_objects.position import Position, DetailedPosition
from backend.core.domain.value_objects.rating_value import RatingValue
from backend.config.constants import POSITION_ATTRIBUTES


class RatingCalculator:
    """
    Rating Calculator Domain Service

    Pure domain service with no dependencies on infrastructure.
    Encapsulates position-specific rating calculation logic.
    """

    # Position-specific attribute weights
    # Each weight represents the importance of that attribute for the position
    POSITION_WEIGHTS = {
        DetailedPosition.GK: {
            'reflexes': 0.17,
            'positioning': 0.17,
            'handling': 0.15,
            'one_on_one': 0.14,
            'aerial_control': 0.12,
            'buildup': 0.13,
            'leadership_communication': 0.07,
            'long_kick': 0.05
        },
        DetailedPosition.CB: {
            'positioning_reading': 0.15,
            'composure_judgement': 0.12,
            'interception': 0.10,
            'aerial_duel': 0.09,
            'tackle_marking': 0.11,
            'speed': 0.10,
            'passing': 0.13,
            'physical_jumping': 0.08,
            'buildup_contribution': 0.10,
            'leadership': 0.02
        },
        DetailedPosition.FB: {
            'stamina': 0.16,
            'speed': 0.15,
            'defensive_positioning': 0.12,
            'one_on_one_tackle': 0.13,
            'overlapping': 0.11,
            'crossing_accuracy': 0.11,
            'covering': 0.09,
            'agility': 0.07,
            'press_resistance': 0.04,
            'long_shot': 0.02
        },
        DetailedPosition.DM: {
            'positioning': 0.12,
            'ball_winning': 0.12,
            'pass_accuracy': 0.10,
            'composure_press_resistance': 0.12,
            'backline_protection': 0.10,
            'pressing_transition_blocking': 0.10,
            'progressive_play': 0.09,
            'tempo_control': 0.07,
            'stamina': 0.06,
            'physicality_mobility': 0.10,
            'leadership': 0.02
        },
        DetailedPosition.CM: {
            'stamina': 0.11,
            'ball_possession_circulation': 0.11,
            'pass_accuracy_vision': 0.13,
            'transition': 0.10,
            'dribbling_press_resistance': 0.10,
            'space_creation': 0.09,
            'defensive_contribution': 0.09,
            'ball_retention': 0.07,
            'long_shot': 0.06,
            'agility_acceleration': 0.09,
            'physicality': 0.05
        },
        DetailedPosition.CAM: {
            'creativity': 0.13,
            'vision_killpass': 0.12,
            'dribbling': 0.11,
            'decision_making': 0.11,
            'penetration': 0.10,
            'shooting_finishing': 0.11,
            'one_touch_pass': 0.08,
            'pass_and_move': 0.07,
            'acceleration': 0.07,
            'agility': 0.06,
            'set_piece': 0.04
        },
        DetailedPosition.WG: {
            'speed_dribbling': 0.12,
            'one_on_one_beating': 0.11,
            'speed': 0.10,
            'acceleration': 0.09,
            'crossing_accuracy': 0.10,
            'shooting_accuracy': 0.09,
            'agility_direction_change': 0.10,
            'cutting_in': 0.08,
            'creativity': 0.06,
            'defensive_contribution': 0.07,
            'cutback_pass': 0.04,
            'link_up_play': 0.04
        },
        DetailedPosition.ST: {
            'finishing': 0.15,
            'shot_power': 0.14,
            'composure': 0.12,
            'off_ball_movement': 0.13,
            'hold_up_play': 0.11,
            'heading': 0.09,
            'acceleration': 0.08,
            'physicality_balance': 0.11,
            'jumping': 0.07
        }
    }

    @classmethod
    def calculate_weighted_average(
        cls,
        ratings: Dict[str, float],
        position: Position
    ) -> RatingValue:
        """
        Calculate weighted average rating for a position

        Args:
            ratings: Dictionary of {attribute_name: rating_value}
            position: Player's position

        Returns:
            Weighted average RatingValue

        Raises:
            ValueError: If no weights defined for position or no valid ratings

        Business Logic:
        - Each attribute has a position-specific weight
        - Weighted sum = Σ(rating × weight)
        - Result is rounded to 0.25 step for RatingValue compliance
        """
        weights = cls.POSITION_WEIGHTS.get(position.detailed)
        if not weights:
            raise ValueError(f"No weights defined for position: {position.detailed.value}")

        total_weight = 0.0
        weighted_sum = 0.0

        for attribute, weight in weights.items():
            if attribute not in ratings:
                # Skip missing attributes (could log warning)
                continue

            value = ratings[attribute]

            # Validate rating value
            if not isinstance(value, (int, float)):
                continue
            if value < 0.0 or value > 5.0:
                continue

            weighted_sum += value * weight
            total_weight += weight

        if total_weight == 0:
            raise ValueError("No valid ratings provided for calculation")

        # Calculate average
        average = weighted_sum / total_weight

        # Round to 0.25 step
        rounded = round(average / 0.25) * 0.25

        # Ensure within bounds
        rounded = max(0.0, min(5.0, rounded))

        return RatingValue(value=rounded)

    @classmethod
    def get_required_attributes(cls, position: Position) -> List[str]:
        """
        Get list of required attributes for a position

        Args:
            position: Player position

        Returns:
            List of attribute names required for this position
        """
        weights = cls.POSITION_WEIGHTS.get(position.detailed)
        if not weights:
            return []
        return list(weights.keys())

    @classmethod
    def get_attribute_weight(cls, position: Position, attribute: str) -> float:
        """
        Get weight of specific attribute for a position

        Args:
            position: Player position
            attribute: Attribute name

        Returns:
            Weight value (0.0-1.0), or 0.0 if not found
        """
        weights = cls.POSITION_WEIGHTS.get(position.detailed)
        if not weights:
            return 0.0
        return weights.get(attribute, 0.0)

    @classmethod
    def validate_ratings(
        cls,
        ratings: Dict[str, float],
        position: Position
    ) -> Tuple[bool, List[str]]:
        """
        Validate ratings for completeness

        Args:
            ratings: Dictionary of {attribute_name: rating_value}
            position: Player position

        Returns:
            Tuple of (is_valid, missing_attributes)
            - is_valid: True if all required attributes present
            - missing_attributes: List of missing attribute names
        """
        required = cls.get_required_attributes(position)
        missing = [attr for attr in required if attr not in ratings]

        return len(missing) == 0, missing

    @classmethod
    def get_top_attributes(
        cls,
        ratings: Dict[str, float],
        position: Position,
        n: int = 5
    ) -> List[Tuple[str, float, float]]:
        """
        Get top N most important attributes based on weighted value

        Args:
            ratings: Dictionary of {attribute_name: rating_value}
            position: Player position
            n: Number of top attributes to return

        Returns:
            List of (attribute_name, rating_value, weighted_contribution)
            Sorted by weighted contribution (descending)
        """
        weights = cls.POSITION_WEIGHTS.get(position.detailed)
        if not weights:
            return []

        # Calculate weighted contribution for each attribute
        contributions = []
        for attribute, rating in ratings.items():
            weight = weights.get(attribute, 0.0)
            contribution = rating * weight
            contributions.append((attribute, rating, contribution))

        # Sort by contribution (descending)
        contributions.sort(key=lambda x: x[2], reverse=True)

        return contributions[:n]

    @classmethod
    def compare_players(
        cls,
        player1_ratings: Dict[str, float],
        player2_ratings: Dict[str, float],
        position: Position
    ) -> Dict[str, any]:
        """
        Compare two players at the same position

        Args:
            player1_ratings: Player 1's ratings
            player2_ratings: Player 2's ratings
            position: Common position

        Returns:
            Dictionary with comparison results
        """
        overall1 = cls.calculate_weighted_average(player1_ratings, position)
        overall2 = cls.calculate_weighted_average(player2_ratings, position)

        weights = cls.POSITION_WEIGHTS.get(position.detailed, {})

        # Calculate differences per attribute
        differences = {}
        for attribute in weights.keys():
            val1 = player1_ratings.get(attribute, 0.0)
            val2 = player2_ratings.get(attribute, 0.0)
            differences[attribute] = val1 - val2

        return {
            'player1_overall': float(overall1),
            'player2_overall': float(overall2),
            'overall_difference': float(overall1) - float(overall2),
            'attribute_differences': differences,
            'player1_strengths': [attr for attr, diff in differences.items() if diff > 0.5],
            'player2_strengths': [attr for attr, diff in differences.items() if diff < -0.5],
        }

    @classmethod
    def suggest_improvements(
        cls,
        ratings: Dict[str, float],
        position: Position,
        target_overall: float = 4.0
    ) -> Dict[str, any]:
        """
        Suggest which attributes to improve to reach target overall rating

        Args:
            ratings: Current ratings
            position: Player position
            target_overall: Target overall rating

        Returns:
            Dictionary with improvement suggestions
        """
        current_overall = cls.calculate_weighted_average(ratings, position)
        gap = target_overall - float(current_overall)

        if gap <= 0:
            return {
                'current_overall': float(current_overall),
                'target_overall': target_overall,
                'suggestions': ['Already at or above target rating']
            }

        weights = cls.POSITION_WEIGHTS.get(position.detailed, {})

        # Find attributes with highest weight and lowest current rating
        improvement_potential = []
        for attribute, weight in weights.items():
            current_rating = ratings.get(attribute, 0.0)
            potential_gain = weight * (5.0 - current_rating)
            improvement_potential.append({
                'attribute': attribute,
                'current_rating': current_rating,
                'weight': weight,
                'potential_gain': potential_gain
            })

        # Sort by potential gain
        improvement_potential.sort(key=lambda x: x['potential_gain'], reverse=True)

        return {
            'current_overall': float(current_overall),
            'target_overall': target_overall,
            'gap': gap,
            'top_improvement_areas': improvement_potential[:5]
        }
