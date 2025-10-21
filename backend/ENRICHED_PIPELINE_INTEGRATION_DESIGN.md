# Enriched Pipeline Integration - Detailed Design

**Date**: 2025-10-17
**Author**: Claude Code
**Status**: 🔵 DESIGN PHASE

---

## Executive Summary

This document provides the **complete and detailed design** for integrating **Enriched Domain Input** with **V2 Pipeline** to create a comprehensive AI-driven simulation engine.

**Goal:**
```
User Domain Input (11 players × 10-12 attributes)
  ↓
EnrichedAIScenarioGenerator
  ↓
Phase 1-7 Pipeline (5-7 scenarios × 100 runs → convergence → 3,000 final runs)
  ↓
Aggregated probabilities
```

**Current Problem:**
- `EnrichedQwenClient` only does **1 AI call** → direct prediction ❌
- User requires: **5-7 scenarios × 100 runs + 3,000 final runs** ✅

---

## Architecture Analysis

### Component Inventory

#### ✅ Existing Components (No Changes Required)

1. **EnrichedTeamInput** (`ai/enriched_data_models.py`)
   - 11 players with 10-12 position-specific attributes
   - User commentary (player-specific + team strategy)
   - TacticsInput (defensive, offensive, transition)
   - DerivedTeamStrengths (auto-calculated)

2. **Scenario** (`simulation/v2/scenario.py`)
   - Data structure for scenarios
   - ScenarioEvent with minute_range, type, probability_boost
   - parameter_adjustments dict
   - expected_probability (0-1)

3. **SimulationPipeline** (`simulation/v2/simulation_pipeline.py`)
   - Phase 1-7 orchestration
   - Iterative refinement loop (Phase 2-5)
   - Final high-resolution simulation (Phase 6)
   - Uses `MatchParameters` (generic dict-based format)

4. **MultiScenarioValidator** (`simulation/v2/multi_scenario_validator.py`)
   - Validates scenarios with N runs
   - Uses `EventBasedSimulationEngine`
   - Returns validation_results (win_rate, avg_score, etc.)

5. **AIAnalyzer** (`simulation/v2/ai_analyzer.py`)
   - Analyzes validation results
   - Suggests adjustments
   - Checks convergence

6. **EnrichedQwenClient** (`ai/enriched_qwen_client.py`)
   - QwenClient with enriched prompts
   - `_build_enriched_system_prompt()`
   - `_build_enriched_match_prompt()` (7 sections)

#### 🔨 Components to Create

1. **EnrichedAIScenarioGenerator** (`simulation/v2/ai_scenario_generator_enriched.py`)
   - **NEW CLASS**
   - Purpose: Generate 5-7 scenarios from EnrichedTeamInput
   - Uses EnrichedQwenClient for AI generation
   - Returns List[Scenario]

2. **enriched_to_match_params()** (helper function)
   - **NEW FUNCTION**
   - Purpose: Convert EnrichedTeamInput → MatchParameters
   - Location: `simulation/v2/enriched_helpers.py` (new file)

#### 🔧 Components to Modify

1. **SimulationPipeline** (`simulation/v2/simulation_pipeline.py`)
   - **ADD METHOD**: `run_enriched()`
   - Uses EnrichedAIScenarioGenerator in Phase 1
   - Converts EnrichedTeamInput → MatchParameters for Phase 2-7

2. **EnrichedSimulationService** (`services/enriched_simulation_service.py`)
   - **REPLACE**: Direct AI call → Pipeline call
   - Lines 146-150: Replace `self.client.simulate_match_enriched()`
   - With: `pipeline.run_enriched()`

---

## Detailed Design

### 1. EnrichedAIScenarioGenerator

**File:** `/backend/simulation/v2/ai_scenario_generator_enriched.py`

#### 1.1 Class Definition

```python
"""
Enriched AI Multi-Scenario Generator
Enriched Domain Data를 활용한 5-7개 다중 시나리오 생성

AIScenarioGenerator와 동일한 역할이지만 EnrichedTeamInput을 사용
"""

import json
import logging
import re
from typing import Dict, List, Optional, Tuple

from ai.enriched_qwen_client import get_enriched_qwen_client
from ai.enriched_data_models import EnrichedTeamInput
from .scenario import Scenario, ScenarioEvent, EventType

logger = logging.getLogger(__name__)


class EnrichedAIScenarioGenerator:
    """
    AI 기반 다중 시나리오 생성기 (Enriched Domain Data)

    Generate 5-7 distinct scenarios using enriched team data:
    - 11 players × 10-12 attributes
    - User commentary (PRIMARY FACTOR)
    - Tactical parameters (15 parameters)
    - Derived team strengths
    """

    def __init__(self, model: str = "qwen2.5:14b"):
        """
        Args:
            model: Qwen model name
        """
        self.ai_client = get_enriched_qwen_client(model=model)
        logger.info(f"EnrichedAIScenarioGenerator initialized with {model}")

    def generate_scenarios_enriched(
        self,
        home_team: EnrichedTeamInput,
        away_team: EnrichedTeamInput,
        match_context: Optional[Dict] = None
    ) -> Tuple[bool, Optional[List[Scenario]], Optional[str]]:
        """
        5-7개 다중 시나리오 생성 (Enriched Domain Data 기반)

        Args:
            home_team: 홈팀 Enriched Domain Data
            away_team: 원정팀 Enriched Domain Data
            match_context: 매치 컨텍스트 (optional)

        Returns:
            Tuple of (success, scenarios_list, error_message)
        """
```

