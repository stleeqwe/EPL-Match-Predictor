import React from 'react';
import PropTypes from 'prop-types';
import Standings from './Standings';
import Fixtures from './Fixtures';
import Leaderboard from './Leaderboard';

const EPLDashboard = ({ darkMode = false, onTeamClick, onMatchSimulatorClick, onMatchPredictionClick, onPlayerClick }) => {
  return (
    <div className="py-4 min-h-screen">
      <div className="container-custom">
        {/* Main Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          {/* Left: Fixtures */}
          <div className="animate-fade-in-up" style={{ animationDelay: '0.1s' }}>
            <Fixtures
              darkMode={darkMode}
              limit={10}
              onMatchSimulatorClick={onMatchSimulatorClick}
              onMatchPredictionClick={onMatchPredictionClick}
            />
          </div>

          {/* Right: Standings + Leaderboard (2 columns on large screens) */}
          <div className="lg:col-span-2 space-y-4">
            <div className="animate-fade-in-up" style={{ animationDelay: '0.2s' }}>
              <Standings darkMode={darkMode} onTeamClick={onTeamClick} />
            </div>
            <div className="animate-fade-in-up" style={{ animationDelay: '0.3s' }}>
              <Leaderboard darkMode={darkMode} onPlayerClick={onPlayerClick} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

EPLDashboard.propTypes = {
  darkMode: PropTypes.bool,
  onTeamClick: PropTypes.func,
  onMatchSimulatorClick: PropTypes.func,
  onMatchPredictionClick: PropTypes.func,
  onPlayerClick: PropTypes.func
};

EPLDashboard.defaultProps = {
  darkMode: false,
  onTeamClick: () => {},
  onMatchSimulatorClick: () => {},
  onMatchPredictionClick: () => {},
  onPlayerClick: () => {}
};

export default EPLDashboard;
