"""
Few-Shot Examples Library
Provide 2-3 high-quality examples to LLMs for better pattern recognition

Key benefits:
- Clear output format demonstration
- Appropriate detail level guidance
- Consistent tone/style modeling
- 17-25% quality improvement over zero-shot
"""

from typing import List, Dict, Tuple
from dataclasses import dataclass


@dataclass
class FewShotExample:
    """
    Single few-shot example
    Contains both input context and expected output
    """
    name: str
    input_context: str
    expected_output: str
    explanation: str  # Why this is a good example


class FewShotExampleLibrary:
    """
    Library of curated few-shot examples

    Provides high-quality examples for:
    - Scenario generation (Phase 1)
    - Result analysis (Phase 3)
    - Report generation (Phase 7)
    """

    def __init__(self):
        """Initialize example library"""
        self.scenario_examples = self._create_scenario_examples()
        self.analysis_examples = self._create_analysis_examples()
        self.report_examples = self._create_report_examples()

    # ==========================================================================
    # Scenario Generation Examples (Phase 1)
    # ==========================================================================

    def _create_scenario_examples(self) -> List[FewShotExample]:
        """
        Create scenario generation examples

        Covers different match types:
        1. Strong vs Weak (expected dominance)
        2. Balanced clash (even match)
        3. Counter-attacking style
        """
        examples = []

        # Example 1: Strong vs Weak
        examples.append(FewShotExample(
            name="Strong vs Weak",
            input_context="""
**Match Context:**
- Home: Manchester City (공격력: 92/100, 수비력: 88/100, 스타일: possession)
- Away: Sheffield United (공격력: 58/100, 수비력: 60/100, 스타일: direct)
- Form: Man City (WWWWW), Sheffield (LLDLL)
- Venue: Etihad Stadium (Home)
""",
            expected_output="""{
  "events": [
    {
      "minute_range": [5, 20],
      "event_type": "pressure",
      "team": "home",
      "description": "Man City dominates possession from kickoff, pressing high and controlling midfield through Rodri and De Bruyne",
      "probability_boost": 0.25,
      "actor": "De Bruyne",
      "reason": "Superior technical quality and home advantage"
    },
    {
      "minute_range": [15, 30],
      "event_type": "goal_opportunity",
      "team": "home",
      "description": "City creates multiple chances through intricate passing, Haaland finds space in the box",
      "probability_boost": 0.35,
      "actor": "Haaland",
      "reason": "Sustained pressure against weaker defense"
    },
    {
      "minute_range": [25, 40],
      "event_type": "wing_breakthrough",
      "team": "home",
      "description": "Foden and Grealish exploit wide areas, stretching Sheffield's compact defense",
      "probability_boost": 0.20,
      "actor": "Foden",
      "reason": "Width advantage in possession-based system"
    },
    {
      "minute_range": [50, 65],
      "event_type": "counter_attack",
      "team": "away",
      "description": "Sheffield briefly threatens on the break after City corner, using directness",
      "probability_boost": 0.10,
      "actor": "McBurnie",
      "reason": "Rare opportunity on transition"
    },
    {
      "minute_range": [70, 85],
      "event_type": "pressure",
      "team": "home",
      "description": "City tightens grip in final third, fresh legs from bench maintain intensity",
      "probability_boost": 0.30,
      "reason": "Superior squad depth and fitness"
    }
  ],
  "description": "Man City expected to dominate possession (70%+) and create numerous chances. Sheffield will sit deep and try to limit damage, with occasional direct counters their only threat. Home team's technical superiority should overwhelm visitors.",
  "predicted_score": {"home": 3, "away": 0},
  "confidence": 0.85
}""",
            explanation="Clear power imbalance → dominant home team, few away threats, high confidence"
        ))

        # Example 2: Balanced Clash
        examples.append(FewShotExample(
            name="Balanced Top Clash",
            input_context="""
**Match Context:**
- Home: Arsenal (공격력: 85/100, 수비력: 82/100, 스타일: mixed)
- Away: Liverpool (공격력: 88/100, 수비력: 80/100, 스타일: direct)
- Form: Arsenal (WWDWL), Liverpool (WDWWL)
- Venue: Emirates Stadium (Home)
""",
            expected_output="""{
  "events": [
    {
      "minute_range": [10, 25],
      "event_type": "midfield_battle",
      "team": "home",
      "description": "Intense midfield contest between Odegaard/Rice and Mac Allister/Szoboszlai, neither side gaining clear control",
      "probability_boost": 0.05,
      "actor": "Odegaard",
      "reason": "Evenly matched technical midfielders"
    },
    {
      "minute_range": [20, 35],
      "event_type": "wing_breakthrough",
      "team": "home",
      "description": "Saka tests Robertson on Arsenal's right, exploiting space when Liverpool commits forward",
      "probability_boost": 0.15,
      "actor": "Saka",
      "reason": "Home team targets Liverpool's attacking fullback"
    },
    {
      "minute_range": [30, 45],
      "event_type": "counter_attack",
      "team": "away",
      "description": "Liverpool's front three (Salah, Nunez, Diaz) threatens on transitions, Salah vs Zinchenko 1v1",
      "probability_boost": 0.18,
      "actor": "Salah",
      "reason": "Liverpool's speed on the break vs Arsenal's high line"
    },
    {
      "minute_range": [55, 70],
      "event_type": "set_piece",
      "team": "home",
      "description": "Arsenal creates danger from corners and free kicks, utilizing height advantage",
      "probability_boost": 0.12,
      "actor": "Gabriel",
      "reason": "Set piece strength vs Liverpool's zonal marking"
    },
    {
      "minute_range": [75, 90],
      "event_type": "transition",
      "team": "away",
      "description": "End-to-end finale as both teams push for winner, spaces opening up",
      "probability_boost": 0.10,
      "reason": "Fatigue and tactical desperation create chaos"
    }
  ],
  "description": "High-quality tactical battle between two attacking sides. Arsenal will try to control tempo at home, while Liverpool's direct transitions pose constant threat. Expect open game with chances for both, tight margin between teams.",
  "predicted_score": {"home": 2, "away": 2},
  "confidence": 0.65
}""",
            explanation="Balanced strength → contested midfield, threats both ways, moderate confidence, draw prediction"
        ))

        # Example 3: Counter-attacking Style
        examples.append(FewShotExample(
            name="Counter-Attacking Setup",
            input_context="""
**Match Context:**
- Home: Brighton (공격력: 75/100, 수비력: 72/100, 스타일: possession)
- Away: Tottenham (공격력: 82/100, 수비력: 68/100, 스타일: direct)
- Form: Brighton (WDWDL), Tottenham (WWLWW)
- Venue: Amex Stadium (Home)
""",
            expected_output="""{
  "events": [
    {
      "minute_range": [8, 22],
      "event_type": "pressure",
      "team": "home",
      "description": "Brighton builds patiently from the back, probing Spurs' mid-block with intricate rotations",
      "probability_boost": 0.12,
      "actor": "Gross",
      "reason": "Home team's possession philosophy vs Spurs' compact shape"
    },
    {
      "minute_range": [18, 35],
      "event_type": "counter_attack",
      "team": "away",
      "description": "Tottenham sits deep then explodes on transition, Son and Johnson racing into space",
      "probability_boost": 0.25,
      "actor": "Son",
      "reason": "Spurs' counter-attacking identity vs Brighton's high possession line"
    },
    {
      "minute_range": [40, 55],
      "event_type": "midfield_battle",
      "team": "home",
      "description": "Brighton adjusts to press higher, trying to pin Spurs back and prevent counters",
      "probability_boost": 0.08,
      "reason": "Tactical adjustment to nullify Spurs' transition threat"
    },
    {
      "minute_range": [60, 75],
      "event_type": "goal_opportunity",
      "team": "away",
      "description": "Spurs finds joy in behind Brighton's aggressive press, Maddison threading passes",
      "probability_boost": 0.22,
      "actor": "Maddison",
      "reason": "Space exploitation during Brighton's high-risk pressing"
    },
    {
      "minute_range": [78, 90],
      "event_type": "pressure",
      "team": "home",
      "description": "Brighton throws numbers forward chasing equalizer, leaving gaps at back",
      "probability_boost": 0.15,
      "reason": "Desperation creates offensive opportunities but defensive risk"
    }
  ],
  "description": "Tactical contrast: Brighton's patient possession vs Tottenham's lethal counters. Home team will dominate ball (60%+) but Spurs' transitions are dangerous. Brighton needs to break down deep block while avoiding being caught on break.",
  "predicted_score": {"home": 1, "away": 2},
  "confidence": 0.72
}""",
            explanation="Style clash → possession vs counter, tactical nuance, Spurs' efficiency beats Brighton's control"
        ))

        return examples

    # ==========================================================================
    # Analysis Examples (Phase 3)
    # ==========================================================================

    def _create_analysis_examples(self) -> List[FewShotExample]:
        """
        Create result analysis examples

        Covers:
        1. Converged case (good match)
        2. Needs adjustment (significant discrepancy)
        """
        examples = []

        # Example 1: Converged
        examples.append(FewShotExample(
            name="Converged Analysis",
            input_context="""
**Original Scenario:**
- Predicted: Man City 3-0 Sheffield United
- Key Events: Early pressure (0.25 boost), Goal opportunity 15-30min (0.35 boost)

**Simulation Result:**
- Actual Score: 3-1
- Narrative Adherence: 73%
- Events Matched: 4/5 key moments occurred
""",
            expected_output="""{
  "state": "converged",
  "issues": [],
  "adjusted_scenario": null,
  "confidence": 0.88,
  "reasoning": "Simulation closely matches predicted scenario. Man City dominated as expected (3 goals), Sheffield's single goal was within reasonable variance. 73% narrative adherence exceeds 60% convergence threshold. Key tactical moments (early pressure, goal opportunities) occurred as scripted. Minor deviation acceptable."
}""",
            explanation="High adherence (73%) → converged, no adjustment needed"
        ))

        # Example 2: Needs Adjustment
        examples.append(FewShotExample(
            name="Needs Adjustment",
            input_context="""
**Original Scenario:**
- Predicted: Arsenal 2-2 Liverpool
- Key Events: Balanced midfield (0.05 boost), Saka breakthrough (0.15 boost), Salah counter (0.18 boost)

**Simulation Result:**
- Actual Score: 0-1
- Narrative Adherence: 28%
- Events Matched: 1/5 key moments occurred (only Salah counter worked)
""",
            expected_output="""{
  "state": "needs_adjustment",
  "issues": [
    {
      "type": "score_mismatch",
      "description": "Arsenal failed to score despite 2-goal prediction, Saka breakthrough underperformed",
      "severity": "high"
    },
    {
      "type": "event_missing",
      "description": "Midfield battle and home attacking events did not materialize as expected",
      "severity": "medium"
    },
    {
      "type": "probability_deviation",
      "description": "Salah counter-attack was only successful event, may need higher boost",
      "severity": "low"
    }
  ],
  "adjusted_scenario": {
    "events": [
      {
        "minute_range": [10, 25],
        "event_type": "midfield_battle",
        "team": "away",
        "description": "Liverpool dominates midfield, Arsenal struggles to impose rhythm",
        "probability_boost": 0.15,
        "actor": "Mac Allister",
        "reason": "Adjusted: Liverpool midfield superiority underestimated"
      },
      {
        "minute_range": [20, 35],
        "event_type": "wing_breakthrough",
        "team": "home",
        "description": "Saka attempts to break through but Robertson defends well",
        "probability_boost": 0.08,
        "actor": "Saka",
        "reason": "Reduced: Arsenal's wing threat was overstated"
      },
      {
        "minute_range": [30, 45],
        "event_type": "counter_attack",
        "team": "away",
        "description": "Liverpool's front three exploits space, Salah clinical",
        "probability_boost": 0.30,
        "actor": "Salah",
        "reason": "Increased: This was Liverpool's key weapon, needs emphasis"
      },
      {
        "minute_range": [50, 65],
        "event_type": "defensive_action",
        "team": "away",
        "description": "Liverpool's backline stays compact, nullifying Arsenal attacks",
        "probability_boost": 0.12,
        "reason": "Added: Defensive solidity was critical factor"
      },
      {
        "minute_range": [70, 85],
        "event_type": "pressure",
        "team": "home",
        "description": "Arsenal pushes desperately but lacks cutting edge",
        "probability_boost": 0.05,
        "reason": "Reduced: Pressure was ineffective, lower boost"
      }
    ],
    "description": "Liverpool's defensive organization and counter-attacking threat proved decisive. Arsenal's possession-based approach failed to create clear chances. Tactical adjustment: emphasize Liverpool's control and Arsenal's struggles.",
    "predicted_score": {"home": 0, "away": 1},
    "confidence": 0.75
  },
  "confidence": 0.70,
  "reasoning": "28% adherence is far below 60% threshold. Arsenal's attacking events vastly overestimated (Saka boost 0.15→0.08), Liverpool's counter threat underestimated (0.18→0.30). Simulation revealed Liverpool's midfield and defensive dominance not captured in original scenario. Adjusted boosts to reflect Liverpool's control."
}""",
            explanation="Low adherence (28%) → needs adjustment, rebalance event probabilities toward actual result"
        ))

        return examples

    # ==========================================================================
    # Report Examples (Phase 7)
    # ==========================================================================

    def _create_report_examples(self) -> List[FewShotExample]:
        """
        Create report generation examples

        Shows desired markdown format and narrative style
        """
        examples = []

        examples.append(FewShotExample(
            name="Match Report",
            input_context="""
**Match:** Arsenal 2-1 Tottenham
**Key Events:** Odegaard goal 23', Kane goal 58', Saka winner 81'
**Stats:** Arsenal 16 shots, Tottenham 11 shots
""",
            expected_output="""# Arsenal 2-1 Tottenham - Match Report

## 경기 요약
Arsenal이 Emirates Stadium에서 열린 North London Derby에서 Tottenham을 2-1로 꺾으며 귀중한 승점 3점을 획득했습니다.

## 주요 순간

### 23분 - Arsenal 선제골 ⚽
**Odegaard**가 중거리 슛으로 경기를 열었습니다. Saka의 패스를 받아 페널티 박스 밖에서 정확한 슛을 날려 골망을 흔들었습니다.

### 58분 - Tottenham 동점골 ⚽
**Kane**이 헤딩골로 Spurs를 경기로 복귀시켰습니다. Son의 크로스를 머리로 연결해 득점에 성공했습니다.

### 81분 - Arsenal 결승골 ⚽
**Saka**가 경기 막판 우측에서 돌파한 후 침착하게 마무리하며 Arsenal에 승리를 안겼습니다.

## 팀별 통계

| 항목 | Arsenal | Tottenham |
|------|---------|-----------|
| 슈팅 | 16 | 11 |
| 유효슈팅 | 7 | 4 |
| 점유율 | 58% | 42% |
| 패스 성공률 | 87% | 82% |

## 전술 분석
Arsenal은 홈에서 경기를 주도하며 더 많은 기회를 창출했습니다. Odegaard의 중원 플레이메이킹이 돋보였고, Saka의 우측 돌파가 핵심 무기였습니다. Tottenham은 Kane의 골로 반격했으나, 후반 체력 저하로 Arsenal의 압박을 견디지 못했습니다.

## 결론
Arsenal의 홈 우위와 막판 집중력이 Derby 승리를 가져왔습니다. **Man of the Match: Bukayo Saka** 🌟
""",
            explanation="Clear structure, Korean narrative, tactical insights, proper formatting"
        ))

        return examples

    # ==========================================================================
    # Helper Methods
    # ==========================================================================

    def get_scenario_examples(self, n: int = 2) -> List[FewShotExample]:
        """
        Get N scenario generation examples

        Args:
            n: Number of examples (default 2, max 3)

        Returns:
            List of examples
        """
        return self.scenario_examples[:min(n, len(self.scenario_examples))]

    def get_analysis_examples(self, n: int = 2) -> List[FewShotExample]:
        """
        Get N analysis examples

        Args:
            n: Number of examples (default 2)

        Returns:
            List of examples
        """
        return self.analysis_examples[:min(n, len(self.analysis_examples))]

    def get_report_examples(self, n: int = 1) -> List[FewShotExample]:
        """
        Get N report examples

        Args:
            n: Number of examples (default 1)

        Returns:
            List of examples
        """
        return self.report_examples[:min(n, len(self.report_examples))]

    def format_examples_for_prompt(self, examples: List[FewShotExample]) -> str:
        """
        Format examples for inclusion in prompt

        Args:
            examples: List of FewShotExample objects

        Returns:
            Formatted string for prompt

        Example output:
            ## Example 1: Strong vs Weak

            **Input:**
            <input context>

            **Expected Output:**
            <expected output>

            ---
        """
        formatted = []

        for i, example in enumerate(examples, 1):
            formatted.append(f"## Example {i}: {example.name}\n")
            formatted.append(f"**Input:**\n{example.input_context}\n")
            formatted.append(f"**Expected Output:**\n{example.expected_output}\n")

            if i < len(examples):
                formatted.append("---\n")

        return "\n".join(formatted)


