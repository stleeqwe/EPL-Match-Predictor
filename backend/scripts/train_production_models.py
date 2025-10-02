"""
Train production models with real data
=======================================

Trains:
1. Bayesian Dixon-Coles
2. XGBoost ensemble
3. Evaluates performance

Usage:
    python train_production_models.py
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.schema import init_db, get_session, Match, Team
import pandas as pd
import numpy as np
from models.bayesian_dixon_coles_simplified import SimplifiedBayesianDixonColes
from models.dixon_coles import DixonColesModel
import pickle
from datetime import datetime

def load_real_data():
    """Load real match data from database"""
    db_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'soccer_predictor.db'
    )
    db_url = f'sqlite:///{os.path.abspath(db_path)}'
    engine = init_db(db_url)
    session = get_session(engine)

    # Get completed matches
    matches = session.query(Match).filter_by(status='completed').all()

    data = []
    for m in matches:
        if m.home_team and m.away_team and m.home_score is not None:
            data.append({
                'date': m.match_date,
                'season': m.season or '2024-2025',
                'home_team': m.home_team.name,
                'away_team': m.away_team.name,
                'home_score': int(m.home_score),
                'away_score': int(m.away_score),
                'home_xg': m.home_xg,
                'away_xg': m.away_xg
            })

    session.close()

    df = pd.DataFrame(data)
    df['date'] = pd.to_datetime(df['date'])

    print(f"✓ Loaded {len(df)} completed matches")
    print(f"  Date range: {df['date'].min()} to {df['date'].max()}")
    print(f"  Teams: {df['home_team'].nunique()}")

    return df


def train_bayesian_model(df, quick_mode=False):
    """Train Bayesian Dixon-Coles"""
    print("\n" + "="*60)
    print("Training Bayesian Dixon-Coles Model")
    print("="*60)

    if quick_mode:
        model = SimplifiedBayesianDixonColes(
            n_samples=500,   # Quick training
            burnin=250,
            thin=2
        )
        print("Mode: Quick (500 samples)")
    else:
        model = SimplifiedBayesianDixonColes(
            n_samples=3000,  # Production quality
            burnin=1500,
            thin=3
        )
        print("Mode: Production (3000 samples)")

    model.fit(df, verbose=True)

    # Save model
    model_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'model_cache',
        'bayesian_model_real.pkl'
    )
    os.makedirs(os.path.dirname(model_path), exist_ok=True)

    with open(model_path, 'wb') as f:
        pickle.dump(model, f)

    print(f"\n✓ Model saved to: {model_path}")

    return model


def train_dixon_coles(df):
    """Train standard Dixon-Coles for comparison"""
    print("\n" + "="*60)
    print("Training Dixon-Coles Model (MLE)")
    print("="*60)

    model = DixonColesModel(xi=0.0065)  # Time decay
    model.fit(df)

    # Save
    model_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'model_cache',
        'dixon_coles_real.pkl'
    )

    with open(model_path, 'wb') as f:
        pickle.dump(model, f)

    print(f"✓ Model saved to: {model_path}")

    return model


def evaluate_models(bayesian_model, dixon_coles_model, test_df):
    """Evaluate both models on test set"""
    print("\n" + "="*60)
    print("Model Evaluation (Test Set)")
    print("="*60)

    results = {
        'bayesian': {'correct': 0, 'total': 0, 'log_loss': 0},
        'dixon_coles': {'correct': 0, 'total': 0, 'log_loss': 0}
    }

    for _, match in test_df.iterrows():
        home_team = match['home_team']
        away_team = match['away_team']
        actual_result = 'H' if match['home_score'] > match['away_score'] else \
                       ('A' if match['away_score'] > match['home_score'] else 'D')

        # Bayesian prediction
        try:
            bay_pred = bayesian_model.predict_match(home_team, away_team, n_sims=1000)
            bay_predicted = 'H' if bay_pred['home_win'] > max(bay_pred['draw'], bay_pred['away_win']) else \
                           ('A' if bay_pred['away_win'] > max(bay_pred['home_win'], bay_pred['draw']) else 'D')

            if bay_predicted == actual_result:
                results['bayesian']['correct'] += 1
            results['bayesian']['total'] += 1

            # Log loss
            probs = [bay_pred['home_win']/100, bay_pred['draw']/100, bay_pred['away_win']/100]
            actual_idx = {'H': 0, 'D': 1, 'A': 2}[actual_result]
            results['bayesian']['log_loss'] += -np.log(max(probs[actual_idx], 1e-15))

        except Exception as e:
            pass

        # Dixon-Coles prediction
        try:
            dc_pred = dixon_coles_model.predict_match(home_team, away_team)
            dc_predicted = 'H' if dc_pred['home_win'] > max(dc_pred['draw'], dc_pred['away_win']) else \
                          ('A' if dc_pred['away_win'] > max(dc_pred['home_win'], dc_pred['draw']) else 'D')

            if dc_predicted == actual_result:
                results['dixon_coles']['correct'] += 1
            results['dixon_coles']['total'] += 1

            # Log loss
            probs = [dc_pred['home_win']/100, dc_pred['draw']/100, dc_pred['away_win']/100]
            actual_idx = {'H': 0, 'D': 1, 'A': 2}[actual_result]
            results['dixon_coles']['log_loss'] += -np.log(max(probs[actual_idx], 1e-15))

        except Exception as e:
            pass

    # Print results
    print(f"\nTest set: {len(test_df)} matches\n")

    for model_name, res in results.items():
        if res['total'] > 0:
            accuracy = res['correct'] / res['total'] * 100
            avg_log_loss = res['log_loss'] / res['total']
            print(f"{model_name.upper()}:")
            print(f"  Accuracy: {accuracy:.1f}% ({res['correct']}/{res['total']})")
            print(f"  Log Loss: {avg_log_loss:.4f}")
            print()


def demo_predictions(bayesian_model, teams):
    """Show sample predictions"""
    print("\n" + "="*60)
    print("Sample Predictions (Bayesian Model)")
    print("="*60)

    # Pick interesting matchups
    matchups = [
        ('Manchester City', 'Liverpool'),
        ('Arsenal', 'Tottenham'),
        ('Manchester United', 'Chelsea'),
    ]

    for home, away in matchups:
        if home in teams and away in teams:
            print(f"\n{home} vs {away}")
            print("-" * 40)

            pred = bayesian_model.predict_match(home, away, n_sims=2000)

            print(f"  Home Win: {pred['home_win']:.1f}%")
            print(f"  Draw: {pred['draw']:.1f}%")
            print(f"  Away Win: {pred['away_win']:.1f}%")

            print(f"\n  Expected Goals:")
            print(f"    {home}: {pred['expected_home_goals']:.2f} "
                  f"[{pred['credible_intervals']['home_goals'][0]:.1f}-"
                  f"{pred['credible_intervals']['home_goals'][1]:.1f}]")
            print(f"    {away}: {pred['expected_away_goals']:.2f} "
                  f"[{pred['credible_intervals']['away_goals'][0]:.1f}-"
                  f"{pred['credible_intervals']['away_goals'][1]:.1f}]")

            print(f"\n  Most Likely Scores:")
            for score in pred['top_scores'][:3]:
                print(f"    {score['score']}: {score['probability']:.1f}%")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Train production models')
    parser.add_argument('--quick', action='store_true', help='Quick training mode (500 samples)')
    parser.add_argument('--skip-eval', action='store_true', help='Skip evaluation')

    args = parser.parse_args()

    print("\n" + "="*60)
    print("PRODUCTION MODEL TRAINING")
    print("Real EPL Data")
    print("="*60)

    # Load data
    df = load_real_data()

    # Split train/test (80/20)
    df = df.sort_values('date')
    split_idx = int(len(df) * 0.8)
    train_df = df.iloc[:split_idx]
    test_df = df.iloc[split_idx:]

    print(f"\nTrain set: {len(train_df)} matches")
    print(f"Test set: {len(test_df)} matches")

    # Train models
    bayesian_model = train_bayesian_model(train_df, quick_mode=args.quick)
    dixon_coles_model = train_dixon_coles(train_df)

    # Evaluate
    if not args.skip_eval and len(test_df) > 0:
        evaluate_models(bayesian_model, dixon_coles_model, test_df)

    # Demo predictions
    teams = set(df['home_team'].unique())
    demo_predictions(bayesian_model, teams)

    print("\n" + "="*60)
    print("✅ TRAINING COMPLETE!")
    print("="*60)
    print("\nModels saved to backend/model_cache/")
    print("  - bayesian_model_real.pkl")
    print("  - dixon_coles_real.pkl")
    print("\nReady for use in Flask API!")
