"""
Team Strength Repository
Repository pattern for team domain data (strengths, formations, lineups, tactics)
"""

import sys
import os
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import logging

# Add parent directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from database.connection import DatabasePool, db_pool

logger = logging.getLogger(__name__)


class TeamStrengthRepository:
    """
    Repository for team strength data

    Provides CRUD operations with automatic versioning and derived attributes
    """

    def __init__(self, db: DatabasePool = None):
        """
        Initialize repository

        Args:
            db: DatabasePool instance (default: global db_pool)
        """
        self.db = db or db_pool

    # ==========================================================================
    # CREATE Operations
    # ==========================================================================

    def save_team_strength(
        self,
        team_name: str,
        ratings: Dict[str, float],
        comment: Optional[str] = None,
        pc_components: Optional[Dict[str, float]] = None
    ) -> int:
        """
        Save new version of team strength

        Args:
            team_name: Team name
            ratings: Dictionary of 18 attribute ratings (0-5 scale)
            comment: Optional comment
            pc_components: Optional PCA components (pc1, pc2, pc3, pc4)

        Returns:
            ID of created team_strengths record

        Example:
            >>> repo = TeamStrengthRepository()
            >>> ratings = {
            ...     'tactical_understanding': 3.5,
            ...     'positioning_balance': 3.2,
            ...     # ... 16 more attributes
            ... }
            >>> strength_id = repo.save_team_strength('Arsenal', ratings, 'Week 10 update')
        """
        with self.db.get_cursor() as cursor:
            # Get or create team
            cursor.execute("""
                INSERT INTO teams (name)
                VALUES (%s)
                ON CONFLICT (name) DO UPDATE
                SET updated_at = CURRENT_TIMESTAMP
                RETURNING id
            """, (team_name,))

            team_id = cursor.fetchone()['id']

            # Extract rating values in order
            rating_columns = [
                'tactical_understanding', 'positioning_balance', 'role_clarity',
                'buildup_quality', 'pass_network', 'final_third_penetration', 'goal_conversion',
                'backline_organization', 'central_control', 'flank_defense', 'counter_prevention',
                'pressing_organization', 'attack_to_defense_transition', 'defense_to_attack_transition',
                'set_piece_threat', 'defensive_resilience',
                'game_reading', 'team_chemistry'
            ]

            # Build insert query
            columns = rating_columns.copy()
            values = [ratings.get(col) for col in rating_columns]

            # Add PCA components if provided
            if pc_components:
                for pc in ['pc1', 'pc2', 'pc3', 'pc4']:
                    if pc in pc_components:
                        columns.append(pc)
                        values.append(pc_components[pc])

            # Add metadata
            columns.append('comment')
            values.append(comment)

            placeholders = ', '.join(['%s'] * len(columns))
            column_list = ', '.join(columns)

            cursor.execute(f"""
                INSERT INTO team_strengths (team_id, {column_list})
                VALUES (%s, {placeholders})
                RETURNING id, version, attack_strength_manual, defense_strength_manual, press_intensity_manual
            """, [team_id] + values)

            result = cursor.fetchone()

            logger.info(
                f"Saved team strength for {team_name} "
                f"(v{result['version']}, attack={result['attack_strength_manual']:.1f}, "
                f"defense={result['defense_strength_manual']:.1f})"
            )

            return result['id']

    def save_formation(
        self,
        team_name: str,
        formation: str,
        formation_data: Optional[Dict] = None
    ) -> int:
        """
        Save team formation

        Args:
            team_name: Team name
            formation: Formation string (e.g., "4-3-3")
            formation_data: Optional tactical details (JSONB)

        Returns:
            Formation record ID
        """
        with self.db.get_cursor() as cursor:
            # Get team ID
            cursor.execute("SELECT id FROM teams WHERE name = %s", (team_name,))
            team = cursor.fetchone()

            if not team:
                raise ValueError(f"Team '{team_name}' not found")

            team_id = team['id']

            # Insert formation
            cursor.execute("""
                INSERT INTO formations (team_id, formation, formation_data)
                VALUES (%s, %s, %s)
                RETURNING id, version
            """, (team_id, formation, formation_data or {}))

            result = cursor.fetchone()
            logger.info(f"Saved formation for {team_name}: {formation} (v{result['version']})")

            return result['id']

    def save_lineup(
        self,
        team_name: str,
        formation: str,
        lineup: Dict[str, str]
    ) -> int:
        """
        Save team lineup

        Args:
            team_name: Team name
            formation: Formation string
            lineup: Position’Player mapping (e.g., {"GK": "Ramsdale", "LB": "Zinchenko", ...})

        Returns:
            Lineup record ID
        """
        with self.db.get_cursor() as cursor:
            cursor.execute("SELECT id FROM teams WHERE name = %s", (team_name,))
            team = cursor.fetchone()

            if not team:
                raise ValueError(f"Team '{team_name}' not found")

            team_id = team['id']

            cursor.execute("""
                INSERT INTO lineups (team_id, formation, lineup)
                VALUES (%s, %s, %s)
                RETURNING id, version
            """, (team_id, formation, lineup))

            result = cursor.fetchone()
            logger.info(f"Saved lineup for {team_name} ({formation}, v{result['version']})")

            return result['id']

    def save_tactics(
        self,
        team_name: str,
        defensive_line: str = None,
        pressing_trigger: str = None,
        width: str = None,
        buildup_tempo: str = None
    ) -> int:
        """
        Save team tactics

        Args:
            team_name: Team name
            defensive_line: "high", "medium", "low"
            pressing_trigger: e.g., "loss_of_possession"
            width: "narrow", "balanced", "wide"
            buildup_tempo: "slow", "medium", "fast"

        Returns:
            Tactics record ID
        """
        with self.db.get_cursor() as cursor:
            cursor.execute("SELECT id FROM teams WHERE name = %s", (team_name,))
            team = cursor.fetchone()

            if not team:
                raise ValueError(f"Team '{team_name}' not found")

            team_id = team['id']

            cursor.execute("""
                INSERT INTO tactics (team_id, defensive_line, pressing_trigger, width, buildup_tempo)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id, version
            """, (team_id, defensive_line, pressing_trigger, width, buildup_tempo))

            result = cursor.fetchone()
            logger.info(f"Saved tactics for {team_name} (v{result['version']})")

            return result['id']

    # ==========================================================================
    # READ Operations
    # ==========================================================================

    def get_team_strength(self, team_name: str) -> Optional[Dict]:
        """
        Get active team strength by team name

        Args:
            team_name: Team name

        Returns:
            Dictionary with all strength attributes, or None if not found

        Example:
            >>> strength = repo.get_team_strength('Arsenal')
            >>> print(strength['attack_strength_manual'])  # 85.5
        """
        with self.db.get_cursor() as cursor:
            cursor.execute("""
                SELECT ts.*
                FROM team_strengths ts
                JOIN teams t ON ts.team_id = t.id
                WHERE t.name = %s AND ts.is_active = TRUE
            """, (team_name,))

            return cursor.fetchone()

    def get_all_team_strengths(self) -> List[Dict]:
        """
        Get all active team strengths

        Returns:
            List of team strength dictionaries
        """
        with self.db.get_cursor() as cursor:
            cursor.execute("""
                SELECT t.name, ts.*
                FROM team_strengths ts
                JOIN teams t ON ts.team_id = t.id
                WHERE ts.is_active = TRUE
                ORDER BY t.name
            """)

            return cursor.fetchall()

    def get_formation(self, team_name: str) -> Optional[Dict]:
        """Get active formation"""
        with self.db.get_cursor() as cursor:
            cursor.execute("""
                SELECT f.*
                FROM formations f
                JOIN teams t ON f.team_id = t.id
                WHERE t.name = %s AND f.is_active = TRUE
            """, (team_name,))

            return cursor.fetchone()

    def get_lineup(self, team_name: str) -> Optional[Dict]:
        """Get active lineup"""
        with self.db.get_cursor() as cursor:
            cursor.execute("""
                SELECT l.*
                FROM lineups l
                JOIN teams t ON l.team_id = t.id
                WHERE t.name = %s AND l.is_active = TRUE
            """, (team_name,))

            return cursor.fetchone()

    def get_tactics(self, team_name: str) -> Optional[Dict]:
        """Get active tactics"""
        with self.db.get_cursor() as cursor:
            cursor.execute("""
                SELECT tac.*
                FROM tactics tac
                JOIN teams t ON tac.team_id = t.id
                WHERE t.name = %s AND tac.is_active = TRUE
            """, (team_name,))

            return cursor.fetchone()

    def get_team_complete(self, team_name: str) -> Optional[Dict]:
        """
        Get complete team data (strength, formation, lineup, tactics)

        Args:
            team_name: Team name

        Returns:
            Dictionary with all team data
        """
        with self.db.get_cursor() as cursor:
            cursor.execute("""
                SELECT
                    t.id,
                    t.name,
                    ts.attack_strength_manual,
                    ts.defense_strength_manual,
                    ts.press_intensity_manual,
                    ts.tactical_understanding,
                    ts.team_chemistry,
                    ts.buildup_quality,
                    ts.pass_network,
                    ts.final_third_penetration,
                    ts.goal_conversion,
                    ts.backline_organization,
                    ts.central_control,
                    ts.flank_defense,
                    ts.counter_prevention,
                    ts.pressing_organization,
                    ts.attack_to_defense_transition,
                    ts.defense_to_attack_transition,
                    ts.set_piece_threat,
                    ts.defensive_resilience,
                    ts.game_reading,
                    ts.role_clarity,
                    ts.positioning_balance,
                    ts.pc1,
                    ts.pc2,
                    ts.pc3,
                    ts.pc4,
                    ts.comment,
                    ts.version AS strength_version,
                    ts.created_at AS strength_updated,
                    f.formation,
                    f.formation_data,
                    l.lineup,
                    tac.defensive_line,
                    tac.pressing_trigger,
                    tac.width,
                    tac.buildup_tempo
                FROM teams t
                LEFT JOIN team_strengths ts ON t.id = ts.team_id AND ts.is_active = TRUE
                LEFT JOIN formations f ON t.id = f.team_id AND f.is_active = TRUE
                LEFT JOIN lineups l ON t.id = l.team_id AND l.is_active = TRUE
                LEFT JOIN tactics tac ON t.id = tac.team_id AND tac.is_active = TRUE
                WHERE t.name = %s
            """, (team_name,))

            return cursor.fetchone()

    def get_team_rankings(self, limit: int = 20) -> List[Dict]:
        """
        Get team rankings by overall strength

        Args:
            limit: Max number of teams to return

        Returns:
            List of teams ranked by strength
        """
        with self.db.get_cursor() as cursor:
            cursor.execute("""
                SELECT
                    t.name,
                    ts.attack_strength_manual,
                    ts.defense_strength_manual,
                    ts.press_intensity_manual,
                    (ts.attack_strength_manual + ts.defense_strength_manual) / 2.0 AS overall_strength,
                    RANK() OVER (ORDER BY (ts.attack_strength_manual + ts.defense_strength_manual) DESC) AS rank
                FROM teams t
                JOIN team_strengths ts ON t.id = ts.team_id
                WHERE ts.is_active = TRUE
                ORDER BY rank
                LIMIT %s
            """, (limit,))

            return cursor.fetchall()

    # ==========================================================================
    # VERSIONING Operations
    # ==========================================================================

    def get_strength_history(self, team_name: str, limit: int = 10) -> List[Dict]:
        """
        Get historical versions of team strength

        Args:
            team_name: Team name
            limit: Max number of versions to return

        Returns:
            List of historical strength records
        """
        with self.db.get_cursor() as cursor:
            cursor.execute("""
                SELECT
                    ts.id,
                    ts.version,
                    ts.attack_strength_manual,
                    ts.defense_strength_manual,
                    ts.press_intensity_manual,
                    ts.comment,
                    ts.created_at,
                    ts.is_active
                FROM team_strengths ts
                JOIN teams t ON ts.team_id = t.id
                WHERE t.name = %s
                ORDER BY ts.created_at DESC
                LIMIT %s
            """, (team_name, limit))

            return cursor.fetchall()

    def compare_strength_versions(
        self,
        team_name: str,
        version1: int,
        version2: int
    ) -> Dict:
        """
        Compare two versions of team strength

        Args:
            team_name: Team name
            version1: First version number
            version2: Second version number

        Returns:
            Dictionary with version comparison

        Example:
            >>> diff = repo.compare_strength_versions('Arsenal', 1, 2)
            >>> print(diff['differences']['attack_strength_manual'])  # +2.5
        """
        with self.db.get_cursor() as cursor:
            cursor.execute("""
                SELECT
                    ts.version,
                    ts.attack_strength_manual,
                    ts.defense_strength_manual,
                    ts.press_intensity_manual,
                    ts.tactical_understanding,
                    ts.positioning_balance,
                    ts.role_clarity,
                    ts.buildup_quality,
                    ts.pass_network,
                    ts.final_third_penetration,
                    ts.goal_conversion,
                    ts.backline_organization,
                    ts.central_control,
                    ts.flank_defense,
                    ts.counter_prevention,
                    ts.pressing_organization,
                    ts.attack_to_defense_transition,
                    ts.defense_to_attack_transition,
                    ts.set_piece_threat,
                    ts.defensive_resilience,
                    ts.game_reading,
                    ts.team_chemistry,
                    ts.created_at,
                    ts.comment
                FROM team_strengths ts
                JOIN teams t ON ts.team_id = t.id
                WHERE t.name = %s AND ts.version IN (%s, %s)
                ORDER BY ts.version
            """, (team_name, version1, version2))

            versions = cursor.fetchall()

            if len(versions) != 2:
                return {'error': f'Could not find both versions {version1} and {version2}'}

            v1, v2 = versions

            # Calculate differences
            differences = {}
            numeric_columns = [
                'attack_strength_manual', 'defense_strength_manual', 'press_intensity_manual',
                'tactical_understanding', 'positioning_balance', 'role_clarity',
                'buildup_quality', 'pass_network', 'final_third_penetration', 'goal_conversion',
                'backline_organization', 'central_control', 'flank_defense', 'counter_prevention',
                'pressing_organization', 'attack_to_defense_transition', 'defense_to_attack_transition',
                'set_piece_threat', 'defensive_resilience', 'game_reading', 'team_chemistry'
            ]

            for col in numeric_columns:
                if v1[col] is not None and v2[col] is not None:
                    diff = float(v2[col]) - float(v1[col])
                    if abs(diff) > 0.01:  # Only show meaningful differences
                        differences[col] = diff

            return {
                'team': team_name,
                'version1': dict(v1),
                'version2': dict(v2),
                'differences': differences
            }

    # ==========================================================================
    # UTILITY Operations
    # ==========================================================================

    def compare_teams(self, team1: str, team2: str) -> Dict:
        """
        Compare two teams' strengths

        Args:
            team1: First team name
            team2: Second team name

        Returns:
            Comparison dictionary

        Example:
            >>> comparison = repo.compare_teams('Arsenal', 'Tottenham')
            >>> print(comparison['attack_diff'])  # +2.5 (Arsenal stronger)
        """
        with self.db.get_cursor() as cursor:
            cursor.execute("""
                SELECT * FROM compare_teams(%s, %s)
            """, (team1, team2))

            results = cursor.fetchall()

            comparison = {
                'team1': team1,
                'team2': team2,
                'attributes': {}
            }

            for row in results:
                comparison['attributes'][row['attribute']] = {
                    'team1': float(row['team1_value']) if row['team1_value'] else None,
                    'team2': float(row['team2_value']) if row['team2_value'] else None,
                    'difference': float(row['difference']) if row['difference'] else None
                }

            return comparison

    def list_teams(self) -> List[str]:
        """
        Get list of all team names

        Returns:
            List of team names
        """
        with self.db.get_cursor() as cursor:
            cursor.execute("SELECT name FROM teams ORDER BY name")
            return [row['name'] for row in cursor.fetchall()]