#### 1.2 System Prompt

```python
def _build_enriched_system_prompt_for_scenarios(self) -> str:
    """
    Enriched Domain Data 기반 시나리오 생성 시스템 프롬프트

    Returns:
        시나리오 생성용 시스템 프롬프트
    """
    return """You are an EPL tactical simulation expert.

Your role is to generate 5-7 DISTINCT match scenarios based on enriched domain data.

INPUT DATA PRIORITY:
1. **User Domain Knowledge** (HIGHEST PRIORITY): User commentary on players and team strategies
2. **Player Attributes** (10-12 position-specific attributes per player)
3. **Tactical Parameters** (defensive, offensive, transition)
4. **Formation & Lineup** (11 players with positional roles)
5. **Derived Team Strengths** (attack, defense, midfield, physical, press intensity)

SCENARIO GENERATION RULES:
1. Generate EXACTLY 5-7 distinct scenarios
2. Each scenario must tell a DIFFERENT story:
   - Scenario 1: Dominant home win (early goal → control)
   - Scenario 2: Close home win (tight match → late winner)
   - Scenario 3: Draw (balanced match → shared points)
   - Scenario 4: Close away win (resilient defense → counter-attack)
   - Scenario 5: Dominant away win (away control)
   - Scenario 6: High-scoring draw (both teams attack)
   - Scenario 7: Low-scoring draw (defensive battle)
3. Each scenario must have:
   - Unique narrative based on user insights
   - 3-8 ScenarioEvents with specific timing and probability boosts
   - Parameter adjustments reflecting tactical changes
   - Expected probability (sum of all scenarios ≈ 1.0)

OUTPUT FORMAT:
Return ONLY a valid JSON object (no markdown, no explanations):

{
  "scenarios": [
    {
      "id": "SYNTH_001",
      "name": "시나리오 이름 (한글)",
      "reasoning": "Why this scenario is relevant based on user insights and data",
      "events": [
        {
          "minute_range": [10, 25],
          "type": "wing_breakthrough",
          "team": "home",
          "actor": "Player Name",
          "method": "wing_attack",
          "probability_boost": 2.5,
          "reason": "Specific reason from user commentary or attributes",
          "trigger": null,
          "to": null
        }
      ],
      "parameter_adjustments": {
        "home_attack_modifier": 1.15,
        "away_left_defense_modifier": 0.85
      },
      "expected_probability": 0.18
    }
  ],
  "total_probability": 0.98,
  "confidence": 0.85,
  "reasoning": "Overall reasoning for scenario distribution"
}

AVAILABLE EVENT TYPES:
- wing_breakthrough: Winger beats defender on flank
- central_penetration: Through-ball or dribble through middle
- goal: Goal scored (most important event)
- shot_on_target: Shot saved or blocked
- shot_off_target: Shot misses target
- corner: Corner kick awarded
- formation_change: Tactical formation switch (include "to" field)
- substitution: Player substitution
- foul: Foul committed
- yellow_card: Caution
- red_card: Sending off

VALIDATION REQUIREMENTS:
1. Number of scenarios: 5-7 (exactly)
2. Probability sum: 0.9 - 1.1
3. probability_boost range: 1.0 - 3.0
4. minute_range: [start, end] where 0 ≤ start ≤ end ≤ 90
5. Each scenario must have unique name
6. Events must be logically sequenced (early events before late events)

IMPORTANT: Return ONLY the JSON object. No markdown code blocks, no explanations."""
```

#### 1.3 User Prompt Builder

