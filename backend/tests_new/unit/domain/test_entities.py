"""
Phase 2 Unit Tests - Domain Entities
Tests core domain entities
"""
import pytest
from datetime import datetime
from backend.core.domain.entities.player import Player, PlayerStats
from backend.core.domain.entities.team import Team, TeamStats
from backend.core.domain.entities.rating import PlayerRatings, AttributeRating
from backend.core.domain.entities.match import Match, MatchScore, MatchStatus, MatchResult
from backend.core.domain.value_objects.player_id import PlayerId, TeamId, MatchId
from backend.core.domain.value_objects.position import Position
from backend.core.domain.value_objects.rating_value import RatingValue


class TestPlayerEntity:
    """Test Player entity"""

    def test_create_valid_player(self):
        """Test creating valid Player"""
        player = Player(
            id=PlayerId(1),
            external_id=100,
            name="Test Player",
            position=Position.from_string("FW", "ST"),
            team_id=TeamId(10),
            age=25
        )

        assert player.id == PlayerId(1)
        assert player.name == "Test Player"
        assert player.age == 25

    def test_player_name_validation(self):
        """Test player name cannot be empty"""
        with pytest.raises(ValueError, match="name cannot be empty"):
            Player(
                id=PlayerId(1),
                external_id=100,
                name="",
                position=Position.from_string("FW", "ST"),
                team_id=TeamId(10),
                age=25
            )

    def test_player_age_validation(self):
        """Test player age must be 16-50"""
        # Too young
        with pytest.raises(ValueError, match="Invalid age"):
            Player(
                id=PlayerId(1),
                external_id=100,
                name="Test Player",
                position=Position.from_string("FW", "ST"),
                team_id=TeamId(10),
                age=15
            )

        # Too old
        with pytest.raises(ValueError, match="Invalid age"):
            Player(
                id=PlayerId(1),
                external_id=100,
                name="Test Player",
                position=Position.from_string("FW", "ST"),
                team_id=TeamId(10),
                age=51
            )

    def test_player_stats(self):
        """Test PlayerStats calculations"""
        stats = PlayerStats(
            appearances=10,
            starts=8,
            minutes=720,
            goals=5,
            assists=3
        )

        assert stats.minutes_per_appearance == 72.0
        assert stats.goals_per_90 == 0.625  # (5/720) * 90
        assert stats.goal_contributions_per_90 == 1.0  # ((5+3)/720) * 90

    def test_player_is_regular_starter(self):
        """Test is_regular_starter()"""
        player = Player(
            id=PlayerId(1),
            external_id=100,
            name="Test Player",
            position=Position.from_string("FW", "ST"),
            team_id=TeamId(10),
            age=25,
            stats=PlayerStats(appearances=10, starts=8)
        )

        assert player.is_regular_starter(min_start_ratio=0.5) is True
        assert player.is_regular_starter(min_start_ratio=0.9) is False

    def test_player_equality(self):
        """Test player equality based on ID"""
        player1 = Player(
            id=PlayerId(1),
            external_id=100,
            name="Player 1",
            position=Position.from_string("FW", "ST"),
            team_id=TeamId(10),
            age=25
        )

        player2 = Player(
            id=PlayerId(1),
            external_id=200,
            name="Player 2",
            position=Position.from_string("GK"),
            team_id=TeamId(20),
            age=30
        )

        # Same ID = equal
        assert player1 == player2
        assert hash(player1) == hash(player2)


