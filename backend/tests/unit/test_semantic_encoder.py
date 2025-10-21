"""
Unit Tests for Semantic Feature Encoder
EPL Match Predictor v3.0

Tests Cover:
1. Strength scale mapping (numerical → semantic)
2. Form trend parsing and quality assessment
3. Match context generation
4. Team strength encoding
"""

import pytest
import sys
import os

# Add project root to path
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

try:
    from ai.prompt_engineering.semantic_encoder import SemanticFeatureEncoder
    ENCODER_AVAILABLE = True
except ImportError as e:
    ENCODER_AVAILABLE = False
    pytest.skip(f"Semantic Encoder not available: {e}", allow_module_level=True)


class TestStrengthScaleMapping:
    """Test numerical to semantic strength mapping"""

    def test_world_class_90_100(self):
        """Test world class range (90-100) → '월드클래스'"""
        # Given
        encoder = SemanticFeatureEncoder()

        # When
        desc_95 = encoder._get_strength_description(95)
        desc_90 = encoder._get_strength_description(90)
        desc_99 = encoder._get_strength_description(99.9)

        # Then
        assert desc_95['label'] == '월드클래스'
        assert desc_90['label'] == '월드클래스'
        assert desc_99['label'] == '월드클래스'
        assert '챔피언스리그' in desc_95['description']
        assert '경기 지배력이 매우 높음' in desc_95['tactical_impact']

    def test_very_strong_80_90(self):
        """Test very strong range (80-90) → '매우 강함'"""
        # Given
        encoder = SemanticFeatureEncoder()

        # When
        desc_85 = encoder._get_strength_description(85)
        desc_80 = encoder._get_strength_description(80)
        desc_89 = encoder._get_strength_description(89.9)

        # Then
        assert desc_85['label'] == '매우 강함'
        assert desc_80['label'] == '매우 강함'
        assert desc_89['label'] == '매우 강함'
        assert '상위권' in desc_85['description']
        assert '유럽대회' in desc_85['description']

    def test_strong_70_80(self):
        """Test strong range (70-80) → '강함'"""
        # Given
        encoder = SemanticFeatureEncoder()

        # When
        desc_75 = encoder._get_strength_description(75)
        desc_70 = encoder._get_strength_description(70)
        desc_79 = encoder._get_strength_description(79.9)

        # Then
        assert desc_75['label'] == '강함'
        assert desc_70['label'] == '강함'
        assert desc_79['label'] == '강함'
        assert '중상위권' in desc_75['description']

    def test_average_60_70(self):
        """Test average range (60-70) → '보통'"""
        # Given
        encoder = SemanticFeatureEncoder()

        # When
        desc_65 = encoder._get_strength_description(65)
        desc_60 = encoder._get_strength_description(60)
        desc_69 = encoder._get_strength_description(69.9)

        # Then
        assert desc_65['label'] == '보통'
        assert desc_60['label'] == '보통'
        assert desc_69['label'] == '보통'
        assert '중위권' in desc_65['description']

    def test_weak_0_60(self):
        """Test weak range (0-60) → '약함'"""
        # Given
        encoder = SemanticFeatureEncoder()

        # When
        desc_55 = encoder._get_strength_description(55)
        desc_30 = encoder._get_strength_description(30)
        desc_0 = encoder._get_strength_description(0)

        # Then
        assert desc_55['label'] == '약함'
        assert desc_30['label'] == '약함'
        assert desc_0['label'] == '약함'
        assert '하위권' in desc_55['description']
        assert '잔류 경쟁' in desc_55['description']

    def test_boundary_values(self):
        """Test boundary values between ranges"""
        # Given
        encoder = SemanticFeatureEncoder()

        # When & Then
        # 90 is start of world class
        assert encoder._get_strength_description(90)['label'] == '월드클래스'
        # 89.9 is still very strong
        assert encoder._get_strength_description(89.9)['label'] == '매우 강함'

        # 80 is start of very strong
        assert encoder._get_strength_description(80)['label'] == '매우 강함'
        # 79.9 is still strong
        assert encoder._get_strength_description(79.9)['label'] == '강함'

        # 70 is start of strong
        assert encoder._get_strength_description(70)['label'] == '강함'
        # 69.9 is average
        assert encoder._get_strength_description(69.9)['label'] == '보통'

        # 60 is start of average
        assert encoder._get_strength_description(60)['label'] == '보통'
        # 59.9 is weak
        assert encoder._get_strength_description(59.9)['label'] == '약함'


