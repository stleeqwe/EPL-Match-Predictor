"""
Chain-of-Thought (CoT) Prompting
Explicit step-by-step reasoning for better LLM decision-making

Key benefits:
- Improved accuracy on complex reasoning tasks (57% → 78% in research)
- Transparent decision process (debuggable)
- Better handling of multi-step analysis
- Reasoning chain extraction for validation

Research basis:
- Wei et al. (2022) "Chain-of-Thought Prompting Elicits Reasoning in LLMs"
- Complexity-dependent gains (simple tasks: +5%, complex tasks: +30%)
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import re


@dataclass
class ReasoningStep:
    """
    Single step in reasoning chain
    """
    step_number: int
    thought: str
    conclusion: str


class CoTPromptTemplate:
    """
    Chain-of-Thought prompt template generator

    Generates prompts that elicit explicit step-by-step reasoning
    """

    # ==========================================================================
    # Template Components
    # ==========================================================================

    COT_TRIGGER = "Let's approach this step by step:"

    REASONING_STRUCTURE = """
Please structure your reasoning as follows:

**Step 1: Context Analysis**
Analyze the given match context (team strengths, form, styles).

**Step 2: Tactical Implications**
Determine how tactical styles will interact (possession vs direct, press intensity, etc.).

**Step 3: Key Factors**
Identify 2-3 decisive factors that will shape the match outcome.

**Step 4: Event Prediction**
Based on above analysis, predict key match events with justified probability boosts.

**Step 5: Final Scenario**
Synthesize into cohesive match scenario with confidence level.
"""

    ANALYSIS_STRUCTURE = """
Please structure your analysis as follows:

**Step 1: Discrepancy Identification**
Compare predicted scenario vs actual simulation results. What diverged?

**Step 2: Root Cause Analysis**
Why did these divergences occur? (Probability boosts too high/low? Missing events? Wrong emphasis?)

**Step 3: Impact Assessment**
Which discrepancies are critical vs minor? Prioritize by severity.

**Step 4: Adjustment Strategy**
How should scenario be modified? Specific boost changes, event additions/removals.

**Step 5: Convergence Decision**
Based on narrative adherence (threshold: 60%), decide converged vs needs_adjustment.
"""

    # ==========================================================================
    # Template Generation
    # ==========================================================================

    @classmethod
    def generate_scenario_cot_prompt(
        cls,
        base_prompt: str,
        include_reasoning_structure: bool = True
    ) -> str:
        """
        Generate CoT-enhanced scenario generation prompt

        Args:
            base_prompt: Original user prompt with match context
            include_reasoning_structure: Whether to include explicit step structure

        Returns:
            CoT-enhanced prompt

        Example:
            >>> base = "Predict Arsenal vs Liverpool scenario"
            >>> cot_prompt = CoTPromptTemplate.generate_scenario_cot_prompt(base)
            >>> # Contains "Let's approach this step by step" + structured reasoning guide
        """
        cot_prompt = base_prompt + "\n\n"
        cot_prompt += f"## Reasoning Approach\n\n"
        cot_prompt += f"{cls.COT_TRIGGER}\n\n"

        if include_reasoning_structure:
            cot_prompt += cls.REASONING_STRUCTURE + "\n"

        cot_prompt += """
**Important:**
- Show your reasoning for each step
- Justify probability boosts with tactical logic
- Connect team strengths to predicted events
- Explain confidence level based on certainty of predictions

After completing your step-by-step reasoning, provide the final JSON scenario.
"""

        return cot_prompt

    @classmethod
    def generate_analysis_cot_prompt(
        cls,
        base_prompt: str,
        include_reasoning_structure: bool = True
    ) -> str:
        """
        Generate CoT-enhanced result analysis prompt

        Args:
            base_prompt: Original analysis prompt with scenario + results
            include_reasoning_structure: Whether to include explicit step structure

        Returns:
            CoT-enhanced prompt

        Example:
            >>> base = "Analyze scenario vs simulation result"
            >>> cot_prompt = CoTPromptTemplate.generate_analysis_cot_prompt(base)
            >>> # Contains step-by-step analysis structure
        """
        cot_prompt = base_prompt + "\n\n"
        cot_prompt += f"## Analysis Approach\n\n"
        cot_prompt += f"{cls.COT_TRIGGER}\n\n"

        if include_reasoning_structure:
            cot_prompt += cls.ANALYSIS_STRUCTURE + "\n"

        cot_prompt += """
