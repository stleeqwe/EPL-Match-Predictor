"""
Phase 1 Integration Tests - Configuration Management
Tests centralized settings and constants
"""
import pytest
import os
from backend.config.settings import get_settings, Settings
from backend.config import constants


class TestPhase1Configuration:
    """Test Phase 1 configuration system"""

    def test_settings_singleton(self):
        """Test that get_settings returns singleton instance"""
        settings1 = get_settings()
        settings2 = get_settings()

        assert settings1 is settings2, "Settings should be singleton"

    def test_settings_structure(self):
        """Test settings has all required sub-configurations"""
        settings = get_settings()

        # Check all sub-settings exist
        assert hasattr(settings, 'database')
        assert hasattr(settings, 'redis')
        assert hasattr(settings, 'cache')
        assert hasattr(settings, 'ai')
        assert hasattr(settings, 'api')
        assert hasattr(settings, 'external_api')
        assert hasattr(settings, 'features')
        assert hasattr(settings, 'logging')

    def test_database_settings(self):
        """Test database configuration"""
        settings = get_settings()

        assert settings.database.url is not None
        assert settings.database.pool_size > 0
        assert settings.database.max_overflow > 0

        # URL should start with postgresql:// or sqlite://
        assert settings.database.url.startswith(('postgresql://', 'sqlite://'))

    def test_cache_settings(self):
        """Test cache configuration"""
        settings = get_settings()

        assert isinstance(settings.cache.enabled, bool)
        assert settings.cache.default_ttl > 0
        assert settings.cache.player_rating_ttl > 0
        assert settings.cache.team_lineup_ttl > 0

    def test_ai_settings(self):
        """Test AI provider configuration"""
        settings = get_settings()

        assert settings.ai.provider in ['gemini', 'claude', 'qwen']
        assert settings.ai.max_requests_per_minute > 0
        assert settings.ai.timeout > 0

    def test_api_settings(self):
        """Test API server configuration"""
        settings = get_settings()

        assert settings.api.host is not None
        assert settings.api.port > 0
        assert isinstance(settings.api.debug, bool)
        assert isinstance(settings.api.cors_origins, list)

    def test_feature_flags(self):
        """Test feature flags"""
        settings = get_settings()

        # All feature flags should be boolean
        assert isinstance(settings.features.enable_v3_simulation, bool)
        assert isinstance(settings.features.enable_payment, bool)
        assert isinstance(settings.features.enable_ai_rating, bool)
        assert isinstance(settings.features.enable_value_betting, bool)
        assert isinstance(settings.features.enable_injury_tracking, bool)

    def test_constants_availability(self):
        """Test that constants module has required values"""
        # Application metadata
        assert hasattr(constants, 'APP_NAME')
        assert hasattr(constants, 'APP_VERSION')
        assert hasattr(constants, 'API_VERSION')

        # Position constants
        assert hasattr(constants, 'GENERAL_POSITIONS')
        assert hasattr(constants, 'DETAILED_POSITIONS')
        assert hasattr(constants, 'POSITION_ATTRIBUTES')

        # Rating constants
        assert hasattr(constants, 'RATING_MIN')
        assert hasattr(constants, 'RATING_MAX')
        assert hasattr(constants, 'RATING_STEP')

        # Formation constants
        assert hasattr(constants, 'SUPPORTED_FORMATIONS')

        # EPL Teams
        assert hasattr(constants, 'EPL_TEAMS')
        assert len(constants.EPL_TEAMS) == 20

    def test_position_attributes_structure(self):
        """Test position attributes are properly defined"""
        from backend.config.constants import POSITION_ATTRIBUTES

        # All detailed positions should have attributes
        required_positions = ['GK', 'CB', 'FB', 'DM', 'CM', 'CAM', 'WG', 'ST']

        for position in required_positions:
            assert position in POSITION_ATTRIBUTES, f"Missing attributes for {position}"
            assert isinstance(POSITION_ATTRIBUTES[position], list)
            assert len(POSITION_ATTRIBUTES[position]) > 0

    def test_supported_formations(self):
        """Test supported formations list"""
        from backend.config.constants import SUPPORTED_FORMATIONS

        assert isinstance(SUPPORTED_FORMATIONS, list)
        assert len(SUPPORTED_FORMATIONS) > 0

        # Common formations should be supported
        assert '4-3-3' in SUPPORTED_FORMATIONS
        assert '4-4-2' in SUPPORTED_FORMATIONS
        assert '4-2-3-1' in SUPPORTED_FORMATIONS

    def test_environment_detection(self):
        """Test environment detection functions"""
        from backend.config.settings import is_production, is_development, is_testing

        # At least one should be true
        environments = [is_production(), is_development(), is_testing()]
        assert any(environments), "At least one environment should be active"

    def test_convenience_functions(self):
        """Test convenience getter functions"""
        from backend.config.settings import get_database_url, get_redis_url

        db_url = get_database_url()
        redis_url = get_redis_url()

        assert db_url is not None
        assert redis_url is not None
        assert db_url.startswith(('postgresql://', 'sqlite://'))
        assert redis_url.startswith('redis://')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