```python
def _build_enriched_scenario_generation_prompt(
    self,
    home_team: EnrichedTeamInput,
    away_team: EnrichedTeamInput,
    match_context: Optional[Dict]
) -> str:
    """
    Enriched Domain Data 기반 시나리오 생성 프롬프트

    7 Sections:
    1. User Domain Knowledge (PRIMARY)
    2. Team Overview
    3. Tactical Setup
    4. Key Players Detailed Attributes
    5. Position Group Analysis
    6. Match Context (optional)
    7. Scenario Generation Instructions
    """
    prompt_parts = [
        f"# Match Scenario Generation: {home_team.name} vs {away_team.name}\n"
    ]

    # ============================================================
    # Section 1: User Domain Knowledge (최우선!)
    # ============================================================
    prompt_parts.append("\n## 🎯 User Domain Knowledge (PRIMARY FACTOR)\n")
    prompt_parts.append("Use this knowledge as the PRIMARY BASIS for scenario generation.\n")

    # Team Strategy Commentary
    if home_team.team_strategy_commentary:
        prompt_parts.append(f"\n**{home_team.name} Strategy**: {home_team.team_strategy_commentary}")
    if away_team.team_strategy_commentary:
        prompt_parts.append(f"\n**{away_team.name} Strategy**: {away_team.team_strategy_commentary}")

    # Key Players Commentary (Top 5)
    prompt_parts.append(f"\n\n**Key Players Insights**:")

    for team, label in [(home_team, 'Home'), (away_team, 'Away')]:
        key_players = team.get_key_players(top_n=5)
        prompt_parts.append(f"\n\n{label} Team ({team.name}):")

        for player in key_players:
            if player.user_commentary:
                prompt_parts.append(f"- **{player.name}** ({player.position}): {player.user_commentary}")

    # ============================================================
    # Section 2: Team Overview
    # ============================================================
    prompt_parts.append("\n\n## 📊 Team Overview\n")

    for team, label in [(home_team, 'Home'), (away_team, 'Away')]:
        prompt_parts.append(f"\n**{label} Team: {team.name}**")
        prompt_parts.append(f"- Formation: {team.formation}")

        if team.derived_strengths:
            ds = team.derived_strengths
            prompt_parts.append(f"- Attack Strength: {ds.attack_strength:.1f}/100")
            prompt_parts.append(f"- Defense Strength: {ds.defense_strength:.1f}/100")
            prompt_parts.append(f"- Midfield Control: {ds.midfield_control:.1f}/100")
            prompt_parts.append(f"- Physical Intensity: {ds.physical_intensity:.1f}/100")
            prompt_parts.append(f"- Press Intensity: {ds.press_intensity:.1f}/100")
            prompt_parts.append(f"- Buildup Style: {ds.buildup_style}")

    # ============================================================
    # Section 3: Tactical Setup
    # ============================================================
    prompt_parts.append("\n\n## ⚙️ Tactical Setup\n")

    for team, label in [(home_team, 'Home'), (away_team, 'Away')]:
        prompt_parts.append(f"\n**{label} Team ({team.name})**:")
        tactics = team.tactics

        prompt_parts.append(
            f"- **Defensive**: Pressing {tactics.defensive.pressing_intensity}/10, "
            f"Line Height {tactics.defensive.defensive_line}/10, "
            f"Width {tactics.defensive.defensive_width}/10, "
            f"Compactness {tactics.defensive.compactness}/10"
        )

        prompt_parts.append(
            f"- **Offensive**: Tempo {tactics.offensive.tempo}/10, "
            f"Style '{tactics.offensive.buildup_style}', "
            f"Width {tactics.offensive.width}/10, "
            f"Creativity {tactics.offensive.creativity}/10"
        )

        prompt_parts.append(
            f"- **Transition**: Counter Press {tactics.transition.counter_press}/10, "
            f"Counter Speed {tactics.transition.counter_speed}/10"
        )

    # ============================================================
    # Section 4: Key Players Detailed Attributes
    # ============================================================
    prompt_parts.append("\n\n## 🌟 Key Players Detailed Attributes\n")

    for team, label in [(home_team, 'Home'), (away_team, 'Away')]:
        key_players = team.get_key_players(top_n=5)
        prompt_parts.append(f"\n**{label} Team ({team.name}) - Top 5 Players**:")

        for player in key_players:
            prompt_parts.append(f"\n{player.name} ({player.position}) - Overall: {player.overall_rating:.2f}")

            if player.ratings:
                top_attrs = player.get_key_strengths(top_n=5)
                attr_strs = [f"{attr}: {player.ratings[attr]:.2f}" for attr in top_attrs]
                prompt_parts.append(f"  Key Strengths: {', '.join(attr_strs)}")

            if player.user_commentary:
                prompt_parts.append(f"  User Notes: {player.user_commentary}")

    # ============================================================
    # Section 5: Position Group Analysis
    # ============================================================
    prompt_parts.append("\n\n## 📍 Position Group Analysis\n")

    for team, label in [(home_team, 'Home'), (away_team, 'Away')]:
        prompt_parts.append(f"\n**{label} Team ({team.name})**:")

        # Categorize by position
        attackers = [p for pos, p in team.lineup.items() if pos in ['ST', 'LW', 'RW', 'CF', 'ST1', 'ST2']]
        midfielders = [p for pos, p in team.lineup.items() if 'M' in pos or pos in ['CAM', 'CM', 'CDM', 'DM']]
        defenders = [p for pos, p in team.lineup.items() if pos in ['CB', 'LB', 'RB', 'CB1', 'CB2', 'CB-L', 'CB-R']]

        if attackers:
            avg = sum(p.overall_rating for p in attackers) / len(attackers)
            prompt_parts.append(f"- **Attack** ({len(attackers)} players): Avg {avg:.2f}")

        if midfielders:
            avg = sum(p.overall_rating for p in midfielders) / len(midfielders)
            prompt_parts.append(f"- **Midfield** ({len(midfielders)} players): Avg {avg:.2f}")

        if defenders:
            avg = sum(p.overall_rating for p in defenders) / len(defenders)
            prompt_parts.append(f"- **Defense** ({len(defenders)} players): Avg {avg:.2f}")

    # ============================================================
    # Section 6: Match Context (Optional)
    # ============================================================
    if match_context:
        prompt_parts.append("\n\n## 🏟️ Match Context\n")
        for key, value in match_context.items():
            prompt_parts.append(f"- {key.capitalize()}: {value}")

    # ============================================================
    # Section 7: Scenario Generation Instructions
    # ============================================================
    prompt_parts.append("\n\n## 📝 Scenario Generation Instructions\n")
    prompt_parts.append("Generate 5-7 DISTINCT scenarios exploring different match outcomes.\n")
    prompt_parts.append("**CRITICAL**: Each scenario must tell a DIFFERENT story:\n")
    prompt_parts.append("1. **Dominant Home Win**: Home team controls match, scores early, maintains lead")
    prompt_parts.append("2. **Close Home Win**: Tight match, home team wins by 1 goal, tense finish")
    prompt_parts.append("3. **Draw**: Balanced match, both teams create chances, shared points")
    prompt_parts.append("4. **Close Away Win**: Away team resilient, scores on counter-attack or set-piece")
    prompt_parts.append("5. **Dominant Away Win**: Away team controls, superior tactics/execution")
    prompt_parts.append("6. **High-Scoring Draw** (optional): Both teams attack, 2-2 or 3-3")
    prompt_parts.append("7. **Low-Scoring Draw** (optional): Defensive battle, 0-0 or 1-1\n")
    prompt_parts.append("**Key Considerations**:")
    prompt_parts.append("- User commentary is the MOST IMPORTANT factor")
    prompt_parts.append("- Use player attributes to justify probability boosts")
    prompt_parts.append("- Consider tactical matchups (formation vs formation)")
    prompt_parts.append("- Include key moments (goals, formation changes, cards)")
    prompt_parts.append("- Ensure events are logically sequenced within minute_range\n")
    prompt_parts.append("**Return ONLY the JSON object, no markdown blocks, no explanations.**")

    return "\n".join(prompt_parts)
```

