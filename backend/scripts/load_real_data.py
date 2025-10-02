"""
Load real EPL data into SQLite database
"""

import pandas as pd
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.schema import init_db, get_session, Team, Match

def load_real_data(csv_path: str, db_path: str = None):
    """
    Load real EPL data from CSV into database

    Parameters:
    -----------
    csv_path : str
        Path to CSV file with match data
    db_path : str
        Path to SQLite database (default: ../soccer_predictor.db)
    """
    if db_path is None:
        db_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'soccer_predictor.db'
        )

    # Initialize database
    db_url = f'sqlite:///{os.path.abspath(db_path)}'
    engine = init_db(db_url)
    session = get_session(engine)

    print(f"Loading data from: {csv_path}")
    print(f"Database: {db_path}\n")

    # Read CSV
    df = pd.read_csv(csv_path)
    df['date'] = pd.to_datetime(df['date'])

    print(f"Total matches in CSV: {len(df)}")
    print(f"Date range: {df['date'].min()} to {df['date'].max()}\n")

    # Get or create teams
    teams_added = 0
    team_cache = {}

    all_teams = set(df['home_team'].unique()) | set(df['away_team'].unique())
    all_teams = {t for t in all_teams if pd.notna(t)}

    for team_name in sorted(all_teams):
        # Check if team exists
        team = session.query(Team).filter_by(name=team_name).first()

        if not team:
            # Create new team
            team = Team(
                name=team_name,
                league='EPL'
            )
            session.add(team)
            teams_added += 1

        team_cache[team_name] = team

    session.commit()
    print(f"Teams: {len(team_cache)} total ({teams_added} added)\n")

    # Load matches
    matches_added = 0
    matches_updated = 0
    matches_skipped = 0

    for _, row in df.iterrows():
        home_team_name = row['home_team']
        away_team_name = row['away_team']

        # Skip if teams missing
        if pd.isna(home_team_name) or pd.isna(away_team_name):
            matches_skipped += 1
            continue

        if home_team_name not in team_cache or away_team_name not in team_cache:
            matches_skipped += 1
            continue

        home_team = team_cache[home_team_name]
        away_team = team_cache[away_team_name]

        # Determine status
        if pd.notna(row.get('home_score')) and pd.notna(row.get('away_score')):
            status = 'completed'
        else:
            status = 'scheduled'

        # Check if match exists
        existing_match = session.query(Match).filter_by(
            match_date=row['date'],
            home_team_id=home_team.id,
            away_team_id=away_team.id
        ).first()

        if existing_match:
            # Update existing match
            existing_match.home_score = row.get('home_score') if pd.notna(row.get('home_score')) else None
            existing_match.away_score = row.get('away_score') if pd.notna(row.get('away_score')) else None
            existing_match.home_xg = row.get('home_xg') if pd.notna(row.get('home_xg')) else None
            existing_match.away_xg = row.get('away_xg') if pd.notna(row.get('away_xg')) else None
            existing_match.status = status
            matches_updated += 1
        else:
            # Create new match
            match = Match(
                match_date=row['date'],
                season=row.get('season', '2024-2025'),
                home_team_id=home_team.id,
                away_team_id=away_team.id,
                home_score=row.get('home_score') if pd.notna(row.get('home_score')) else None,
                away_score=row.get('away_score') if pd.notna(row.get('away_score')) else None,
                home_xg=row.get('home_xg') if pd.notna(row.get('home_xg')) else None,
                away_xg=row.get('away_xg') if pd.notna(row.get('away_xg')) else None,
                status=status
            )
            session.add(match)
            matches_added += 1

        # Commit in batches
        if (matches_added + matches_updated) % 50 == 0:
            session.commit()

    session.commit()

    print(f"Matches:")
    print(f"  Added: {matches_added}")
    print(f"  Updated: {matches_updated}")
    print(f"  Skipped: {matches_skipped}")

    # Verify
    total_matches = session.query(Match).count()
    completed_matches = session.query(Match).filter_by(status='completed').count()

    print(f"\nDatabase summary:")
    print(f"  Total matches: {total_matches}")
    print(f"  Completed: {completed_matches}")
    print(f"  Scheduled: {total_matches - completed_matches}")

    session.close()
    print("\n✅ Data loaded successfully!")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Load real EPL data')
    parser.add_argument('csv_file', help='Path to CSV file')
    parser.add_argument('--db', default=None, help='Database path')

    args = parser.parse_args()

    load_real_data(args.csv_file, args.db)
