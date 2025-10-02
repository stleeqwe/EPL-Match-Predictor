import React, { useState } from 'react';
import { ChevronDown, ChevronUp } from 'lucide-react';

function AnalysisDetails({ recent5Weight, currentSeasonWeight, lastSeasonWeight, darkMode }) {
  const [showDetailed, setShowDetailed] = useState(false);

  const cardBg = darkMode ? 'bg-gray-800' : 'bg-white';
  const borderColor = darkMode ? 'border-gray-700' : 'border-gray-200';

  return (
    <div className={`${cardBg} border ${borderColor} rounded-lg p-6`}>
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-bold text-gray-900 dark:text-white">분석 요소 상세</h3>
        <button
          onClick={() => setShowDetailed(!showDetailed)}
          className={`px-3 py-2 rounded-lg font-medium transition-colors flex items-center gap-2 ${
            showDetailed
              ? 'bg-blue-500 text-white'
              : darkMode
                ? 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
          }`}
        >
          {showDetailed ? (
            <>
              <ChevronUp className="w-4 h-4" />
              요약
            </>
          ) : (
            <>
              <ChevronDown className="w-4 h-4" />
              상세
            </>
          )}
        </button>
      </div>

      {!showDetailed ? (
        /* 요약 뷰 */
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* 최근 5경기 */}
          <div className={`p-4 rounded-lg border ${borderColor} ${darkMode ? 'bg-gray-700' : 'bg-gray-50'}`}>
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-semibold text-gray-900 dark:text-white">최근 5경기</h3>
              <span className="text-xs font-semibold bg-blue-500 text-white px-2 py-1 rounded">
                {recent5Weight}%
              </span>
            </div>
            <div className="space-y-2 text-sm text-gray-600 dark:text-gray-400">
              <div>• Expected Goals (xG) - 최근 공격력</div>
              <div>• Expected Goals Against (xGA) - 수비 안정성</div>
              <div>• 승점 추이 - 팀 모멘텀</div>
            </div>
            <div className={`mt-3 p-3 rounded text-xs text-gray-600 dark:text-gray-400 ${darkMode ? 'bg-gray-800' : 'bg-white'}`}>
              현재 팀 컨디션과 최근 폼을 정확하게 반영
            </div>
          </div>

          {/* 현재 시즌 */}
          <div className={`p-4 rounded-lg border ${borderColor} ${darkMode ? 'bg-gray-700' : 'bg-gray-50'}`}>
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-semibold text-gray-900 dark:text-white">현재 시즌</h3>
              <span className="text-xs font-semibold bg-blue-500 text-white px-2 py-1 rounded">
                {currentSeasonWeight}%
              </span>
            </div>
            <div className="space-y-2 text-sm text-gray-600 dark:text-gray-400">
              <div>• 시즌 평균 xG/xGA - 전체 실력</div>
              <div>• 홈/원정 성적 차이</div>
              <div>• 슈팅 효율 - 득점 전환율</div>
              <div>• 키패스 & 빌드업</div>
            </div>
            <div className={`mt-3 p-3 rounded text-xs text-gray-600 dark:text-gray-400 ${darkMode ? 'bg-gray-800' : 'bg-white'}`}>
              충분한 샘플로 팀 실력을 안정적으로 평가
            </div>
          </div>

          {/* 지난 시즌 */}
          <div className={`p-4 rounded-lg border ${borderColor} ${darkMode ? 'bg-gray-700' : 'bg-gray-50'}`}>
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-semibold text-gray-900 dark:text-white">지난 시즌</h3>
              <span className="text-xs font-semibold bg-blue-500 text-white px-2 py-1 rounded">
                {lastSeasonWeight}%
              </span>
            </div>
            <div className="space-y-2 text-sm text-gray-600 dark:text-gray-400">
              <div>• 최종 순위 & 승점 - 팀 등급</div>
              <div>• H2H 전적 - 상대 전적</div>
              <div>• 팀 스타일 - 역사적 성향</div>
            </div>
            <div className={`mt-3 p-3 rounded text-xs text-gray-600 dark:text-gray-400 ${darkMode ? 'bg-gray-800' : 'bg-white'}`}>
              시즌 초반 데이터 부족 시 보완 및 역사적 맥락 제공
            </div>
          </div>
        </div>
      ) : (
        /* 상세 뷰 */
        <div className="space-y-6">
          {/* 추가 보정 요소 */}
          <div className={`p-4 rounded-lg border ${borderColor} ${darkMode ? 'bg-gray-700' : 'bg-gray-50'}`}>
            <h3 className="font-semibold mb-3 text-gray-900 dark:text-white">추가 보정 요소</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm text-gray-600 dark:text-gray-400">
              <div>
                <div className="font-medium mb-1">홈 어드밴티지 (γ)</div>
                <div className="text-xs">통상 +20~30% 공격력</div>
              </div>
              <div>
                <div className="font-medium mb-1">Dixon-Coles τ</div>
                <div className="text-xs">저점수 경기 보정</div>
              </div>
              <div>
                <div className="font-medium mb-1">리그 평균 기준</div>
                <div className="text-xs">1.43 득점/경기</div>
              </div>
              <div>
                <div className="font-medium mb-1">시간 가중치</div>
                <div className="text-xs">최신 데이터 우선</div>
              </div>
            </div>
          </div>

          {/* 최종 계산식 */}
          <div className={`p-4 rounded-lg border ${borderColor} ${darkMode ? 'bg-gray-700' : 'bg-gray-50'}`}>
            <h3 className="font-semibold mb-3 text-gray-900 dark:text-white">최종 예측 공식</h3>
            <div className="font-mono text-sm space-y-2 text-gray-700 dark:text-gray-300">
              <div>
                λ = (최근5 × {recent5Weight/100}) + (현시즌 × {currentSeasonWeight/100}) + (지난시즌 × {lastSeasonWeight/100})
              </div>
              <div>
                λ_home = α_home × β_away × γ × φ × 1.43
              </div>
              <div>
                P(결과) = Poisson(λ) × Dixon-Coles(τ)
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default AnalysisDetails;
