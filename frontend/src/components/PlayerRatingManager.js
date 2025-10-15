import React, { useState, useEffect, useRef, useCallback } from 'react';
import PropTypes from 'prop-types';
import { Star, Shield, Grid3x3, BarChart3, ChevronLeft } from 'lucide-react';
import TeamSelector from './TeamSelector';
import PlayerList from './PlayerList';
import RatingEditor from './RatingEditor';
import TeamAnalytics from './TeamAnalytics';
import TeamRating from './TeamRating';
import DataManager from './DataManager';
import SquadBuilder from './SquadBuilder';
import api from '../services/api';

/**
 * PlayerRatingManager Component
 * EPL 선수 능력치 관리 메인 컴포넌트
 */
function PlayerRatingManager({ darkMode = false, initialTeam = null, initialPlayer = null, onRatingsUpdate = null }) {
  const [selectedTeam, setSelectedTeam] = useState(initialTeam);
  const [selectedPlayer, setSelectedPlayer] = useState(null);
  const [players, setPlayers] = useState([]); // 선수 목록
  const [playerRatings, setPlayerRatings] = useState({}); // { playerId: { attr: rating, ... }, ... }
  const [loading, setLoading] = useState(false); // 팀 데이터 로딩
  // 🔧 isSaving 제거 (더 이상 사용하지 않음)
  const [initialLoading, setInitialLoading] = useState(true); // 첫 로딩 여부
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('squad'); // 'squad', 'players', 'strength', 'analytics'
  const hasSelectedInitialPlayer = useRef(false); // initialPlayer 처리 여부 추적

  /**
   * 팀 데이터 로드 (선수 목록 + 능력치)
   */
  const loadTeamData = useCallback(async () => {
    try {
      setLoading(true);

      // 1. 선수 목록 가져오기
      const squadResponse = await api.teams.getSquad(selectedTeam);

      setPlayers(squadResponse.squad || []);

      // 2. localStorage에서 능력치 로드 (임시 저장용)
      const saved = localStorage.getItem(`team_ratings_${selectedTeam}`);
      if (saved) {
        const loadedRatings = JSON.parse(saved);
        setPlayerRatings(loadedRatings);

        // 🔧 App.js의 상태도 업데이트 (팀 로드 시)
        if (onRatingsUpdate) {
          onRatingsUpdate(selectedTeam, loadedRatings);
        }
      } else {
        // 평가 데이터가 없으면 빈 객체로 설정
        setPlayerRatings({});
        if (onRatingsUpdate) {
          onRatingsUpdate(selectedTeam, {});
        }
      }

      setError(null);
      setInitialLoading(false); // 🔧 첫 로딩 완료
    } catch (err) {
      console.error('❌ Failed to load team data:', err);
      setError('팀 데이터를 불러오는데 실패했습니다');
      setInitialLoading(false); // 🔧 에러 발생 시에도 초기 로딩 종료
    } finally {
      setLoading(false);
    }
  }, [selectedTeam, onRatingsUpdate]);

  // 🔧 초기 진입 시 Arsenal을 기본 팀으로 설정
  useEffect(() => {
    if (!initialTeam && !selectedTeam) {
      setSelectedTeam('Arsenal');
      setActiveTab('squad');
    }
  }, []); // 컴포넌트 마운트 시 한 번만 실행

  // initialTeam이 변경되면 selectedTeam도 업데이트하고 상태 초기화
  useEffect(() => {
    if (initialTeam) {
      setSelectedTeam(initialTeam);
      // initialPlayer가 없는 경우에만 선수 선택 초기화
      if (!initialPlayer) {
        setSelectedPlayer(null);
        hasSelectedInitialPlayer.current = false;
      }
      setActiveTab('squad'); // 🔧 항상 스쿼드 탭으로 시작

      // 페이지 전환 애니메이션 완료 후 스크롤 (300ms transition + 여유)
      setTimeout(() => {
        window.scrollTo({ top: 0, behavior: 'auto' });
      }, 350);
    }
  }, [initialTeam, initialPlayer]);

  // 팀이 선택되면 해당 팀의 모든 선수 능력치 및 선수 목록 로드
  useEffect(() => {
    if (selectedTeam) {
      loadTeamData();
    }
  }, [selectedTeam, loadTeamData]);

  // 🔧 스크롤 자동 이동 기능 제거 (2025-10-08)
  // 코멘트 작성 후 저장 시 스크롤 위치 유지를 위해 제거됨

  // initialPlayer가 변경될 때 처리 플래그 초기화
  useEffect(() => {
    if (initialPlayer) {
      hasSelectedInitialPlayer.current = false;
    }
  }, [initialPlayer]);

  // initialPlayer가 제공되고 팀 데이터가 로드된 후 자동으로 선수 선택
  useEffect(() => {
    const selectInitialPlayer = async () => {
      if (initialPlayer && players.length > 0 && !loading && !hasSelectedInitialPlayer.current) {
        // players 배열에서 initialPlayer와 일치하는 선수 찾기
        // 1. ID 매칭 (가장 정확)
        let matchedPlayer = players.find(p => p.id === initialPlayer.id);

        // 2. 정확한 이름 매칭
        if (!matchedPlayer) {
          matchedPlayer = players.find(p => p.name === initialPlayer.name);
        }

        // 3. 부분 이름 매칭 (이름이 포함되어 있는지)
        if (!matchedPlayer) {
          matchedPlayer = players.find(p =>
            p.name.toLowerCase().includes(initialPlayer.name.toLowerCase()) ||
            initialPlayer.name.toLowerCase().includes(p.name.toLowerCase())
          );
        }

        if (matchedPlayer) {
          hasSelectedInitialPlayer.current = true; // 처리 완료 표시

          // handlePlayerSelect 로직을 직접 실행
          try {
            setLoading(true);

            // 선수 능력치 조회
            let ratings = playerRatings[matchedPlayer.id];

            if (!ratings) {
              // 백엔드에서 조회 시도
              try {
                const response = await api.ratings.get(matchedPlayer.id);
                const backendRatings = response.ratings || {};

                // 백엔드 응답 형식 변환
                ratings = {};
                for (const [key, value] of Object.entries(backendRatings)) {
                  if (key === '_comment' || key === '_subPosition') {
                    ratings[key] = value.notes || (key === '_subPosition' ? 'CM' : '');
                  } else if (typeof value === 'object' && value !== null && 'rating' in value) {
                    ratings[key] = value.rating;
                  } else {
                    ratings[key] = value;
                  }
                }
              } catch (err) {
                ratings = {};
              }
            }

            setSelectedPlayer({
              ...matchedPlayer,
              currentRatings: ratings
            });

            // 🔧 스크롤을 최상단으로 이동 (팀 선택 없이 선수만 선택된 경우)
            requestAnimationFrame(() => {
              requestAnimationFrame(() => {
                window.scrollTo({ top: 0, behavior: 'auto' });
              });
            });
          } catch (err) {
            console.error('❌ Failed to load player ratings:', err);
            setSelectedPlayer(matchedPlayer);
          } finally {
            setLoading(false);
          }
        }
      }
    };

    selectInitialPlayer();
  }, [initialPlayer, players, loading, playerRatings]);

  /**
   * 선수 능력치 저장
   */
  const handleSaveRatings = async (playerId, ratings) => {
    try {
      // 🔧 전체 화면 오버레이 제거 (깜빡임 방지)
      // RatingEditor에 이미 저장 중 표시가 있으므로 중복 제거

      // 백엔드 API로 저장
      await api.ratings.save(playerId, ratings);

      // 로컬 state 업데이트
      setPlayerRatings(prev => ({
        ...prev,
        [playerId]: ratings
      }));

      // localStorage에도 백업 저장
      const updated = {
        ...playerRatings,
        [playerId]: ratings
      };
      localStorage.setItem(`team_ratings_${selectedTeam}`, JSON.stringify(updated));

      // 🔧 App.js의 상태도 업데이트 (다른 컴포넌트에서 실시간 반영)
      if (onRatingsUpdate && selectedTeam) {
        onRatingsUpdate(selectedTeam, updated);
      }

      // 🔧 selectedPlayer 업데이트 제거 (불필요한 리렌더링 방지)
      // RatingEditor는 이미 저장된 값을 가지고 있으므로 업데이트 불필요

    } catch (err) {
      console.error('Failed to save ratings:', err);
      setError('저장에 실패했습니다: ' + err.message);
    }
  };

  /**
   * 선수 선택 핸들러
   */
  const handlePlayerSelect = async (player) => {
    try {
      setLoading(true);

      // 선수 능력치 조회
      let ratings = playerRatings[player.id];

      if (!ratings) {
        // 백엔드에서 조회 시도
        try {
          const response = await api.ratings.get(player.id);
          const backendRatings = response.ratings || {};

          // 백엔드 응답 형식 변환
          ratings = {};
          for (const [key, value] of Object.entries(backendRatings)) {
            if (key === '_comment' || key === '_subPosition') {
              ratings[key] = value.notes || (key === '_subPosition' ? 'CM' : '');
            } else if (typeof value === 'object' && value !== null && 'rating' in value) {
              ratings[key] = value.rating;
            } else {
              ratings[key] = value;
            }
          }
        } catch (err) {
          ratings = {};
        }
      }

      setSelectedPlayer({
        ...player,
        currentRatings: ratings
      });

    } catch (err) {
      console.error('Failed to load player ratings:', err);
      setSelectedPlayer(player);
    } finally {
      setLoading(false);
    }
  };

  /**
   * 팀 선택 핸들러
   */
  const handleTeamSelect = (team) => {
    setSelectedTeam(team);
    setSelectedPlayer(null);
    setActiveTab('squad'); // 팀 선택 시 항상 스쿼드 탭으로 이동
  };

  /**
   * RatingEditor 닫기
   */
  const handleCancelEdit = () => {
    setSelectedPlayer(null);

    // 🔧 선수 카드 화면으로 돌아갈 때 스크롤 초기화 (2025-10-08)
    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        window.scrollTo({ top: 0, behavior: 'smooth' });
      });
    });
  };

  /**
   * 로컬 저장
   */
  const handleSaveToLocal = () => {
    if (!selectedTeam) return;
    localStorage.setItem(`team_ratings_${selectedTeam}`, JSON.stringify(playerRatings));
    alert('능력치가 로컬에 저장되었습니다!');
  };

  /**
   * 데이터 내보내기
   */
  const handleExportData = () => {
    // DataManager 컴포넌트에서 처리
  };

  /**
   * 데이터 가져오기
   */
  const handleImportData = (importedRatings) => {
    setPlayerRatings(importedRatings);
    if (selectedTeam) {
      localStorage.setItem(`team_ratings_${selectedTeam}`, JSON.stringify(importedRatings));

      // 🔧 App.js의 상태도 업데이트
      if (onRatingsUpdate) {
        onRatingsUpdate(selectedTeam, importedRatings);
      }
    }
  };

  return (
    <div className="py-4 min-h-screen">
      <div className="container-custom">
        {/* Main Content */}
        <div>
          {/* 선수 능력치 편집 모드 */}
          <div className={`transition-opacity duration-300 ${
            selectedPlayer ? 'opacity-100' : 'opacity-0 absolute pointer-events-none'
          }`}>
            {selectedPlayer && (
              <RatingEditor
                player={selectedPlayer}
                darkMode={darkMode}
                onSave={handleSaveRatings}
                onCancel={handleCancelEdit}
                initialRatings={selectedPlayer.currentRatings || {}}
              />
            )}
          </div>

          {/* 팀 선택 & 선수 목록 모드 */}
          <div className={`transition-opacity duration-300 ${
            !selectedPlayer ? 'opacity-100' : 'opacity-0 absolute pointer-events-none'
          }`}>
          <div className="grid grid-cols-1 lg:grid-cols-5 gap-4">
              {/* Left: Unified Sidebar */}
              <div className="lg:col-span-1">
                <div className="animate-fade-in-up relative" style={{ animationDelay: '0.1s' }}>
                  {/* Unified Sidebar Container */}
                  <div className="relative rounded bg-gradient-to-br from-slate-900/80 via-blue-950/60 to-slate-900/80 backdrop-blur-sm border border-cyan-500/20 shadow-2xl p-6">
                    {/* Tech Grid Pattern */}
                    <div
                      className="absolute inset-0 opacity-[0.02] pointer-events-none"
                      style={{
                        backgroundImage: `
                          linear-gradient(rgba(6, 182, 212, 0.5) 1px, transparent 1px),
                          linear-gradient(90deg, rgba(6, 182, 212, 0.5) 1px, transparent 1px)
                        `,
                        backgroundSize: '20px 20px'
                      }}
                    />

                    {/* Section 1: Team Selector */}
                    <div className="relative z-[100]">
                      <TeamSelector
                        darkMode={darkMode}
                        onTeamSelect={handleTeamSelect}
                        selectedTeam={selectedTeam}
                        nested={true}
                      />
                    </div>

                    {/* Divider */}
                    <div className="relative h-[1px] bg-gradient-to-r from-transparent via-cyan-500/50 to-transparent my-6" />

                    {/* Section 2: Navigation Menu */}
                    {selectedTeam && (
                      <div className="relative z-10">
                        <div className="space-y-1">
                          {/* Section Title */}
                          <div className="mb-3">
                            <h3 className="text-xs font-bold text-cyan-400/60 uppercase tracking-wider font-mono">
                              Menu
                            </h3>
                          </div>

                          <button
                            onClick={() => setActiveTab('squad')}
                            className={`
                              w-full px-4 py-3 rounded-sm transition-all flex items-center gap-3
                              ${activeTab === 'squad'
                                ? 'bg-slate-900/80 text-cyan-400 font-bold shadow-sm border border-cyan-500/40'
                                : 'bg-slate-900/40 text-white/60 font-medium hover:text-cyan-300 hover:bg-slate-900/60 border border-transparent'}
                            `}
                          >
                            <Grid3x3 className="w-4 h-4" />
                            <span className="text-sm font-grotesk">SQUAD</span>
                          </button>

                          <button
                            onClick={() => setActiveTab('players')}
                            className={`
                              w-full px-4 py-3 rounded-sm transition-all flex items-center gap-3
                              ${activeTab === 'players'
                                ? 'bg-slate-900/80 text-cyan-400 font-bold shadow-sm border border-cyan-500/40'
                                : 'bg-slate-900/40 text-white/60 font-medium hover:text-cyan-300 hover:bg-slate-900/60 border border-transparent'}
                            `}
                          >
                            <Star className="w-4 h-4" />
                            <span className="text-sm font-grotesk">PLAYER</span>
                          </button>

                          <button
                            onClick={() => setActiveTab('strength')}
                            className={`
                              w-full px-4 py-3 rounded-sm transition-all flex items-center gap-3
                              ${activeTab === 'strength'
                                ? 'bg-slate-900/80 text-cyan-400 font-bold shadow-sm border border-cyan-500/40'
                                : 'bg-slate-900/40 text-white/60 font-medium hover:text-cyan-300 hover:bg-slate-900/60 border border-transparent'}
                            `}
                          >
                            <Shield className="w-4 h-4" />
                            <span className="text-sm font-grotesk">TEAM</span>
                          </button>

                          <button
                            onClick={() => setActiveTab('analytics')}
                            className={`
                              w-full px-4 py-3 rounded-sm transition-all flex items-center gap-3
                              ${activeTab === 'analytics'
                                ? 'bg-slate-900/80 text-cyan-400 font-bold shadow-sm border border-cyan-500/40'
                                : 'bg-slate-900/40 text-white/60 font-medium hover:text-cyan-300 hover:bg-slate-900/60 border border-transparent'}
                            `}
                          >
                            <BarChart3 className="w-4 h-4" />
                            <span className="text-sm font-grotesk">ANALYSIS</span>
                          </button>
                        </div>
                      </div>
                    )}

                    {/* Divider */}
                    <div className="relative h-[1px] bg-gradient-to-r from-transparent via-cyan-500/50 to-transparent my-6" />

                    {/* Section 3: Data Manager */}
                    <div className="relative z-10">
                      <DataManager
                        selectedTeam={selectedTeam}
                        players={players}
                        playerRatings={playerRatings}
                        onSave={handleSaveToLocal}
                        onExport={handleExportData}
                        onImport={handleImportData}
                        darkMode={darkMode}
                        nested={true}
                      />
                    </div>
                  </div>
                </div>
              </div>

              {/* Right: Content Area */}
              <div className="lg:col-span-4 animate-fade-in-up" style={{ animationDelay: '0.3s' }}>
                {selectedTeam ? (
                  <div>
                    {/* Content */}
                    {activeTab === 'analytics' ? (
                      <TeamAnalytics
                        team={selectedTeam}
                        players={players}
                        playerRatings={playerRatings}
                        darkMode={darkMode}
                      />
                    ) : activeTab === 'strength' ? (
                      <TeamRating
                        team={selectedTeam}
                        darkMode={darkMode}
                      />
                    ) : activeTab === 'squad' ? (
                      <SquadBuilder
                        team={selectedTeam}
                        darkMode={darkMode}
                        playerRatings={playerRatings}
                        onPlayerSelect={handlePlayerSelect}
                      />
                    ) : (
                      <PlayerList
                        team={selectedTeam}
                        players={players}
                        darkMode={darkMode}
                        onPlayerSelect={handlePlayerSelect}
                        playerRatings={playerRatings}
                      />
                    )}
                  </div>
                ) : (
                  <div className="bg-slate-900/60 border border-cyan-500/20 rounded-sm p-16 text-center">
                    <ChevronLeft className="w-24 h-24 mx-auto mb-6 text-cyan-400/50" />
                    <p className="text-xl text-white/80 mb-2">
                      왼쪽에서 팀을 선택해주세요
                    </p>
                    <p className="text-sm text-white/50">
                      선수 능력치 평가를 시작합니다
                    </p>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* 🔧 Loading Overlay 제거 (깜빡임 방지) */}
        {/* RatingEditor에 이미 저장 중 표시가 있으므로 제거 */}

        {/* Error Toast */}
        {error && (
          <div className="fixed bottom-4 right-4 bg-error text-white px-6 py-4 rounded-sm shadow-lg z-50 animate-slide-in-right">
            <p className="font-semibold">{error}</p>
            <button
              onClick={() => setError(null)}
              className="mt-2 text-sm underline hover:no-underline"
            >
              닫기
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

PlayerRatingManager.propTypes = {
  darkMode: PropTypes.bool,
  initialTeam: PropTypes.string,
  initialPlayer: PropTypes.object,
  onRatingsUpdate: PropTypes.func
};

PlayerRatingManager.defaultProps = {
  darkMode: false,
  initialTeam: null,
  initialPlayer: null,
  onRatingsUpdate: null
};

export default PlayerRatingManager;