#### 1.4 JSON Parsing

```python
def _parse_scenarios(
    self,
    response_text: str
) -> Optional[List[Scenario]]:
    """
    AI 응답을 Scenario 객체 리스트로 파싱

    Returns:
        List[Scenario] or None if parsing fails
    """
    try:
        # Extract JSON (handle markdown code blocks)
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
        else:
            json_str = response_text.strip()

        # Parse JSON
        data = json.loads(json_str)

        # Convert to Scenario objects
        scenarios = []
        for scenario_data in data.get('scenarios', []):
            scenario = self._dict_to_scenario(scenario_data)
            scenarios.append(scenario)

        logger.info(f"Parsed {len(scenarios)} scenarios from AI response")
        return scenarios

    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing failed: {e}")
        logger.error(f"Response: {response_text[:500]}")
        return None
    except Exception as e:
        logger.error(f"Scenario parsing error: {e}")
        return None

def _dict_to_scenario(self, data: Dict) -> Scenario:
    """딕셔너리를 Scenario 객체로 변환"""
    # Parse events
    events = []
    for event_data in data.get('events', []):
        try:
            event = ScenarioEvent(
                minute_range=tuple(event_data['minute_range']),
                type=EventType(event_data['type']),
                team=event_data['team'],
                actor=event_data.get('actor'),
                method=event_data.get('method'),
                probability_boost=event_data.get('probability_boost', 1.0),
                reason=event_data.get('reason', ''),
                trigger=event_data.get('trigger'),
                to=event_data.get('to')
            )
            events.append(event)
        except Exception as e:
            logger.warning(f"Failed to parse event: {e}")
            continue

    # Create scenario
    scenario = Scenario(
        id=data['id'],
        name=data['name'],
        reasoning=data.get('reasoning', ''),
        events=events,
        parameter_adjustments=data.get('parameter_adjustments', {}),
        expected_probability=data.get('expected_probability', 0.0),
        base_narrative=data.get('base_narrative')
    )

    return scenario

def _validate_scenarios(
    self,
    scenarios: List[Scenario]
) -> Tuple[bool, Optional[str]]:
    """
    시나리오 검증

    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check count
    if not (5 <= len(scenarios) <= 7):
        return False, f"Expected 5-7 scenarios, got {len(scenarios)}"

    # Check probability sum
    total_prob = sum(s.expected_probability for s in scenarios)
    if not (0.9 <= total_prob <= 1.1):
        return False, f"Total probability {total_prob:.2f} outside range [0.9, 1.1]"

    # Check distinctness
    names = [s.name for s in scenarios]
    if len(names) != len(set(names)):
        return False, "Duplicate scenario names detected"

    return True, None
```

#### 1.5 Global Instance

```python
# Global instance
_enriched_scenario_generator = None

def get_enriched_scenario_generator(model: str = "qwen2.5:14b") -> EnrichedAIScenarioGenerator:
    """Get global enriched scenario generator instance (singleton)."""
    global _enriched_scenario_generator
    if _enriched_scenario_generator is None:
        _enriched_scenario_generator = EnrichedAIScenarioGenerator(model=model)
    return _enriched_scenario_generator
```

---

### 2. EnrichedTeamInput → MatchParameters Conversion

**File:** `/backend/simulation/v2/enriched_helpers.py` (NEW FILE)