# ==========================================================================
# Testing
# ==========================================================================

def test_few_shot_library():
    """Test Few-Shot Examples Library"""
    print("=" * 70)
    print("Testing Few-Shot Examples Library")
    print("=" * 70)

    library = FewShotExampleLibrary()

    # Test 1: Scenario examples
    print("\nTest 1: Scenario Examples")
    print("-" * 70)
    scenario_examples = library.get_scenario_examples(n=2)
    print(f"Retrieved {len(scenario_examples)} scenario examples:")
    for ex in scenario_examples:
        print(f"  - {ex.name}")
    assert len(scenario_examples) == 2
    assert scenario_examples[0].name == "Strong vs Weak"
    print("✅ Test 1 PASSED")

    # Test 2: Analysis examples
    print("\nTest 2: Analysis Examples")
    print("-" * 70)
    analysis_examples = library.get_analysis_examples(n=2)
    print(f"Retrieved {len(analysis_examples)} analysis examples:")
    for ex in analysis_examples:
        print(f"  - {ex.name}")
    assert len(analysis_examples) == 2
    assert "Converged" in analysis_examples[0].name
    print("✅ Test 2 PASSED")

    # Test 3: Report examples
    print("\nTest 3: Report Examples")
    print("-" * 70)
    report_examples = library.get_report_examples(n=1)
    print(f"Retrieved {len(report_examples)} report examples:")
    for ex in report_examples:
        print(f"  - {ex.name}")
    assert len(report_examples) == 1
    print("✅ Test 3 PASSED")

    # Test 4: Format for prompt
    print("\nTest 4: Format Examples for Prompt")
    print("-" * 70)
    formatted = library.format_examples_for_prompt(scenario_examples[:1])
    print(f"Formatted prompt length: {len(formatted)} characters")
    print("\nSample (first 300 chars):")
    print(formatted[:300] + "...")
    assert "Example 1:" in formatted
    assert "**Input:**" in formatted
    assert "**Expected Output:**" in formatted
    print("✅ Test 4 PASSED")

    # Test 5: Content quality check
    print("\nTest 5: Content Quality Check")
    print("-" * 70)
    strong_vs_weak = scenario_examples[0]
    print(f"Example: {strong_vs_weak.name}")
    print(f"  Input length: {len(strong_vs_weak.input_context)} chars")
    print(f"  Output length: {len(strong_vs_weak.expected_output)} chars")
    print(f"  Explanation: {strong_vs_weak.explanation[:60]}...")

    # Check that output contains JSON
    assert "{" in strong_vs_weak.expected_output
    assert "events" in strong_vs_weak.expected_output
    assert "probability_boost" in strong_vs_weak.expected_output
    print("✅ Test 5 PASSED")

    print("\n" + "=" * 70)
    print("✅ All Few-Shot Library Tests PASSED!")
    print("=" * 70)


if __name__ == "__main__":
    test_few_shot_library()
