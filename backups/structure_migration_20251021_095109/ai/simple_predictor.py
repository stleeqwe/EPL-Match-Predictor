#!/usr/bin/env python3
"""
Simple AI Match Predictor
Uses Claude Haiku for fast, basic match predictions

Version: 1.0 (Haiku)
"""

import os
import json
from typing import Dict, Optional
from anthropic import Anthropic
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class SimpleAIPredictor:
    """
    Simple AI-powered match predictor using Claude Haiku

    Features:
    - Fast predictions (3-5 seconds)
    - Low cost ($0.004 per prediction)
    - Basic tactical analysis
    - User evaluation integration
    """

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the predictor"""
        self.api_key = api_key or os.getenv('CLAUDE_API_KEY')

        if not self.api_key:
            raise ValueError("CLAUDE_API_KEY not found")

        self.client = Anthropic(api_key=self.api_key)
        self.model = "claude-3-haiku-20240307"
        self.max_tokens = 2500  # 더 깊이 있는 분석을 위해 증가

    def predict(
        self,
        home_team: str,
        away_team: str,
        user_evaluation: Dict,
        sharp_odds: Optional[Dict] = None,
        recent_form: Optional[Dict] = None
    ) -> Dict:
        """
        Predict match outcome

        Args:
            home_team: Home team name
            away_team: Away team name
            user_evaluation: User's team ratings and analysis
            sharp_odds: Optional Sharp bookmaker odds
            recent_form: Optional recent form data

        Returns:
            Prediction with probabilities, score, and reasoning
        """

        # Build prompt
        prompt = self._build_prompt(
            home_team,
            away_team,
            user_evaluation,
            sharp_odds,
            recent_form
        )

        # Call Claude API
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=0.5,  # 더 일관성 있는 전술적 분석을 위해 낮춤
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            # Parse response
            response_text = message.content[0].text
            result = self._parse_response(response_text)

            # Add metadata
            result['metadata'] = {
                'model': self.model,
                'tokens_used': {
                    'input': message.usage.input_tokens,
                    'output': message.usage.output_tokens,
                    'total': message.usage.input_tokens + message.usage.output_tokens
                },
                'cost_usd': self._calculate_cost(message.usage.input_tokens, message.usage.output_tokens)
            }

            return result

        except Exception as e:
            return {
                'error': str(e),
                'success': False
            }

    def _build_prompt(
        self,
        home_team: str,
        away_team: str,
        user_evaluation: Dict,
        sharp_odds: Optional[Dict],
        recent_form: Optional[Dict]
    ) -> str:
        """Build the prediction prompt"""

        prompt = f"""당신은 EPL(프리미어리그) 전문 전술 분석가이자 축구 통계 전문가입니다.
프로 수준의 깊이 있는 경기 분석을 제공해야 합니다.

## 🏆 경기 정보
**{home_team}** (홈) vs **{away_team}** (원정)

## 📊 팀 평가 데이터 (가중치: 65%)

### {home_team} (홈팀)
- **종합 평가**: {user_evaluation.get('home_overall', 'N/A')}/100점
- **선수 개인 능력**: {user_evaluation.get('home_player_score', 'N/A')}/100점
- **팀 조직력/전력**: {user_evaluation.get('home_strength_score', 'N/A')}/100점
- **평가 코멘트**: {user_evaluation.get('home_comments', '평가 없음')}

### {away_team} (원정팀)
- **종합 평가**: {user_evaluation.get('away_overall', 'N/A')}/100점
- **선수 개인 능력**: {user_evaluation.get('away_player_score', 'N/A')}/100점
- **팀 조직력/전력**: {user_evaluation.get('away_strength_score', 'N/A')}/100점
- **평가 코멘트**: {user_evaluation.get('away_comments', '평가 없음')}
"""

        # Add Sharp odds if available
        if sharp_odds:
            prompt += f"""
## Sharp 북메이커 배당 (가중치: 20%)
- 홈 승: {sharp_odds.get('home', 'N/A')}
- 무승부: {sharp_odds.get('draw', 'N/A')}
- 원정 승: {sharp_odds.get('away', 'N/A')}
"""

        # Add recent form if available
        if recent_form:
            prompt += f"""
## 최근 폼 (가중치: 15%)
**{home_team}**: {recent_form.get('home_form', 'N/A')} (최근 5경기)
**{away_team}**: {recent_form.get('away_form', 'N/A')} (최근 5경기)
"""

        prompt += """
## 📋 분석 프레임워크

다음 요소들을 **반드시** 고려하여 깊이 있는 분석을 수행하세요:

### 1. 전술적 분석
- 양 팀의 플레이 스타일 (점유율 축구 vs 역습, 하이 프레스 vs 로우 블록 등)
- 포메이션 매치업과 전술적 우위
- 중원 지배력과 측면 공격 능력
- 세트피스 위협도

### 2. 팀 전력 비교 ⚠️ **매우 중요**
**점수 차이를 정확히 반영하세요!**