```python
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
    """
    home_dict = {
        'name': home_team.name,
        'attack_strength': home_team.derived_strengths.attack_strength,
        'defense_strength': home_team.derived_strengths.defense_strength,
        'midfield_strength': home_team.derived_strengths.midfield_control,
        'physical_strength': home_team.derived_strengths.physical_intensity,
        'press_intensity': home_team.derived_strengths.press_intensity,
        'buildup_style': home_team.derived_strengths.buildup_style
    }

    away_dict = {
        'name': away_team.name,
        'attack_strength': away_team.derived_strengths.attack_strength,
        'defense_strength': away_team.derived_strengths.defense_strength,
        'midfield_strength': away_team.derived_strengths.midfield_control,
        'physical_strength': away_team.derived_strengths.physical_intensity,
        'press_intensity': away_team.derived_strengths.press_intensity,
        'buildup_style': away_team.derived_strengths.buildup_style
    }

    return MatchParameters(
        home_team=home_dict,
        away_team=away_dict,
        home_formation=home_team.formation,
        away_formation=away_team.formation
    )
```

---

### 3. SimulationPipeline Extension

**File:** `/backend/simulation/v2/simulation_pipeline.py` (MODIFY)

#### 3.1 Add Import

```python
from ai.enriched_data_models import EnrichedTeamInput
from .enriched_helpers import enriched_to_match_params
from .ai_scenario_generator_enriched import get_enriched_scenario_generator
```

#### 3.2 Add run_enriched() Method

```python
def run_enriched(
    self,
    home_team: EnrichedTeamInput,
    away_team: EnrichedTeamInput,
    match_context: Optional[Dict] = None
) -> Tuple[bool, Optional[Dict], Optional[str]]:
    """
    전체 파이프라인 실행 (Enriched Domain Input)

    Args:
        home_team: 홈팀 Enriched Domain Data
        away_team: 원정팀 Enriched Domain Data
        match_context: 매치 컨텍스트 (optional)

    Returns:
        Tuple of (success, result_dict, error_message)
    """
    try:
        logger.info("="*70)
        logger.info("Enriched Simulation Pipeline Started")
        logger.info("="*70)
        logger.info(f"Match: {home_team.name} vs {away_team.name}")

        # Convert EnrichedTeamInput to MatchParameters
        base_params = enriched_to_match_params(home_team, away_team)

        # Build match context
        if match_context is None:
            match_context = {}
        match_context['home_team'] = home_team.name
        match_context['away_team'] = away_team.name

        # Phase 1: Enriched AI Scenario Generation
        logger.info("\n[Phase 1] Enriched AI Scenario Generation")
        logger.info("-"*70)

        enriched_generator = get_enriched_scenario_generator()
        success, scenarios, error = enriched_generator.generate_scenarios_enriched(
            home_team=home_team,
            away_team=away_team,
            match_context=match_context
        )

        if not success:
            return False, None, f"Phase 1 failed: {error}"

        logger.info(f"✓ Generated {len(scenarios)} enriched scenarios")

        # Phase 2-5: Iterative Refinement Loop
        logger.info("\n[Phase 2-5] Iterative Refinement Loop")
        logger.info("-"*70)

        iteration = 1
        converged = False
        history = []
        current_scenarios = scenarios

        while not converged and iteration <= self.config.max_iterations:
            logger.info(f"\n>>> Iteration {iteration}/{self.config.max_iterations}")

            # Phase 2: Simulate (100 runs per scenario)
            logger.info(f"  Phase 2: Simulating ({len(current_scenarios)} × {self.config.initial_runs})...")
            validation_results = self.validator.validate_scenarios(
                scenarios=current_scenarios,
                base_params=base_params,
                n=self.config.initial_runs
            )

            # Phase 3: AI Analysis
            logger.info(f"  Phase 3: AI Analysis...")
            success, ai_analysis, error = self.analyzer.analyze_and_adjust(
                scenarios=current_scenarios,
                validation_results=validation_results,
                iteration=iteration
            )

            if not success:
                logger.warning(f"  ⚠ Analysis failed: {error}")
                break

            # Record history
            history.append({
                "iteration": iteration,
                "scenarios": current_scenarios,
                "validation_results": validation_results,
                "ai_analysis": ai_analysis
            })

            # Phase 5: Convergence Check
            convergence = ai_analysis['convergence']
            logger.info(f"  Phase 5: Convergence Check")
            logger.info(f"    Converged: {convergence['converged']}")
            logger.info(f"    Confidence: {convergence['confidence']:.1%}")

            if convergence['converged'] and convergence['confidence'] >= self.config.convergence_threshold:
                converged = True
                logger.info(f"  ✓ Convergence achieved!")
                break

            # Phase 4: Apply Adjustments
            logger.info(f"  Phase 4: Applying adjustments...")
            current_scenarios = apply_adjustments(current_scenarios, ai_analysis)
            logger.info(f"    → {len(current_scenarios)} scenarios adjusted")

            iteration += 1

        if not converged:
            logger.warning(f"\n⚠ Max iterations reached without convergence")
            logger.info(f"  Proceeding with best available scenarios")

        # Phase 6: Final High-Resolution Simulation
        logger.info(f"\n[Phase 6] Final High-Resolution Simulation")
        logger.info("-"*70)
        logger.info(f"  Simulating ({len(current_scenarios)} × {self.config.final_runs})...")

        final_results = self.validator.validate_scenarios(
            scenarios=current_scenarios,
            base_params=base_params,
            n=self.config.final_runs
        )

        logger.info(f"✓ Completed {len(current_scenarios) * self.config.final_runs} simulations")

        # Phase 7: Final Report
        logger.info(f"\n[Phase 7] Final Report")
        logger.info("-"*70)

        final_report = self._build_simplified_report(
            current_scenarios,
            final_results,
            history,
            match_context
        )

        # Compile final output
        output = {
            "scenarios": [s.to_dict() for s in current_scenarios],
            "final_results": final_results,
            "report": final_report,
            "history": history,
            "converged": converged,
            "iterations": iteration - 1 if converged else iteration,
            "metadata": {
                "home_team": home_team.name,
                "away_team": away_team.name,
                "total_simulations": (iteration - 1) * len(scenarios) * self.config.initial_runs + len(current_scenarios) * self.config.final_runs,
                "enriched_data_used": True
            }
        }

        logger.info("\n" + "="*70)
        logger.info("Enriched Simulation Pipeline Completed Successfully")
        logger.info("="*70)

        return True, output, None

    except Exception as e:
        error_msg = f"Enriched pipeline error: {str(e)}"
        logger.error(error_msg)
        return False, None, error_msg
```

