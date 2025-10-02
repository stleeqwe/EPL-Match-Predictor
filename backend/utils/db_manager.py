"""
데이터베이스 관리 유틸리티
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from database.schema import (
    init_db, get_session, Base,
    Team, Match, MatchStats, TeamStats,
    Player, PlayerRating, Prediction
)
from sqlalchemy import desc, and_
import pandas as pd
from datetime import datetime, timedelta

class DatabaseManager:
    def __init__(self, db_path='sqlite:///soccer_predictor.db'):
        self.engine = init_db(db_path)
        self.session = get_session(self.engine)

    def add_team(self, name, short_name=None, league='EPL'):
        """팀 추가"""
        team = self.session.query(Team).filter_by(name=name).first()
        if not team:
            team = Team(name=name, short_name=short_name, league=league)
            self.session.add(team)
            self.session.commit()
        return team

    def add_match(self, home_team_name, away_team_name, season, gameweek, match_date,
                  home_score=None, away_score=None, home_xg=None, away_xg=None, status='scheduled'):
        """경기 추가"""
        home_team = self.add_team(home_team_name)
        away_team = self.add_team(away_team_name)

        match = Match(
            season=season,
            gameweek=gameweek,
            match_date=match_date,
            home_team_id=home_team.id,
            away_team_id=away_team.id,
            home_score=home_score,
            away_score=away_score,
            home_xg=home_xg,
            away_xg=away_xg,
            status=status
        )
        self.session.add(match)
        self.session.commit()
        return match

    def save_prediction(self, match_id, home_win_prob, draw_prob, away_win_prob,
                       expected_home_goals, expected_away_goals, model_type,
                       stats_weight=None, personal_weight=None):
        """예측 결과 저장"""
        prediction = Prediction(
            match_id=match_id,
            home_win_prob=home_win_prob,
            draw_prob=draw_prob,
            away_win_prob=away_win_prob,
            expected_home_goals=expected_home_goals,
            expected_away_goals=expected_away_goals,
            model_type=model_type,
            stats_weight=stats_weight,
            personal_weight=personal_weight
        )
        self.session.add(prediction)
        self.session.commit()
        return prediction

    def get_predictions_history(self, limit=20):
        """예측 히스토리 조회"""
        predictions = self.session.query(Prediction)\
            .order_by(desc(Prediction.created_at))\
            .limit(limit)\
            .all()

        history = []
        for pred in predictions:
            match = self.session.query(Match).filter_by(id=pred.match_id).first()
            if match:
                history.append({
                    'match_date': match.match_date,
                    'home_team': match.home_team.name,
                    'away_team': match.away_team.name,
                    'predicted_home_win': pred.home_win_prob,
                    'predicted_draw': pred.draw_prob,
                    'predicted_away_win': pred.away_win_prob,
                    'actual_home_score': match.home_score,
                    'actual_away_score': match.away_score,
                    'model_type': pred.model_type,
                    'prediction_date': pred.created_at
                })

        return history

    def calculate_prediction_accuracy(self, days=30):
        """예측 정확도 계산"""
        cutoff_date = datetime.now() - timedelta(days=days)

        predictions = self.session.query(Prediction)\
            .filter(Prediction.created_at >= cutoff_date)\
            .all()

        total = 0
        correct = 0

        for pred in predictions:
            match = self.session.query(Match).filter_by(id=pred.match_id).first()

            # 완료된 경기만
            if not match or match.status != 'completed':
                continue

            total += 1

            # 실제 결과
            if match.home_score > match.away_score:
                actual = 'home_win'
            elif match.home_score < match.away_score:
                actual = 'away_win'
            else:
                actual = 'draw'

            # 예측 결과
            probs = {
                'home_win': pred.home_win_prob,
                'draw': pred.draw_prob,
                'away_win': pred.away_win_prob
            }
            predicted = max(probs, key=probs.get)

            if predicted == actual:
                correct += 1

        accuracy = (correct / total * 100) if total > 0 else 0

        return {
            'accuracy': accuracy,
            'total_predictions': total,
            'correct_predictions': correct,
            'period_days': days
        }

    def get_player_ratings(self, player_id):
        """선수 능력치 조회"""
        ratings = self.session.query(PlayerRating)\
            .filter_by(player_id=player_id)\
            .all()

        return {r.attribute_name: r.rating for r in ratings}

    def save_player_rating(self, player_id, attribute_name, rating):
        """선수 능력치 저장"""
        rating_obj = self.session.query(PlayerRating)\
            .filter_by(player_id=player_id, attribute_name=attribute_name)\
            .first()

        if rating_obj:
            rating_obj.rating = rating
            rating_obj.updated_at = datetime.utcnow()
        else:
            rating_obj = PlayerRating(
                player_id=player_id,
                attribute_name=attribute_name,
                rating=rating
            )
            self.session.add(rating_obj)

        self.session.commit()
        return rating_obj

    def get_upcoming_matches(self, days=7):
        """다가오는 경기 조회"""
        now = datetime.now()
        future = now + timedelta(days=days)

        matches = self.session.query(Match)\
            .filter(
                and_(
                    Match.match_date >= now,
                    Match.match_date <= future,
                    Match.status == 'scheduled'
                )
            )\
            .order_by(Match.match_date)\
            .all()

        return [{
            'id': m.id,
            'date': m.match_date,
            'home_team': m.home_team.name,
            'away_team': m.away_team.name,
            'gameweek': m.gameweek
        } for m in matches]

    def close(self):
        """세션 종료"""
        self.session.close()

if __name__ == "__main__":
    # 테스트
    db = DatabaseManager()

    # 팀 추가
    db.add_team("Manchester City", "MCI", "EPL")
    db.add_team("Liverpool", "LIV", "EPL")

    # 경기 추가
    match = db.add_match(
        "Manchester City", "Liverpool",
        season="2024-25",
        gameweek=8,
        match_date=datetime(2024, 10, 5, 15, 0),
        status='scheduled'
    )

    # 예측 저장
    db.save_prediction(
        match.id,
        home_win_prob=55.0,
        draw_prob=25.0,
        away_win_prob=20.0,
        expected_home_goals=2.3,
        expected_away_goals=1.5,
        model_type='dixon-coles'
    )

    # 히스토리 조회
    history = db.get_predictions_history(limit=5)
    print("=== Prediction History ===")
    for h in history:
        print(f"{h['home_team']} vs {h['away_team']}: {h['predicted_home_win']:.1f}% / {h['predicted_draw']:.1f}% / {h['predicted_away_win']:.1f}%")

    db.close()
