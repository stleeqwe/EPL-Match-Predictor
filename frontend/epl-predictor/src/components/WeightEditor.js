import React, { useState } from 'react';
import { Save, X, Sliders, ChevronDown, ChevronUp } from 'lucide-react';

const PRESETS = {
  default: { recent5: 50, current: 35, last: 15, name: '기본값' },
  recentFocus: { recent5: 70, current: 25, last: 5, name: '최근 중시' },
  seasonFocus: { recent5: 30, current: 60, last: 10, name: '시즌 중시' },
  balanced: { recent5: 40, current: 40, last: 20, name: '균형' }
};

function WeightEditor({
  recent5Weight,
  currentSeasonWeight,
  lastSeasonWeight,
  onSave,
  darkMode,
  showAnalysisDetails = false
}) {
  const [showEditor, setShowEditor] = useState(false);
  const [showDetailed, setShowDetailed] = useState(false);
  const [tempRecent5, setTempRecent5] = useState(recent5Weight);
  const [tempCurrent, setTempCurrent] = useState(currentSeasonWeight);
  const [tempLast, setTempLast] = useState(lastSeasonWeight);

  const handleStartEdit = () => {
    setTempRecent5(recent5Weight);
    setTempCurrent(currentSeasonWeight);
    setTempLast(lastSeasonWeight);
    setShowEditor(true);
  };

  const handleSave = () => {
    const total = tempRecent5 + tempCurrent + tempLast;

    if (total !== 100) {
      alert(`⚠️ 가중치 합계 오류\n\n현재 합계: ${total}%\n총 가중치는 반드시 100%여야 합니다.\n\n각 가중치를 조정해주세요.`);
      return;
    }

    onSave(tempRecent5, tempCurrent, tempLast);
    setShowEditor(false);
  };

  const handleCancel = () => {
    setTempRecent5(recent5Weight);
    setTempCurrent(currentSeasonWeight);
    setTempLast(lastSeasonWeight);
    setShowEditor(false);
  };

  const applyPreset = (preset) => {
    setTempRecent5(PRESETS[preset].recent5);
    setTempCurrent(PRESETS[preset].current);
    setTempLast(PRESETS[preset].last);
  };

  const total = tempRecent5 + tempCurrent + tempLast;
  const isValid = total === 100;

  const cardBg = darkMode ? 'bg-gray-800' : 'bg-white';
  const borderColor = darkMode ? 'border-gray-700' : 'border-gray-200';

  return (
    <div className={`${cardBg} border-2 ${borderColor} rounded-2xl p-6 shadow-lg`}>
      {/* 헤더 */}
      <div className="flex items-center justify-between mb-6 pb-4 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg">
            <Sliders className="w-6 h-6 text-white" />
          </div>
          <div>
            <h2 className="text-2xl font-bold">분석 요소 가중치</h2>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              {showEditor ? '가중치를 조정하세요 (합계 100%)' : '현재 적용중인 가중치'}
            </p>
          </div>
        </div>
        {!showEditor ? (
          <button
            onClick={handleStartEdit}
            className="px-5 py-3 bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white rounded-xl font-semibold transition-all shadow-lg hover:shadow-xl flex items-center gap-2"
          >
            <Sliders className="w-4 h-4" />
            수정하기
          </button>
        ) : (
          <div className="flex gap-2">
            <button
              onClick={handleSave}
              disabled={!isValid}
              className={`px-5 py-3 rounded-xl font-semibold transition-all flex items-center gap-2 ${
                isValid
                  ? 'bg-gradient-to-r from-green-500 to-green-600 hover:from-green-600 hover:to-green-700 text-white shadow-lg'
                  : 'bg-gray-300 dark:bg-gray-700 text-gray-500 cursor-not-allowed'
              }`}
            >
              <Save className="w-4 h-4" />
              저장
            </button>
            <button
              onClick={handleCancel}
              className="px-5 py-3 bg-gray-500 hover:bg-gray-600 text-white rounded-xl font-semibold transition-colors flex items-center gap-2"
            >
              <X className="w-4 h-4" />
              취소
            </button>
          </div>
        )}
      </div>

      {/* 가중치 시각화 바 - 개선된 버전 */}
      <div className="mb-8">
        <div className="mb-4">
          <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">가중치 분포</h3>
        </div>
        <div className="relative">
          <div className="flex h-16 rounded-xl overflow-hidden shadow-lg border-2 border-gray-300 dark:border-gray-600">
            {/* 최근 5경기 */}
            <div
              className="bg-gradient-to-br from-red-500 to-red-600 flex flex-col items-center justify-center text-white font-bold transition-all duration-500 hover:brightness-110"
              style={{ width: `${showEditor ? tempRecent5 : recent5Weight}%` }}
            >
              {(showEditor ? tempRecent5 : recent5Weight) > 10 && (
                <>
                  <span className="text-xs opacity-90">🔥</span>
                  <span className="text-lg">{showEditor ? tempRecent5 : recent5Weight}%</span>
                </>
              )}
            </div>
            {/* 현재 시즌 */}
            <div
              className="bg-gradient-to-br from-blue-500 to-blue-600 flex flex-col items-center justify-center text-white font-bold transition-all duration-500 hover:brightness-110"
              style={{ width: `${showEditor ? tempCurrent : currentSeasonWeight}%` }}
            >
              {(showEditor ? tempCurrent : currentSeasonWeight) > 10 && (
                <>
                  <span className="text-xs opacity-90">📊</span>
                  <span className="text-lg">{showEditor ? tempCurrent : currentSeasonWeight}%</span>
                </>
              )}
            </div>
            {/* 지난 시즌 */}
            <div
              className="bg-gradient-to-br from-gray-500 to-gray-600 flex flex-col items-center justify-center text-white font-bold transition-all duration-500 hover:brightness-110"
              style={{ width: `${showEditor ? tempLast : lastSeasonWeight}%` }}
            >
              {(showEditor ? tempLast : lastSeasonWeight) > 10 && (
                <>
                  <span className="text-xs opacity-90">📅</span>
                  <span className="text-lg">{showEditor ? tempLast : lastSeasonWeight}%</span>
                </>
              )}
            </div>
          </div>
          {/* 라벨 */}
          <div className="grid grid-cols-3 gap-2 mt-3">
            <div className="text-center">
              <div className="text-xs font-semibold text-red-600 dark:text-red-400">🔥 최근 5경기</div>
              <div className="text-xs text-gray-500 dark:text-gray-400">현재 폼 반영</div>
            </div>
            <div className="text-center">
              <div className="text-xs font-semibold text-blue-600 dark:text-blue-400">📊 현재 시즌</div>
              <div className="text-xs text-gray-500 dark:text-gray-400">시즌 전체 평가</div>
            </div>
            <div className="text-center">
              <div className="text-xs font-semibold text-gray-600 dark:text-gray-400">📅 지난 시즌</div>
              <div className="text-xs text-gray-500 dark:text-gray-400">역사적 데이터</div>
            </div>
          </div>
        </div>
      </div>

      {/* 편집 UI */}
      {showEditor && (
        <div className="space-y-6">
          {/* 프리셋 버튼 - 개선된 버전 */}
          <div>
            <div className="flex items-center gap-2 mb-4">
              <span className="text-lg">⚡</span>
              <h4 className="text-sm font-bold text-gray-700 dark:text-gray-300">빠른 설정 프리셋</h4>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {Object.entries(PRESETS).map(([key, preset]) => (
                <button
                  key={key}
                  onClick={() => applyPreset(key)}
                  className={`
                    p-4 rounded-xl border-2 transition-all
                    ${darkMode
                      ? 'border-gray-600 bg-gray-700/50 hover:bg-gray-600 hover:border-blue-500'
                      : 'border-gray-300 bg-gray-50 hover:bg-white hover:border-blue-500'
                    }
                    hover:shadow-lg transform hover:scale-105
                  `}
                >
                  <div className="font-bold mb-2 text-blue-600 dark:text-blue-400">{preset.name}</div>
                  <div className="flex justify-center items-center gap-1 text-xs font-mono">
                    <span className="px-2 py-1 bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300 rounded">{preset.recent5}</span>
                    <span className="text-gray-400">/</span>
                    <span className="px-2 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded">{preset.current}</span>
                    <span className="text-gray-400">/</span>
                    <span className="px-2 py-1 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded">{preset.last}</span>
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* 숫자 입력 */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <label className="block text-sm font-semibold mb-2">🔥 최근 5경기</label>
              <div className="relative">
                <input
                  type="number"
                  min="0"
                  max="100"
                  value={tempRecent5}
                  onChange={(e) => setTempRecent5(Math.max(0, Math.min(100, parseInt(e.target.value) || 0)))}
                  className={`w-full p-3 pr-10 rounded-lg border-2 ${
                    darkMode ? 'bg-gray-700 border-gray-600 text-white' : 'bg-white border-gray-300'
                  } text-xl font-bold text-center focus:border-red-500 focus:outline-none`}
                />
                <span className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 font-semibold">%</span>
              </div>
            </div>

            <div>
              <label className="block text-sm font-semibold mb-2">📊 현재 시즌</label>
              <div className="relative">
                <input
                  type="number"
                  min="0"
                  max="100"
                  value={tempCurrent}
                  onChange={(e) => setTempCurrent(Math.max(0, Math.min(100, parseInt(e.target.value) || 0)))}
                  className={`w-full p-3 pr-10 rounded-lg border-2 ${
                    darkMode ? 'bg-gray-700 border-gray-600 text-white' : 'bg-white border-gray-300'
                  } text-xl font-bold text-center focus:border-blue-500 focus:outline-none`}
                />
                <span className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 font-semibold">%</span>
              </div>
            </div>

            <div>
              <label className="block text-sm font-semibold mb-2">📅 지난 시즌</label>
              <div className="relative">
                <input
                  type="number"
                  min="0"
                  max="100"
                  value={tempLast}
                  onChange={(e) => setTempLast(Math.max(0, Math.min(100, parseInt(e.target.value) || 0)))}
                  className={`w-full p-3 pr-10 rounded-lg border-2 ${
                    darkMode ? 'bg-gray-700 border-gray-600 text-white' : 'bg-white border-gray-300'
                  } text-xl font-bold text-center focus:border-gray-500 focus:outline-none`}
                />
                <span className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 font-semibold">%</span>
              </div>
            </div>
          </div>

          {/* 합계 표시 */}
          <div className={`p-4 rounded-lg ${
            isValid
              ? darkMode ? 'bg-green-900/20 border border-green-700' : 'bg-green-50 border border-green-200'
              : darkMode ? 'bg-red-900/20 border border-red-700' : 'bg-red-50 border border-red-200'
          }`}>
            <div className="flex justify-between items-center">
              <span className="font-semibold">총 가중치</span>
              <span className={`text-2xl font-bold ${isValid ? 'text-green-600' : 'text-red-600'}`}>
                {total}%
              </span>
            </div>
            {!isValid && (
              <div className="text-xs text-red-600 mt-2 flex items-center gap-1">
                <span>⚠️</span>
                <span>총 가중치는 100%여야 합니다 (현재: {total}%)</span>
              </div>
            )}
            {isValid && (
              <div className="text-xs text-green-600 mt-2 flex items-center gap-1">
                <span>✓</span>
                <span>가중치 합계가 올바릅니다. [저장] 버튼을 눌러주세요.</span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* 분석 요소 상세 - 통합 */}
      {showAnalysisDetails && (
        <div className="mt-8 pt-8 border-t border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-xl font-bold">📊 분석 요소 상세</h3>
            <button
              onClick={() => setShowDetailed(!showDetailed)}
              className={`px-4 py-2 rounded-lg font-semibold transition-colors flex items-center gap-2 ${
                showDetailed
                  ? 'bg-gradient-to-r from-purple-500 to-purple-600 text-white'
                  : darkMode
                    ? 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              {showDetailed ? (
                <>
                  <ChevronUp className="w-4 h-4" />
                  요약 보기
                </>
              ) : (
                <>
                  <ChevronDown className="w-4 h-4" />
                  상세 보기
                </>
              )}
            </button>
          </div>

          {!showDetailed ? (
            /* 요약 뷰 */
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* 최근 5경기 */}
              <div className={`p-5 rounded-xl border-2 border-red-500 ${darkMode ? 'bg-red-900/10' : 'bg-red-50'}`}>
                <div className="flex items-center justify-between mb-4">
                  <h3 className="font-bold text-red-600">🔥 최근 5경기</h3>
                  <span className="text-xs font-bold bg-red-500 text-white px-2 py-1 rounded">
                    {recent5Weight}%
                  </span>
                </div>
                <div className="space-y-3 text-sm">
                  <div className={`p-3 rounded ${darkMode ? 'bg-gray-800' : 'bg-white'}`}>
                    <div className="flex justify-between items-center mb-1">
                      <span className="text-xs text-gray-500">Expected Goals (xG)</span>
                      <span className="font-bold text-red-600">25%</span>
                    </div>
                    <div className="text-xs text-gray-600 dark:text-gray-400">최근 공격 퍼포먼스</div>
                  </div>
                  <div className={`p-3 rounded ${darkMode ? 'bg-gray-800' : 'bg-white'}`}>
                    <div className="flex justify-between items-center mb-1">
                      <span className="text-xs text-gray-500">Expected Goals Against (xGA)</span>
                      <span className="font-bold text-red-600">15%</span>
                    </div>
                    <div className="text-xs text-gray-600 dark:text-gray-400">최근 수비 안정성</div>
                  </div>
                  <div className={`p-3 rounded ${darkMode ? 'bg-gray-800' : 'bg-white'}`}>
                    <div className="flex justify-between items-center mb-1">
                      <span className="text-xs text-gray-500">승점 추이</span>
                      <span className="font-bold text-red-600">10%</span>
                    </div>
                    <div className="text-xs text-gray-600 dark:text-gray-400">팀 모멘텀</div>
                  </div>
                </div>
                <div className={`mt-4 p-3 rounded ${darkMode ? 'bg-red-900/20' : 'bg-red-100'} text-xs`}>
                  <strong>분석 이유:</strong> 현재 팀 컨디션, 부상자, 전술 변화, 최근 폼을 가장 정확하게 반영
                </div>
              </div>

              {/* 현재 시즌 */}
              <div className={`p-5 rounded-xl border-2 border-blue-500 ${darkMode ? 'bg-blue-900/10' : 'bg-blue-50'}`}>
                <div className="flex items-center justify-between mb-4">
                  <h3 className="font-bold text-blue-600">📊 현재 시즌</h3>
                  <span className="text-xs font-bold bg-blue-500 text-white px-2 py-1 rounded">
                    {currentSeasonWeight}%
                  </span>
                </div>
                <div className="space-y-3 text-sm">
                  <div className={`p-3 rounded ${darkMode ? 'bg-gray-800' : 'bg-white'}`}>
                    <div className="flex justify-between items-center mb-1">
                      <span className="text-xs text-gray-500">시즌 평균 xG/xGA</span>
                      <span className="font-bold text-blue-600">15%</span>
                    </div>
                    <div className="text-xs text-gray-600 dark:text-gray-400">전체 시즌 공격/수비력</div>
                  </div>
                  <div className={`p-3 rounded ${darkMode ? 'bg-gray-800' : 'bg-white'}`}>
                    <div className="flex justify-between items-center mb-1">
                      <span className="text-xs text-gray-500">홈/원정 성적 차이</span>
                      <span className="font-bold text-blue-600">10%</span>
                    </div>
                    <div className="text-xs text-gray-600 dark:text-gray-400">홈 어드밴티지 (γ)</div>
                  </div>
                  <div className={`p-3 rounded ${darkMode ? 'bg-gray-800' : 'bg-white'}`}>
                    <div className="flex justify-between items-center mb-1">
                      <span className="text-xs text-gray-500">슈팅 효율 & 빌드업</span>
                      <span className="font-bold text-blue-600">10%</span>
                    </div>
                    <div className="text-xs text-gray-600 dark:text-gray-400">득점 전환율 & 창출 능력</div>
                  </div>
                </div>
                <div className={`mt-4 p-3 rounded ${darkMode ? 'bg-blue-900/20' : 'bg-blue-100'} text-xs`}>
                  <strong>분석 이유:</strong> 충분한 샘플 크기로 팀의 실력을 안정적으로 평가
                </div>
              </div>

              {/* 지난 시즌 */}
              <div className={`p-5 rounded-xl border-2 border-gray-500 ${darkMode ? 'bg-gray-700/30' : 'bg-gray-50'}`}>
                <div className="flex items-center justify-between mb-4">
                  <h3 className="font-bold text-gray-600 dark:text-gray-400">📅 지난 시즌</h3>
                  <span className="text-xs font-bold bg-gray-500 text-white px-2 py-1 rounded">
                    {lastSeasonWeight}%
                  </span>
                </div>
                <div className="space-y-3 text-sm">
                  <div className={`p-3 rounded ${darkMode ? 'bg-gray-800' : 'bg-white'}`}>
                    <div className="flex justify-between items-center mb-1">
                      <span className="text-xs text-gray-500">최종 순위 & 승점</span>
                      <span className="font-bold text-gray-600">8%</span>
                    </div>
                    <div className="text-xs text-gray-600 dark:text-gray-400">팀 등급 참고</div>
                  </div>
                  <div className={`p-3 rounded ${darkMode ? 'bg-gray-800' : 'bg-white'}`}>
                    <div className="flex justify-between items-center mb-1">
                      <span className="text-xs text-gray-500">H2H 전적</span>
                      <span className="font-bold text-gray-600">5%</span>
                    </div>
                    <div className="text-xs text-gray-600 dark:text-gray-400">상대 전적</div>
                  </div>
                  <div className={`p-3 rounded ${darkMode ? 'bg-gray-800' : 'bg-white'}`}>
                    <div className="flex justify-between items-center mb-1">
                      <span className="text-xs text-gray-500">팀 스타일</span>
                      <span className="font-bold text-gray-600">2%</span>
                    </div>
                    <div className="text-xs text-gray-600 dark:text-gray-400">역사적 성향</div>
                  </div>
                </div>
                <div className={`mt-4 p-3 rounded ${darkMode ? 'bg-gray-700' : 'bg-gray-100'} text-xs`}>
                  <strong>분석 이유:</strong> 시즌 초반 데이터 부족 시 보완용, 팀 역사적 맥락 제공
                </div>
              </div>
            </div>
          ) : (
            /* 상세 뷰 */
            <div className="space-y-6">
              {/* 추가 보정 요소 */}
              <div className={`p-5 rounded-xl border-2 ${darkMode ? 'border-purple-700 bg-purple-900/10' : 'border-purple-300 bg-purple-50'}`}>
                <h3 className="font-bold mb-4 text-purple-600">⚡ 추가 보정 요소</h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                  <div>
                    <div className="font-semibold mb-1">홈 어드밴티지 (γ)</div>
                    <div className="text-xs text-gray-600 dark:text-gray-400">통상 +20~30% 공격력</div>
                  </div>
                  <div>
                    <div className="font-semibold mb-1">Dixon-Coles τ</div>
                    <div className="text-xs text-gray-600 dark:text-gray-400">저점수 경기 보정</div>
                  </div>
                  <div>
                    <div className="font-semibold mb-1">리그 평균 기준</div>
                    <div className="text-xs text-gray-600 dark:text-gray-400">1.43 득점/경기</div>
                  </div>
                  <div>
                    <div className="font-semibold mb-1">시간 가중치</div>
                    <div className="text-xs text-gray-600 dark:text-gray-400">최신 데이터 우선</div>
                  </div>
                </div>
              </div>

              {/* 최종 계산식 */}
              <div className={`p-5 rounded-xl ${darkMode ? 'bg-gradient-to-r from-gray-800 to-gray-700' : 'bg-gradient-to-r from-gray-100 to-gray-50'} border-2 border-gray-400`}>
                <h3 className="font-bold mb-3">🔢 최종 예측 공식</h3>
                <div className="font-mono text-sm space-y-2">
                  <div className={darkMode ? 'text-blue-400' : 'text-blue-600'}>
                    λ = (최근5 × {recent5Weight/100}) + (현시즌 × {currentSeasonWeight/100}) + (지난시즌 × {lastSeasonWeight/100})
                  </div>
                  <div className={darkMode ? 'text-green-400' : 'text-green-600'}>
                    λ_home = α_home × β_away × γ × φ × 1.43
                  </div>
                  <div className={darkMode ? 'text-orange-400' : 'text-orange-600'}>
                    P(결과) = Poisson(λ) × Dixon-Coles(τ)
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default WeightEditor;
