"""
Semantic Feature Encoder
Convert numerical features to semantic descriptions for better LLM understanding

Key benefits:
- Numerical reasoning → Semantic reasoning
- Domain context anchoring (85 = "매우 강함")
- Richer prompt context
- Better LLM comprehension
"""

from typing import Dict


class SemanticFeatureEncoder:
    """
    Convert numerical features to semantic descriptions

    Transforms raw numbers (e.g., attack_strength=85) into
    meaningful text (e.g., "매우 강함 - 상위권 팀, 유럽대회 진출권")
    """

    # Strength scales (0-100)
    STRENGTH_SCALE = {
        (90, 100): {
            'label': '월드클래스',
            'description': '리그 최상위권, 챔피언스리그 수준',
            'tactical_impact': '경기 지배력이 매우 높음'
        },
        (80, 90): {
            'label': '매우 강함',
            'description': '상위권 팀, 유럽대회 진출권',
            'tactical_impact': '대부분 경기에서 우위 점유'
        },
        (70, 80): {
            'label': '강함',
            'description': '중상위권 팀, 안정적 리그 위치',
            'tactical_impact': '일정한 경쟁력 보유'
        },
        (60, 70): {
            'label': '보통',
            'description': '중위권 팀, 잔류 안정적',
            'tactical_impact': '상대에 따라 부침 존재'
        },
        (0, 60): {
            'label': '약함',
            'description': '하위권 팀, 잔류 경쟁',
            'tactical_impact': '대부분 경기에서 열세'
        }
    }

    # Style descriptions
    STYLE_DESCRIPTIONS = {
        'possession': {
            'philosophy': '점유율 기반 빌드업',
            'characteristics': [
                '짧은 패스 위주의 볼 순환',
                '높은 라인과 압박',
                '중앙 밀집 수비 조직'
            ],
            'strengths': ['볼 지배력', '상대 체력 소진'],
            'weaknesses': ['역습 취약', '돌파 의존도']
        },
        'direct': {
            'philosophy': '빠른 전진과 직접 플레이',
            'characteristics': [
                '긴 볼과 사이드 공격',
                '신속한 전환',
                '피지컬 우위 활용'
            ],
            'strengths': ['역습 위협', '효율적 득점'],
            'weaknesses': ['볼 지배력 부족', '체력 소모']
        },
        'mixed': {
            'philosophy': '상황 적응형 전술',
            'characteristics': [
                '상대와 상황에 따른 조정',
                '다양한 공격 루트',
                '균형잡힌 수비 조직'
            ],
            'strengths': ['전술 유연성', '예측 어려움'],
            'weaknesses': ['명확한 정체성 부족']
        }
    }

    def encode_team_strength(
        self,
        attack: float,
        defense: float,
        press: float,
        style: str
    ) -> str:
        """
        Convert numerical strengths to semantic description

        Args:
            attack: Attack strength (0-100)
            defense: Defense strength (0-100)
            press: Press intensity (0-100)
            style: Buildup style ('possession', 'direct', 'mixed')

        Returns:
            Formatted semantic description

        Example:
            >>> encoder = SemanticFeatureEncoder()
            >>> desc = encoder.encode_team_strength(85, 80, 75, 'possession')
            >>> print(desc)
            ## 팀 전력 프로필
            ### 공격력: 85.0/100 - 매우 강함
            ...
        """
        attack_desc = self._get_strength_description(attack)
        defense_desc = self._get_strength_description(defense)
        press_desc = self._get_strength_description(press)
        style_desc = self.STYLE_DESCRIPTIONS.get(style, self.STYLE_DESCRIPTIONS['mixed'])

        return f"""
## 팀 전력 프로필

### 공격력: {attack:.1f}/100 - {attack_desc['label']}
{attack_desc['description']}
전술적 의미: {attack_desc['tactical_impact']}

### 수비력: {defense:.1f}/100 - {defense_desc['label']}
{defense_desc['description']}
전술적 의미: {defense_desc['tactical_impact']}

### 압박 강도: {press:.1f}/100 - {press_desc['label']}
{press_desc['description']}
전술적 의미: {press_desc['tactical_impact']}

### 빌드업 스타일: {style_desc['philosophy']}
**특징:**
{chr(10).join('- ' + c for c in style_desc['characteristics'])}

**강점:** {', '.join(style_desc['strengths'])}
**약점:** {', '.join(style_desc['weaknesses'])}
"""

    def _get_strength_description(self, value: float) -> Dict[str, str]:
        """
        Get semantic description for strength value

        Args:
            value: Strength value (0-100)

        Returns:
            Dictionary with label, description, tactical_impact
        """
        for (low, high), desc in self.STRENGTH_SCALE.items():
            if low <= value < high:
                return desc
        return self.STRENGTH_SCALE[(0, 60)]  # Default to weakest

    def encode_match_context(
        self,
        home_strength: float,
        away_strength: float,
        venue: str = "Home",
        importance: str = "regular"
    ) -> str:
        """
        Encode match context semantically

        Args:
            home_strength: Average home team strength
            away_strength: Average away team strength
            venue: Match venue
            importance: Match importance level

        Returns:
            Formatted match context description

        Example:
            >>> encoder = SemanticFeatureEncoder()
            >>> context = encoder.encode_match_context(85, 70, "Home", "regular")
            >>> print(context)
            ## 경기 맥락
            **매치 성격:** 전력 우위가 있는 대결
            ...
        """
        strength_diff = abs(home_strength - away_strength)

        if strength_diff > 20:
            match_type = "명백한 전력 차이가 있는 대결"
            expectation = "강팀의 압도적 우세 예상"
        elif strength_diff > 10:
            match_type = "전력 우위가 있는 대결"
            expectation = "우세팀의 승리 가능성 높음"
        else:
            match_type = "박빙의 대결"
            expectation = "결과 예측이 어려운 접전 예상"

        importance_context = {
            'regular': '일반 리그 경기',
            'top_clash': '상위권 직접 대결',
            'derby': '라이벌 더비 매치',
            'relegation': '잔류 사활 대결'
        }.get(importance, '일반 리그 경기')

        return f"""
## 경기 맥락

**매치 성격:** {match_type}
**경기 중요도:** {importance_context}
**예상 전개:** {expectation}
**홈 어드밴티지:** {venue} - 홈팀 심리적/전술적 이점 존재
"""

    def encode_form_trend(self, recent_form: str) -> str:
        """
        Encode recent form string to semantic description

        Args:
            recent_form: Recent form string (e.g., "WWDWL")

        Returns:
            Semantic description of form

        Example:
            >>> encoder = SemanticFeatureEncoder()
            >>> desc = encoder.encode_form_trend("WWDWL")
            >>> print(desc)
            최근 5경기: 3승 1무 1패 (승점 10/15)
            ...
        """
        if not recent_form:
            return "최근 폼 데이터 없음"

        wins = recent_form.count('W')
        draws = recent_form.count('D')
        losses = recent_form.count('L')
        total = len(recent_form)
        points = wins * 3 + draws

        # Form quality assessment
        if wins >= 4:
            quality = "매우 좋음 🔥"
        elif wins >= 3:
            quality = "좋음 ⬆️"
        elif wins >= 2:
            quality = "보통 ➡️"
        elif wins >= 1:
            quality = "나쁨 ⬇️"
        else:
            quality = "매우 나쁨 ❄️"

        return f"""최근 {total}경기: {wins}승 {draws}무 {losses}패 (승점 {points}/{total*3})
폼 상태: {quality}"""


