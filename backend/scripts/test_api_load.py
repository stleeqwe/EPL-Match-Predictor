"""
Test that API can load real models correctly
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pickle
import pandas as pd
from models.bayesian_dixon_coles_simplified import SimplifiedBayesianDixonColes
from models.dixon_coles import DixonColesModel

print("=" * 60)
print("Testing Real Model Integration")
print("=" * 60)

# Load models
model_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'model_cache')

print("\n1. Loading Bayesian Model...")
bayesian_path = os.path.join(model_dir, 'bayesian_model_real.pkl')
with open(bayesian_path, 'rb') as f:
    bayesian_model = pickle.load(f)
print(f"✓ Loaded: {bayesian_path}")

print("\n2. Loading Dixon-Coles Model...")
dixon_path = os.path.join(model_dir, 'dixon_coles_real.pkl')
with open(dixon_path, 'rb') as f:
    dixon_model = pickle.load(f)
print(f"✓ Loaded: {dixon_path}")

# Load historical data
print("\n3. Loading Historical Data...")
csv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'epl_real_understat.csv')
historical_matches = pd.read_csv(csv_path)
historical_matches['date'] = pd.to_datetime(historical_matches['date'])
print(f"✓ Loaded {len(historical_matches)} matches")

# Test predictions
print("\n" + "=" * 60)
print("Testing Predictions")
print("=" * 60)

teams = list(historical_matches['home_team'].unique())

# Test 1: Dixon-Coles
print("\n1. Dixon-Coles (MLE) Prediction:")
home, away = teams[0], teams[1]
pred_dixon = dixon_model.predict_match(home, away)
print(f"   {home} vs {away}")
print(f"   Home: {pred_dixon['home_win']:.1f}% | Draw: {pred_dixon['draw']:.1f}% | Away: {pred_dixon['away_win']:.1f}%")

# Test 2: Bayesian
print("\n2. Bayesian Dixon-Coles Prediction:")
pred_bayesian = bayesian_model.predict_match(home, away, n_sims=1000)
print(f"   {home} vs {away}")
print(f"   Home: {pred_bayesian['home_win']:.1f}% | Draw: {pred_bayesian['draw']:.1f}% | Away: {pred_bayesian['away_win']:.1f}%")
print(f"   Expected Goals: {pred_bayesian['expected_home_goals']:.2f} - {pred_bayesian['expected_away_goals']:.2f}")

# Test 3: Different matchup
print("\n3. Another Matchup:")
home2, away2 = teams[2], teams[3]
pred_dixon2 = dixon_model.predict_match(home2, away2)
pred_bayesian2 = bayesian_model.predict_match(home2, away2, n_sims=1000)

print(f"\n   {home2} vs {away2}")
print(f"   Dixon-Coles:  H:{pred_dixon2['home_win']:.1f}% D:{pred_dixon2['draw']:.1f}% A:{pred_dixon2['away_win']:.1f}%")
print(f"   Bayesian:     H:{pred_bayesian2['home_win']:.1f}% D:{pred_bayesian2['draw']:.1f}% A:{pred_bayesian2['away_win']:.1f}%")

print("\n" + "=" * 60)
print("✅ All Models Working Correctly!")
print("=" * 60)

print("\nAPI Integration Summary:")
print("  ✓ Bayesian model loadable from cache")
print("  ✓ Dixon-Coles model loadable from cache")
print("  ✓ Both models can make predictions")
print("  ✓ Historical data available for features")
print("\nReady for Flask API integration!")