**Important:**
- Systematically compare each predicted event against simulation
- Quantify discrepancies (e.g., "boost was 0.25 but should be 0.15")
- Prioritize issues by impact on narrative adherence
- Make data-driven adjustment decisions

Provide explicit reasoning for your convergence decision and any adjustments.
"""

        return cot_prompt

    # ==========================================================================
    # Self-Consistency (Advanced)
    # ==========================================================================

    @classmethod
    def generate_self_consistency_prompt(
        cls,
        base_prompt: str,
        num_paths: int = 3
    ) -> str:
        """
        Generate prompt for self-consistency CoT

        Self-consistency: Generate multiple reasoning paths, then aggregate
        (Wang et al. 2022 - improves accuracy by ~10% over single CoT)

        Args:
            base_prompt: Original prompt
            num_paths: Number of reasoning paths to generate (default 3)

        Returns:
            Self-consistency CoT prompt

        Note:
            This requires multiple LLM calls and majority voting.
            Only use for critical decisions where accuracy > latency.
        """
        sc_prompt = base_prompt + "\n\n"
        sc_prompt += f"## Self-Consistency Reasoning\n\n"
        sc_prompt += f"Generate {num_paths} independent reasoning paths:\n\n"

        for i in range(1, num_paths + 1):
            sc_prompt += f"**Path {i}:**\n"
            sc_prompt += f"{cls.COT_TRIGGER}\n"
            sc_prompt += f"[Your reasoning for Path {i}]\n"
            sc_prompt += f"[Conclusion for Path {i}]\n\n"

        sc_prompt += """
**Final Answer:**
Compare the conclusions from all paths. If they agree, use that answer with high confidence.
If they disagree, identify the most well-reasoned path and explain why.
"""

        return sc_prompt


class ReasoningChainParser:
    """
    Parse and extract reasoning chains from CoT responses

    Useful for:
    - Debugging (why did AI make this decision?)
    - Validation (is reasoning sound?)
    - Logging (track decision process)
    """

    @staticmethod
    def extract_reasoning_steps(response: str) -> List[ReasoningStep]:
        """
        Extract step-by-step reasoning from CoT response

        Args:
            response: LLM response text containing CoT reasoning

        Returns:
            List of ReasoningStep objects

        Example:
            >>> response = "Step 1: Arsenal has 85/100 attack..."
            >>> steps = ReasoningChainParser.extract_reasoning_steps(response)
            >>> steps[0].thought  # "Arsenal has 85/100 attack..."
        """
        steps = []

        # Pattern: **Step N: Title** followed by content
        pattern = r'\*\*Step (\d+):([^*]+)\*\*\s*(.*?)(?=\*\*Step \d+:|$)'
        matches = re.finditer(pattern, response, re.DOTALL | re.IGNORECASE)

        for match in matches:
            step_num = int(match.group(1))
            title = match.group(2).strip()
            content = match.group(3).strip()

            # Extract conclusion (usually last sentence or paragraph)
            sentences = content.split('\n')
            conclusion = sentences[-1].strip() if sentences else content[:100]

            step = ReasoningStep(
                step_number=step_num,
                thought=content,
                conclusion=conclusion
            )
            steps.append(step)

        return steps

    @staticmethod
    def extract_key_decisions(response: str) -> Dict[str, str]:
        """
        Extract key decisions from reasoning chain

        Args:
            response: LLM response with reasoning

        Returns:
            Dictionary of decision types and rationales

        Example:
            {
                "probability_boost": "Set to 0.25 because...",
                "event_type": "Chose wing_breakthrough because...",
                "confidence": "0.75 due to..."
            }
        """
        decisions = {}

        # Look for common decision patterns
        patterns = {
            'probability_boost': r'(?:set\s+(?:the\s+)?probability\s+boost|probability\s+boost|boost)\s+(?:to\s+|at\s+)?([\d.]+).*?because\s*(.{20,150})',
            'event_type': r'(?:chose|selected|pick)\s*(\w+).*?because\s*(.{20,150})',
            'confidence': r'confidence.*?(?:is\s+)?(\d\.\d+).*?(?:due to|because)\s*(.{20,150})',
            'convergence': r'(?:converged|needs_adjustment).*?because\s*(.{20,150})'
        }

        for decision_type, pattern in patterns.items():
            match = re.search(pattern, response, re.IGNORECASE | re.DOTALL)
            if match:
                if decision_type == 'convergence':
                    decisions[decision_type] = match.group(1).strip()
                else:
                    value = match.group(1).strip() if match.lastindex >= 1 else "N/A"
                    rationale = match.group(2).strip() if match.lastindex >= 2 else "N/A"
                    decisions[decision_type] = f"{value}: {rationale[:100]}"

        return decisions

    @staticmethod
    def validate_reasoning_completeness(
        response: str,
        expected_steps: int = 5
    ) -> Tuple[bool, List[str]]:
        """
        Validate that reasoning chain is complete

        Args:
            response: LLM response
            expected_steps: Expected number of reasoning steps (default 5)

        Returns:
            (is_complete, missing_elements)

        Example:
            >>> is_valid, missing = validate_reasoning_completeness(response, 5)
            >>> if not is_valid:
            >>>     print(f"Missing: {missing}")
        """
        missing = []

        # Check for step-by-step structure
        steps = ReasoningChainParser.extract_reasoning_steps(response)
        if len(steps) < expected_steps:
            missing.append(f"Only {len(steps)}/{expected_steps} reasoning steps found")

        # Check for key reasoning elements
        required_elements = [
            ("context", r"(?:context|situation|background)", "Context analysis"),
            ("tactical", r"(?:tactical|strategy|style)", "Tactical analysis"),
            ("factors", r"(?:factors|key|decisive)", "Key factors identification"),
            ("justification", r"(?:because|due to|reason)", "Justification/reasoning"),
            ("conclusion", r"(?:conclusion|therefore|thus|final)", "Conclusion")
        ]

        for element_id, pattern, description in required_elements:
            if not re.search(pattern, response, re.IGNORECASE):
                missing.append(f"Missing {description}")

        is_complete = len(missing) == 0
        return is_complete, missing


# ==========================================================================
# Usage Examples
# ==========================================================================

def create_example_cot_prompts():
    """Create example CoT prompts for testing"""

    print("=" * 70)
    print("Chain-of-Thought Prompting Examples")
    print("=" * 70)

    # Example 1: Scenario generation with CoT
    print("\n1. Scenario Generation CoT Prompt")
    print("-" * 70)

    base_scenario_prompt = """