- 종합 점수 차이가 **10점 이상**이면 압도적 우위 → xG 차이 1.5+ 이상
- 종합 점수 차이가 **20점 이상**이면 완전한 우위 → xG 차이 2.5+ 이상
- 종합 점수 차이가 **30점 이상**이면 격차 경기 → xG 차이 3.0+ 이상

**점수 차이별 예상 스코어:**
- 10점 차: 2-0, 2-1 수준
- 20점 차: 3-0, 3-1 수준
- 30점 차: 4-0, 4-1, 5-1 수준

공격 화력, 수비 안정성, 중원 컨트롤을 모두 고려하되,
**점수 차이가 크면 클수록 골 차이도 크게 벌어져야 합니다.**

### 3. 핵심 매치업
- 양 팀의 핵심 선수 대결 (공격수 vs 수비수, 미드필더 대결)
- 각 팀의 X-Factor 선수 영향력
- 약점 노출 지점과 상대의 활용 가능성

### 4. 상황적 요인
- **홈 어드밴티지**: 홈팀은 심리적, 환경적 이점 (+3~5% 승률)
- 최근 경기력과 자신감
- 팀 간 역사적 전적과 심리전

### 5. 시나리오 분석
- 가장 가능성 높은 시나리오 (3가지)
- 각 시나리오의 발생 조건
- 예상 골 패턴 (초반/중반/후반 득점 시점)

---

## 🎯 출력 형식

위 분석을 바탕으로 다음 JSON 형식으로 **전문적이고 상세한** 예측을 제공하세요:

{
  "predicted_score": "2-1",
  "probabilities": {
    "home_win": 0.45,
    "draw": 0.28,
    "away_win": 0.27
  },
  "confidence": "보통",
  "confidence_score": 62,
  "reasoning": "**3-5문장**의 깊이 있는 전술적 분석. 단순히 점수가 높다/낮다가 아니라, WHY(왜 그렇게 예측하는가)에 집중하세요. 예: '홈팀의 하이 프레싱이 원정팀의 빌드업을 교란할 것으로 예상되며, 특히 중원에서의 수적 우위를 바탕으로 측면 공격을 활성화할 것입니다. 원정팀은 역습에 의존할 것이나, 홈팀 수비진의 빠른 복귀로 기회가 제한될 전망입니다.'",
  "key_factors": [
    "구체적이고 전술적인 요인 1 (예: 홈팀 윙어의 1대1 돌파력이 원정팀 풀백의 약점을 공략)",
    "구체적이고 전술적인 요인 2 (예: 중원에서의 피지컬 우위로 세컨드 볼 장악)",
    "구체적이고 전술적인 요인 3 (예: 원정팀 주전 공격수 부재로 득점력 30% 감소 예상)",
    "추가 요인 4 (선택사항, 있다면 추가)"
  ],
  "expected_goals": {
    "home": 1.8,
    "away": 1.2
  }
}

---

## ⚠️ 필수 요구사항

1. **JSON만 출력** (다른 텍스트 없이)
2. **확률 합계 = 1.0** (정확히)
3. **confidence**: "낮음", "보통", "높음" 중 하나
4. **confidence_score**: 0-100 사이 정수
5. **reasoning**: 최소 3문장, 전술적 깊이 필수
6. **key_factors**: 3-4개, 구체적이고 실전적인 요인
7. **한글 작성** (reasoning, key_factors)
8. **홈 어드밴티지 반영** (홈팀 +3~7점 보정)
9. **사용자 평가 우선** (65% 가중치)

---

## 💡 분석 예시 (참고용)

### 예시 1: 비슷한 실력 (85점 vs 82점, 3점 차)
**Expected Goals**: 2.1 - 1.4 (0.7골 차)
**Predicted Score**: 2-1
**Reasoning**: "양 팀의 전력이 비슷하지만, 홈팀이 약간의 우위를 점하고 있습니다. 특히 중원에서의 볼 소유율 싸움이 치열할 것으로 예상되며..."

### 예시 2: 중간 격차 (78점 vs 58점, 20점 차)
**Expected Goals**: 2.8 - 0.9 (1.9골 차)
**Predicted Score**: 3-1
**Reasoning**: "홈팀의 압도적인 전력 차이가 경기 전반에 걸쳐 드러날 것입니다. 특히 개인 기량 차이가 측면 공격에서 두드러질 것으로 보이며, 원정팀의 수비 조직력으로는 홈팀의 다양한 공격루트를 모두 막기 어려울 전망입니다..."

