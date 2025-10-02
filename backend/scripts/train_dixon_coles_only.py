"""
Train only Dixon-Coles model quickly
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.schema import init_db, get_session, Match, Team
import pandas as pd
from models.dixon_coles import DixonColesModel
import pickle
from sqlalchemy.orm import joinedload

def load_data():
    """Load data from database with optimized query"""
    db_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'soccer_predictor.db'
    )
    db_url = f'sqlite:///{os.path.abspath(db_path)}'
    engine = init_db(db_url)
    session = get_session(engine)

    # Use eager loading to avoid N+1 queries
    matches = session.query(Match).options(
        joinedload(Match.home_team),
        joinedload(Match.away_team)
    ).filter_by(status='completed').all()

    data = []
    for m in matches:
        if m.home_team and m.away_team and m.home_score is not None:
            data.append({
                'date': m.match_date,
                'home_team': m.home_team.name,
                'away_team': m.away_team.name,
                'home_score': int(m.home_score),
                'away_score': int(m.away_score),
            })

    session.close()
    df = pd.DataFrame(data)
    df['date'] = pd.to_datetime(df['date'])

    print(f"✓ Loaded {len(df)} matches")
    return df


if __name__ == "__main__":
    print("Training Dixon-Coles Model...")
    print("=" * 60)

    df = load_data()

    # Train
    model = DixonColesModel(xi=0.0065)
    model.fit(df)

    # Save
    model_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'model_cache',
        'dixon_coles_real.pkl'
    )

    with open(model_path, 'wb') as f:
        pickle.dump(model, f)

    print(f"\n✓ Model saved to: {model_path}")

    # Quick test
    print("\nQuick test prediction:")
    teams = list(df['home_team'].unique())
    if len(teams) >= 2:
        pred = model.predict_match(teams[0], teams[1])
        print(f"{teams[0]} vs {teams[1]}")
        print(f"  Home: {pred['home_win']:.1f}% | Draw: {pred['draw']:.1f}% | Away: {pred['away_win']:.1f}%")

    print("\n✅ Done!")
