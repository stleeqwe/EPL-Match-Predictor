# -*- coding: utf-8 -*-
"""
FieldState - Spatial Game State Representation

Part of Phase 2.0 Architecture Redesign
Provides spatial awareness through zone-based field representation

Features:
- 96-zone grid (8 wide x 12 long)
- Zone control tracking (which team dominates each zone)
- Pressure maps (pressure level at each location)
- Passing lane analysis (which passes are blocked)
- Local density calculation (crowding detection)
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


# Field dimensions (in meters)
FIELD_LENGTH = 105.0  # Standard pitch length
FIELD_WIDTH = 68.0    # Standard pitch width

# Grid configuration
ZONES_WIDTH = 8   # 8 zones across width
ZONES_LENGTH = 12  # 12 zones along length
TOTAL_ZONES = ZONES_WIDTH * ZONES_LENGTH  # 96 zones

# Zone dimensions
ZONE_WIDTH = FIELD_WIDTH / ZONES_WIDTH    # ~8.5m
ZONE_LENGTH = FIELD_LENGTH / ZONES_LENGTH  # ~8.75m

# Influence radii
PLAYER_CONTROL_RADIUS = 2.0   # Immediate control
PLAYER_PRESSURE_RADIUS = 5.0  # Pressure/threat zone
PLAYER_VISION_RANGE = 20.0    # Passing/awareness range


@dataclass
class Zone:
    """Represents a zone on the field"""
    id: int
    x_min: float
    x_max: float
    y_min: float
    y_max: float
    center_x: float
    center_y: float

    def contains_point(self, x: float, y: float) -> bool:
        """Check if point is in this zone"""
        return (self.x_min <= x < self.x_max and
                self.y_min <= y < self.y_max)

    def distance_to_point(self, x: float, y: float) -> float:
        """Distance from zone center to point"""
        dx = self.center_x - x
        dy = self.center_y - y
        return np.sqrt(dx*dx + dy*dy)


@dataclass
class PassingLane:
    """Represents a passing lane between two players"""
    clear: bool
    risk: float  # 0.0 to 1.0 (0 = safe, 1 = very risky)
    interceptors: List[any]  # Players who could intercept
    distance: float
    blocked_by_zones: List[int]


class FieldState:
    """
    Spatial representation of game state

    Provides:
    - Zone-based field control tracking
    - Pressure maps showing contested areas
    - Passing lane analysis
    - Local density calculation
    - Spatial queries (who's near what, etc.)

    This is the foundation for realistic spatial-aware simulation.
    Without this, players are just points in space with no awareness
    of their surroundings.
    """

    def __init__(self):
        """Initialize field state with zone grid"""
        # Create 96-zone grid
        self.zones: List[Zone] = self._create_zone_grid()

        # Zone control tracking
        self.zone_control: Dict[int, Dict[str, float]] = {}
        for zone in self.zones:
            self.zone_control[zone.id] = {
                'home': 0.0,
                'away': 0.0,
                'contested': 0.0
            }

        # Pressure map (track pressure at key locations)
        self.pressure_map: Dict[str, float] = {}  # team -> pressure value

        # Player influence tracking
        self.player_influences: Dict[str, List[Tuple[float, float, float]]] = {
            'home': [],  # [(x, y, influence_strength)]
            'away': []
        }

        # Cached calculations (updated each tick)
        self._cached_passing_lanes = {}
        self._cached_densities = {}

    def _create_zone_grid(self) -> List[Zone]:
        """
        Create 96-zone grid covering the field

        Field coordinates:
        - X: -52.5 to +52.5 (length, 105m)
        - Y: -34.0 to +34.0 (width, 68m)
        - Origin at center circle

        Returns:
            List of 96 Zone objects
        """
        zones = []
        zone_id = 0

        # Starting coordinates
        x_start = -FIELD_LENGTH / 2
        y_start = -FIELD_WIDTH / 2

        # Create grid (12 rows x 8 columns)
        for i in range(ZONES_LENGTH):
            x_min = x_start + i * ZONE_LENGTH
            x_max = x_min + ZONE_LENGTH
            x_center = (x_min + x_max) / 2

            for j in range(ZONES_WIDTH):
                y_min = y_start + j * ZONE_WIDTH
                y_max = y_min + ZONE_WIDTH
                y_center = (y_min + y_max) / 2

                zone = Zone(
                    id=zone_id,
                    x_min=x_min,
                    x_max=x_max,
                    y_min=y_min,
                    y_max=y_max,
                    center_x=x_center,
                    center_y=y_center
                )
                zones.append(zone)
                zone_id += 1

        return zones

    def update(self, home_players: List[any], away_players: List[any],
               ball_position: np.ndarray) -> None:
        """
        Update field state based on current player positions

        Args:
            home_players: List of home team player states
            away_players: List of away team player states
            ball_position: Current ball position [x, y, z]
        """
        # Clear previous frame data
        self._clear_frame_data()

        # Calculate zone control
        self._calculate_zone_control(home_players, away_players)

        # Update player influences
        self._update_player_influences(home_players, away_players)

        # Update pressure map
        self._update_pressure_map(home_players, away_players, ball_position)

        # Clear caches (will be recalculated on demand)
        self._cached_passing_lanes.clear()
        self._cached_densities.clear()

    def _clear_frame_data(self) -> None:
        """Clear data from previous frame"""
        for zone_id in self.zone_control:
            self.zone_control[zone_id] = {
                'home': 0.0,
                'away': 0.0,
                'contested': 0.0
            }
        self.player_influences = {'home': [], 'away': []}
        self.pressure_map.clear()

    def _calculate_zone_control(self, home_players: List[any],
                                 away_players: List[any]) -> None:
        """
        Calculate which team controls each zone

        Control is based on:
        - Number of players in/near zone
        - Distance from zone center
        - Player positioning attributes
        """
        for zone in self.zones:
            home_influence = 0.0
            away_influence = 0.0

            # Calculate home team influence on this zone
            for player in home_players:
                influence = self._calculate_player_zone_influence(
                    player, zone
                )
                home_influence += influence

            # Calculate away team influence on this zone
            for player in away_players:
                influence = self._calculate_player_zone_influence(
                    player, zone
                )
                away_influence += influence

            # Normalize to percentages
            total = home_influence + away_influence
            if total > 0:
                home_pct = home_influence / total
                away_pct = away_influence / total

                # Contested if both teams have 30%+ control
                contested = 1.0 if (home_pct >= 0.3 and away_pct >= 0.3) else 0.0

                self.zone_control[zone.id] = {
                    'home': home_pct,
                    'away': away_pct,
                    'contested': contested
                }
            else:
                self.zone_control[zone.id] = {
                    'home': 0.0,
                    'away': 0.0,
                    'contested': 0.0
                }

    def _calculate_player_zone_influence(self, player: any, zone: Zone) -> float:
        """
        Calculate how much influence a player has on a zone

        Factors:
        - Distance from zone center
        - Player positioning attribute (optional)
        - Inverse square law (closer = much stronger)

        Args:
            player: Player state object
            zone: Zone object

        Returns:
            Influence value (0.0 to ~1.0)
        """
        # Get player position
        px = player.position[0]
        py = player.position[1]

        # Distance from zone center
        distance = zone.distance_to_point(px, py)

        # No influence if too far
        if distance > PLAYER_PRESSURE_RADIUS:
            return 0.0

        # Inverse square law (closer = stronger)
        # At distance=0: influence=1.0
        # At distance=5m: influence=0.0
        influence = (1.0 - (distance / PLAYER_PRESSURE_RADIUS)) ** 2

        # Optional: weight by positioning attribute if available
        if hasattr(player, 'attributes') and hasattr(player.attributes, 'positioning'):
            positioning_factor = player.attributes.positioning / 100.0
            influence *= (0.7 + 0.3 * positioning_factor)  # 70% base, 30% positioning

        return influence

    def _update_player_influences(self, home_players: List[any],
                                   away_players: List[any]) -> None:
        """Store player influence points for spatial queries"""
        for player in home_players:
            px = player.position[0]
            py = player.position[1]
            # Influence strength based on positioning attribute
            strength = 1.0
            if hasattr(player, 'attributes') and hasattr(player.attributes, 'positioning'):
                strength = player.attributes.positioning / 100.0
            self.player_influences['home'].append((px, py, strength))

        for player in away_players:
            px = player.position[0]
            py = player.position[1]
            strength = 1.0
            if hasattr(player, 'attributes') and hasattr(player.attributes, 'positioning'):
                strength = player.attributes.positioning / 100.0
            self.player_influences['away'].append((px, py, strength))

    def _update_pressure_map(self, home_players: List[any],
                             away_players: List[any],
                             ball_position: np.ndarray) -> None:
        """
        Calculate pressure levels near the ball

        Pressure = number of opponents within PLAYER_PRESSURE_RADIUS
        """
        ball_x = ball_position[0]
        ball_y = ball_position[1]

        home_pressure = 0
        away_pressure = 0

        for player in home_players:
            dist = self._distance_2d(
                player.position[0], player.position[1],
                ball_x, ball_y
            )
            if dist < PLAYER_PRESSURE_RADIUS:
                home_pressure += 1

        for player in away_players:
            dist = self._distance_2d(
                player.position[0], player.position[1],
                ball_x, ball_y
            )
            if dist < PLAYER_PRESSURE_RADIUS:
                away_pressure += 1

        self.pressure_map['home'] = home_pressure
        self.pressure_map['away'] = away_pressure

    def get_zone_at_position(self, x: float, y: float) -> Optional[Zone]:
        """
        Get zone containing the given position

        Args:
            x, y: Position coordinates

        Returns:
            Zone object, or None if out of bounds
        """
        for zone in self.zones:
            if zone.contains_point(x, y):
                return zone
        return None

    def get_zone_control(self, zone_id: int) -> Dict[str, float]:
        """
        Get control percentages for a zone

        Returns:
            {'home': 0.0-1.0, 'away': 0.0-1.0, 'contested': 0.0/1.0}
        """
        return self.zone_control.get(zone_id, {'home': 0.0, 'away': 0.0, 'contested': 0.0})

    def get_local_density(self, position: np.ndarray, radius: float = 10.0,
                         home_players: List[any] = None,
                         away_players: List[any] = None) -> Dict[str, int]:
        """
        Count players within radius of position

        Args:
            position: Center point [x, y, z]
            radius: Search radius in meters
            home_players: Home team players
            away_players: Away team players

        Returns:
            {'home': count, 'away': count, 'total': count}
        """
        # Use cached result if available
        cache_key = f"{position[0]:.1f},{position[1]:.1f},{radius}"
        if cache_key in self._cached_densities:
            return self._cached_densities[cache_key]

        x, y = position[0], position[1]

        home_count = 0
        away_count = 0

        if home_players:
            for player in home_players:
                dist = self._distance_2d(player.position[0], player.position[1], x, y)
                if dist < radius:
                    home_count += 1

        if away_players:
            for player in away_players:
                dist = self._distance_2d(player.position[0], player.position[1], x, y)
                if dist < radius:
                    away_count += 1

        result = {
            'home': home_count,
            'away': away_count,
            'total': home_count + away_count
        }

        self._cached_densities[cache_key] = result
        return result

    def analyze_passing_lane(self, passer_pos: np.ndarray, receiver_pos: np.ndarray,
                            opponents: List[any]) -> PassingLane:
        """
        Analyze a passing lane for interception risk

        Args:
            passer_pos: Passer position [x, y, z]
            receiver_pos: Receiver position [x, y, z]
            opponents: List of opponent player states

        Returns:
            PassingLane object with risk analysis
        """
        # Calculate lane
        p1 = np.array([passer_pos[0], passer_pos[1]])
        p2 = np.array([receiver_pos[0], receiver_pos[1]])
        distance = np.linalg.norm(p2 - p1)

        # Find potential interceptors
        interceptors = []
        max_intercept_risk = 0.0

        for opponent in opponents:
            opp_pos = np.array([opponent.position[0], opponent.position[1]])

            # Calculate distance from opponent to passing lane
            lane_dist = self._point_to_line_distance(opp_pos, p1, p2)

            # Only consider if close enough to lane
            if lane_dist < 3.0:  # 3m intercept radius
                # Calculate position along lane (0.0 to 1.0)
                projection = self._project_point_on_line(opp_pos, p1, p2)

                # Only if opponent is between passer and receiver
                if 0.0 <= projection <= 1.0:
                    # Calculate intercept risk
                    risk = 1.0 - (lane_dist / 3.0)  # Closer = higher risk

                    # Bonus risk if opponent has high interception attribute
                    if hasattr(opponent, 'attributes') and hasattr(opponent.attributes, 'interception'):
                        intercept_attr = opponent.attributes.interception / 100.0
                        risk *= (0.7 + 0.3 * intercept_attr)

                    interceptors.append(opponent)
                    max_intercept_risk = max(max_intercept_risk, risk)

        # Determine if lane is clear
        clear = len(interceptors) == 0
        overall_risk = min(1.0, max_intercept_risk * 1.5)  # Scale up risk

        return PassingLane(
            clear=clear,
            risk=overall_risk,
            interceptors=interceptors,
            distance=distance,
            blocked_by_zones=[]  # Could add zone analysis later
        )

    def get_pressure_on_player(self, player_pos: np.ndarray,
                              opponents: List[any]) -> float:
        """
        Calculate pressure level on a player

        Returns:
            Pressure value (0.0 = no pressure, 1.0+ = high pressure)
        """
        pressure = 0.0

        for opponent in opponents:
            dist = self._distance_2d(
                player_pos[0], player_pos[1],
                opponent.position[0], opponent.position[1]
            )

            if dist < PLAYER_PRESSURE_RADIUS:
                # Closer = more pressure (inverse relationship)
                contribution = (1.0 - dist / PLAYER_PRESSURE_RADIUS)
                pressure += contribution

        return pressure

    def get_space_available(self, position: np.ndarray, direction: np.ndarray,
                           opponents: List[any], distance: float = 10.0) -> float:
        """
        Calculate how much space is available in a direction

        Args:
            position: Starting position
            direction: Direction vector (normalized)
            opponents: Opponent players
            distance: How far to look ahead

        Returns:
            Space value (0.0 = blocked, 1.0 = completely open)
        """
        # Cast a ray in the direction and see how close opponents are
        # Sample points along the ray
        samples = 5
        min_clearance = float('inf')

        for i in range(1, samples + 1):
            t = (i / samples) * distance
            sample_point = position[:2] + direction[:2] * t

            # Find nearest opponent to this point
            for opponent in opponents:
                opp_pos = np.array([opponent.position[0], opponent.position[1]])
                dist_to_sample = np.linalg.norm(opp_pos - sample_point)
                min_clearance = min(min_clearance, dist_to_sample)

        # Convert to space metric (0.0 to 1.0)
        # If nearest opponent is 5m+ away, consider it open
        space = min(1.0, min_clearance / 5.0)
        return space

    def _distance_2d(self, x1: float, y1: float, x2: float, y2: float) -> float:
        """Calculate 2D distance"""
        dx = x2 - x1
        dy = y2 - y1
        return np.sqrt(dx*dx + dy*dy)

    def _point_to_line_distance(self, point: np.ndarray,
                                line_start: np.ndarray,
                                line_end: np.ndarray) -> float:
        """
        Calculate perpendicular distance from point to line segment

        Args:
            point: Point coordinates [x, y]
            line_start: Line start [x, y]
            line_end: Line end [x, y]

        Returns:
            Distance in meters
        """
        # Vector from start to end
        line_vec = line_end - line_start
        line_len = np.linalg.norm(line_vec)

        if line_len < 0.001:  # Degenerate line
            return np.linalg.norm(point - line_start)

        # Normalized line vector
        line_dir = line_vec / line_len

        # Vector from line start to point
        start_to_point = point - line_start

        # Project onto line
        projection = np.dot(start_to_point, line_dir)

        # Closest point on line
        if projection < 0:
            closest = line_start
        elif projection > line_len:
            closest = line_end
        else:
            closest = line_start + line_dir * projection

        # Distance from point to closest point
        return np.linalg.norm(point - closest)

    def _project_point_on_line(self, point: np.ndarray,
                              line_start: np.ndarray,
                              line_end: np.ndarray) -> float:
        """
        Project point onto line and return normalized position

        Returns:
            0.0 = at line_start, 1.0 = at line_end, <0 or >1 = beyond endpoints
        """
        line_vec = line_end - line_start
        line_len = np.linalg.norm(line_vec)

        if line_len < 0.001:
            return 0.0

        line_dir = line_vec / line_len
        start_to_point = point - line_start
        projection = np.dot(start_to_point, line_dir)

        return projection / line_len

    def get_summary(self) -> Dict:
        """
        Get summary of current field state

        Returns:
            Dictionary with field state statistics
        """
        # Count controlled zones
        home_controlled = 0
        away_controlled = 0
        contested_count = 0

        for zone_id, control in self.zone_control.items():
            if control['contested'] > 0.5:
                contested_count += 1
            elif control['home'] > control['away']:
                home_controlled += 1
            elif control['away'] > control['home']:
                away_controlled += 1

        return {
            'total_zones': TOTAL_ZONES,
            'home_controlled': home_controlled,
            'away_controlled': away_controlled,
            'contested': contested_count,
            'pressure_home': self.pressure_map.get('home', 0),
            'pressure_away': self.pressure_map.get('away', 0)
        }


# =============================================================================
# EXPORT
# =============================================================================

__all__ = ['FieldState', 'Zone', 'PassingLane']
