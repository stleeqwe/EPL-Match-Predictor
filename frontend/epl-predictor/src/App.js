import React, { useState, useEffect } from 'react';
import { Sliders } from 'lucide-react';
import Header from './components/Header';
import TabButton from './components/TabButton';
import MatchSelector from './components/MatchSelector';
import PredictionResult from './components/PredictionResult';
import PredictionLoadingState from './components/PredictionLoadingState';
import { Accordion, AccordionItem } from './components/Accordion';
import StatsChart from './components/StatsChart';
import PlayerRatingManager from './components/PlayerRatingManager';
import StandingsTable from './components/StandingsTable';
import WeightEditor from './components/WeightEditor';
import TopScores from './components/TopScores';
import ModelContribution from './components/ModelContribution';
import ExpectedThreatVisualizer from './components/ExpectedThreatVisualizer';
import EvaluationDashboard from './components/EvaluationDashboard';
import EnsemblePredictor from './components/EnsemblePredictor';
import { ToastContainer } from './components/Toast';
import { useToast } from './hooks/useToast';
import { predictionsAPI, fixturesAPI } from './services/api';
import './App.css';

function App() {
  const [mainView, setMainView] = useState('predict'); // 'predict', 'standings', 'advanced'
  const [activeTab, setActiveTab] = useState('statistical');
  const [darkMode, setDarkMode] = useState(false);
  const [fixtures, setFixtures] = useState([]);
  const [selectedFixtureIndex, setSelectedFixtureIndex] = useState(0);
  const [prediction, setPrediction] = useState(null);
  const [loading, setLoading] = useState(false);
  const [statsWeight, setStatsWeight] = useState(75);
  const [personalWeight, setPersonalWeight] = useState(25);
  const [recent5Weight, setRecent5Weight] = useState(50);
  const [currentSeasonWeight, setCurrentSeasonWeight] = useState(35);
  const [lastSeasonWeight, setLastSeasonWeight] = useState(15);
  const { toasts, removeToast, success, error: showError, info } = useToast();

  // 경기 일정 가져오기
  useEffect(() => {
    fetchFixtures();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const fetchFixtures = async () => {
    try {
      const data = await fixturesAPI.getAll();
      setFixtures(data);
      info('경기 일정을 불러왔습니다');
    } catch (error) {
      console.error('Error fetching fixtures:', error);
      showError('경기 일정을 불러올 수 없습니다.');
      setFixtures([]);
    }
  };

  const selectedFixture = fixtures[selectedFixtureIndex] || {};
  const homeTeam = selectedFixture.home_team || 'Manchester City';
  const awayTeam = selectedFixture.away_team || 'Liverpool';

  // 예측 가져오기
  useEffect(() => {
    if (homeTeam && awayTeam) {
      fetchPrediction();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedFixtureIndex, activeTab, homeTeam, awayTeam]);

  const fetchPrediction = async () => {
    setLoading(true);
    try {
      const data = await predictionsAPI.predict({
        home_team: homeTeam,
        away_team: awayTeam,
        model_type: activeTab,
        stats_weight: statsWeight,
        personal_weight: personalWeight,
        recent5_weight: recent5Weight,
        current_season_weight: currentSeasonWeight,
        last_season_weight: lastSeasonWeight,
        save_prediction: true
      });
      setPrediction(data);
      success('예측이 완료되고 저장되었습니다!');
    } catch (error) {
      console.error('Error:', error);
      showError('예측을 불러올 수 없습니다.');
      setPrediction(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (homeTeam && awayTeam && activeTab === 'hybrid') {
      fetchPrediction();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [statsWeight, personalWeight]);

  useEffect(() => {
    if (homeTeam && awayTeam && activeTab === 'statistical') {
      fetchPrediction();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [recent5Weight, currentSeasonWeight, lastSeasonWeight]);

  const handleWeightSave = (recent5, current, last) => {
    setRecent5Weight(recent5);
    setCurrentSeasonWeight(current);
    setLastSeasonWeight(last);
    success('가중치가 저장되었습니다!');
  };

  const bgColor = darkMode ? 'bg-gray-900' : 'bg-gray-50';
  const cardBg = darkMode ? 'bg-gray-800' : 'bg-white';
  const textColor = darkMode ? 'text-gray-100' : 'text-gray-900';
  const borderColor = darkMode ? 'border-gray-700' : 'border-gray-200';

  return (
    <>
      <ToastContainer toasts={toasts} removeToast={removeToast} />
      <div className={`min-h-screen ${bgColor} ${textColor} p-4 md:p-6 transition-colors duration-300 ${darkMode ? 'dark' : ''}`}>
        <Header darkMode={darkMode} setDarkMode={setDarkMode} />

      {/* 메인 뷰 탭 */}
      <div className="max-w-7xl mx-auto mb-8">
        <div className={`${cardBg} border ${borderColor} rounded-2xl p-2 shadow-lg flex gap-2`}>
          <button
            onClick={() => setMainView('predict')}
            className={`
              flex-1 px-4 py-4 font-semibold rounded-xl transition-all
              ${mainView === 'predict'
                ? 'bg-gradient-to-r from-blue-500 to-blue-600 text-white shadow-lg scale-105'
                : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'
              }
            `}
          >
            <div className="flex flex-col items-center gap-1">
              <span className="text-2xl">🎯</span>
              <span>경기 예측</span>
            </div>
          </button>
          <button
            onClick={() => setMainView('standings')}
            className={`
              flex-1 px-4 py-4 font-semibold rounded-xl transition-all
              ${mainView === 'standings'
                ? 'bg-gradient-to-r from-amber-500 to-amber-600 text-white shadow-lg scale-105'
                : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'
              }
            `}
          >
            <div className="flex flex-col items-center gap-1">
              <span className="text-2xl">🏆</span>
              <span>리그 순위표</span>
            </div>
          </button>
          <button
            onClick={() => setMainView('advanced')}
            className={`
              flex-1 px-4 py-4 font-semibold rounded-xl transition-all
              ${mainView === 'advanced'
                ? 'bg-gradient-to-r from-purple-500 to-purple-600 text-white shadow-lg scale-105'
                : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'
              }
            `}
          >
            <div className="flex flex-col items-center gap-1">
              <span className="text-2xl">🚀</span>
              <span>고급 분석</span>
            </div>
          </button>
        </div>
      </div>

      {mainView === 'predict' && (
        <>
          <div className="max-w-7xl mx-auto mb-8">
            <div className="flex flex-wrap gap-3 md:gap-4">
              <TabButton id="statistical" label="Data 분석" icon="📊" activeTab={activeTab} setActiveTab={setActiveTab} />
              <TabButton id="personal" label="개인분석" icon="⚙️" activeTab={activeTab} setActiveTab={setActiveTab} />
              <TabButton id="hybrid" label="하이브리드" icon="🎯" activeTab={activeTab} setActiveTab={setActiveTab} />
            </div>
          </div>

          <div className="max-w-7xl mx-auto">
            <MatchSelector
          fixtures={fixtures}
          selectedFixtureIndex={selectedFixtureIndex}
          setSelectedFixtureIndex={setSelectedFixtureIndex}
          darkMode={darkMode}
        />

        {/* 하이브리드 모드 슬라이더 */}
        {activeTab === 'hybrid' && (
          <div className={`${cardBg} border ${borderColor} rounded-xl p-6 mb-6`}>
            <div className="flex items-center gap-2 mb-4">
              <Sliders className="w-5 h-5" />
              <h3 className="text-lg font-bold">모델 가중치 조절</h3>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <div className="flex justify-between mb-2">
                  <span className="font-semibold">📊 Data 분석</span>
                  <span className="font-bold text-blue-600">{statsWeight}%</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={statsWeight}
                  onChange={(e) => {
                    const val = parseInt(e.target.value);
                    setStatsWeight(val);
                    setPersonalWeight(100 - val);
                  }}
                  className="w-full h-3 bg-gradient-to-r from-blue-500 to-purple-500 rounded-lg appearance-none cursor-pointer"
                />
              </div>
              <div>
                <div className="flex justify-between mb-2">
                  <span className="font-semibold">⚙️ 개인 분석</span>
                  <span className="font-bold text-purple-600">{personalWeight}%</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={personalWeight}
                  onChange={(e) => {
                    const val = parseInt(e.target.value);
                    setPersonalWeight(val);
                    setStatsWeight(100 - val);
                  }}
                  className="w-full h-3 bg-gradient-to-r from-purple-500 to-blue-500 rounded-lg appearance-none cursor-pointer"
                />
              </div>
            </div>
          </div>
        )}

        {/* 예측 결과 - 경기 선택 바로 아래 */}
        {loading ? (
          <PredictionLoadingState darkMode={darkMode} />
        ) : prediction ? (
          <>
            <PredictionResult
              prediction={prediction}
              homeTeam={homeTeam}
              awayTeam={awayTeam}
              darkMode={darkMode}
            />

            {/* Progressive Disclosure로 부가 정보 정리 */}
            <div className="my-6">
              <Accordion>
                <AccordionItem
                  title="가능 스코어"
                  icon="🎯"
                  defaultOpen={true}
                  darkMode={darkMode}
                >
                  <TopScores topScores={prediction.top_scores} darkMode={darkMode} />
                </AccordionItem>

                <AccordionItem
                  title="상세 통계"
                  icon="📊"
                  defaultOpen={false}
                  darkMode={darkMode}
                >
                  <StatsChart
                    prediction={prediction}
                    homeTeam={homeTeam}
                    awayTeam={awayTeam}
                    darkMode={darkMode}
                  />
                </AccordionItem>
              </Accordion>
            </div>
          </>
        ) : null}

        {/* Data 분석 모드 - 가중치 및 분석 요소 통합 */}
        {activeTab === 'statistical' && (
          <div className="my-6">
            <WeightEditor
              recent5Weight={recent5Weight}
              currentSeasonWeight={currentSeasonWeight}
              lastSeasonWeight={lastSeasonWeight}
              onSave={handleWeightSave}
              darkMode={darkMode}
              showAnalysisDetails={true}
            />
          </div>
        )}

        {/* 개인 분석 모드 - 선수 능력치 입력 */}
        {activeTab === 'personal' && (
          <div className="mb-6">
            <PlayerRatingManager homeTeam={homeTeam} awayTeam={awayTeam} darkMode={darkMode} />
          </div>
        )}

        {/* 하이브리드 모드 - 모델 기여도 분석 */}
        {activeTab === 'hybrid' && prediction && (
          <div className="mb-6">
            <ModelContribution
              statsWeight={statsWeight}
              personalWeight={personalWeight}
              prediction={prediction}
              darkMode={darkMode}
            />
          </div>
        )}
          </div>
        </>
      )}

      {mainView === 'standings' && (
        <StandingsTable darkMode={darkMode} />
      )}

      {mainView === 'advanced' && (
        <div className="max-w-7xl mx-auto space-y-6">
          <div className="grid grid-cols-1 gap-6">
            <EnsemblePredictor />
            <ExpectedThreatVisualizer />
            <EvaluationDashboard />
          </div>
        </div>
      )}
    </div>
    </>
  );
}

export default App;
