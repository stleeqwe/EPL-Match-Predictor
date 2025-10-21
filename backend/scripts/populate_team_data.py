"""
팀 데이터 자동 생성 스크립트
모든 팀의 선수 평가, 전술, 라인업, 포메이션 데이터 생성

핵심 4개 팀: Arsenal, Liverpool, Man City, Chelsea
"""

import os
import sys
import json
from datetime import datetime

# 경로 설정
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from database.player_schema import Player, PlayerRating, get_player_session

# 디렉토리 경로
DATA_DIR = os.path.join(backend_dir, 'data')
DB_PATH = os.path.join(DATA_DIR, 'epl_data.db')


# ==========================================================================
# 포지션별 속성 템플릿
# ==========================================================================

POSITION_ATTRIBUTES = {
    'Goalkeeper': [
        'reflexes', 'positioning_reading', 'handling', 'kicking',
        'aerial_duel', 'one_on_one', 'composure_judgement', 'distribution',
        'speed', 'leadership'
    ],
    'Defender': [  # CB, LB, RB
        'positioning_reading', 'composure_judgement', 'interception',
        'aerial_duel', 'tackle_marking', 'speed', 'passing',
        'physical_jumping', 'buildup_contribution', 'leadership'
    ],
    'Midfielder': [  # CM, CDM
        'passing', 'vision', 'positioning_reading', 'interception',
        'tackle_marking', 'stamina', 'composure_judgement',
        'buildup_contribution', 'leadership', 'speed'
    ],
    'Winger': [  # LW, RW
        'speed_dribbling', 'one_on_one_beating', 'speed', 'acceleration',
        'crossing_accuracy', 'shooting_accuracy', 'agility_direction_change',
        'cutting_in', 'defensive_contribution', 'creativity',
        'link_up_play', 'cutback_pass'
    ],
    'Striker': [  # ST, CF
        'finishing', 'positioning_reading', 'shooting_accuracy',
        'heading', 'one_on_one_beating', 'speed', 'acceleration',
        'link_up_play', 'physical_jumping', 'composure_judgement'
    ]
}


# ==========================================================================
# 팀 데이터 정의
# ==========================================================================

