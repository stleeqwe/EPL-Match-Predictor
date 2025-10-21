/**
 * SimulationDashboard Component - V2 Pipeline Edition
 * Premium Real-time AI Simulation Progress Monitoring
 * Features: 7-Phase Pipeline, Scenario Cards, Convergence Graph, Live Stats
 */

import React, { useState, useEffect, useMemo, useRef } from 'react';
import useSSESimulation from '../hooks/useSSESimulation';
import './SimulationDashboard.css';

const SimulationDashboard = ({
  homeTeam,
  awayTeam,
  onComplete,
  onCancel
}) => {
  const {
    status,
    events,
    currentEvent,
    result,
    error,
    progress,
    // V2 Pipeline State
    currentPhase,
    scenarios,
    currentIteration,
    maxIterations,
    convergenceData,
    phaseTimeline,
    simulationStats,
    // Methods
    startSimulation,
    cancelSimulation,
    getElapsedTime,
    isStreaming,
    isCompleted,
    hasError
  } = useSSESimulation();

  const [elapsedTime, setElapsedTime] = useState(0);
  const [showResult, setShowResult] = useState(false);
  const hasStartedRef = useRef(false);
  const mountCountRef = useRef(0);

  // Debug: Log component mount
  useEffect(() => {
    mountCountRef.current += 1;
    console.log(`🔍 [SimulationDashboard] Component mounted/updated (count: ${mountCountRef.current})`);
    console.log(`🔍 [SimulationDashboard] homeTeam: ${homeTeam}, awayTeam: ${awayTeam}`);
    console.log(`🔍 [SimulationDashboard] hasStartedRef.current: ${hasStartedRef.current}`);
  });

  // Start simulation on mount (only once)
  useEffect(() => {
    console.log(`🔍 [SimulationDashboard] useEffect triggered`);
    console.log(`🔍 [SimulationDashboard] homeTeam: ${homeTeam}, awayTeam: ${awayTeam}`);
    console.log(`🔍 [SimulationDashboard] hasStartedRef.current: ${hasStartedRef.current}`);

    if (homeTeam && awayTeam && !hasStartedRef.current) {
      hasStartedRef.current = true;
      console.log(`✅ [SimulationDashboard] Starting simulation: ${homeTeam} vs ${awayTeam}`);
      startSimulation(homeTeam, awayTeam);
    } else {
      console.log(`⏭️ [SimulationDashboard] Skipping simulation start (already started or missing teams)`);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [homeTeam, awayTeam]);

  // Update elapsed time
  useEffect(() => {
    if (isStreaming) {
      const interval = setInterval(() => {
        setElapsedTime(getElapsedTime());
      }, 100);
      return () => clearInterval(interval);
    }
  }, [isStreaming, getElapsedTime]);

  // Handle completion
  useEffect(() => {
    if (isCompleted && result) {
      setTimeout(() => {
        setShowResult(true);
        setTimeout(() => {
          onComplete && onComplete(result);
        }, 500);
      }, 2000);
    }
  }, [isCompleted, result, onComplete]);

  // Handle cancel
  const handleCancel = () => {
    cancelSimulation();
    onCancel && onCancel();
  };

  // Format elapsed time
  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  // Pipeline phases configuration
  const pipelinePhases = [
    { id: 1, label: 'Generate', icon: '🎯', title: 'Generate Scenarios' },
    { id: '2-5', label: 'Refine', icon: '🔄', title: 'Iterative Refinement' },
    { id: 6, label: 'Simulate', icon: '⚡', title: 'Final Simulation' },
    { id: 7, label: 'Aggregate', icon: '📊', title: 'Result Aggregation' }
  ];

  // Get phase status
  const getPhaseStatus = (phaseId) => {
    const phaseIdStr = String(phaseId);
    const currentPhaseStr = String(currentPhase);

    if (currentPhaseStr === phaseIdStr) return 'active';
    if (phaseIdStr === '2-5' && ['2', '3', '4', '5'].includes(currentPhaseStr)) return 'active';

    const phaseOrder = ['1', '2-5', '6', '7'];
    const currentIndex = phaseOrder.indexOf(currentPhaseStr);
    const phaseIndex = phaseOrder.indexOf(phaseIdStr);

    if (currentIndex > phaseIndex) return 'completed';
    return 'pending';
  };

  // Get scenario status badge
  const getScenarioStatusBadge = (scenario) => {
    const statusConfig = {
      'generated': { label: 'Generated', color: 'blue', icon: '✓' },
      'validating': { label: 'Validating', color: 'yellow', icon: '⏳' },
      'converged': { label: 'Converged', color: 'green', icon: '✓' },
      'final': { label: 'Final', color: 'purple', icon: '⚡' }
    };
    return statusConfig[scenario.status] || statusConfig['generated'];
  };

  if (showResult) {
    return null; // Parent will handle result display
  }

  return (
    <div className="simulation-dashboard v2-pipeline">
      <div className="dashboard-container">

        {/* Header */}
        <div className="dashboard-header-v2">
          <div className="header-main">
            <div className="title-section">
              <div className="icon-wrapper-v2">
                <span className="header-icon-v2">🤖</span>
              </div>
              <div>
                <h1 className="title-text-v2 text-gradient">AI Match Simulator V2</h1>
                <p className="subtitle-text-v2">Multi-Scenario Pipeline • Powered by Google Gemini 2.5 Flash</p>
              </div>
            </div>

            <div className="match-info-v2">
              <div className="team-badge-v2 home">
                <span className="team-name-v2">{homeTeam}</span>
              </div>
              <div className="vs-divider-v2">
                <span className="vs-text-v2">VS</span>
              </div>
              <div className="team-badge-v2 away">
                <span className="team-name-v2">{awayTeam}</span>
              </div>
            </div>
          </div>

          {/* Progress Bar */}
          <div className="global-progress-section">
            <div className="progress-header">
              <span className="progress-label">Overall Progress</span>
              <span className="progress-percentage">{Math.round(progress)}%</span>
            </div>
            <div className="progress-bar-wrapper-v2">
              <div className="progress-bar-track-v2">
                <div
                  className="progress-bar-fill-v2"
                  style={{ width: `${progress}%` }}
                >
                  <div className="progress-glow-v2"></div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Pipeline Stepper */}
        <div className="pipeline-stepper">
          {pipelinePhases.map((phase, index) => {
            const status = getPhaseStatus(phase.id);
            return (
              <React.Fragment key={phase.id}>
                <div className={`pipeline-step ${status}`}>
                  <div className="step-icon-wrapper">
                    <span className="step-icon">{phase.icon}</span>
                    {status === 'completed' && (
                      <div className="step-checkmark">✓</div>
                    )}
                    {status === 'active' && (
                      <div className="step-pulse"></div>
                    )}
                  </div>
                  <div className="step-content">
                    <span className="step-number">Phase {phase.id}</span>
                    <span className="step-label">{phase.label}</span>
                  </div>
                </div>
                {index < pipelinePhases.length - 1 && (
                  <div className={`pipeline-connector ${status === 'completed' ? 'active' : ''}`}>
                    <div className="connector-line"></div>
                  </div>
                )}
              </React.Fragment>
            );
          })}
        </div>

        {/* Main Content Grid */}
        <div className="main-grid-v2">

          {/* Left Panel - Scenario Cards */}
          <div className="left-panel-v2">
            <div className="scenarios-section glass-v2">
              <div className="section-header-v2">
                <h2 className="section-title-v2">
                  <span className="title-icon">🎯</span>
                  Tactical Scenarios
                </h2>
                <span className="badge-v2 badge-primary">
                  {scenarios.length} scenario{scenarios.length !== 1 ? 's' : ''}
                </span>
              </div>

              <div className="scenarios-grid">
                {scenarios.length === 0 ? (
                  <div className="empty-state">
                    <div className="empty-icon">⏳</div>
                    <p className="empty-text">Generating tactical scenarios...</p>
                  </div>
                ) : (
                  scenarios.map((scenario, index) => {
                    const statusBadge = getScenarioStatusBadge(scenario);
                    return (
                      <div
                        key={index}
                        className={`scenario-card glass-v2 status-${scenario.status}`}
                        style={{ animationDelay: `${index * 0.1}s` }}
                      >
                        <div className="scenario-header">
                          <div className="scenario-title-row">
                            <span className="scenario-number">#{index + 1}</span>
                            <h3 className="scenario-name">{scenario.name}</h3>
                          </div>
                          <div className={`status-badge badge-${statusBadge.color}`}>
                            <span className="badge-icon">{statusBadge.icon}</span>
                            <span className="badge-text">{statusBadge.label}</span>
                          </div>
                        </div>

                        <div className="scenario-body">
                          <div className="scenario-stat">
                            <span className="stat-label">Probability</span>
                            <span className="stat-value">
                              {(scenario.probability * 100).toFixed(1)}%
                            </span>
                          </div>

                          {scenario.validationRuns > 0 && (
                            <div className="scenario-stat">
                              <span className="stat-label">Validation Runs</span>
                              <span className="stat-value">{scenario.validationRuns}</span>
                            </div>
                          )}

                          {scenario.status === 'validating' && (
                            <div className="scenario-progress">
                              <div className="progress-spinner"></div>
                            </div>
                          )}

                          {scenario.status === 'converged' && (
                            <div className="scenario-badge success">
                              <span>✓ Converged</span>
                            </div>
                          )}
                        </div>
                      </div>
                    );
                  })
                )}
              </div>

              {/* Iteration Info (Phase 2-5) */}
              {currentPhase >= 2 && currentPhase <= 5 && (
                <div className="iteration-info glass-v2">
                  <div className="iteration-header">
                    <span className="iteration-icon">🔄</span>
                    <span className="iteration-text">
                      Iteration {currentIteration} of {maxIterations}
                    </span>
                  </div>
                  <div className="iteration-progress-bar">
                    <div
                      className="iteration-progress-fill"
                      style={{ width: `${(currentIteration / maxIterations) * 100}%` }}
                    ></div>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Right Panel - Stats & Convergence */}
          <div className="right-panel-v2">

            {/* Live Statistics */}
            <div className="stats-card-v2 glass-v2">
              <div className="section-header-v2">
                <h3 className="section-title-v2">
                  <span className="title-icon">📊</span>
                  Live Statistics
                </h3>
              </div>

              <div className="stats-list-v2">
                <div className="stat-item-v2">
                  <div className="stat-icon-v2">🔢</div>
                  <div className="stat-content-v2">
                    <span className="stat-label-v2">Current Phase</span>
                    <span className="stat-value-v2">
                      {currentPhase > 0 ? `Phase ${currentPhase}` : 'Initializing'}
                    </span>
                  </div>
                </div>

                <div className="stat-item-v2">
                  <div className="stat-icon-v2">🔄</div>
                  <div className="stat-content-v2">
                    <span className="stat-label-v2">Iterations</span>
                    <span className="stat-value-v2">
                      {currentIteration} / {maxIterations}
                    </span>
                  </div>
                </div>

                <div className="stat-item-v2">
                  <div className="stat-icon-v2">⚡</div>
                  <div className="stat-content-v2">
                    <span className="stat-label-v2">Total Simulations</span>
                    <span className="stat-value-v2">
                      {simulationStats.totalSimulations.toLocaleString()}
                    </span>
                  </div>
                </div>

                <div className="stat-item-v2">
                  <div className="stat-icon-v2">⏱️</div>
                  <div className="stat-content-v2">
                    <span className="stat-label-v2">Elapsed Time</span>
                    <span className="stat-value-v2">{formatTime(elapsedTime)}</span>
                  </div>
                </div>

                <div className="stat-item-v2">
                  <div className="stat-icon-v2">📡</div>
                  <div className="stat-content-v2">
                    <span className="stat-label-v2">Status</span>
                    <span className={`stat-value-v2 status-${status}`}>
                      {status === 'streaming' ? 'Running' :
                       status === 'completed' ? 'Complete' :
                       status === 'error' ? 'Error' : 'Idle'}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* Convergence Graph */}
            {convergenceData.history.length > 0 && (
              <div className="convergence-card-v2 glass-v2">
                <div className="section-header-v2">
                  <h3 className="section-title-v2">
                    <span className="title-icon">📈</span>
                    Convergence Progress
                  </h3>
                  {convergenceData.converged && (
                    <div className="badge-v2 badge-success">
                      <span>✓ Converged</span>
                    </div>
                  )}
                </div>

                <div className="convergence-info">
                  <div className="convergence-stat">
                    <span className="label">Current Confidence</span>
                    <span className="value text-gradient">
                      {(convergenceData.confidence * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="convergence-stat">
                    <span className="label">Threshold</span>
                    <span className="value">
                      {(convergenceData.threshold * 100).toFixed(0)}%
                    </span>
                  </div>
                </div>

                {/* Simple ASCII-style convergence graph */}
                <div className="convergence-graph">
                  <div className="graph-container">
                    {convergenceData.history.map((point, index) => {
                      const height = (point.confidence / convergenceData.threshold) * 100;
                      const isConverged = point.confidence >= convergenceData.threshold;
                      return (
                        <div
                          key={index}
                          className="graph-bar"
                          style={{
                            height: `${Math.min(height, 100)}%`,
                            backgroundColor: isConverged ? '#10b981' : '#06b6d4'
                          }}
                          title={`Iteration ${point.iteration}: ${(point.confidence * 100).toFixed(1)}%`}
                        >
                          <div className="graph-bar-glow"></div>
                        </div>
                      );
                    })}
                  </div>
                  <div className="graph-threshold-line" style={{ bottom: '85%' }}>
                    <span className="threshold-label">Threshold</span>
                  </div>
                </div>
              </div>
            )}

            {/* Phase Timeline */}
            {phaseTimeline.length > 0 && (
              <div className="phase-timeline-card glass-v2">
                <div className="section-header-v2">
                  <h3 className="section-title-v2">
                    <span className="title-icon">📋</span>
                    Phase Timeline
                  </h3>
                </div>

                <div className="timeline-list-v2">
                  {phaseTimeline.map((phase, index) => (
                    <div
                      key={index}
                      className={`timeline-item-v2 ${phase.status}`}
                    >
                      <div className="timeline-marker-v2">
                        <div className={`marker-dot-v2 ${phase.status}`}></div>
                      </div>
                      <div className="timeline-content-v2">
                        <span className="timeline-phase">Phase {phase.phase}</span>
                        <span className="timeline-title-v2">{phase.title}</span>
                        {phase.status === 'completed' && (
                          <span className="timeline-check">✓</span>
                        )}
                        {phase.status === 'active' && (
                          <span className="timeline-pulse">⚡</span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Current Event Message (Sticky Bottom) */}
        {currentEvent && !isCompleted && (
          <div className="current-event-banner glass-v2">
            <div className="event-content">
              <span className="event-icon">⚡</span>
              <span className="event-message">
                {currentEvent.data?.message || 'Processing...'}
              </span>
            </div>
          </div>
        )}

        {/* Error Display */}
        {hasError && (
          <div className="error-card-v2 glass-v2">
            <div className="error-icon-v2">⚠️</div>
            <div className="error-content-v2">
              <h3 className="error-title-v2">Simulation Error</h3>
              <p className="error-message-v2">{error}</p>
            </div>
          </div>
        )}

        {/* Control Buttons */}
        <div className="control-buttons-v2">
          {isStreaming && (
            <button
              className="btn-v2 btn-error"
              onClick={handleCancel}
            >
              <span className="btn-icon">✕</span>
              <span className="btn-text">Cancel Simulation</span>
            </button>
          )}
        </div>

        {/* Completion Overlay */}
        {isCompleted && !showResult && (
          <div className="completion-overlay-v2">
            <div className="completion-content-v2">
              <div className="completion-icon-v2">✓</div>
              <h2 className="completion-title-v2 text-gradient">Analysis Complete!</h2>
              <p className="completion-message-v2">
                Processed {simulationStats.totalSimulations.toLocaleString()} simulations
                across {scenarios.length} scenarios
              </p>
              <div className="spinner-v2"></div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default SimulationDashboard;
