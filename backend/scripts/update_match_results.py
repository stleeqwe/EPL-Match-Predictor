"""
경기 결과 업데이트 스크립트
FBref에서 완료된 경기 결과를 가져와 DB 업데이트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.schema import init_db, get_session, Match, Team, Prediction
from data_collection.fbref_scraper import FBrefScraper
import pandas as pd
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class MatchResultUpdater:
    def __init__(self):
        db_path = os.path.join(os.path.dirname(__file__), '..', 'soccer_predictor.db')
        db_url = f'sqlite:///{os.path.abspath(db_path)}'
        engine = init_db(db_url)
        self.session = get_session(engine)
        self.scraper = FBrefScraper()

    def update_results(self):
        """
        FBref에서 최신 경기 결과를 가져와 DB 업데이트
        """
        logger.info("Fetching latest match results from FBref...")

        try:
            # FBref에서 경기 일정 가져오기
            fixtures_df = self.scraper.get_epl_fixtures()

            # 완료된 경기만 필터링 (스코어가 있는 경기)
            completed = fixtures_df[
                (fixtures_df['home_score'].notna()) &
                (fixtures_df['away_score'].notna())
            ]

            logger.info(f"Found {len(completed)} completed matches")

            updated_count = 0

            for _, row in completed.iterrows():
                home_team_name = row['home_team']
                away_team_name = row['away_team']
                home_score = int(row['home_score'])
                away_score = int(row['away_score'])
                match_date = pd.to_datetime(row['date'])

                # DB에서 팀 찾기
                home_team = self.session.query(Team).filter_by(name=home_team_name).first()
                away_team = self.session.query(Team).filter_by(name=away_team_name).first()

                if not home_team or not away_team:
                    logger.warning(f"Teams not found in DB: {home_team_name} vs {away_team_name}")
                    continue

                # DB에서 매칭되는 경기 찾기
                match = self.session.query(Match).filter(
                    Match.home_team_id == home_team.id,
                    Match.away_team_id == away_team.id,
                    Match.match_date >= match_date - pd.Timedelta(days=1),
                    Match.match_date <= match_date + pd.Timedelta(days=1)
                ).first()

                if match:
                    # 경기 결과 업데이트
                    if match.home_score is None or match.away_score is None:
                        match.home_score = home_score
                        match.away_score = away_score
                        match.status = 'completed'
                        self.session.commit()
                        updated_count += 1
                        logger.info(f"✓ Updated: {home_team_name} {home_score}-{away_score} {away_team_name}")
                else:
                    logger.info(f"No match found in DB for {home_team_name} vs {away_team_name} on {match_date.date()}")

            logger.info(f"\n✅ Updated {updated_count} match results")
            return updated_count

        except Exception as e:
            logger.error(f"Error updating results: {e}")
            self.session.rollback()
            return 0

    def calculate_accuracy(self):
        """
        예측 정확도 계산
        """
        logger.info("\nCalculating prediction accuracy...")

        # 결과가 있는 경기의 예측 조회
        predictions = self.session.query(Prediction).join(Match).filter(
            Match.home_score.isnot(None),
            Match.away_score.isnot(None)
        ).all()

        if not predictions:
            logger.info("No predictions with match results found")
            return

        total = len(predictions)
        correct = 0
        by_model = {}

        for pred in predictions:
            match = pred.match

            # 실제 결과 판정
            if match.home_score > match.away_score:
                actual_result = 'home_win'
            elif match.home_score < match.away_score:
                actual_result = 'away_win'
            else:
                actual_result = 'draw'

            # 예측 결과 판정 (가장 높은 확률)
            probs = {
                'home_win': pred.home_win_prob,
                'draw': pred.draw_prob,
                'away_win': pred.away_win_prob
            }
            predicted_result = max(probs, key=probs.get)

            # 정확도 체크
            if predicted_result == actual_result:
                correct += 1

            # 모델별 집계
            model = pred.model_type
            if model not in by_model:
                by_model[model] = {'total': 0, 'correct': 0}
            by_model[model]['total'] += 1
            if predicted_result == actual_result:
                by_model[model]['correct'] += 1

        overall_accuracy = (correct / total * 100) if total > 0 else 0

        logger.info(f"\n📊 Overall Accuracy: {correct}/{total} = {overall_accuracy:.1f}%")
        logger.info("\nBy Model:")
        for model, stats in by_model.items():
            model_accuracy = (stats['correct'] / stats['total'] * 100) if stats['total'] > 0 else 0
            logger.info(f"  {model}: {stats['correct']}/{stats['total']} = {model_accuracy:.1f}%")

    def close(self):
        self.session.close()


if __name__ == "__main__":
    updater = MatchResultUpdater()

    try:
        logger.info("="*60)
        logger.info("Match Result Update Script")
        logger.info("="*60)

        # 1. 경기 결과 업데이트
        updated = updater.update_results()

        # 2. 정확도 계산
        if updated > 0:
            updater.calculate_accuracy()

        logger.info("\n" + "="*60)
        logger.info("✅ Update complete!")
        logger.info("="*60)

    except Exception as e:
        logger.error(f"Error: {e}")
        raise
    finally:
        updater.close()