# ==========================================================================
# Testing
# ==========================================================================

def test_team_repository():
    """Test TeamStrengthRepository"""
    print("=" * 70)
    print("Testing TeamStrengthRepository")
    print("=" * 70)

    try:
        # Initialize DB pool
        db_pool.initialize()

        repo = TeamStrengthRepository()

        # Test 1: Save team strength
        print("\nTest 1: Save Team Strength")
        print("-" * 70)

        ratings = {
            'tactical_understanding': 3.5,
            'positioning_balance': 3.2,
            'role_clarity': 3.3,
            'buildup_quality': 3.8,
            'pass_network': 3.7,
            'final_third_penetration': 3.6,
            'goal_conversion': 3.4,
            'backline_organization': 3.1,
            'central_control': 3.0,
            'flank_defense': 2.9,
            'counter_prevention': 3.2,
            'pressing_organization': 3.4,
            'attack_to_defense_transition': 3.3,
            'defense_to_attack_transition': 3.5,
            'set_piece_threat': 3.2,
            'defensive_resilience': 3.1,
            'game_reading': 3.3,
            'team_chemistry': 3.4
        }

        strength_id = repo.save_team_strength('Test Team FC', ratings, 'Initial test data')
        print(f" Saved team strength (ID: {strength_id})")

        # Test 2: Retrieve team strength
        print("\nTest 2: Retrieve Team Strength")
        print("-" * 70)

        strength = repo.get_team_strength('Test Team FC')
        print(f"Attack: {strength['attack_strength_manual']:.1f}")
        print(f"Defense: {strength['defense_strength_manual']:.1f}")
        print(f"Press: {strength['press_intensity_manual']:.1f}")
        print(" Retrieved team strength")

        # Test 3: Version history
        print("\nTest 3: Version History")
        print("-" * 70)

        # Save another version
        ratings['buildup_quality'] = 4.0  # Improve buildup
        repo.save_team_strength('Test Team FC', ratings, 'Improved buildup')

        history = repo.get_strength_history('Test Team FC', limit=5)
        print(f"Versions found: {len(history)}")
        for v in history:
            print(f"  v{v['version']}: {v['comment']} (Active: {v['is_active']})")
        print(" Version history working")

        # Test 4: Team rankings
        print("\nTest 4: Team Rankings")
        print("-" * 70)

        rankings = repo.get_team_rankings(limit=5)
        print("Top teams:")
        for rank in rankings:
            print(f"  {rank['rank']}. {rank['name']}: {rank['overall_strength']:.1f}")
        print(" Team rankings working")

        print("\n" + "=" * 70)
        print(" All TeamStrengthRepository Tests PASSED!")
        print("=" * 70)

    except Exception as e:
        print(f"L Test failed: {e}")
        import traceback
        traceback.print_exc()

    finally:
        db_pool.close()


if __name__ == "__main__":
    test_team_repository()
