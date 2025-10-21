"""
Enriched Pipeline Integration Helpers
Helper functions for integrating EnrichedTeamInput with V2 Pipeline
"""

from typing import Dict
from ai.enriched_data_models import EnrichedTeamInput
from .event_simulation_engine import MatchParameters


def enriched_to_match_params(
    home_team: EnrichedTeamInput,
    away_team: EnrichedTeamInput
) -> MatchParameters:
    """
    Convert EnrichedTeamInput to MatchParameters for V2 Pipeline

    Args:
        home_team: Home team enriched data
        away_team: Away team enriched data

    Returns:
        MatchParameters object

    Conversion Logic:
        EnrichedTeamInput.derived_strengths → MatchParameters dict
        - attack_strength (0-100) → attack_strength
        - defense_strength (0-100) → defense_strength
        - midfield_control (0-100) → midfield_strength
        - physical_intensity (0-100) → physical_strength

    Note: press_intensity and buildup_style are derived from formation tactics
    or set to defaults as they were removed from DerivedTeamStrengths
    """
    # Determine press_intensity from formation tactics or default
    home_press = 70.0  # Default medium press
    away_press = 70.0

    # Determine buildup style from formation tactics or default
    home_buildup = "mixed"  # Default
    away_buildup = "mixed"

    if home_team.formation_tactics:
        # Infer press intensity from pressing description
        if "high" in home_team.formation_tactics.pressing.lower():
            home_press = 85.0
        elif "low" in home_team.formation_tactics.pressing.lower():
            home_press = 55.0

        # Infer buildup style from buildup description
        if "possession" in home_team.formation_tactics.buildup.lower():
            home_buildup = "possession"
        elif "direct" in home_team.formation_tactics.buildup.lower():
            home_buildup = "direct"

    if away_team.formation_tactics:
        if "high" in away_team.formation_tactics.pressing.lower():
            away_press = 85.0
        elif "low" in away_team.formation_tactics.pressing.lower():
            away_press = 55.0

        if "possession" in away_team.formation_tactics.buildup.lower():
            away_buildup = "possession"
        elif "direct" in away_team.formation_tactics.buildup.lower():
            away_buildup = "direct"

    home_dict = {
        'name': home_team.name,
        'attack_strength': home_team.derived_strengths.attack_strength,
        'defense_strength': home_team.derived_strengths.defense_strength,
        'midfield_strength': home_team.derived_strengths.midfield_control,
        'physical_strength': home_team.derived_strengths.physical_intensity,
        'press_intensity': home_press,
        'buildup_style': home_buildup
    }

    away_dict = {
        'name': away_team.name,
        'attack_strength': away_team.derived_strengths.attack_strength,
        'defense_strength': away_team.derived_strengths.defense_strength,
        'midfield_strength': away_team.derived_strengths.midfield_control,
        'physical_strength': away_team.derived_strengths.physical_intensity,
        'press_intensity': away_press,
        'buildup_style': away_buildup
    }

    return MatchParameters(
        home_team=home_dict,
        away_team=away_dict,
        home_formation=home_team.formation,
        away_formation=away_team.formation
    )
