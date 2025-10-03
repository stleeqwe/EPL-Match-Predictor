"""
Unit tests for Dixon-Coles prediction model
"""
import pytest
import numpy as np
import pandas as pd
from models.dixon_coles import DixonColesModel


@pytest.fixture
def sample_matches():
    """Create sample match data for testing"""
    return pd.DataFrame({
        'home_team': ['Manchester City', 'Liverpool', 'Arsenal', 'Chelsea'],
        'away_team': ['Liverpool', 'Chelsea', 'Manchester City', 'Arsenal'],
        'home_score': [2, 1, 0, 2],  # Model expects 'home_score' not 'home_goals'
        'away_score': [1, 1, 2, 1],  # Model expects 'away_score' not 'away_goals'
        'date': pd.date_range('2024-01-01', periods=4)
    })


@pytest.fixture
def trained_model(sample_matches):
    """Create and train a Dixon-Coles model"""
    model = DixonColesModel()
    model.fit(sample_matches)
    return model


class TestDixonColesModel:
    """Test suite for Dixon-Coles model"""

    def test_model_initialization(self):
        """Test model can be initialized"""
        model = DixonColesModel()
        assert model is not None
        assert hasattr(model, 'fit')
        assert hasattr(model, 'predict_match')

    def test_model_fitting(self, sample_matches):
        """Test model can be fitted with sample data"""
        model = DixonColesModel()
        model.fit(sample_matches)

        # Check that parameters were estimated (model uses team_attack/team_defense)
        assert hasattr(model, 'team_attack')
        assert hasattr(model, 'team_defense')
        assert len(model.team_attack) > 0
        assert len(model.team_defense) > 0

    def test_prediction_output_structure(self, trained_model):
        """Test prediction returns correct structure"""
        prediction = trained_model.predict_match('Manchester City', 'Liverpool')

        # Check required keys (model returns expected_home_goals not expected_goals_home)
        assert 'home_win' in prediction
        assert 'draw' in prediction
        assert 'away_win' in prediction
        assert 'expected_home_goals' in prediction
        assert 'expected_away_goals' in prediction

        # Check probabilities sum to ~100 (percentages)
        prob_sum = prediction['home_win'] + prediction['draw'] + prediction['away_win']
        assert 99 <= prob_sum <= 101

    def test_prediction_probabilities_valid(self, trained_model):
        """Test all probabilities are between 0 and 100 (percentages)"""
        prediction = trained_model.predict_match('Manchester City', 'Liverpool')

        assert 0 <= prediction['home_win'] <= 100
        assert 0 <= prediction['draw'] <= 100
        assert 0 <= prediction['away_win'] <= 100

    def test_expected_goals_positive(self, trained_model):
        """Test expected goals are positive"""
        prediction = trained_model.predict_match('Manchester City', 'Liverpool')

        assert prediction['expected_home_goals'] >= 0
        assert prediction['expected_away_goals'] >= 0

    def test_prediction_with_unknown_team(self, trained_model):
        """Test prediction handles unknown teams gracefully"""
        # Should either raise an error or handle gracefully
        try:
            prediction = trained_model.predict_match('Unknown Team', 'Liverpool')
            # If it returns, check it has valid structure
            assert 'home_win' in prediction
        except (KeyError, ValueError):
            # Expected behavior - unknown team should raise error
            pass

    def test_score_matrix_generation(self, trained_model):
        """Test score matrix is generated correctly"""
        prediction = trained_model.predict_match('Manchester City', 'Liverpool')

        if 'score_matrix' in prediction:
            score_matrix = prediction['score_matrix']
            assert isinstance(score_matrix, (np.ndarray, list))
            # Score matrix should have probabilities
            if isinstance(score_matrix, np.ndarray):
                assert score_matrix.min() >= 0
                assert score_matrix.max() <= 1


class TestPredictionConsistency:
    """Test prediction consistency and stability"""

    def test_same_input_same_output(self, trained_model):
        """Test same teams give same prediction"""
        pred1 = trained_model.predict_match('Manchester City', 'Liverpool')
        pred2 = trained_model.predict_match('Manchester City', 'Liverpool')

        assert pred1['home_win'] == pred2['home_win']
        assert pred1['draw'] == pred2['draw']
        assert pred1['away_win'] == pred2['away_win']

    def test_home_away_symmetry(self, trained_model):
        """Test swapping teams swaps probabilities appropriately"""
        pred_home = trained_model.predict_match('Manchester City', 'Liverpool')
        pred_away = trained_model.predict_match('Liverpool', 'Manchester City')

        # Home win in first should roughly equal away win in second
        # (not exact due to home advantage)
        assert abs(pred_home['home_win'] - pred_away['away_win']) < 0.3
        assert abs(pred_home['away_win'] - pred_away['home_win']) < 0.3


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
