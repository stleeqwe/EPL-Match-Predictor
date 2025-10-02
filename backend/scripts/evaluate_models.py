"""
Evaluate trained models on test set
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
import pickle
from models.bayesian_dixon_coles_simplified import SimplifiedBayesianDixonColes
from models.dixon_coles import DixonColesModel

def load_models():
    """Load trained models"""
    model_dir = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'model_cache'
    )

    with open(os.path.join(model_dir, 'bayesian_model_real.pkl'), 'rb') as f:
        bayesian_model = pickle.load(f)

    with open(os.path.join(model_dir, 'dixon_coles_real.pkl'), 'rb') as f:
        dixon_coles_model = pickle.load(f)

    return bayesian_model, dixon_coles_model


def load_test_data():
    """Load test data (last 20% of matches)"""
    csv_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        'data',
        'epl_real_understat.csv'
    )

    df = pd.read_csv(csv_path)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')

    # Split: last 20% as test
    split_idx = int(len(df) * 0.8)
    test_df = df.iloc[split_idx:]

    return test_df


def evaluate_model(model, test_df, model_name, use_bayesian=False):
    """Evaluate a model on test set"""
    results = {
        'correct': 0,
        'total': 0,
        'log_loss': 0,
        'predictions': []
    }

    for _, match in test_df.iterrows():
        home_team = match['home_team']
        away_team = match['away_team']
        actual_result = 'H' if match['home_score'] > match['away_score'] else \
                       ('A' if match['away_score'] > match['home_score'] else 'D')

        try:
            if use_bayesian:
                pred = model.predict_match(home_team, away_team, n_sims=1000)
            else:
                pred = model.predict_match(home_team, away_team)

            # Determine predicted result
            probs = [pred['home_win'], pred['draw'], pred['away_win']]
            predicted_result = ['H', 'D', 'A'][np.argmax(probs)]

            if predicted_result == actual_result:
                results['correct'] += 1

            results['total'] += 1

            # Log loss
            prob_values = [p/100 for p in probs]
            actual_idx = {'H': 0, 'D': 1, 'A': 2}[actual_result]
            results['log_loss'] += -np.log(max(prob_values[actual_idx], 1e-15))

            # Store prediction
            results['predictions'].append({
                'match': f"{home_team} vs {away_team}",
                'actual': actual_result,
                'predicted': predicted_result,
                'probs': prob_values
            })

        except Exception as e:
            print(f"Error predicting {home_team} vs {away_team}: {e}")
            continue

    return results


if __name__ == "__main__":
    print("=" * 70)
    print("MODEL EVALUATION")
    print("=" * 70)

    # Load models
    print("\nLoading models...")
    bayesian_model, dixon_coles_model = load_models()
    print("✓ Models loaded")

    # Load test data
    print("\nLoading test data...")
    test_df = load_test_data()
    print(f"✓ Test set: {len(test_df)} matches")
    print(f"  Date range: {test_df['date'].min().date()} to {test_df['date'].max().date()}")

    # Evaluate Bayesian model
    print("\n" + "-" * 70)
    print("Evaluating Bayesian Dixon-Coles...")
    print("-" * 70)
    bayesian_results = evaluate_model(bayesian_model, test_df, "Bayesian", use_bayesian=True)

    # Evaluate Dixon-Coles MLE
    print("\n" + "-" * 70)
    print("Evaluating Dixon-Coles (MLE)...")
    print("-" * 70)
    dixon_results = evaluate_model(dixon_coles_model, test_df, "Dixon-Coles", use_bayesian=False)

    # Print results
    print("\n" + "=" * 70)
    print("RESULTS SUMMARY")
    print("=" * 70)

    print(f"\nTest Set: {len(test_df)} matches\n")

    for model_name, results in [("Bayesian Dixon-Coles", bayesian_results),
                                 ("Dixon-Coles (MLE)", dixon_results)]:
        if results['total'] > 0:
            accuracy = results['correct'] / results['total'] * 100
            avg_log_loss = results['log_loss'] / results['total']

            print(f"{model_name}:")
            print(f"  Accuracy: {accuracy:.1f}% ({results['correct']}/{results['total']})")
            print(f"  Log Loss: {avg_log_loss:.4f}")
            print()

    # Show some example predictions
    print("=" * 70)
    print("SAMPLE PREDICTIONS (First 5 Test Matches)")
    print("=" * 70)

    for i, pred in enumerate(bayesian_results['predictions'][:5]):
        print(f"\n{i+1}. {pred['match']}")
        print(f"   Actual: {pred['actual']} | Predicted: {pred['predicted']}")
        print(f"   Probabilities - H: {pred['probs'][0]*100:.1f}% | "
              f"D: {pred['probs'][1]*100:.1f}% | A: {pred['probs'][2]*100:.1f}%")

    print("\n" + "=" * 70)
    print("✅ EVALUATION COMPLETE")
    print("=" * 70)