TEAMS_DATA = {
    'Arsenal': {
        'formation': '4-3-3',
        'lineup': {
            'GK': {
                'id': 7975,
                'name': 'David Raya',
                'position_type': 'Goalkeeper',
                'ratings': {
                    'reflexes': 4.5, 'positioning_reading': 4.25, 'handling': 4.0,
                    'kicking': 4.5, 'aerial_duel': 3.75, 'one_on_one': 4.25,
                    'composure_judgement': 4.5, 'distribution': 4.75,
                    'speed': 3.0, 'leadership': 4.0
                },
                'comment': 'Top-class shot-stopper with excellent distribution. Key for Arsenal\'s build-up play.'
            },
            'LB': {
                'id': 69914,
                'name': 'Riccardo Calafiori',
                'position_type': 'Defender',
                'ratings': {
                    'positioning_reading': 4.0, 'composure_judgement': 4.0,
                    'interception': 3.75, 'aerial_duel': 3.5, 'tackle_marking': 4.0,
                    'speed': 4.25, 'passing': 4.0, 'physical_jumping': 3.25,
                    'buildup_contribution': 4.25, 'leadership': 3.5
                },
                'comment': 'Modern full-back with excellent ball-playing ability. Contributes to attacking phases.'
            },
            'CB1': {
                'id': 67776,
                'name': 'Jurriën Timber',
                'position_type': 'Defender',
                'ratings': {
                    'positioning_reading': 4.25, 'composure_judgement': 4.0,
                    'interception': 4.0, 'aerial_duel': 3.5, 'tackle_marking': 4.0,
                    'speed': 4.0, 'passing': 4.0, 'physical_jumping': 3.25,
                    'buildup_contribution': 4.25, 'leadership': 3.75
                },
                'comment': 'Versatile defender with great pace and reading of the game. Can play multiple positions.'
            },
            'CB2': {
                'id': 50234,
                'name': 'Gabriel Magalhães',
                'position_type': 'Defender',
                'ratings': {
                    'positioning_reading': 4.5, 'composure_judgement': 4.25,
                    'interception': 4.25, 'aerial_duel': 4.75, 'tackle_marking': 4.5,
                    'speed': 3.75, 'passing': 3.75, 'physical_jumping': 4.75,
                    'buildup_contribution': 3.75, 'leadership': 4.5
                },
                'comment': 'Dominant aerial presence and Arsenal\'s defensive leader. Strong in both boxes.'
            },
            'RB': {
                'id': 114564,
                'name': 'Myles Lewis-Skelly',
                'position_type': 'Defender',
                'ratings': {
                    'positioning_reading': 3.75, 'composure_judgement': 3.75,
                    'interception': 3.5, 'aerial_duel': 3.0, 'tackle_marking': 3.75,
                    'speed': 4.25, 'passing': 4.0, 'physical_jumping': 3.0,
                    'buildup_contribution': 4.0, 'leadership': 3.25
                },
                'comment': 'Young versatile player with high potential. Good technical ability.'
            },
            'DM': {
                'id': 64523,
                'name': 'Martín Zubimendi',
                'position_type': 'Midfielder',
                'ratings': {
                    'passing': 4.5, 'vision': 4.25, 'positioning_reading': 4.5,
                    'interception': 4.5, 'tackle_marking': 4.25, 'stamina': 4.25,
                    'composure_judgement': 4.5, 'buildup_contribution': 4.75,
                    'leadership': 4.0, 'speed': 3.75
                },
                'comment': 'Elite defensive midfielder. Excellent ball retention and positional discipline.'
            },
            'CM1': {
                'id': 15202,
                'name': 'Declan Rice',
                'position_type': 'Midfielder',
                'ratings': {
                    'passing': 4.25, 'vision': 4.0, 'positioning_reading': 4.5,
                    'interception': 4.5, 'tackle_marking': 4.5, 'stamina': 4.75,
                    'composure_judgement': 4.25, 'buildup_contribution': 4.25,
                    'leadership': 4.5, 'speed': 4.0
                },
                'comment': 'Box-to-box midfielder with exceptional work rate. Arsenal\'s midfield anchor.'
            },
            'CM2': {
                'id': 19778,
                'name': 'Mikel Merino',
                'position_type': 'Midfielder',
                'ratings': {
                    'passing': 4.0, 'vision': 4.0, 'positioning_reading': 4.0,
                    'interception': 3.75, 'tackle_marking': 3.75, 'stamina': 4.25,
                    'composure_judgement': 4.0, 'buildup_contribution': 4.0,
                    'leadership': 4.0, 'speed': 3.5
                },
                'comment': 'Experienced midfielder providing balance. Good aerial threat from midfield.'
            },
            'LW': {
                'id': 67407,
                'name': 'Noni Madueke',
                'position_type': 'Winger',
                'ratings': {
                    'speed_dribbling': 4.25, 'one_on_one_beating': 4.0, 'speed': 4.5,
                    'acceleration': 4.5, 'crossing_accuracy': 3.75, 'shooting_accuracy': 4.0,
                    'agility_direction_change': 4.25, 'cutting_in': 4.0,
                    'defensive_contribution': 3.0, 'creativity': 4.0,
                    'link_up_play': 3.75, 'cutback_pass': 3.75
                },
                'comment': 'Explosive winger with direct dribbling. Threat in 1v1 situations.'
            },
            'ST': {
                'id': 32728,
                'name': 'Viktor Gyökeres',
                'position_type': 'Striker',
                'ratings': {
                    'finishing': 4.5, 'positioning_reading': 4.5, 'shooting_accuracy': 4.25,
                    'heading': 4.0, 'one_on_one_beating': 4.25, 'speed': 4.25,
                    'acceleration': 4.0, 'link_up_play': 4.0, 'physical_jumping': 4.0,
                    'composure_judgement': 4.25
                },
                'comment': 'Clinical finisher with excellent movement. Consistent goal threat.'
            },
            'RW': {
                'id': 20486,
                'name': 'Leandro Trossard',
                'position_type': 'Winger',
                'ratings': {
                    'speed_dribbling': 4.0, 'one_on_one_beating': 4.0, 'speed': 3.75,
                    'acceleration': 4.0, 'crossing_accuracy': 4.0, 'shooting_accuracy': 4.25,
                    'agility_direction_change': 4.0, 'cutting_in': 4.5,
                    'defensive_contribution': 3.5, 'creativity': 4.25,
                    'link_up_play': 4.5, 'cutback_pass': 4.0
                },
                'comment': 'Versatile attacker who can cut inside and finish. Good link-up play.'
            }
        },
        'tactics': {
            'defensive': {
                'pressing_intensity': 9,
                'defensive_line': 8,
                'defensive_width': 8,
                'compactness': 7,
                'line_distance': 10.0
            },
            'offensive': {
                'tempo': 8,
                'buildup_style': 'short_passing',
                'width': 9,
                'creativity': 8,
                'passing_directness': 3
            },
            'transition': {
                'counter_press': 9,
                'counter_speed': 8,
                'transition_time': 2.5,
                'recovery_speed': 8
            }
        },
        'team_strength': {
            'tactical_understanding': 4.5,
            'positioning_balance': 4.25,
            'buildup_quality': 4.5
        },
        'team_comment': 'Arsenal play possession-based football with high pressing intensity. Strong technical quality across the squad with emphasis on build-up play and wide attacks.'
    },

    'Liverpool': {
        'formation': '4-3-3',
        'lineup': {
            'GK': {'id': None, 'find_by_name': 'Alisson', 'position_type': 'Goalkeeper',
                   'ratings': {
                       'reflexes': 4.75, 'positioning_reading': 4.75, 'handling': 4.5,
                       'kicking': 4.75, 'aerial_duel': 4.5, 'one_on_one': 4.75,
                       'composure_judgement': 4.75, 'distribution': 4.75,
                       'speed': 3.5, 'leadership': 4.5
                   },
                   'comment': 'World-class goalkeeper. Excellent shot-stopping and distribution.'},
            'LB': {'id': None, 'find_by_name': 'Robertson', 'position_type': 'Defender',
                   'ratings': {
                       'positioning_reading': 4.25, 'composure_judgement': 4.0,
                       'interception': 4.0, 'aerial_duel': 3.75, 'tackle_marking': 4.25,
                       'speed': 4.5, 'passing': 4.25, 'physical_jumping': 3.5,
                       'buildup_contribution': 4.5, 'leadership': 4.5
                   },
                   'comment': 'Tireless left-back with excellent crossing ability. Key to Liverpool\'s attacking width.'},
            'CB1': {'id': None, 'find_by_name': 'van Dijk', 'position_type': 'Defender',
                    'ratings': {
                        'positioning_reading': 4.75, 'composure_judgement': 4.75,
                        'interception': 4.75, 'aerial_duel': 5.0, 'tackle_marking': 4.75,
                        'speed': 4.0, 'passing': 4.5, 'physical_jumping': 5.0,
                        'buildup_contribution': 4.25, 'leadership': 5.0
                    },
                    'comment': 'World-class defender and Liverpool\'s leader. Dominates aerially and organizes the defense.'},
            'CB2': {'id': None, 'find_by_name': 'Konaté', 'position_type': 'Defender',
                    'ratings': {
                        'positioning_reading': 4.0, 'composure_judgement': 4.0,
                        'interception': 4.25, 'aerial_duel': 4.5, 'tackle_marking': 4.25,
                        'speed': 4.5, 'passing': 3.75, 'physical_jumping': 4.5,
                        'buildup_contribution': 3.5, 'leadership': 3.75
                    },
                    'comment': 'Physically imposing defender with great pace. Strong in duels.'},
            'RB': {'id': 68582, 'find_by_name': 'Bradley', 'position_type': 'Defender',
                   'ratings': {
                       'positioning_reading': 3.75, 'composure_judgement': 3.75,
                       'interception': 3.75, 'aerial_duel': 3.25, 'tackle_marking': 3.75,
                       'speed': 4.5, 'passing': 4.0, 'physical_jumping': 3.25,
                       'buildup_contribution': 4.0, 'leadership': 3.5
                   },
                   'comment': 'Young attacking full-back with great pace. Developing playmaking skills.'},
            'DM': {'id': None, 'find_by_name': 'Mac Allister', 'position_type': 'Midfielder',
                   'ratings': {
                       'passing': 4.5, 'vision': 4.5, 'positioning_reading': 4.25,
                       'interception': 4.0, 'tackle_marking': 4.0, 'stamina': 4.25,
                       'composure_judgement': 4.5, 'buildup_contribution': 4.5,
                       'leadership': 4.0, 'speed': 3.75
                   },
                   'comment': 'Composed midfielder excellent at dictating tempo. Good technical quality.'},
            'CM1': {'id': None, 'find_by_name': 'Szoboszlai', 'position_type': 'Midfielder',
                    'ratings': {
                        'passing': 4.25, 'vision': 4.25, 'positioning_reading': 4.0,
                        'interception': 3.75, 'tackle_marking': 3.75, 'stamina': 4.5,
                        'composure_judgement': 4.0, 'buildup_contribution': 4.25,
                        'leadership': 3.75, 'speed': 4.25
                    },
                    'comment': 'Dynamic box-to-box midfielder with powerful shooting. High work rate.'},
            'CM2': {'id': None, 'find_by_name': 'Gravenberch', 'position_type': 'Midfielder',
                    'ratings': {
                        'passing': 4.0, 'vision': 4.0, 'positioning_reading': 4.25,
                        'interception': 4.25, 'tackle_marking': 4.0, 'stamina': 4.5,
                        'composure_judgement': 4.25, 'buildup_contribution': 4.0,
                        'leadership': 3.75, 'speed': 4.25
                    },
                    'comment': 'Athletic midfielder with good ball-carrying ability. Developing into key player.'},
            'LW': {'id': None, 'find_by_name': 'Díaz', 'position_type': 'Winger',
                   'ratings': {
                       'speed_dribbling': 4.75, 'one_on_one_beating': 4.5, 'speed': 4.75,
                       'acceleration': 4.75, 'crossing_accuracy': 4.0, 'shooting_accuracy': 4.0,
                       'agility_direction_change': 4.75, 'cutting_in': 4.25,
                       'defensive_contribution': 3.75, 'creativity': 4.25,
                       'link_up_play': 4.0, 'cutback_pass': 4.0
                   },
                   'comment': 'Electric winger with exceptional dribbling. Direct runner who excels in 1v1s.'},
            'ST': {'id': None, 'find_by_name': 'Núñez', 'position_type': 'Striker',
                   'ratings': {
                       'finishing': 4.0, 'positioning_reading': 4.25, 'shooting_accuracy': 3.75,
                       'heading': 4.25, 'one_on_one_beating': 4.25, 'speed': 4.75,
                       'acceleration': 4.75, 'link_up_play': 3.75, 'physical_jumping': 4.25,
                       'composure_judgement': 3.75
                   },
                   'comment': 'Powerful striker with exceptional pace. High energy and pressing from the front.'},
            'RW': {'id': None, 'find_by_name': 'Salah', 'position_type': 'Winger',
                   'ratings': {
                       'speed_dribbling': 4.75, 'one_on_one_beating': 4.75, 'speed': 4.75,
                       'acceleration': 4.75, 'crossing_accuracy': 4.25, 'shooting_accuracy': 4.75,
                       'agility_direction_change': 4.5, 'cutting_in': 5.0,
                       'defensive_contribution': 3.25, 'creativity': 4.5,
                       'link_up_play': 4.25, 'cutback_pass': 4.0
                   },
                   'comment': 'World-class winger and prolific goalscorer. Elite finishing when cutting inside.'}
        },
        'tactics': {
            'defensive': {
                'pressing_intensity': 10,
                'defensive_line': 9,
                'defensive_width': 7,
                'compactness': 8,
                'line_distance': 12.0
            },
            'offensive': {
                'tempo': 9,
                'buildup_style': 'mixed',
                'width': 10,
                'creativity': 8,
                'passing_directness': 6
            },
            'transition': {
                'counter_press': 10,
                'counter_speed': 10,
                'transition_time': 2.0,
                'recovery_speed': 9
            }
        },
        'team_strength': {
            'tactical_understanding': 4.75,
            'positioning_balance': 4.5,
            'buildup_quality': 4.25
        },
        'team_comment': 'Liverpool deploy an aggressive high-pressing system with rapid transitions. Emphasis on width and pace with full-backs providing creative threat.'
    },

    'Man City': {
        'formation': '4-3-3',
        'lineup': {
            'GK': {'id': None, 'find_by_name': 'Ederson', 'position_type': 'Goalkeeper',
                   'ratings': {
                       'reflexes': 4.5, 'positioning_reading': 4.5, 'handling': 4.25,
                       'kicking': 5.0, 'aerial_duel': 4.25, 'one_on_one': 4.5,
                       'composure_judgement': 4.75, 'distribution': 5.0,
                       'speed': 3.75, 'leadership': 4.25
                   },
                   'comment': 'Elite ball-playing goalkeeper. Best distribution in the world.'},
            'LB': {'id': None, 'find_by_name': 'Gvardiol', 'position_type': 'Defender',
                   'ratings': {
                       'positioning_reading': 4.25, 'composure_judgement': 4.25,
                       'interception': 4.25, 'aerial_duel': 4.5, 'tackle_marking': 4.25,
                       'speed': 4.5, 'passing': 4.25, 'physical_jumping': 4.5,
                       'buildup_contribution': 4.5, 'leadership': 3.75
                   },
                   'comment': 'Versatile defender comfortable on the ball. Can play CB or LB.'},
            'CB1': {'id': None, 'find_by_name': 'Rúben Dias', 'position_type': 'Defender',
                    'ratings': {
                        'positioning_reading': 4.75, 'composure_judgement': 4.75,
                        'interception': 4.75, 'aerial_duel': 4.5, 'tackle_marking': 4.75,
                        'speed': 3.75, 'passing': 4.25, 'physical_jumping': 4.5,
                        'buildup_contribution': 4.0, 'leadership': 4.75
                    },
                    'comment': 'World-class defender and City\'s defensive leader. Excellent reading of the game.'},
            'CB2': {'id': None, 'find_by_name': 'Akanji', 'position_type': 'Defender',
                    'ratings': {
                        'positioning_reading': 4.25, 'composure_judgement': 4.25,
                        'interception': 4.25, 'aerial_duel': 4.25, 'tackle_marking': 4.25,
                        'speed': 4.25, 'passing': 4.0, 'physical_jumping': 4.25,
                        'buildup_contribution': 4.0, 'leadership': 4.0
                    },
                    'comment': 'Reliable defender with good pace. Comfortable in possession.'},
            'RB': {'id': None, 'find_by_name': 'Walker', 'position_type': 'Defender',
                   'ratings': {
                       'positioning_reading': 4.25, 'composure_judgement': 4.0,
                       'interception': 4.25, 'aerial_duel': 3.75, 'tackle_marking': 4.25,
                       'speed': 4.75, 'passing': 3.75, 'physical_jumping': 3.75,
                       'buildup_contribution': 3.75, 'leadership': 4.25
                   },
                   'comment': 'Experienced defender with exceptional pace. Covers vast areas.'},
            'DM': {'id': None, 'find_by_name': 'Rodri', 'position_type': 'Midfielder',
                   'ratings': {
                       'passing': 4.75, 'vision': 4.75, 'positioning_reading': 4.75,
                       'interception': 4.75, 'tackle_marking': 4.5, 'stamina': 4.5,
                       'composure_judgement': 4.75, 'buildup_contribution': 4.75,
                       'leadership': 4.75, 'speed': 3.5
                   },
                   'comment': 'World-class holding midfielder. Controls tempo and dictates play.'},
            'CM1': {'id': None, 'find_by_name': 'De Bruyne', 'position_type': 'Midfielder',
                    'ratings': {
                        'passing': 5.0, 'vision': 5.0, 'positioning_reading': 4.5,
                        'interception': 3.5, 'tackle_marking': 3.5, 'stamina': 4.25,
                        'composure_judgement': 4.75, 'buildup_contribution': 4.75,
                        'leadership': 4.75, 'speed': 3.75
                    },
                    'comment': 'Elite playmaker with world-class passing and vision. Can unlock any defense.'},
            'CM2': {'id': None, 'find_by_name': 'Bernardo Silva', 'position_type': 'Midfielder',
                    'ratings': {
                        'passing': 4.75, 'vision': 4.5, 'positioning_reading': 4.5,
                        'interception': 4.0, 'tackle_marking': 3.75, 'stamina': 4.75,
                        'composure_judgement': 4.75, 'buildup_contribution': 4.75,
                        'leadership': 4.25, 'speed': 4.0
                    },
                    'comment': 'Technically gifted midfielder. Excellent ball retention and work rate.'},
            'LW': {'id': None, 'find_by_name': 'Grealish', 'position_type': 'Winger',
                   'ratings': {
                       'speed_dribbling': 4.5, 'one_on_one_beating': 4.5, 'speed': 4.0,
                       'acceleration': 4.25, 'crossing_accuracy': 4.25, 'shooting_accuracy': 3.75,
                       'agility_direction_change': 4.5, 'cutting_in': 4.0,
                       'defensive_contribution': 3.75, 'creativity': 4.5,
                       'link_up_play': 4.75, 'cutback_pass': 4.5
                   },
                   'comment': 'Exceptional ball retention. Draws fouls and controls possession.'},
            'ST': {'id': None, 'find_by_name': 'Haaland', 'position_type': 'Striker',
                   'ratings': {
                       'finishing': 5.0, 'positioning_reading': 4.75, 'shooting_accuracy': 4.75,
                       'heading': 4.5, 'one_on_one_beating': 4.75, 'speed': 4.75,
                       'acceleration': 4.75, 'link_up_play': 4.0, 'physical_jumping': 4.5,
                       'composure_judgement': 4.75
                   },
                   'comment': 'Elite goalscorer with exceptional physical attributes. Lethal finisher.'},
            'RW': {'id': None, 'find_by_name': 'Foden', 'position_type': 'Winger',
                   'ratings': {
                       'speed_dribbling': 4.75, 'one_on_one_beating': 4.5, 'speed': 4.5,
                       'acceleration': 4.5, 'crossing_accuracy': 4.25, 'shooting_accuracy': 4.5,
                       'agility_direction_change': 4.75, 'cutting_in': 4.75,
                       'defensive_contribution': 3.75, 'creativity': 4.75,
                       'link_up_play': 4.5, 'cutback_pass': 4.25
                   },
                   'comment': 'Technically brilliant winger. Versatile and intelligent movement.'}
        },
        'tactics': {
            'defensive': {
                'pressing_intensity': 8,
                'defensive_line': 9,
                'defensive_width': 9,
                'compactness': 9,
                'line_distance': 15.0
            },
            'offensive': {
                'tempo': 7,
                'buildup_style': 'short_passing',
                'width': 10,
                'creativity': 10,
                'passing_directness': 2
            },
            'transition': {
                'counter_press': 8,
                'counter_speed': 7,
                'transition_time': 3.0,
                'recovery_speed': 7
            }
        },
        'team_strength': {
            'tactical_understanding': 5.0,
            'positioning_balance': 4.75,
            'buildup_quality': 5.0
        },
        'team_comment': 'Man City dominate possession with intricate passing patterns. World-class technical quality and tactical discipline under Guardiola.'
    },

    'Chelsea': {
        'formation': '4-2-3-1',
        'lineup': {
            'GK': {'id': None, 'find_by_name': 'Sánchez', 'position_type': 'Goalkeeper',
                   'ratings': {
                       'reflexes': 4.25, 'positioning_reading': 4.0, 'handling': 4.0,
                       'kicking': 4.25, 'aerial_duel': 4.25, 'one_on_one': 4.25,
                       'composure_judgement': 4.0, 'distribution': 4.25,
                       'speed': 3.5, 'leadership': 4.0
                   },
                   'comment': 'Reliable goalkeeper with good distribution. Improving under Pochettino.'},
            'LB': {'id': None, 'find_by_name': 'Chilwell', 'position_type': 'Defender',
                   'ratings': {
                       'positioning_reading': 4.0, 'composure_judgement': 3.75,
                       'interception': 3.75, 'aerial_duel': 3.5, 'tackle_marking': 4.0,
                       'speed': 4.25, 'passing': 4.0, 'physical_jumping': 3.5,
                       'buildup_contribution': 4.25, 'leadership': 3.75
                   },
                   'comment': 'Attacking full-back when fit. Good crossing and overlapping runs.'},
            'CB1': {'id': None, 'find_by_name': 'Silva', 'position_type': 'Defender',
                    'ratings': {
                        'positioning_reading': 4.5, 'composure_judgement': 4.75,
                        'interception': 4.5, 'aerial_duel': 4.0, 'tackle_marking': 4.5,
                        'speed': 3.5, 'passing': 4.5, 'physical_jumping': 4.0,
                        'buildup_contribution': 4.5, 'leadership': 4.75
                    },
                    'comment': 'Experienced leader with excellent reading of the game. Chelsea\'s defensive anchor.'},
            'CB2': {'id': None, 'find_by_name': 'Disasi', 'position_type': 'Defender',
                    'ratings': {
                        'positioning_reading': 4.0, 'composure_judgement': 4.0,
                        'interception': 4.0, 'aerial_duel': 4.25, 'tackle_marking': 4.0,
                        'speed': 4.0, 'passing': 3.75, 'physical_jumping': 4.25,
                        'buildup_contribution': 3.75, 'leadership': 3.75
                    },
                    'comment': 'Physical defender with good pace. Solid in aerial duels.'},
            'RB': {'id': None, 'find_by_name': 'James', 'position_type': 'Defender',
                   'ratings': {
                       'positioning_reading': 4.0, 'composure_judgement': 4.0,
                       'interception': 4.0, 'aerial_duel': 3.75, 'tackle_marking': 4.0,
                       'speed': 4.25, 'passing': 4.5, 'physical_jumping': 3.75,
                       'buildup_contribution': 4.5, 'leadership': 4.25
                   },
                   'comment': 'Elite attacking full-back. Powerful shot and excellent crossing.'},
            'DM1': {'id': None, 'find_by_name': 'Fernández', 'position_type': 'Midfielder',
                    'ratings': {
                        'passing': 4.5, 'vision': 4.5, 'positioning_reading': 4.25,
                        'interception': 4.0, 'tackle_marking': 4.0, 'stamina': 4.25,
                        'composure_judgement': 4.5, 'buildup_contribution': 4.5,
                        'leadership': 4.25, 'speed': 3.75
                    },
                    'comment': 'Composed midfielder with excellent passing range. Controls the tempo.'},
            'DM2': {'id': None, 'find_by_name': 'Caicedo', 'position_type': 'Midfielder',
                    'ratings': {
                        'passing': 4.0, 'vision': 3.75, 'positioning_reading': 4.25,
                        'interception': 4.5, 'tackle_marking': 4.5, 'stamina': 4.75,
                        'composure_judgement': 4.0, 'buildup_contribution': 4.0,
                        'leadership': 4.0, 'speed': 4.25
                    },
                    'comment': 'Athletic defensive midfielder. Excellent ball-winner and work rate.'},
            'CAM': {'id': None, 'find_by_name': 'Palmer', 'position_type': 'Midfielder',
                    'ratings': {
                        'passing': 4.5, 'vision': 4.5, 'positioning_reading': 4.25,
                        'interception': 3.25, 'tackle_marking': 3.0, 'stamina': 4.0,
                        'composure_judgement': 4.5, 'buildup_contribution': 4.5,
                        'leadership': 3.75, 'speed': 3.75
                    },
                    'comment': 'Talented playmaker with great composure. Chelsea\'s creative hub.'},
            'LW': {'id': None, 'find_by_name': 'Sterling', 'position_type': 'Winger',
                   'ratings': {
                       'speed_dribbling': 4.5, 'one_on_one_beating': 4.25, 'speed': 4.5,
                       'acceleration': 4.5, 'crossing_accuracy': 4.0, 'shooting_accuracy': 4.0,
                       'agility_direction_change': 4.5, 'cutting_in': 4.25,
                       'defensive_contribution': 3.5, 'creativity': 4.25,
                       'link_up_play': 4.0, 'cutback_pass': 4.0
                   },
                   'comment': 'Experienced winger with pace and directness. Proven goalscorer.'},
            'ST': {'id': None, 'find_by_name': 'Jackson', 'position_type': 'Striker',
                   'ratings': {
                       'finishing': 3.75, 'positioning_reading': 4.0, 'shooting_accuracy': 3.75,
                       'heading': 3.75, 'one_on_one_beating': 4.0, 'speed': 4.5,
                       'acceleration': 4.5, 'link_up_play': 3.75, 'physical_jumping': 3.75,
                       'composure_judgement': 3.75
                   },
                   'comment': 'Fast striker with high work rate. Developing finishing consistency.'},
            'RW': {'id': None, 'find_by_name': 'Nkunku', 'position_type': 'Winger',
                   'ratings': {
                       'speed_dribbling': 4.25, 'one_on_one_beating': 4.25, 'speed': 4.25,
                       'acceleration': 4.25, 'crossing_accuracy': 4.0, 'shooting_accuracy': 4.5,
                       'agility_direction_change': 4.25, 'cutting_in': 4.5,
                       'defensive_contribution': 3.5, 'creativity': 4.5,
                       'link_up_play': 4.5, 'cutback_pass': 4.25
                   },
                   'comment': 'Versatile attacker who can play multiple positions. Excellent finisher.'}
        },
        'tactics': {
            'defensive': {
                'pressing_intensity': 8,
                'defensive_line': 7,
                'defensive_width': 7,
                'compactness': 7,
                'line_distance': 8.0
            },
            'offensive': {
                'tempo': 7,
                'buildup_style': 'mixed',
                'width': 8,
                'creativity': 7,
                'passing_directness': 5
            },
            'transition': {
                'counter_press': 8,
                'counter_speed': 8,
                'transition_time': 2.5,
                'recovery_speed': 7
            }
        },
        'team_strength': {
            'tactical_understanding': 4.0,
            'positioning_balance': 4.0,
            'buildup_quality': 4.25
        },
        'team_comment': 'Chelsea blend possession with direct play under Pochettino. Young squad with developing chemistry and tactical flexibility.'
    }
}