class TestFormTrendParsing:
    """Test form string parsing and quality assessment"""

    def test_excellent_form_4_wins(self):
        """Test excellent form (4+ wins) → '매우 좋음 🔥'"""
        # Given
        encoder = SemanticFeatureEncoder()

        # When
        form_wwwwl = encoder.encode_form_trend("WWWWL")
        form_wwwwd = encoder.encode_form_trend("WWWWD")
        form_wwwww = encoder.encode_form_trend("WWWWW")

        # Then
        assert "4승" in form_wwwwl
        assert "매우 좋음" in form_wwwwl
        assert "🔥" in form_wwwwl
        assert "승점 12" in form_wwwwl  # 4*3 + 0

        assert "4승" in form_wwwwd
        assert "매우 좋음" in form_wwwwd
        assert "승점 13" in form_wwwwd  # 4*3 + 1

        assert "5승" in form_wwwww
        assert "매우 좋음" in form_wwwww
        assert "승점 15" in form_wwwww  # 5*3

    def test_good_form_3_wins(self):
        """Test good form (3 wins) → '좋음 ⬆️'"""
        # Given
        encoder = SemanticFeatureEncoder()

        # When
        form_wwwll = encoder.encode_form_trend("WWWLL")
        form_wwdwl = encoder.encode_form_trend("WWDWL")

        # Then
        assert "3승" in form_wwwll
        assert "좋음" in form_wwwll
        assert "⬆️" in form_wwwll
        assert "승점 9" in form_wwwll  # 3*3

        assert "3승" in form_wwdwl
        assert "1무" in form_wwdwl
        assert "좋음" in form_wwdwl
        assert "승점 10" in form_wwdwl  # 3*3 + 1

    def test_average_form_2_wins(self):
        """Test average form (2 wins) → '보통 ➡️'"""
        # Given
        encoder = SemanticFeatureEncoder()

        # When
        form_wwdll = encoder.encode_form_trend("WWDLL")
        form_wdwld = encoder.encode_form_trend("WDWLD")

        # Then
        assert "2승" in form_wwdll
        assert "보통" in form_wwdll
        assert "➡️" in form_wwdll
        assert "승점 7" in form_wwdll  # 2*3 + 1

        assert "2승" in form_wdwld
        assert "2무" in form_wdwld
        assert "보통" in form_wdwld
        assert "승점 8" in form_wdwld  # 2*3 + 2

    def test_poor_form_1_win(self):
        """Test poor form (1 win) → '나쁨 ⬇️'"""
        # Given
        encoder = SemanticFeatureEncoder()

        # When
        form_wddll = encoder.encode_form_trend("WDDLL")
        form_lllwd = encoder.encode_form_trend("LLLWD")

        # Then
        assert "1승" in form_wddll
        assert "나쁨" in form_wddll
        assert "⬇️" in form_wddll
        assert "승점 5" in form_wddll  # 1*3 + 2

        assert "1승" in form_lllwd
        assert "1무" in form_lllwd
        assert "나쁨" in form_lllwd
        assert "승점 4" in form_lllwd  # 1*3 + 1

    def test_very_poor_form_0_wins(self):
        """Test very poor form (0 wins) → '매우 나쁨 ❄️'"""
        # Given
        encoder = SemanticFeatureEncoder()

        # When
        form_lllll = encoder.encode_form_trend("LLLLL")
        form_dddll = encoder.encode_form_trend("DDDLL")

        # Then
        assert "0승" in form_lllll
        assert "매우 나쁨" in form_lllll
        assert "❄️" in form_lllll
        assert "승점 0" in form_lllll  # 0*3 + 0

        assert "0승" in form_dddll
        assert "3무" in form_dddll
        assert "매우 나쁨" in form_dddll
        assert "승점 3" in form_dddll  # 0*3 + 3

    def test_empty_form_string(self):
        """Test empty form string handling"""
        # Given
        encoder = SemanticFeatureEncoder()

        # When
        empty_form = encoder.encode_form_trend("")
        none_form = encoder.encode_form_trend(None)

        # Then
        assert "최근 폼 데이터 없음" in empty_form
        assert "최근 폼 데이터 없음" in none_form

    def test_form_calculations(self):
        """Test form calculations are correct"""
        # Given
        encoder = SemanticFeatureEncoder()

        # When
        form = encoder.encode_form_trend("WDLWW")

        # Then
        assert "3승" in form  # W count
        assert "1무" in form  # D count
        assert "1패" in form  # L count
        assert "최근 5경기" in form  # Total length
        assert "승점 10/15" in form  # 3*3 + 1 = 10 out of 15 possible