---

### 4. EnrichedSimulationService Update

**File:** `/backend/services/enriched_simulation_service.py` (MODIFY)

#### 4.1 Add Import

```python
from simulation.v2.simulation_pipeline import get_pipeline, PipelineConfig
```

#### 4.2 Replace simulate_match_enriched() Implementation

**Replace lines 93-189:**

```python
def simulate_match_enriched(
    self,
    home_team: str,
    away_team: str,
    match_context: Optional[Dict] = None
) -> Tuple[bool, Optional[Dict], Optional[str]]:
    """
    Run enriched match simulation with V2 Pipeline (Phase 1-7)

    Args:
        home_team: Home team name (e.g., "Arsenal")
        away_team: Away team name (e.g., "Liverpool")
        match_context: Optional match context

    Returns:
        Tuple of (success, result_dict, error_message)
    """
    logger.info(f"Enriched simulation starting: {home_team} vs {away_team}")

    # Set default match context
    if match_context is None:
        match_context = {}

    # Validate Qwen availability
    is_healthy, health_error = self.client.health_check()
    if not is_healthy:
        error_msg = f"Qwen AI not available: {health_error}"
        logger.error(error_msg)
        return False, None, error_msg

    # Step 1: Load home team data
    try:
        logger.info(f"Loading enriched data for {home_team}...")
        home_team_data = self.loader.load_team_data(home_team)
        logger.info(f"✓ {home_team} data loaded: {len(home_team_data.lineup)} players")
    except Exception as e:
        error_msg = f"Failed to load home team '{home_team}': {str(e)}"
        logger.error(error_msg)
        return False, None, error_msg

    # Step 2: Load away team data
    try:
        logger.info(f"Loading enriched data for {away_team}...")
        away_team_data = self.loader.load_team_data(away_team)
        logger.info(f"✓ {away_team} data loaded: {len(away_team_data.lineup)} players")
    except Exception as e:
        error_msg = f"Failed to load away team '{away_team}': {str(e)}"
        logger.error(error_msg)
        return False, None, error_msg

    # Step 3: Run V2 Pipeline (Phase 1-7)
    logger.info(f"Running V2 Pipeline with Enriched Domain Data...")
    start_time = datetime.utcnow()

    # Get pipeline
    pipeline = get_pipeline(config=PipelineConfig(
        max_iterations=5,
        initial_runs=100,
        final_runs=3000,
        convergence_threshold=0.85
    ))

    # Run enriched pipeline
    success, pipeline_result, error = pipeline.run_enriched(
        home_team=home_team_data,
        away_team=away_team_data,
        match_context=match_context
    )

    processing_time = (datetime.utcnow() - start_time).total_seconds()

    if not success:
        error_msg = f"Pipeline failed: {error}"
        logger.error(error_msg)
        return False, None, error_msg

    logger.info(f"✓ Pipeline complete ({processing_time:.1f}s)")

    # Step 4: Format response
    report = pipeline_result['report']
    prediction = report['prediction']

    result = {
        'success': True,
        'prediction': prediction['win_probabilities'],  # {home, draw, away}
        'predicted_score': f"{prediction['expected_goals']['home']:.0f}-{prediction['expected_goals']['away']:.0f}",
        'expected_goals': prediction['expected_goals'],
        'confidence': 'high' if pipeline_result['converged'] else 'medium',
        'analysis': {
            'key_factors': [],  # Can extract from scenarios
            'dominant_scenario': report['dominant_scenario'],
            'all_scenarios': report['all_scenarios'],
            'tactical_insight': f"Simulation converged after {pipeline_result['iterations']} iterations."
        },
        'summary': f"{home_team} vs {away_team}: {report['dominant_scenario']['name']}",
        'teams': {
            'home': {
                'name': home_team_data.name,
                'formation': home_team_data.formation
            },
            'away': {
                'name': away_team_data.name,
                'formation': away_team_data.formation
            }
        },
        'pipeline_metadata': {
            'converged': pipeline_result['converged'],
            'iterations': pipeline_result['iterations'],
            'total_simulations': pipeline_result['metadata']['total_simulations'],
            'scenarios_count': len(pipeline_result['scenarios'])
        },
        'usage': {
            'total_tokens': 0,  # Pipeline doesn't track tokens (multiple AI calls)
            'processing_time': processing_time,
            'cost_usd': 0.0  # Local = 0
        },
        'match_context': match_context,
        'timestamp': datetime.utcnow().isoformat()
    }

    logger.info(f"Enriched simulation successful: {home_team} vs {away_team}")
    return True, result, None
```

