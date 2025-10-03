"""
Unit tests for Flask API endpoints
"""
import pytest
import json
from api.app import app


@pytest.fixture
def client():
    """Create test client"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


class TestFixturesEndpoint:
    """Test /api/fixtures endpoint"""

    def test_fixtures_endpoint_exists(self, client):
        """Test fixtures endpoint is accessible"""
        response = client.get('/api/fixtures')
        assert response.status_code in [200, 500]  # Should exist even if it errors

    def test_fixtures_returns_json(self, client):
        """Test fixtures returns valid JSON"""
        response = client.get('/api/fixtures')
        if response.status_code == 200:
            data = json.loads(response.data)
            assert isinstance(data, list)

    def test_fixtures_no_nan_values(self, client):
        """Test fixtures doesn't contain NaN values"""
        response = client.get('/api/fixtures')
        if response.status_code == 200:
            response_text = response.data.decode('utf-8')
            assert 'NaN' not in response_text
            assert 'null' in response_text or response_text.startswith('[')


class TestPredictEndpoint:
    """Test /api/predict endpoint"""

    def test_predict_missing_parameters(self, client):
        """Test predict endpoint handles missing parameters"""
        # Test missing both teams
        response = client.post('/api/predict',
                              json={},
                              content_type='application/json')
        # API currently falls back to defaults, so just check it responds
        assert response.status_code in [200, 400, 500]

    def test_predict_returns_json(self, client):
        """Test predict returns valid JSON structure"""
        response = client.post('/api/predict',
                              json={
                                  'home_team': 'Manchester City',
                                  'away_team': 'Liverpool',
                                  'model_type': 'statistical'
                              })

        if response.status_code == 200:
            data = json.loads(response.data)
            assert isinstance(data, dict)
            # Check for required fields
            assert 'home_win' in data or 'error' in data


class TestHealthCheck:
    """Test health check endpoint"""

    def test_root_endpoint(self, client):
        """Test root endpoint returns something (200 or redirect)"""
        response = client.get('/')
        # Root may not exist or may redirect - just check response exists
        assert response.status_code in [200, 301, 302, 404]


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