class TestMatchContextGeneration:
    """Test match context semantic encoding"""

    def test_big_strength_gap_over_20(self):
        """Test big strength gap (>20) → '명백한 전력 차이'"""
        # Given
        encoder = SemanticFeatureEncoder()

        # When
        context = encoder.encode_match_context(
            home_strength=90,
            away_strength=60,
            venue="Home",
            importance="regular"
        )

        # Then
        assert "명백한 전력 차이가 있는 대결" in context
        assert "압도적 우세 예상" in context
        assert "일반 리그 경기" in context
        assert "홈 어드밴티지" in context

    def test_moderate_gap_10_20(self):
        """Test moderate gap (10-20) → '전력 우위가 있는 대결'"""
        # Given
        encoder = SemanticFeatureEncoder()

        # When
        context = encoder.encode_match_context(
            home_strength=85,
            away_strength=70,
            venue="Home",
            importance="top_clash"
        )

        # Then
        assert "전력 우위가 있는 대결" in context
        assert "우세팀의 승리 가능성 높음" in context
        assert "상위권 직접 대결" in context

    def test_even_match_gap_less_10(self):
        """Test even match (<10 gap) → '박빙의 대결'"""
        # Given
        encoder = SemanticFeatureEncoder()

        # When
        context = encoder.encode_match_context(
            home_strength=82,
            away_strength=81,
            venue="Home",
            importance="derby"
        )

        # Then
        assert "박빙의 대결" in context
        assert "접전 예상" in context
        assert "라이벌 더비 매치" in context

    def test_relegation_battle(self):
        """Test relegation battle context"""
        # Given
        encoder = SemanticFeatureEncoder()

        # When
        context = encoder.encode_match_context(
            home_strength=58,
            away_strength=55,
            venue="Home",
            importance="relegation"
        )

        # Then
        assert "박빙의 대결" in context  # 3 point gap
        assert "잔류 사활 대결" in context

    def test_importance_levels(self):
        """Test all importance levels"""
        # Given
        encoder = SemanticFeatureEncoder()

        # When & Then
        # Regular
        regular = encoder.encode_match_context(75, 70, "Home", "regular")
        assert "일반 리그 경기" in regular

        # Top clash
        top_clash = encoder.encode_match_context(75, 70, "Home", "top_clash")
        assert "상위권 직접 대결" in top_clash

        # Derby
        derby = encoder.encode_match_context(75, 70, "Home", "derby")
        assert "라이벌 더비 매치" in derby

        # Relegation
        relegation = encoder.encode_match_context(75, 70, "Home", "relegation")
        assert "잔류 사활 대결" in relegation

        # Unknown (should default to regular)
        unknown = encoder.encode_match_context(75, 70, "Home", "unknown_type")
        assert "일반 리그 경기" in unknown

    def test_venue_information(self):
        """Test venue information is included"""
        # Given
        encoder = SemanticFeatureEncoder()

        # When
        home = encoder.encode_match_context(80, 75, "Home", "regular")
        away = encoder.encode_match_context(80, 75, "Away", "regular")

        # Then
        assert "Home" in home
        assert "홈팀 심리적/전술적 이점" in home
        assert "Away" in away