# ==========================================================================
# Testing
# ==========================================================================

def test_semantic_encoder():
    """Test Semantic Feature Encoder"""
    print("=" * 70)
    print("Testing Semantic Feature Encoder")
    print("=" * 70)

    encoder = SemanticFeatureEncoder()

    # Test 1: Strong team encoding
    print("\nTest 1: Strong Team (Man City profile)")
    print("-" * 70)
    desc = encoder.encode_team_strength(
        attack=92,
        defense=88,
        press=85,
        style='possession'
    )
    print(desc)
    assert '월드클래스' in desc
    assert '점유율 기반' in desc
    print("✅ Test 1 PASSED")

    # Test 2: Weak team encoding
    print("\nTest 2: Weak Team (Relegation candidate profile)")
    print("-" * 70)
    desc = encoder.encode_team_strength(
        attack=55,
        defense=58,
        press=52,
        style='direct'
    )
    print(desc)
    assert '약함' in desc
    assert '빠른 전진' in desc
    print("✅ Test 2 PASSED")

    # Test 3: Match context - Big gap
    print("\nTest 3: Match Context - Big Strength Gap")
    print("-" * 70)
    context = encoder.encode_match_context(
        home_strength=90,
        away_strength=60,
        venue="Home",
        importance="regular"
    )
    print(context)
    assert '명백한 전력 차이' in context
    assert '압도적 우세' in context
    print("✅ Test 3 PASSED")

    # Test 4: Match context - Even match
    print("\nTest 4: Match Context - Even Match")
    print("-" * 70)
    context = encoder.encode_match_context(
        home_strength=82,
        away_strength=81,
        venue="Home",
        importance="top_clash"
    )
    print(context)
    assert '박빙의 대결' in context
    assert '상위권 직접 대결' in context
    print("✅ Test 4 PASSED")

    # Test 5: Form encoding
    print("\nTest 5: Form Encoding")
    print("-" * 70)
    good_form = encoder.encode_form_trend("WWWDW")
    print(f"Good form: {good_form}")
    assert "4승" in good_form
    assert "매우 좋음" in good_form

    bad_form = encoder.encode_form_trend("LLLWD")
    print(f"Bad form: {bad_form}")
    assert "1승" in bad_form
    print("✅ Test 5 PASSED")

    print("\n" + "=" * 70)
    print("✅ All Semantic Encoder Tests PASSED!")
    print("=" * 70)


if __name__ == "__main__":
    test_semantic_encoder()