class TestTeamEntity:
    """Test Team entity"""

    def test_create_valid_team(self):
        """Test creating valid Team"""
        team = Team(
            id=TeamId(1),
            external_id=10,
            name="Test FC",
            short_name="TST"
        )

        assert team.id == TeamId(1)
        assert team.name == "Test FC"
        assert team.get_squad_size() == 0

    def test_team_add_player(self):
        """Test adding player to squad"""
        team = Team(
            id=TeamId(1),
            external_id=10,
            name="Test FC",
            short_name="TST"
        )

        player_id = PlayerId(100)
        team.add_player(player_id)

        assert team.get_squad_size() == 1
        assert team.has_player(player_id) is True

    def test_team_remove_player(self):
        """Test removing player from squad"""
        team = Team(
            id=TeamId(1),
            external_id=10,
            name="Test FC",
            short_name="TST"
        )

        player_id = PlayerId(100)
        team.add_player(player_id)
        team.remove_player(player_id)

        assert team.get_squad_size() == 0
        assert team.has_player(player_id) is False

    def test_team_stats_calculations(self):
        """Test TeamStats calculated properties"""
        stats = TeamStats(
            matches_played=10,
            wins=6,
            draws=2,
            losses=2,
            goals_for=20,
            goals_against=10
        )

        assert stats.points == 20  # 6*3 + 2*1
        assert stats.goal_difference == 10
        assert stats.win_rate == 60.0
        assert stats.goals_per_game == 2.0


class TestPlayerRatingsEntity:
    """Test PlayerRatings entity"""

    def test_create_player_ratings(self):
        """Test creating PlayerRatings"""
        ratings = PlayerRatings(player_id=PlayerId(1))

        assert ratings.player_id == PlayerId(1)
        assert ratings.get_rating_count() == 0

    def test_add_rating(self):
        """Test adding attribute rating"""
        ratings = PlayerRatings(player_id=PlayerId(1))

        ratings.add_rating("finishing", RatingValue(4.5), "Great finisher")

        assert ratings.get_rating_count() == 1
        assert ratings.has_rating("finishing") is True
        assert ratings.get_rating_value("finishing") == RatingValue(4.5)

    def test_get_all_ratings_dict(self):
        """Test getting all ratings as dictionary"""
        ratings = PlayerRatings(player_id=PlayerId(1))

        ratings.add_rating("finishing", RatingValue(4.5))
        ratings.add_rating("pace", RatingValue(4.0))

        ratings_dict = ratings.get_all_ratings_dict()

        assert len(ratings_dict) == 2
        assert ratings_dict["finishing"] == RatingValue(4.5)
        assert ratings_dict["pace"] == RatingValue(4.0)


class TestMatchEntity:
    """Test Match entity"""

    def test_create_match(self):
        """Test creating Match"""
        match = Match(
            id=MatchId(1),
            home_team_id=TeamId(10),
            away_team_id=TeamId(20),
            scheduled_date=datetime.utcnow()
        )

        assert match.status == MatchStatus.SCHEDULED
        assert match.score.home == 0
        assert match.score.away == 0

    def test_match_lifecycle(self):
        """Test match status lifecycle"""
        match = Match(
            id=MatchId(1),
            home_team_id=TeamId(10),
            away_team_id=TeamId(20),
            scheduled_date=datetime.utcnow()
        )

        # Start match
        match.start_match()
        assert match.status == MatchStatus.IN_PROGRESS

        # Finish match
        match.finish_match()
        assert match.status == MatchStatus.FINISHED

    def test_record_goal(self):
        """Test recording goal"""
        match = Match(
            id=MatchId(1),
            home_team_id=TeamId(10),
            away_team_id=TeamId(20),
            scheduled_date=datetime.utcnow()
        )

        match.start_match()
        match.record_goal(team="home", minute=23)

        assert match.score.home == 1
        assert match.score.away == 0
        assert len(match.get_goals()) == 1

    def test_match_result(self):
        """Test getting match result"""
        match = Match(
            id=MatchId(1),
            home_team_id=TeamId(10),
            away_team_id=TeamId(20),
            scheduled_date=datetime.utcnow()
        )

        match.start_match()
        match.set_score(2, 1)
        match.finish_match()

        assert match.get_result() == MatchResult.HOME_WIN
        assert match.get_winner_team_id() == TeamId(10)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