### 예시 3: 큰 격차 (60점 vs 26점, 34점 차) ⚠️ **당신의 케이스**
**Expected Goals**: 3.5 - 0.8 (2.7골 차)
**Predicted Score**: 4-1 또는 3-0
**Reasoning**: "홈팀과 원정팀 사이의 전력 차이가 매우 큽니다. 34점이라는 격차는 상위권과 강등권 팀의 대결에 해당하며, 홈팀이 경기를 지배할 것으로 확실시됩니다. 원정팀은 극도로 수비적인 전술로 실점을 최소화하려 할 것이나, 홈팀의 압박과 개인 능력 차이로 인해 반복적으로 위기 상황에 노출될 것입니다. 원정팀의 유일한 희망은 역습과 세트피스뿐이며, 현실적으로 1골 이상 넣기 어려울 전망입니다. 반면 홈팀은 3-4골 이상 득점할 가능성이 높습니다."

**나쁜 예시**:
"홈팀이 점수가 높아서 이길 것 같습니다." ❌
"1.8 vs 1.2 골" (34점 차이에 0.6골 차이는 비현실적) ❌

---

⚠️ **필수**: 점수 차이가 크면 Expected Goals 차이도 **반드시** 크게 벌어져야 합니다!

이제 위의 모든 지침을 따라 **프로 수준의 깊이 있는 분석**을 제공하세요.
"""

        return prompt

    def _parse_response(self, response_text: str) -> Dict:
        """Parse Claude's JSON response"""

        try:
            # Try to find JSON in response
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1

            if start_idx == -1 or end_idx == 0:
                raise ValueError("No JSON found in response")

            json_str = response_text[start_idx:end_idx]
            result = json.loads(json_str)

            # Validate structure
            required_keys = ['predicted_score', 'probabilities', 'confidence', 'reasoning']
            for key in required_keys:
                if key not in result:
                    raise ValueError(f"Missing required key: {key}")

            result['success'] = True
            return result

        except Exception as e:
            # Fallback parsing
            return {
                'success': False,
                'error': f"Failed to parse response: {str(e)}",
                'raw_response': response_text
            }

    def _calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate API call cost in USD"""

        # Haiku pricing (per 1M tokens)
        input_cost_per_1m = 0.25
        output_cost_per_1m = 1.25

        input_cost = (input_tokens / 1_000_000) * input_cost_per_1m
        output_cost = (output_tokens / 1_000_000) * output_cost_per_1m

        return round(input_cost + output_cost, 6)


def test_predictor():
    """Test the predictor with sample data"""

    print("=" * 70)
    print("Simple AI Predictor Test")
    print("=" * 70)
    print()

    predictor = SimpleAIPredictor()

    # Sample user evaluation
    user_evaluation = {
        'home_overall': 85.5,
        'home_player_score': 88.0,
        'home_strength_score': 82.0,
        'home_comments': 'Strong attacking team with excellent midfield control. High pressing style.',

        'away_overall': 78.2,
        'away_player_score': 76.0,
        'away_strength_score': 80.5,
        'away_comments': 'Solid defensive setup but lacking creativity in attack. Counter-attack focused.'
    }

    # Sample sharp odds
    sharp_odds = {
        'home': 1.85,
        'draw': 3.40,
        'away': 4.20
    }

    # Sample form
    recent_form = {
        'home_form': 'W-W-D-W-W',
        'away_form': 'L-D-W-L-D'
    }

    print("🧪 Testing prediction...")
    print(f"Match: Liverpool vs Manchester United")
    print()

    result = predictor.predict(
        home_team="Liverpool",
        away_team="Manchester United",
        user_evaluation=user_evaluation,
        sharp_odds=sharp_odds,
        recent_form=recent_form
    )

    if result.get('success'):
        print("✅ Prediction successful!")
        print()
        print(f"📊 Predicted Score: {result['predicted_score']}")
        print()
        print("📈 Win Probabilities:")
        probs = result['probabilities']
        print(f"   Home Win: {probs['home_win']*100:.1f}%")
        print(f"   Draw:     {probs['draw']*100:.1f}%")
        print(f"   Away Win: {probs['away_win']*100:.1f}%")
        print()
        print(f"🎯 Confidence: {result['confidence'].upper()} ({result.get('confidence_score', 0)}/100)")
        print()
        print("💡 Reasoning:")
        print(f"   {result['reasoning']}")
        print()
        print("🔑 Key Factors:")
        for factor in result.get('key_factors', []):
            print(f"   • {factor}")
        print()

        if 'expected_goals' in result:
            xg = result['expected_goals']
            print(f"⚽ Expected Goals: {xg['home']:.1f} - {xg['away']:.1f}")
            print()

        # Metadata
        meta = result['metadata']
        print("📊 Metadata:")
        print(f"   Model: {meta['model']}")
        print(f"   Tokens: {meta['tokens_used']['total']:,} ({meta['tokens_used']['input']:,} in + {meta['tokens_used']['output']:,} out)")
        print(f"   Cost: ${meta['cost_usd']:.6f}")
        print()

    else:
        print("❌ Prediction failed!")
        print(f"Error: {result.get('error', 'Unknown error')}")
        if 'raw_response' in result:
            print()
            print("Raw response:")
            print(result['raw_response'][:500])

    print("=" * 70)


if __name__ == "__main__":
    test_predictor()
