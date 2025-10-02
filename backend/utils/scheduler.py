"""
자동 스케줄러
- 매일 02:00 KST: 경기 결과 업데이트
- 매일 02:10 KST: 리그 순위표 업데이트
- 매주 월요일 03:00 KST: 선수 로스터 업데이트
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import logging
import sys
import os

# 프로젝트 루트 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = logging.getLogger(__name__)


class MatchUpdateScheduler:
    """경기 결과 및 데이터 자동 업데이트 스케줄러"""

    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.scheduler.configure(timezone='Asia/Seoul')

    def update_match_results_job(self):
        """경기 결과 업데이트 작업"""
        try:
            logger.info("🔄 Starting scheduled match result update...")

            from scripts.update_match_results import MatchResultUpdater

            updater = MatchResultUpdater()
            updated_count = updater.update_results()

            if updated_count > 0:
                updater.calculate_accuracy()

            updater.close()

            logger.info(f"✅ Scheduled update complete: {updated_count} matches updated")

        except Exception as e:
            logger.error(f"❌ Scheduled update failed: {e}")

    def update_standings_job(self):
        """리그 순위표 업데이트 작업"""
        try:
            logger.info("🏆 Starting scheduled standings update...")

            from scripts.update_standings import StandingsUpdater

            updater = StandingsUpdater(season="2024-2025")
            updater.update_standings()
            updater.display_standings()
            updater.close()

            logger.info("✅ Standings update complete")

        except Exception as e:
            logger.error(f"❌ Standings update failed: {e}")

    def update_rosters_job(self):
        """선수 로스터 업데이트 작업 (주간)"""
        try:
            logger.info("👥 Starting scheduled roster update...")

            from scripts.update_squad_rosters import RosterUpdater

            updater = RosterUpdater(season="2024-2025")
            updated_teams, total_players = updater.update_all_rosters()

            if updated_teams > 0:
                updater.update_squad_data_file()

            updater.close()

            logger.info(f"✅ Roster update complete: {updated_teams} teams, {total_players} players")

        except Exception as e:
            logger.error(f"❌ Roster update failed: {e}")

    def start(self):
        """스케줄러 시작"""
        # 1. 매일 오전 2시: 경기 결과 업데이트 (EPL 경기 종료 후)
        self.scheduler.add_job(
            self.update_match_results_job,
            CronTrigger(hour=2, minute=0),
            id='daily_match_update',
            name='Daily Match Result Update',
            replace_existing=True
        )

        # 2. 매일 오전 2시 10분: 리그 순위표 업데이트
        self.scheduler.add_job(
            self.update_standings_job,
            CronTrigger(hour=2, minute=10),
            id='daily_standings_update',
            name='Daily Standings Update',
            replace_existing=True
        )

        # 3. 매주 월요일 오전 3시: 선수 로스터 업데이트
        self.scheduler.add_job(
            self.update_rosters_job,
            CronTrigger(day_of_week='mon', hour=3, minute=0),
            id='weekly_roster_update',
            name='Weekly Roster Update',
            replace_existing=True
        )

        # 테스트용: 서버 시작 1분 후 1회 실행 (선택사항)
        # from datetime import datetime, timedelta
        # self.scheduler.add_job(
        #     self.update_match_results_job,
        #     'date',
        #     run_date=datetime.now() + timedelta(minutes=1),
        #     id='startup_test',
        #     name='Startup Test Update'
        # )

        self.scheduler.start()
        logger.info("📅 Scheduler started with 3 jobs:")
        logger.info("  - Daily match updates: 02:00 KST")
        logger.info("  - Daily standings updates: 02:10 KST")
        logger.info("  - Weekly roster updates: Monday 03:00 KST")

    def stop(self):
        """스케줄러 중지"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Scheduler stopped")

    def get_jobs(self):
        """등록된 작업 목록"""
        return self.scheduler.get_jobs()


# 싱글톤 인스턴스
_scheduler_instance = None


def get_scheduler():
    """스케줄러 인스턴스 가져오기"""
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = MatchUpdateScheduler()
    return _scheduler_instance


if __name__ == "__main__":
    # 테스트
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    scheduler = MatchUpdateScheduler()
    scheduler.start()

    logger.info("Scheduler is running. Press Ctrl+C to exit.")
    logger.info("Registered jobs:")
    for job in scheduler.get_jobs():
        logger.info(f"  - {job.name}: {job.next_run_time}")

    try:
        # Keep running
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down scheduler...")
        scheduler.stop()
