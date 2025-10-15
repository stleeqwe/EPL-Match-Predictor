import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Save, RotateCcw, Shield, Target, TrendingUp, Zap, Heart, Info, MessageSquare } from 'lucide-react';
import RatingSlider from './RatingSlider';

/**
 * 팀 전력 분석 프레임워크
 */
const TEAM_STRENGTH_FRAMEWORK = {
  tactical_organization: {
    name: '전술적 조직력',
    name_en: 'Tactical Organization',
    weight: 0.38,
    icon: Shield,
    color: 'text-blue-400',
    attributes: [
      {
        key: 'tactical_understanding',
        label: '전술 이해도 & 실행력',
        weight: 0.11,
        description: '감독이 요구하는 전술의 구현도, 포메이션 유지 정확성, 상황별 전술 변경 대응력, 전술적 규율 준수도'
      },
      {
        key: 'positioning_balance',
        label: '포지셔닝 균형 & 공간 관리',
        weight: 0.09,
        description: '선수 간 거리의 최적화 유지, 위험 지역 커버 효율성, 공격 시 공간 확장/수비 시 압축 능력, 전체 팀 형태 유지력'
      },
      {
        key: 'attack_to_defense_transition',
        label: '공격→수비 전환 속도',
        weight: 0.07,
        description: '볼 상실 후 5초 이내 압박 조직도, 역습 상황 차단 성공률, 전방 압박의 연계성과 동시성, 수비 전환 시 위치 복귀 속도'
      },
      {
        key: 'defense_to_attack_transition',
        label: '수비→공격 전환 효율성',
        weight: 0.06,
        description: '볼 탈취 후 공격 전개 속도, 역습 성공률과 위험도, 압박 탈출 완성도, 빠른 공격 루트 활용 능력'
      },
      {
        key: 'pressing_organization',
        label: '압박 조직력 & 동시성',
        weight: 0.05,
        description: '집단 압박 타이밍의 정확도, 압박 트리거 정확도, 압박 후 볼 회수율, 3-4명 이상 동시 압박 성공률'
      }
    ]
  },
  attacking_efficiency: {
    name: '공격 효율성',
    name_en: 'Attacking Efficiency',
    weight: 0.25,
    icon: Target,
    color: 'text-red-400',
    attributes: [
      {
        key: 'buildup_quality',
        label: '빌드업 완성도',
        weight: 0.08,
        description: '백라인에서 중원까지 패스 연결 성공률, 상대 압박 상황 돌파력, 빌드업 루트의 다양성, 골키퍼 포함 빌드업 참여도'
      },
      {
        key: 'pass_network',
        label: '패스 네트워크 & 연결성',
        weight: 0.07,
        description: '패스 연결 효율성과 패스맵 밀도, 삼각편대 형성 빈도, 볼 순환 속도와 리듬, 선수 간 패스 연결 균형도'
      },
      {
        key: 'final_third_penetration',
        label: '최종 3분의 1 침투력',
        weight: 0.05,
        description: '페널티 박스 진입 횟수와 성공률, 위험 지역 침투 성공률, 크로스 및 스루패스 정확도, 박스 내 슈팅 기회 창출 빈도'
      },
      {
        key: 'goal_conversion',
        label: '골 결정력 (xG 대비)',
        weight: 0.05,
        description: 'Expected Goals 대비 실제 득점 효율, 빅찬스 전환율, 다양한 득점 루트 보유, 결정적 순간 침착성'
      }
    ]
  },
  defensive_stability: {
    name: '수비 안정성',
    name_en: 'Defensive Stability',
    weight: 0.22,
    icon: Shield,
    color: 'text-green-400',
    attributes: [
      {
        key: 'backline_organization',
        label: '수비 라인 조직력',
        weight: 0.09,
        description: '오프사이드 트랩 성공률, 백라인 간격 유지도, 위험 상황 커버 속도, 수비 라인 높낮이 조절 능력'
      },
      {
        key: 'central_control',
        label: '중앙 지역 장악력',
        weight: 0.06,
        description: '중앙 인터셉트 성공률, 중거리 슈팅 차단율, 중원 볼 회수 빈도, 중앙 돌파 허용률'
      },
      {
        key: 'flank_defense',
        label: '측면 수비 커버력',
        weight: 0.04,
        description: '크로스 차단율, 측면 돌파 허용률, 풀백-윙 수비 연계, 측면 수적 우위 확보 빈도'
      },
      {
        key: 'counter_prevention',
        label: '역습 차단 능력',
        weight: 0.03,
        description: '상대의 빠른 공격 전환 차단율, 수적 열세 상황 대응력, 카운터 상황 실점률, 전술적 파울 활용도'
      }
    ]
  },
  physicality: {
    name: '피지컬 & 체력',
    name_en: 'Physicality & Stamina',
    weight: 0.08,
    icon: Zap,
    color: 'text-yellow-400',
    attributes: [
      {
        key: 'team_stamina',
        label: '팀 평균 지구력',
        weight: 0.05,
        description: '후반전 활동량 유지도, 연속 경기 체력 관리 능력, 경기 종반(75분 이후) 실점률, 시즌 장기전 체력 관리'
      },
      {
        key: 'speed_balance',
        label: '스피드 밸런스',
        weight: 0.03,
        description: '공수 전환 평균 속도, 팀 평균 스프린트 능력, 빠른 선수의 전략적 배치 효율성, 스피드 격차 활용 능력'
      }
    ]
  },
  psychological: {
    name: '심리적 요소',
    name_en: 'Psychological Factors',
    weight: 0.07,
    icon: Heart,
    color: 'text-purple-400',
    attributes: [
      {
        key: 'game_control',
        label: '경기 흐름 제어력',
        weight: 0.03,
        description: '리드 시 경기 관리 능력, 템포 조절 역량, 시간 소모 효율성, 상황별 경기 운영 전략'
      },
      {
        key: 'mental_strength',
        label: '멘탈 & 승부근성',
        weight: 0.02,
        description: '비하인드 상황 역전율, 중요 경기(결승, 더비 등) 승률, 압박 상황 대응력, 동점/역전골 이후 반응'
      },
      {
        key: 'team_chemistry',
        label: '팀 케미스트리',
        weight: 0.02,
        description: '선수 간 암묵적 이해도, 코칭스태프-선수단 신뢰도, 라커룸 분위기와 단합도, 신규 선수 적응 속도'
      }
    ]
  }
};