**Match Context:**
- Home: Manchester City (Attack: 92/100, Defense: 88/100)
- Away: Brighton (Attack: 75/100, Defense: 72/100)
- Styles: City (possession), Brighton (possession)

Generate a match scenario predicting key events and final score.
"""

    cot_scenario_prompt = CoTPromptTemplate.generate_scenario_cot_prompt(
        base_scenario_prompt,
        include_reasoning_structure=True
    )

    print(cot_scenario_prompt)
    print(f"\nPrompt length: {len(cot_scenario_prompt)} characters")

    # Example 2: Analysis with CoT
    print("\n2. Result Analysis CoT Prompt")
    print("-" * 70)

    base_analysis_prompt = """
**Original Scenario:**
- Predicted: Man City 3-0 Brighton
- Events: 5 events with various probability boosts

**Simulation Result:**
- Actual: Man City 2-1 Brighton
- Narrative Adherence: 45%

Analyze discrepancies and decide if adjustment needed.
"""

    cot_analysis_prompt = CoTPromptTemplate.generate_analysis_cot_prompt(
        base_analysis_prompt,
        include_reasoning_structure=True
    )

    print(cot_analysis_prompt[:500] + "...")
    print(f"\nPrompt length: {len(cot_analysis_prompt)} characters")


# ==========================================================================
# Testing
# ==========================================================================

def test_cot_prompting():
    """Test Chain-of-Thought prompting components"""
    print("=" * 70)
    print("Testing Chain-of-Thought Prompting")
    print("=" * 70)

    # Test 1: Scenario CoT prompt generation
    print("\nTest 1: Scenario CoT Prompt Generation")
    print("-" * 70)

    base = "Generate scenario for Arsenal vs Liverpool"
    cot_prompt = CoTPromptTemplate.generate_scenario_cot_prompt(base)

    assert "Let's approach this step by step" in cot_prompt
    assert "Step 1:" in cot_prompt
    assert "Context Analysis" in cot_prompt
    print(f"✅ Generated CoT prompt ({len(cot_prompt)} chars)")
    print("✅ Test 1 PASSED")

    # Test 2: Analysis CoT prompt generation
    print("\nTest 2: Analysis CoT Prompt Generation")
    print("-" * 70)

    base_analysis = "Analyze simulation result vs scenario"
    cot_analysis = CoTPromptTemplate.generate_analysis_cot_prompt(base_analysis)

    assert "Let's approach this step by step" in cot_analysis
    assert "Discrepancy Identification" in cot_analysis
    assert "Convergence Decision" in cot_analysis
    print(f"✅ Generated analysis CoT prompt ({len(cot_analysis)} chars)")
    print("✅ Test 2 PASSED")

    # Test 3: Reasoning chain extraction
    print("\nTest 3: Reasoning Chain Extraction")
    print("-" * 70)

    mock_response = """
