import React from 'react';
import { motion } from 'framer-motion';
import { TrendingUp, Shield, Crown } from 'lucide-react';

/**
 * OddsComparisonTable - 북메이커별 배당률 비교 테이블
 */
const OddsComparisonTable = ({ match }) => {
  const { home_team, away_team, bookmakers_raw, best_odds, consensus_probability } = match;

  if (!bookmakers_raw || Object.keys(bookmakers_raw).length === 0) {
    return (
      <div className="rounded-sm bg-white/5 border border-white/10 p-6 text-center">
        <Shield className="w-12 h-12 text-white/40 mx-auto mb-3" />
        <p className="text-white/60">배당률 데이터가 없습니다</p>
      </div>
    );
  }

  // 최고 배당률 표시
  const isBestOdds = (bookmaker, outcome, odds) => {
    if (!best_odds || !best_odds[outcome]) return false;
    return best_odds[outcome].bookmaker === bookmaker && best_odds[outcome].odds === odds;
  };

  // 북메이커 목록
  const bookmakers = Object.keys(bookmakers_raw);

  return (
    <div className="rounded-2xl bg-white/5 border border-white/10 backdrop-blur-sm overflow-hidden">
      {/* 헤더 */}
      <div className="bg-gradient-to-r from-violet-600/20 to-purple-600/20 border-b border-white/10 p-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-bold text-white mb-1">
              {home_team} vs {away_team}
            </h3>
            <p className="text-sm text-white/60">북메이커 배당률 비교</p>
          </div>
          <div className="flex items-center gap-2 text-xs text-white/60">
            <Crown className="w-4 h-4" />
            <span>최고 배당률</span>
          </div>
        </div>
      </div>

      {/* 테이블 */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-white/10">
              <th className="text-left py-3 px-4 text-xs font-semibold text-white/60 uppercase">
                북메이커
              </th>
              <th className="text-center py-3 px-4 text-xs font-semibold text-white/60 uppercase">
                홈 승
              </th>
              <th className="text-center py-3 px-4 text-xs font-semibold text-white/60 uppercase">
                무승부
              </th>
              <th className="text-center py-3 px-4 text-xs font-semibold text-white/60 uppercase">
                원정 승
              </th>
            </tr>
          </thead>
          <tbody>
            {bookmakers.map((bookmaker, index) => {
              const odds = bookmakers_raw[bookmaker];
              const isPinnacle = bookmaker.toLowerCase() === 'pinnacle';

              return (
                <motion.tr
                  key={bookmaker}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.05 }}
                  className={`border-b border-white/5 hover:bg-white/5 transition-colors ${
                    isPinnacle ? 'bg-violet-500/10' : ''
                  }`}
                >
                  {/* 북메이커 이름 */}
                  <td className="py-3 px-4">
                    <div className="flex items-center gap-2">
                      {isPinnacle && (
                        <Shield className="w-4 h-4 text-violet-400" />
                      )}
                      <span className={`font-semibold ${
                        isPinnacle ? 'text-violet-300' : 'text-white'
                      }`}>
                        {bookmaker}
                      </span>
                      {isPinnacle && (
                        <span className="text-xs px-2 py-0.5 rounded-full bg-violet-500/20 text-violet-300">
                          Sharp
                        </span>
                      )}
                    </div>
                  </td>

                  {/* 홈 승 */}
                  <td className="py-3 px-4 text-center">
                    {odds.home ? (
                      <div className="inline-flex items-center gap-1">
                        {isBestOdds(bookmaker, 'home', odds.home) && (
                          <Crown className="w-3 h-3 text-yellow-400" />
                        )}
                        <span className={`font-bold ${
                          isBestOdds(bookmaker, 'home', odds.home)
                            ? 'text-yellow-300 text-base'
                            : 'text-white text-sm'
                        }`}>
                          {odds.home.toFixed(2)}
                        </span>
                      </div>
                    ) : (
                      <span className="text-white/30 text-sm">-</span>
                    )}
                  </td>

                  {/* 무승부 */}
                  <td className="py-3 px-4 text-center">
                    {odds.draw ? (
                      <div className="inline-flex items-center gap-1">
                        {isBestOdds(bookmaker, 'draw', odds.draw) && (
                          <Crown className="w-3 h-3 text-yellow-400" />
                        )}
                        <span className={`font-bold ${
                          isBestOdds(bookmaker, 'draw', odds.draw)
                            ? 'text-yellow-300 text-base'
                            : 'text-white text-sm'
                        }`}>
                          {odds.draw.toFixed(2)}
                        </span>
                      </div>
                    ) : (
                      <span className="text-white/30 text-sm">-</span>
                    )}
                  </td>

                  {/* 원정 승 */}
                  <td className="py-3 px-4 text-center">
                    {odds.away ? (
                      <div className="inline-flex items-center gap-1">
                        {isBestOdds(bookmaker, 'away', odds.away) && (
                          <Crown className="w-3 h-3 text-yellow-400" />
                        )}
                        <span className={`font-bold ${
                          isBestOdds(bookmaker, 'away', odds.away)
                            ? 'text-yellow-300 text-base'
                            : 'text-white text-sm'
                        }`}>
                          {odds.away.toFixed(2)}
                        </span>
                      </div>
                    ) : (
                      <span className="text-white/30 text-sm">-</span>
                    )}
                  </td>
                </motion.tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Consensus 확률 (있는 경우) */}
      {consensus_probability && (
        <div className="bg-white/5 border-t border-white/10 p-4">
          <div className="flex items-center gap-2 mb-2">
            <TrendingUp className="w-4 h-4 text-white/60" />
            <span className="text-xs font-semibold text-white/60">합의 확률 (Consensus)</span>
          </div>
          <div className="grid grid-cols-3 gap-3">
            <div className="text-center">
              <div className="text-xs text-white/60 mb-1">홈 승</div>
              <div className="text-sm font-bold text-white">
                {(consensus_probability.home * 100).toFixed(1)}%
              </div>
            </div>
            <div className="text-center">
              <div className="text-xs text-white/60 mb-1">무승부</div>
              <div className="text-sm font-bold text-white">
                {(consensus_probability.draw * 100).toFixed(1)}%
              </div>
            </div>
            <div className="text-center">
              <div className="text-xs text-white/60 mb-1">원정 승</div>
              <div className="text-sm font-bold text-white">
                {(consensus_probability.away * 100).toFixed(1)}%
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default OddsComparisonTable;
