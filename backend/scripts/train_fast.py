"""
Quick model training from CSV (bypass slow database ORM)
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from models.dixon_coles import DixonColesModel
import pickle

# Load data directly from CSV
csv_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    'data',
    'epl_real_understat.csv'
)

print("=" * 60)
print("Training Dixon-Coles Model (Fast)")
print("=" * 60)

df = pd.read_csv(csv_path)
df['date'] = pd.to_datetime(df['date'])

print(f"\n✓ Loaded {len(df)} matches from CSV")
print(f"  Date range: {df['date'].min().date()} to {df['date'].max().date()}")
print(f"  Teams: {df['home_team'].nunique()}")

# Train model
print("\nTraining Dixon-Coles...")
model = DixonColesModel(xi=0.0065)
model.fit(df)

# Save
model_path = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    'model_cache',
    'dixon_coles_real.pkl'
)
os.makedirs(os.path.dirname(model_path), exist_ok=True)

with open(model_path, 'wb') as f:
    pickle.dump(model, f)

print(f"\n✓ Model saved to: {model_path}")

# Test prediction
print("\n" + "=" * 60)
print("Sample Predictions")
print("=" * 60)

teams = list(df['home_team'].unique())[:4]
for i in range(0, len(teams)-1, 2):
    home = teams[i]
    away = teams[i+1]
    pred = model.predict_match(home, away)
    print(f"\n{home} vs {away}")
    print(f"  Home: {pred['home_win']:.1f}% | Draw: {pred['draw']:.1f}% | Away: {pred['away_win']:.1f}%")

print("\n✅ Training Complete!")