**Step 1: Context Analysis**
Arsenal has 85/100 attack strength, Liverpool 88/100.
Both teams are in good form. Conclusion: Evenly matched.

**Step 2: Tactical Implications**
Arsenal's mixed style vs Liverpool's direct approach.
Midfield battle will be crucial. Conclusion: Advantage Liverpool on transitions.

**Step 3: Key Factors**
1. Liverpool's counter-attacking speed
2. Arsenal's home advantage
Conclusion: Narrow margin between teams.
"""

    steps = ReasoningChainParser.extract_reasoning_steps(mock_response)
    print(f"Extracted {len(steps)} reasoning steps:")
    for step in steps:
        print(f"  Step {step.step_number}: {step.conclusion[:50]}...")

    assert len(steps) == 3
    assert steps[0].step_number == 1
    print("✅ Test 3 PASSED")

    # Test 4: Key decisions extraction
    print("\nTest 4: Key Decisions Extraction")
    print("-" * 70)

    mock_decision_response = """
I set the probability boost to 0.25 because Man City's attack is significantly
stronger. I chose wing_breakthrough as the event type because Saka often exploits
that area. My confidence is 0.75 due to Arsenal's strong home record but Liverpool's
quality introduces uncertainty.
"""

    decisions = ReasoningChainParser.extract_key_decisions(mock_decision_response)
    print(f"Extracted {len(decisions)} key decisions:")
    for decision_type, rationale in decisions.items():
        print(f"  {decision_type}: {rationale[:60]}...")

    assert 'probability_boost' in decisions
    assert 'confidence' in decisions
    print("✅ Test 4 PASSED")

    # Test 5: Reasoning completeness validation
    print("\nTest 5: Reasoning Completeness Validation")
    print("-" * 70)

    complete_response = """
**Step 1: Context Analysis**
The context shows...

**Step 2: Tactical Implications**
Tactically, this means...

**Step 3: Key Factors**
The key factors are...

**Step 4: Event Prediction**
Because of these factors...

**Step 5: Final Conclusion**
Therefore, I conclude...
"""

    is_complete, missing = ReasoningChainParser.validate_reasoning_completeness(
        complete_response,
        expected_steps=5
    )

    print(f"Completeness: {is_complete}")
    if not is_complete:
        print(f"Missing elements: {missing}")
    else:
        print("All reasoning elements present")

    assert is_complete
    print("✅ Test 5 PASSED")

    # Test 6: Self-consistency prompt
    print("\nTest 6: Self-Consistency Prompt Generation")
    print("-" * 70)

    sc_prompt = CoTPromptTemplate.generate_self_consistency_prompt(
        "Predict match outcome",
        num_paths=3
    )

    assert "Path 1:" in sc_prompt
    assert "Path 2:" in sc_prompt
    assert "Path 3:" in sc_prompt
    print(f"✅ Generated self-consistency prompt ({len(sc_prompt)} chars)")
    print("✅ Test 6 PASSED")

    print("\n" + "=" * 70)
    print("✅ All CoT Prompting Tests PASSED!")
    print("=" * 70)


if __name__ == "__main__":
    # Run tests
    test_cot_prompting()

    print("\n\n")

    # Show examples
    create_example_cot_prompts()
