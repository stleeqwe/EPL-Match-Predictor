import React, { useState, useEffect } from 'react';
import { simulationAPI } from '../services/authAPI';

export default function AISimulator() {
  const [homeTeam, setHomeTeam] = useState('');
  const [awayTeam, setAwayTeam] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [aiInfo, setAiInfo] = useState(null);
  const [teams, setTeams] = useState([]);

  // Load AI info and available teams
  useEffect(() => {
    const loadAIInfo = async () => {
      try {
        const info = await simulationAPI.getAIInfo();
        setAiInfo(info);
      } catch (err) {
        console.error('Failed to load AI info:', err);
      }
    };

    // Load EPL teams from localStorage
    const loadedTeams = localStorage.getItem('epl_teams');
    if (loadedTeams) {
      try {
        setTeams(JSON.parse(loadedTeams));
      } catch (err) {
        console.error('Failed to parse teams:', err);
      }
    }

    loadAIInfo();
  }, []);

  // Get user's team evaluation from localStorage
  const getUserEvaluation = (teamName) => {
    const key = `team_ratings_${teamName}`;
    const data = localStorage.getItem(key);

    if (!data) {
      // Return default values if no user data
      return {
        overall: 75.0,
        player_score: 75.0,
        strength_score: 75.0,
        comments: 'No user analysis available'
      };
    }

    try {
      const parsed = JSON.parse(data);
      return {
        overall: parsed.overall || 75.0,
        player_score: parsed.player_quality || 75.0,
        strength_score: parsed.team_strength || 75.0,
        comments: parsed.analysis || 'User has provided team ratings'
      };
    } catch (err) {
      console.error('Failed to parse team data:', err);
      return {
        overall: 75.0,
        player_score: 75.0,
        strength_score: 75.0,
        comments: 'Error loading user analysis'
      };
    }
  };

  const handlePredict = async () => {
    if (!homeTeam || !awayTeam) {
      setError('Please select both teams');
      return;
    }

    if (homeTeam === awayTeam) {
      setError('Teams must be different');
      return;
    }

    setLoading(true);
    setError('');
    setResult(null);

    try {
      // Get user evaluations from localStorage
      const homeEval = getUserEvaluation(homeTeam);
      const awayEval = getUserEvaluation(awayTeam);

      // Build user_evaluation object for API
      const userEvaluation = {
        home_overall: homeEval.overall,
        home_player_score: homeEval.player_score,
        home_strength_score: homeEval.strength_score,
        home_comments: homeEval.comments,
        away_overall: awayEval.overall,
        away_player_score: awayEval.player_score,
        away_strength_score: awayEval.strength_score,
        away_comments: awayEval.comments
      };

      // Optional: Add Sharp odds if available
      const sharpOdds = null; // TODO: Get from API or user input

      // Optional: Add recent form if available
      const recentForm = null; // TODO: Get from localStorage or API

      // Call Claude AI prediction
      const data = await simulationAPI.aiPredict(
        homeTeam,
        awayTeam,
        userEvaluation,
        sharpOdds,
        recentForm
      );

      setResult(data);
    } catch (err) {
      setError(err.message || 'AI prediction failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto p-6">
      <div className="bg-white rounded-sm shadow-lg p-8">
        {/* Header */}
        <div className="flex justify-between items-center mb-6">
          <div>
            <h2 className="text-3xl font-bold">Claude AI Match Predictor</h2>
            {aiInfo && (
              <p className="text-sm text-gray-600 mt-2">
                Powered by {aiInfo.model_name} • {aiInfo.capabilities.speed} • {aiInfo.capabilities.cost}
              </p>
            )}
          </div>
          <div className="bg-gradient-to-r from-purple-500 to-indigo-600 text-white px-4 py-2 rounded-full font-semibold text-sm">
            AI-POWERED
          </div>
        </div>

        {/* Team Selection */}
        <div className="grid grid-cols-2 gap-4 mb-6">
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">Home Team</label>
            <select
              value={homeTeam}
              onChange={(e) => setHomeTeam(e.target.value)}
              className="w-full px-4 py-3 border rounded-sm focus:ring-2 focus:ring-purple-500"
            >
              <option value="">Select Home Team</option>
              {teams.map((team) => (
                <option key={team} value={team}>{team}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">Away Team</label>
            <select
              value={awayTeam}
              onChange={(e) => setAwayTeam(e.target.value)}
              className="w-full px-4 py-3 border rounded-sm focus:ring-2 focus:ring-purple-500"
            >
              <option value="">Select Away Team</option>
              {teams.map((team) => (
                <option key={team} value={team}>{team}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Predict Button */}
        <button
          onClick={handlePredict}
          disabled={loading}
          className="w-full bg-gradient-to-r from-purple-600 to-indigo-600 text-white py-4 rounded-sm font-semibold hover:from-purple-700 hover:to-indigo-700 disabled:from-gray-400 disabled:to-gray-500 transition-all duration-200 shadow-lg"
        >
          {loading ? (
            <span className="flex items-center justify-center">
              <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              AI is analyzing... (3-5 seconds)
            </span>
          ) : (
            '🤖 Get AI Prediction'
          )}
        </button>

        {/* Error Display */}
        {error && (
          <div className="mt-4 p-4 bg-red-100 border border-red-300 text-red-700 rounded-sm">
            <div className="font-semibold">Error</div>
            <div className="text-sm mt-1">{error}</div>
          </div>
        )}

        {/* Results Display */}
        {result && result.success && (
          <div className="mt-8 space-y-6">
            {/* Predicted Score */}
            <div className="bg-gradient-to-r from-purple-50 to-indigo-50 p-6 rounded-sm border-2 border-purple-200">
              <div className="text-center">
                <div className="text-sm font-semibold text-gray-600 uppercase mb-2">Predicted Score</div>
                <div className="text-5xl font-bold text-purple-900 mb-4">{result.predicted_score}</div>
                <div className="flex justify-center items-center gap-2 text-sm text-gray-600">
                  <span className="font-semibold">Confidence:</span>
                  <span className={`px-3 py-1 rounded-full font-bold uppercase ${
                    result.confidence === 'high' ? 'bg-green-200 text-green-800' :
                    result.confidence === 'medium' ? 'bg-yellow-200 text-yellow-800' :
                    'bg-gray-200 text-gray-800'
                  }`}>
                    {result.confidence} ({result.confidence_score}/100)
                  </span>
                </div>
              </div>
            </div>

            {/* Win Probabilities */}
            <div className="grid grid-cols-3 gap-4">
              <div className="bg-white border-2 border-green-300 rounded-sm p-4 text-center">
                <div className="text-sm font-semibold text-gray-600 mb-2">Home Win</div>
                <div className="text-3xl font-bold text-green-600">
                  {(result.probabilities.home_win * 100).toFixed(1)}%
                </div>
              </div>
              <div className="bg-white border-2 border-gray-300 rounded-sm p-4 text-center">
                <div className="text-sm font-semibold text-gray-600 mb-2">Draw</div>
                <div className="text-3xl font-bold text-gray-600">
                  {(result.probabilities.draw * 100).toFixed(1)}%
                </div>
              </div>
              <div className="bg-white border-2 border-blue-300 rounded-sm p-4 text-center">
                <div className="text-sm font-semibold text-gray-600 mb-2">Away Win</div>
                <div className="text-3xl font-bold text-blue-600">
                  {(result.probabilities.away_win * 100).toFixed(1)}%
                </div>
              </div>
            </div>

            {/* AI Reasoning */}
            <div className="bg-white border-2 border-indigo-200 rounded-sm p-6">
              <h3 className="text-xl font-bold text-indigo-900 mb-3">🧠 AI Analysis</h3>
              <p className="text-gray-700 leading-relaxed">{result.reasoning}</p>
            </div>

            {/* Key Factors */}
            {result.key_factors && result.key_factors.length > 0 && (
              <div className="bg-white border-2 border-purple-200 rounded-sm p-6">
                <h3 className="text-xl font-bold text-purple-900 mb-3">🔑 Key Factors</h3>
                <ul className="space-y-2">
                  {result.key_factors.map((factor, idx) => (
                    <li key={idx} className="flex items-start">
                      <span className="text-purple-600 font-bold mr-2">•</span>
                      <span className="text-gray-700">{factor}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Expected Goals */}
            {result.expected_goals && (
              <div className="bg-gradient-to-r from-green-50 to-blue-50 border-2 border-green-300 rounded-sm p-6">
                <h3 className="text-xl font-bold text-gray-900 mb-3">⚽ Expected Goals (xG)</h3>
                <div className="grid grid-cols-2 gap-4 text-center">
                  <div>
                    <div className="text-sm font-semibold text-gray-600">{homeTeam}</div>
                    <div className="text-4xl font-bold text-green-600">{result.expected_goals.home.toFixed(1)}</div>
                  </div>
                  <div>
                    <div className="text-sm font-semibold text-gray-600">{awayTeam}</div>
                    <div className="text-4xl font-bold text-blue-600">{result.expected_goals.away.toFixed(1)}</div>
                  </div>
                </div>
              </div>
            )}

            {/* Metadata */}
            {result.metadata && (
              <div className="bg-gray-50 border border-gray-300 rounded-sm p-4">
                <h4 className="text-sm font-semibold text-gray-700 mb-3">📊 Prediction Metadata</h4>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                  <div>
                    <div className="text-gray-600">Model</div>
                    <div className="font-mono text-xs text-gray-900">{result.metadata.model}</div>
                  </div>
                  <div>
                    <div className="text-gray-600">Tokens Used</div>
                    <div className="font-semibold text-gray-900">
                      {result.metadata.tokens_used.total.toLocaleString()}
                    </div>
                  </div>
                  <div>
                    <div className="text-gray-600">Cost</div>
                    <div className="font-semibold text-green-700">
                      ${result.metadata.cost_usd.toFixed(6)}
                    </div>
                  </div>
                  <div>
                    <div className="text-gray-600">Processing</div>
                    <div className="font-semibold text-gray-900">
                      {result.metadata.tokens_used.input}→{result.metadata.tokens_used.output}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* AI Info Footer */}
        {aiInfo && !result && (
          <div className="mt-8 bg-indigo-50 border border-indigo-200 rounded-sm p-6">
            <h3 className="text-lg font-bold text-indigo-900 mb-3">About This AI</h3>
            <div className="space-y-2 text-sm text-gray-700">
              <div><span className="font-semibold">Model:</span> {aiInfo.model_name}</div>
              <div><span className="font-semibold">Speed:</span> {aiInfo.capabilities.speed}</div>
              <div><span className="font-semibold">Cost:</span> {aiInfo.capabilities.cost}</div>
              <div>
                <span className="font-semibold">Best For:</span>{' '}
                {aiInfo.capabilities.best_for.join(', ')}
              </div>
              {aiInfo.future_upgrades && (
                <div className="mt-4 pt-4 border-t border-indigo-200">
                  <div className="font-semibold text-indigo-900 mb-2">Future Upgrades:</div>
                  <div className="text-xs text-gray-600">
                    When higher-tier models become available, you'll get better accuracy and deeper tactical analysis.
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