# ==========================================================================
# DB에 데이터 삽입
# ==========================================================================

def find_player_by_name(session, team_name, player_name_partial):
    """이름으로 선수 찾기 (부분 일치)"""
    from sqlalchemy import func
    players = session.query(Player).join(Player.team).filter(
        func.lower(Player.name).like(f'%{player_name_partial.lower()}%')
    ).all()

    if not players:
        print(f"  ⚠️  Player '{player_name_partial}' not found")
        return None

    if len(players) > 1:
        print(f"  ⚠️  Multiple players found for '{player_name_partial}': {[p.name for p in players]}")
        print(f"      Using first match: {players[0].name}")

    return players[0]


def populate_player_ratings(session, team_name, lineup_data):
    """선수 평가 데이터 DB에 삽입"""
    print(f"\n{'='*70}")
    print(f"Populating player ratings for {team_name}")
    print(f"{'='*70}\n")

    inserted_count = 0

    for position, player_data in lineup_data.items():
        player_id = player_data.get('id')

        # ID가 없으면 이름으로 찾기
        if player_id is None:
            player_name = player_data.get('find_by_name')
            if not player_name:
                print(f"  ❌ [{position}] No ID or name provided")
                continue

            player = find_player_by_name(session, team_name, player_name)
            if not player:
                continue
            player_id = player.id
            player_data['id'] = player_id  # 나중에 lineup JSON 생성 시 사용
        else:
            player = session.query(Player).filter_by(id=player_id).first()
            if not player:
                print(f"  ❌ [{position}] Player ID {player_id} not found")
                continue

        print(f"  [{position:6s}] {player.name:25s} (ID: {player_id})")

        # 기존 평가 삭제
        session.query(PlayerRating).filter_by(
            player_id=player_id,
            user_id='default'
        ).delete()

        # 속성 평가 삽입
        ratings = player_data['ratings']
        for attr_name, rating_value in ratings.items():
            rating = PlayerRating(
                player_id=player_id,
                user_id='default',
                attribute_name=attr_name,
                rating=rating_value
            )
            session.add(rating)
            inserted_count += 1

        # 코멘트 삽입
        comment_text = player_data.get('comment', '')
        comment_rating = PlayerRating(
            player_id=player_id,
            user_id='default',
            attribute_name='_comment',
            rating=0.0,
            notes=comment_text
        )
        session.add(comment_rating)
        inserted_count += 1

        # 세부 포지션 삽입 (lineup 포지션 사용)
        sub_pos_rating = PlayerRating(
            player_id=player_id,
            user_id='default',
            attribute_name='_subPosition',
            rating=0.0,
            notes=position
        )
        session.add(sub_pos_rating)
        inserted_count += 1

    session.commit()
    print(f"\n✅ Inserted {inserted_count} rating records for {team_name}")
    return inserted_count