/**
 * TeamRating Component
 * 팀 능력치 측정 컴포넌트
 */
const TeamRating = ({ team, darkMode = false }) => {
  const [ratings, setRatings] = useState({});
  const [comment, setComment] = useState('');
  const [hasChanges, setHasChanges] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [expandedCategory, setExpandedCategory] = useState('tactical_organization');

  // 초기화 및 로드
  useEffect(() => {
    if (team) {
      loadTeamStrength();
    }
  }, [team]);

  const loadTeamStrength = () => {
    // localStorage에서 로드
    const saved = localStorage.getItem(`team_strength_${team}`);
    const savedComment = localStorage.getItem(`team_comment_${team}`);

    if (saved) {
      setRatings(JSON.parse(saved));
    } else {
      // 기본값 2.5로 초기화
      const initialRatings = {};
      Object.values(TEAM_STRENGTH_FRAMEWORK).forEach(category => {
        category.attributes.forEach(attr => {
          initialRatings[attr.key] = 2.5;
        });
      });
      setRatings(initialRatings);
    }

    setComment(savedComment || '');
    setHasChanges(false);
  };

  const handleRatingChange = (key, value) => {
    setRatings(prev => ({
      ...prev,
      [key]: value
    }));
    setHasChanges(true);
  };

  const handleCommentChange = (e) => {
    const value = e.target.value;
    if (value.length <= 1000) {
      setComment(value);
      setHasChanges(true);
    }
  };

  const handleSave = () => {
    setIsSaving(true);
    try {
      localStorage.setItem(`team_strength_${team}`, JSON.stringify(ratings));
      localStorage.setItem(`team_comment_${team}`, comment);
      alert('팀 전력 분석 및 코멘트가 저장되었습니다!');
      setHasChanges(false);
    } catch (error) {
      console.error('Failed to save team strength:', error);
      alert('저장에 실패했습니다: ' + error.message);
    } finally {
      setIsSaving(false);
    }
  };

  const handleReset = () => {
    const initialRatings = {};
    Object.values(TEAM_STRENGTH_FRAMEWORK).forEach(category => {
      category.attributes.forEach(attr => {
        initialRatings[attr.key] = 2.5;
      });
    });
    setRatings(initialRatings);
    setComment('');
    setHasChanges(true);
  };

  // 카테고리별 가중 평균 계산
  const calculateCategoryAverage = (categoryKey) => {
    const category = TEAM_STRENGTH_FRAMEWORK[categoryKey];
    let totalWeight = 0;
    let weightedSum = 0;

    category.attributes.forEach(attr => {
      const value = ratings[attr.key] || 2.5;
      weightedSum += value * attr.weight;
      totalWeight += attr.weight;
    });

    return totalWeight > 0 ? weightedSum / totalWeight : 0;
  };

  // 전체 팀 전력 점수 계산
  const calculateOverallScore = () => {
    let totalScore = 0;

    Object.entries(TEAM_STRENGTH_FRAMEWORK).forEach(([key, category]) => {
      const categoryAvg = calculateCategoryAverage(key);
      totalScore += categoryAvg * category.weight;
    });

    return totalScore;
  };

  const overallScore = calculateOverallScore();

  // 점수 등급
  const getScoreGrade = (score) => {
    if (score >= 4.5) return { label: '월드클래스', color: 'text-success', emoji: '🏆' };
    if (score >= 4.0) return { label: '최상위', color: 'text-brand-accent', emoji: '⭐' };
    if (score >= 3.5) return { label: '상위권', color: 'text-brand-primary', emoji: '✨' };
    if (score >= 3.0) return { label: '중상위권', color: 'text-info', emoji: '💫' };
    if (score >= 2.5) return { label: '중위권', color: 'text-warning', emoji: '⚡' };
    return { label: '하위권', color: 'text-error', emoji: '💭' };
  };

  const scoreGrade = getScoreGrade(overallScore);

  if (!team) {
    return (
      <div className="card p-12 text-center">
        <div className="text-6xl mb-4">⚽</div>
        <p className="text-lg text-white/70">
          팀을 선택해주세요
        </p>
      </div>
    );
  }

  return (
    <div className="relative bg-gradient-to-br from-slate-900/80 via-blue-950/60 to-slate-900/80 backdrop-blur-sm border border-cyan-500/20 rounded p-4 md:p-6 overflow-hidden">
      {/* Tech Grid Pattern */}
      <div
        className="absolute inset-0 opacity-[0.03] pointer-events-none"
        style={{
          backgroundImage: `
            linear-gradient(rgba(6, 182, 212, 0.5) 1px, transparent 1px),
            linear-gradient(90deg, rgba(6, 182, 212, 0.5) 1px, transparent 1px)
          `,
          backgroundSize: '20px 20px'
        }}
      />

      <div className="relative">
      {/* 2-Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Left/Center Column - Main Content (세부평가) */}
        <div className="lg:col-span-3 space-y-6">
          {/* Header */}
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-2">
            <h2 className="text-xl md:text-2xl font-bold text-white flex items-center gap-2">
              <TrendingUp className="w-6 h-6 text-brand-accent" />
              {team} 팀 능력치 측정
            </h2>
            <p className="text-sm text-white/60">
              5개 영역, 18개 세부 항목으로 팀의 종합 전력을 분석합니다
            </p>
          </div>

          {/* Detailed Ratings */}
      {expandedCategory && (
        <motion.div
          className="space-y-3 mb-6"
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <div className="flex items-center gap-2 mb-3">
            <div className="w-1 h-6 bg-brand-primary rounded"></div>
            <h3 className="text-lg font-bold text-white">
              {TEAM_STRENGTH_FRAMEWORK[expandedCategory].name} - 세부 평가
            </h3>
          </div>

          {TEAM_STRENGTH_FRAMEWORK[expandedCategory].attributes.map((attr) => (
            <div key={attr.key} className="glass p-4 rounded-sm">
              <div className="flex items-start gap-2 mb-3">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <h4 className="text-sm font-semibold text-white">{attr.label}</h4>
                    <span className="badge bg-brand-primary/20 text-brand-accent text-xs px-2 py-0.5">
                      {Math.round(attr.weight * 100)}%
                    </span>
                  </div>
                  <p className="text-xs text-white/60 leading-relaxed">
                    {attr.description}
                  </p>
                </div>
              </div>
              <RatingSlider
                label=""
                value={ratings[attr.key] || 2.5}
                onChange={(value) => handleRatingChange(attr.key, value)}
                darkMode={darkMode}
                disabled={isSaving}
                showValue={true}
              />
            </div>
          ))}
        </motion.div>
      )}

      {/* Team Comment */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <label className="flex items-center gap-2 text-sm font-medium text-white/80 mb-2">
              <MessageSquare className="w-4 h-4" />
              팀 전체 코멘트
            </label>
            <textarea
              value={comment}
              onChange={handleCommentChange}
              disabled={isSaving}
              placeholder="팀의 전체적인 전력, 전술, 특징 등을 입력하세요..."
              rows={6}
              className="input w-full resize-none"
            />
            <p className="text-xs text-white/60 mt-2">
              {comment.length}/1000자
            </p>
          </motion.div>

          {/* Actions */}
          <motion.div
            className="flex flex-col sm:flex-row gap-2"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <motion.button
              onClick={handleSave}
              disabled={!hasChanges || isSaving}
              className={`
                flex-1 px-4 py-2.5 rounded-sm font-semibold flex items-center justify-center gap-2 text-base
                transition-all duration-200 focus:outline-none
                ${(hasChanges && !isSaving)
                  ? 'bg-brand-primary text-white hover:bg-brand-primary/90'
                  : 'bg-white/5 text-white/40 cursor-not-allowed'}
              `}
              whileHover={hasChanges && !isSaving ? { scale: 1.02 } : {}}
              whileTap={hasChanges && !isSaving ? { scale: 0.98 } : {}}
            >
              <Save className="w-4 h-4" />
              {isSaving ? '저장 중...' : '저장'}
            </motion.button>

            <motion.button
              onClick={handleReset}
              disabled={isSaving}
              className="px-4 py-2.5 rounded-sm font-semibold flex items-center justify-center gap-2 text-base bg-white/10 text-white hover:bg-white/20 transition-all duration-200"
              whileHover={!isSaving ? { scale: 1.02 } : {}}
              whileTap={!isSaving ? { scale: 0.98 } : {}}
            >
              <RotateCcw className="w-4 h-4" />
              초기화
            </motion.button>
          </motion.div>
        </div>

        {/* Right Column - Sidebar (종합 팀 전력 + 카테고리) */}
        <div className="lg:col-span-1 space-y-6 lg:pt-24">
          {/* Overall Score */}
          <motion.div
            className="glass-strong p-4 rounded-sm border border-white/10"
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
          >
            <div className="flex items-center justify-between mb-3">
              <div>
                <div className="flex items-center gap-2">
                  <TrendingUp className="w-5 h-5 text-brand-accent" />
                  <span className="text-base font-semibold text-white">종합 팀 전력</span>
                </div>
                <p className="text-xs text-white/60 mt-1">
                  5개 영역 가중 평균
                </p>
              </div>
              <div className="text-right">
                <motion.div
                  className={`text-4xl font-bold font-numeric ${scoreGrade.color}`}
                  key={overallScore}
                  initial={{ scale: 0.5 }}
                  animate={{ scale: 1 }}
                  transition={{ type: 'spring', stiffness: 300 }}
                >
                  {overallScore.toFixed(2)}
                </motion.div>
                <div className="text-xs text-white/60">/ 5.0</div>
              </div>
            </div>

            {/* Grade Badge & Progress */}
            <div className="flex items-center gap-2">
              <span className="text-xl">{scoreGrade.emoji}</span>
              <div className="flex-1">
                <div className={`text-sm font-semibold ${scoreGrade.color} mb-1.5`}>
                  {scoreGrade.label}
                </div>
                <div className="h-2 bg-white/10 rounded-full overflow-hidden">
                  <motion.div
                    className={`h-full bg-gradient-to-r ${
                      overallScore >= 4.5 ? 'from-success to-success/70' :
                      overallScore >= 4.0 ? 'from-brand-accent to-brand-accent/70' :
                      overallScore >= 3.0 ? 'from-brand-primary to-brand-primary/70' :
                      'from-error to-error/70'
                    }`}
                    initial={{ width: 0 }}
                    animate={{ width: `${(overallScore / 5) * 100}%` }}
                    transition={{ duration: 0.8, ease: 'easeOut' }}
                  />
                </div>
              </div>
            </div>
          </motion.div>

          {/* Category Breakdown */}
          <div className="space-y-3">
            {Object.entries(TEAM_STRENGTH_FRAMEWORK).map(([key, category]) => {
              const Icon = category.icon;
              const categoryAvg = calculateCategoryAverage(key);

              return (
                <motion.div
                  key={key}
                  className="glass p-3 rounded-sm border border-white/10 cursor-pointer hover:border-brand-primary/50 transition-all"
                  onClick={() => setExpandedCategory(expandedCategory === key ? null : key)}
                  whileHover={{ scale: 1.02 }}
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <Icon className={`w-4 h-4 ${category.color}`} />
                      <span className="text-sm font-semibold text-white">{category.name}</span>
                    </div>
                    <span className="text-xs text-white/60">{Math.round(category.weight * 100)}%</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <div className={`text-xl font-bold font-numeric ${category.color}`}>
                      {categoryAvg.toFixed(2)}
                    </div>
                    <div className="text-xs text-white/60">/ 5.0</div>
                  </div>
                  <div className="mt-2 h-1.5 bg-white/10 rounded-full overflow-hidden">
                    <motion.div
                      className={`h-full bg-gradient-to-r ${
                        categoryAvg >= 4.0 ? 'from-success to-success/70' :
                        categoryAvg >= 3.0 ? 'from-brand-primary to-brand-primary/70' :
                        'from-error to-error/70'
                      }`}
                      initial={{ width: 0 }}
                      animate={{ width: `${(categoryAvg / 5) * 100}%` }}
                      transition={{ duration: 0.6 }}
                    />
                  </div>
                </motion.div>
              );
            })}
          </div>
        </div>
      </div>
      </div>
    </div>
  );
};

export default TeamRating;