---

## Data Flow Diagram

```
User Request (home_team, away_team)
  ↓
EnrichedSimulationService.simulate_match_enriched()
  ↓
[1] Load Team Data
  ├─ EnrichedDomainDataLoader.load_team_data(home_team)
  │   → EnrichedTeamInput (11 players, tactics, commentary)
  └─ EnrichedDomainDataLoader.load_team_data(away_team)
      → EnrichedTeamInput
  ↓
[2] SimulationPipeline.run_enriched()
  ↓
  ├─ enriched_to_match_params() → MatchParameters
  ↓
  [Phase 1] EnrichedAIScenarioGenerator.generate_scenarios_enriched()
    ├─ Build system prompt (5-7 scenarios, JSON format)
    ├─ Build user prompt (7 sections, enriched data)
    ├─ EnrichedQwenClient.generate() → AI JSON response
    └─ Parse JSON → List[Scenario] (5-7 scenarios)
  ↓
  [Phase 2-5] Iterative Loop (max 5 iterations)
    ├─ MultiScenarioValidator.validate_scenarios(100 runs)
    ├─ AIAnalyzer.analyze_and_adjust()
    ├─ apply_adjustments()
    └─ Convergence check → converged? → yes/no
  ↓
  [Phase 6] MultiScenarioValidator.validate_scenarios(3,000 runs)
    └─ Final validation results
  ↓
  [Phase 7] _build_simplified_report()
    └─ Weighted average probabilities
  ↓
  Return pipeline_result
  ↓
EnrichedSimulationService.format_response()
  ↓
Return result to user
```

---

## Implementation Checklist

### Phase 3: Implement EnrichedAIScenarioGenerator ⏳

- [ ] Create file: `simulation/v2/ai_scenario_generator_enriched.py`
- [ ] Implement `EnrichedAIScenarioGenerator` class
- [ ] Implement `_build_enriched_system_prompt_for_scenarios()`
- [ ] Implement `_build_enriched_scenario_generation_prompt()`
- [ ] Implement `generate_scenarios_enriched()`
- [ ] Implement `_parse_scenarios()`
- [ ] Implement `_dict_to_scenario()`
- [ ] Implement `_validate_scenarios()`
- [ ] Add global instance function `get_enriched_scenario_generator()`
- [ ] Test with Arsenal vs Liverpool

### Phase 4: Create Enriched Helpers ⏳

- [ ] Create file: `simulation/v2/enriched_helpers.py`
- [ ] Implement `enriched_to_match_params()`
- [ ] Test conversion with EnrichedTeamInput

### Phase 5: Extend SimulationPipeline ⏳

- [ ] Open file: `simulation/v2/simulation_pipeline.py`
- [ ] Add imports (EnrichedTeamInput, enriched_helpers, etc.)
- [ ] Implement `run_enriched()` method
- [ ] Test pipeline with enriched inputs

### Phase 6: Update EnrichedSimulationService ⏳

- [ ] Open file: `services/enriched_simulation_service.py`
- [ ] Add pipeline imports
- [ ] Replace `simulate_match_enriched()` implementation (lines 93-189)
- [ ] Update `simulate_with_progress()` if needed
- [ ] Test service end-to-end

### Phase 7: Integration Tests ⏳

- [ ] Create file: `test_enriched_pipeline_integration.py`
- [ ] Test 1: EnrichedAIScenarioGenerator generates 5-7 scenarios
- [ ] Test 2: Scenarios contain enriched context (player names, commentary)
- [ ] Test 3: Pipeline completes Phase 1-7
- [ ] Test 4: Final results contain aggregated probabilities
- [ ] Test 5: End-to-end service test (Arsenal vs Liverpool)
- [ ] Test 6: Verify processing time (2-5 minutes expected)
- [ ] Test 7: Verify convergence behavior

### Phase 8: Documentation ⏳

- [ ] Create file: `ENRICHED_PIPELINE_COMPLETE_REPORT.md`
- [ ] Document architecture
- [ ] Document API usage
- [ ] Document test results
- [ ] Document performance metrics
- [ ] Add examples

---

## Expected Behavior

### Input

```python
from services.enriched_simulation_service import get_enriched_simulation_service

service = get_enriched_simulation_service()
success, result, error = service.simulate_match_enriched(
    home_team="Arsenal",
    away_team="Liverpool",
    match_context={'venue': 'Emirates Stadium', 'importance': 'high'}
)
```

### Expected Output