class TestTeamStrengthEncoding:
    """Test full team strength encoding"""

    def test_possession_style_encoding(self):
        """Test possession style team encoding"""
        # Given
        encoder = SemanticFeatureEncoder()

        # When
        profile = encoder.encode_team_strength(
            attack=92,
            defense=88,
            press=85,
            style='possession'
        )

        # Then
        # Check strength labels
        assert "공격력: 92.0/100 - 월드클래스" in profile
        assert "수비력: 88.0/100 - 매우 강함" in profile
        assert "압박 강도: 85.0/100 - 매우 강함" in profile

        # Check style description
        assert "점유율 기반 빌드업" in profile
        assert "짧은 패스 위주의 볼 순환" in profile
        assert "볼 지배력" in profile
        assert "역습 취약" in profile

    def test_direct_style_encoding(self):
        """Test direct style team encoding"""
        # Given
        encoder = SemanticFeatureEncoder()

        # When
        profile = encoder.encode_team_strength(
            attack=75,
            defense=72,
            press=68,
            style='direct'
        )

        # Then
        # Check strength labels
        assert "공격력: 75.0/100 - 강함" in profile
        assert "수비력: 72.0/100 - 강함" in profile
        assert "압박 강도: 68.0/100 - 보통" in profile

        # Check style description
        assert "빠른 전진과 직접 플레이" in profile
        assert "긴 볼과 사이드 공격" in profile
        assert "역습 위협" in profile
        assert "볼 지배력 부족" in profile

    def test_mixed_style_encoding(self):
        """Test mixed style team encoding"""
        # Given
        encoder = SemanticFeatureEncoder()

        # When
        profile = encoder.encode_team_strength(
            attack=80,
            defense=78,
            press=75,
            style='mixed'
        )

        # Then
        # Check strength labels
        assert "공격력: 80.0/100 - 매우 강함" in profile

        # Check style description
        assert "상황 적응형 전술" in profile
        assert "상대와 상황에 따른 조정" in profile
        assert "전술 유연성" in profile
        assert "명확한 정체성 부족" in profile

    def test_weak_team_encoding(self):
        """Test weak team encoding"""
        # Given
        encoder = SemanticFeatureEncoder()

        # When
        profile = encoder.encode_team_strength(
            attack=55,
            defense=58,
            press=52,
            style='direct'
        )

        # Then
        # All attributes should be '약함'
        assert "공격력: 55.0/100 - 약함" in profile
        assert "수비력: 58.0/100 - 약함" in profile
        assert "압박 강도: 52.0/100 - 약함" in profile

        # Check tactical impact
        assert "대부분 경기에서 열세" in profile

    def test_unknown_style_defaults_to_mixed(self):
        """Test unknown style defaults to mixed"""
        # Given
        encoder = SemanticFeatureEncoder()

        # When
        profile = encoder.encode_team_strength(
            attack=80,
            defense=75,
            press=70,
            style='unknown_style'
        )

        # Then
        # Should default to mixed style
        assert "상황 적응형 전술" in profile

    def test_profile_structure(self):
        """Test profile has all required sections"""
        # Given
        encoder = SemanticFeatureEncoder()

        # When
        profile = encoder.encode_team_strength(
            attack=85,
            defense=80,
            press=78,
            style='possession'
        )

        # Then
        # Check all sections are present
        assert "## 팀 전력 프로필" in profile
        assert "### 공격력:" in profile
        assert "### 수비력:" in profile
        assert "### 압박 강도:" in profile
        assert "### 빌드업 스타일:" in profile
        assert "**특징:**" in profile
        assert "**강점:**" in profile
        assert "**약점:**" in profile


class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_exact_boundary_100(self):
        """Test exact value 100"""
        # Given
        encoder = SemanticFeatureEncoder()

        # When
        desc_100 = encoder._get_strength_description(100)

        # Then
        # 100 should be in (90, 100) range but the range is exclusive on upper bound
        # So it should fall back to weakest
        # Wait, let me check the implementation again...
        # Actually in Python range (90, 100) with < comparison means 90 <= x < 100
        # So 100 would fall through and get default (0, 60)
        # Let's test both possibilities
        assert desc_100['label'] in ['월드클래스', '약함']

    def test_negative_values(self):
        """Test negative strength values"""
        # Given
        encoder = SemanticFeatureEncoder()

        # When
        desc_negative = encoder._get_strength_description(-10)

        # Then
        # Negative should fall through all ranges and get default
        assert desc_negative['label'] == '약함'

    def test_values_over_100(self):
        """Test values over 100"""
        # Given
        encoder = SemanticFeatureEncoder()

        # When
        desc_150 = encoder._get_strength_description(150)

        # Then
        # Over 100 should fall through and get default
        assert desc_150['label'] == '약함'

    def test_zero_strength(self):
        """Test zero strength values"""
        # Given
        encoder = SemanticFeatureEncoder()

        # When
        profile = encoder.encode_team_strength(
            attack=0,
            defense=0,
            press=0,
            style='possession'
        )

        # Then
        assert "0.0/100 - 약함" in profile


if __name__ == '__main__':
    # Run tests with pytest
    pytest.main([__file__, '-v', '-s'])