# ==========================================================================
# JSON 파일 생성
# ==========================================================================

def create_json_files(team_name, team_data):
    """모든 JSON 파일 생성"""
    print(f"\n{'='*70}")
    print(f"Creating JSON files for {team_name}")
    print(f"{'='*70}\n")

    # 1. Formation
    formation_path = os.path.join(DATA_DIR, 'formations', f"{team_name}.json")
    formation_data = {
        'team_name': team_name,
        'formation': team_data['formation'],
        'formation_data': {},
        'timestamp': datetime.now().isoformat()
    }
    with open(formation_path, 'w', encoding='utf-8') as f:
        json.dump(formation_data, f, indent=2, ensure_ascii=False)
    print(f"  ✅ Created: formations/{team_name}.json")

    # 2. Lineup
    lineup_path = os.path.join(DATA_DIR, 'lineups', f"{team_name}.json")
    lineup_positions = {}
    for pos, player_data in team_data['lineup'].items():
        player_id = player_data['id']
        if player_id:
            lineup_positions[pos] = player_id

    lineup_data = {
        'team_name': team_name,
        'formation': team_data['formation'],
        'lineup': lineup_positions,
        'timestamp': datetime.now().isoformat()
    }
    with open(lineup_path, 'w', encoding='utf-8') as f:
        json.dump(lineup_data, f, indent=2, ensure_ascii=False)
    print(f"  ✅ Created: lineups/{team_name}.json")

    # 3. Tactics
    tactics_path = os.path.join(DATA_DIR, 'tactics', f"{team_name}.json")
    tactics_data = {
        'team_name': team_name,
        'defensive': team_data['tactics']['defensive'],
        'offensive': team_data['tactics']['offensive'],
        'transition': team_data['tactics']['transition'],
        'timestamp': datetime.now().isoformat()
    }
    with open(tactics_path, 'w', encoding='utf-8') as f:
        json.dump(tactics_data, f, indent=2, ensure_ascii=False)
    print(f"  ✅ Created: tactics/{team_name}.json")

    # 4. Team Strength
    strength_path = os.path.join(DATA_DIR, 'team_strength', f"{team_name}.json")
    strength_data = {
        'team_name': team_name,
        'ratings': team_data['team_strength'],
        'comment': team_data['team_comment'],
        'timestamp': datetime.now().isoformat()
    }
    with open(strength_path, 'w', encoding='utf-8') as f:
        json.dump(strength_data, f, indent=2, ensure_ascii=False)
    print(f"  ✅ Created: team_strength/{team_name}.json")

    print(f"\n✅ All JSON files created for {team_name}")


# ==========================================================================
# Main
# ==========================================================================

def main():
    print("="*70)
    print("팀 데이터 자동 생성 스크립트")
    print("="*70)

    session = None
    try:
        session = get_player_session(DB_PATH)

        # 각 팀 처리
        for team_name, team_data in TEAMS_DATA.items():
            print(f"\n{'#'*70}")
            print(f"# Processing: {team_name}")
            print(f"{'#'*70}")

            # 1. DB에 선수 평가 삽입
            populate_player_ratings(session, team_name, team_data['lineup'])

            # 2. JSON 파일 생성
            create_json_files(team_name, team_data)

        print(f"\n{'='*70}")
        print("✅ All teams processed successfully!")
        print(f"{'='*70}\n")

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        if session:
            session.rollback()
    finally:
        if session:
            session.close()


if __name__ == '__main__':
    main()