```python
{
    'success': True,
    'prediction': {
        'home': 0.42,      # Home win probability (aggregated from 5-7 scenarios × 3,000 runs)
        'draw': 0.28,      # Draw probability
        'away': 0.30       # Away win probability
    },
    'predicted_score': '2-1',
    'expected_goals': {'home': 1.9, 'away': 1.4},
    'confidence': 'high',  # 'high' if converged, 'medium' if max iterations
    'analysis': {
        'dominant_scenario': {
            'id': 'SYNTH_002',
            'name': '아스날 초반 우위 → 리버풀 역습 → 박빙 승부',
            'probability': 0.22,
            'reasoning': 'Saka and Odegaard create early chances...'
        },
        'all_scenarios': [
            {
                'id': 'SYNTH_001',
                'name': '아스날 완승',
                'probability': 0.18,
                'win_rate': {'home': 0.85, 'draw': 0.10, 'away': 0.05},
                'avg_score': {'home': 2.8, 'away': 1.1}
            },
            # ... 4-6 more scenarios
        ],
        'tactical_insight': 'Simulation converged after 3 iterations.'
    },
    'pipeline_metadata': {
        'converged': True,
        'iterations': 3,
        'total_simulations': 18300,  # (3 iterations × 6 scenarios × 100) + (6 scenarios × 3000)
        'scenarios_count': 6
    },
    'usage': {
        'processing_time': 142.5,  # seconds (~2.4 minutes)
        'cost_usd': 0.0
    }
}
```

### Expected Logs

```
Enriched simulation starting: Arsenal vs Liverpool
Loading enriched data for Arsenal...
✓ Arsenal data loaded: 11 players
Loading enriched data for Liverpool...
✓ Liverpool data loaded: 11 players
Running V2 Pipeline with Enriched Domain Data...

======================================================================
Enriched Simulation Pipeline Started
======================================================================
Match: Arsenal vs Liverpool

[Phase 1] Enriched AI Scenario Generation
----------------------------------------------------------------------
Calling Qwen AI for scenario generation...
AI response received (3,245 tokens)
✓ Generated 6 enriched scenarios

[Phase 2-5] Iterative Refinement Loop
----------------------------------------------------------------------

>>> Iteration 1/5
  Phase 2: Simulating (6 × 100)...
  [1/6] Validating SYNTH_001: 아스날 완승
   ✓ Win rate: H=85.0%, D=10.0%, A=5.0%
   ✓ Avg score: 2.80-1.10
   ✓ Narrative adherence: 78.5%
  [2/6] Validating SYNTH_002: 아스날 초반 우위 → 박빙 승부
   ✓ Win rate: H=52.0%, D=28.0%, A=20.0%
   ✓ Avg score: 1.90-1.40
   ✓ Narrative adherence: 82.3%
  ...
  Phase 3: AI Analysis...
  Phase 5: Convergence Check
    Converged: True
    Confidence: 88.5%
  ✓ Convergence achieved!

[Phase 6] Final High-Resolution Simulation
----------------------------------------------------------------------
  Simulating (6 × 3000)...
✓ Completed 18000 simulations

[Phase 7] Final Report
----------------------------------------------------------------------

======================================================================
Enriched Simulation Pipeline Completed Successfully
======================================================================

✓ Pipeline complete (142.5s)
Enriched simulation successful: Arsenal vs Liverpool
```

---

## Risk Analysis

### Potential Issues

1. **AI Scenario Generation Quality**
   - **Risk**: AI might generate invalid JSON or non-distinct scenarios
   - **Mitigation**: Strict JSON parsing + validation + retry logic

2. **Processing Time**
   - **Risk**: 18,000+ simulations might take too long (>5 minutes)
   - **Mitigation**: Use qwen2.5:14b (faster), optimize simulation engine

3. **Convergence Failure**
   - **Risk**: Pipeline might not converge in 5 iterations
   - **Mitigation**: Continue with best scenarios, return 'medium' confidence

4. **Data Conversion Issues**
   - **Risk**: EnrichedTeamInput → MatchParameters conversion might lose data
   - **Mitigation**: Thorough testing, ensure derived_strengths are accurate

### Validation Strategy

1. **Unit Tests**
   - Test EnrichedAIScenarioGenerator independently
   - Test enriched_to_match_params() conversion
   - Test SimulationPipeline.run_enriched() with mock data

2. **Integration Tests**
   - Test full pipeline with Arsenal vs Liverpool
   - Verify output format matches specification
   - Check processing time < 5 minutes
   - Verify probabilities sum to 1.0

3. **Manual Verification**
   - Review generated scenarios for quality
   - Check that user commentary is reflected in scenarios
   - Verify that probabilities are reasonable

---

## Success Criteria

### Phase 3-6 Success Criteria

- [x] Design complete
- [ ] EnrichedAIScenarioGenerator generates 5-7 scenarios
- [ ] Scenarios contain player-specific events (e.g., "Saka wing breakthrough")
- [ ] Scenarios reference user commentary
- [ ] Pipeline completes Phase 1-7 without errors
- [ ] Final output contains aggregated probabilities
- [ ] Processing time < 5 minutes
- [ ] Probabilities sum to 1.0 (±0.05)
- [ ] Converges in 3-5 iterations (or returns 'medium' confidence)

### Phase 7 Success Criteria

- [ ] All unit tests pass
- [ ] Integration test passes (Arsenal vs Liverpool)
- [ ] Manual review confirms high-quality scenarios
- [ ] Documentation complete

---

**Status**: 🔵 Design Complete - Ready for Implementation

**Next Step**: Phase 3 - Implement EnrichedAIScenarioGenerator

