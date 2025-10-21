/**
 * useSSESimulation Hook
 * Server-Sent Events (SSE)를 사용한 실시간 시뮬레이션 진행 상태 모니터링
 */

import { useState, useCallback, useRef, useEffect } from 'react';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5001';

export const useSSESimulation = () => {
  const [status, setStatus] = useState('idle'); // 'idle' | 'connecting' | 'streaming' | 'completed' | 'error'
  const [events, setEvents] = useState([]);
  const [currentEvent, setCurrentEvent] = useState(null);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [progress, setProgress] = useState(0);
  const [matchEvents, setMatchEvents] = useState([]); // Real-time match events

  // V2 Pipeline state
  const [currentPhase, setCurrentPhase] = useState(0); // 1-7
  const [scenarios, setScenarios] = useState([]); // Array of scenario objects
  const [currentIteration, setCurrentIteration] = useState(0);
  const [maxIterations, setMaxIterations] = useState(5);
  const [convergenceData, setConvergenceData] = useState({
    converged: false,
    confidence: 0,
    threshold: 0.85,
    history: [] // Array of {iteration, confidence} for graphing
  });
  const [phaseTimeline, setPhaseTimeline] = useState([]); // Array of completed phases
  const [simulationStats, setSimulationStats] = useState({
    totalSimulations: 0,
    scenariosCount: 0,
    iterations: 0,
    elapsedTime: 0
  });

  const eventSourceRef = useRef(null);
  const startTimeRef = useRef(null);

  // Cleanup function
  const cleanup = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      cleanup();
    };
  }, [cleanup]);

  /**
   * Start simulation with SSE streaming
   */
  const startSimulation = useCallback((homeTeam, awayTeam) => {
    console.log(`🚀 [useSSESimulation] startSimulation called`);
    console.log(`🚀 [useSSESimulation] homeTeam: ${homeTeam}, awayTeam: ${awayTeam}`);

    // Reset state
    setStatus('connecting');
    setEvents([]);
    setCurrentEvent(null);
    setResult(null);
    setError(null);
    setProgress(0);
    setMatchEvents([]);

    // Reset V2 Pipeline state
    setCurrentPhase(0);
    setScenarios([]);
    setCurrentIteration(0);
    setMaxIterations(5);
    setConvergenceData({
      converged: false,
      confidence: 0,
      threshold: 0.85,
      history: []
    });
    setPhaseTimeline([]);
    setSimulationStats({
      totalSimulations: 0,
      scenariosCount: 0,
      iterations: 0,
      elapsedTime: 0
    });

    startTimeRef.current = Date.now();

    // Close existing connection
    cleanup();

    try {
      // POST request body
      const requestBody = {
        home_team: homeTeam,
        away_team: awayTeam
      };

      console.log(`📡 [useSSESimulation] Sending POST request to: ${API_BASE_URL}/v1/simulation/v3/stream`);
      console.log(`📡 [useSSESimulation] Request body:`, requestBody);

      // Use fetch to POST data, then establish SSE connection
      fetch(`${API_BASE_URL}/v1/simulation/v3/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
      }).then(response => {
        console.log(`✅ [useSSESimulation] POST response received, status: ${response.status}`);

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        // Create a ReadableStream reader for SSE
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        setStatus('streaming');
        console.log(`📺 [useSSESimulation] Started streaming...`);

        // Read stream
        function readStream() {
          reader.read().then(({ done, value }) => {
            if (done) {
              console.log('🏁 [SSE] Stream closed');
              return;
            }

            // Decode chunk
            const chunk = decoder.decode(value, { stream: true });
            console.log('📦 [SSE] Received chunk:', chunk.substring(0, 200) + (chunk.length > 200 ? '...' : ''));
            buffer += chunk;

            // Process complete SSE messages
            const messages = buffer.split('\n\n');
            buffer = messages.pop(); // Keep incomplete message in buffer
            console.log(`📨 [SSE] Split into ${messages.length} messages, buffer remainder: ${buffer.length} chars`);

            messages.forEach(message => {
              if (!message.trim()) return;

              console.log('🔍 [SSE] Processing message:', message.substring(0, 150) + (message.length > 150 ? '...' : ''));

              // Parse SSE message (event: type\ndata: json)
              const lines = message.split('\n');
              let eventType = null;
              let eventData = null;

              lines.forEach(line => {
                if (line.startsWith('event:')) {
                  eventType = line.substring(6).trim();
                  console.log('📌 [SSE] Event type:', eventType);
                } else if (line.startsWith('data:')) {
                  try {
                    eventData = JSON.parse(line.substring(5).trim());
                    console.log('📊 [SSE] Event data:', eventData);
                  } catch (e) {
                    console.error('❌ [SSE] Failed to parse SSE data:', e, 'Raw:', line.substring(5, 100));
                  }
                }
              });

              if (eventType && eventData) {
                console.log('✅ [SSE] Calling handleEvent with:', eventType, eventData);
                handleEvent(eventType, eventData);
              } else {
                console.warn('⚠️ [SSE] Incomplete event - type:', eventType, 'data:', !!eventData);
              }
            });

            // Continue reading
            readStream();
          }).catch(err => {
            console.error('❌ [SSE] Stream error:', err);
            setError(err.message);
            setStatus('error');
          });
        }

        readStream();

      }).catch(err => {
        console.error('SSE connection error:', err);
        setError(err.message);
        setStatus('error');
      });

    } catch (err) {
      console.error('SSE start error:', err);
      setError(err.message);
      setStatus('error');
    }
  }, [cleanup]);

  /**
   * Handle SSE event
   */
  const handleEvent = (eventType, eventData) => {
    console.log('🎯 [handleEvent] Called with type:', eventType, 'data:', eventData);

    // V3 Pipeline sends events with type="info"/"success"/"error" and stage in eventData.stage
    // Use stage as the actual event type for processing
    const actualEventType = eventData.stage || eventType;
    console.log('🔄 [handleEvent] Actual event type (using stage):', actualEventType);

    const event = {
      type: actualEventType,
      data: eventData,
      timestamp: eventData.timestamp || new Date().toISOString()
    };

    // ✅ P0 FIX: Don't add heartbeat events to history (prevents clutter)
    if (actualEventType !== 'heartbeat') {
      // Add to events history
      console.log('📝 [handleEvent] Adding event to history');
      setEvents(prev => [...prev, event]);
      setCurrentEvent(event);
    }

    // Calculate progress based on stage
    const stageProgress = {
      // V3 Pipeline events (LATEST - Oct 2025)
      'started': 0,
      'loading_teams': 5,
      'teams_loaded': 10,
      'phase1_started': 15,    // Mathematical Models
      'phase1_complete': 20,
      'phase2_started': 20,    // AI Scenario Generation
      'phase2_complete': 60,   // Biggest time consumer (AI)
      'phase3_started': 60,    // Monte Carlo Validation
      'phase3_complete': 95,
      'completed': 100,

      // V2 Pipeline events (LEGACY)
      'phase2_5_started': 20,
      'iteration_started': null, // Dynamic based on iteration
      'phase2_validating': null, // Dynamic
      'phase3_analyzing': null, // Dynamic
      'convergence_check': null, // Dynamic
      'convergence_reached': 85,
      'phase6_started': 85,
      'phase6_complete': 95,
      'phase7_started': 95,
      'phase7_complete': 98,

      // Legacy V1 events (OLD)
      'loading_home_team': 5,
      'home_team_loaded': 10,
      'loading_away_team': 12,
      'away_team_loaded': 15,
      'building_prompt': 40,
      'prompt_ready': 45,
      'ai_started': 50,
      'ai_generating': 70,
      'ai_completed': 85,
      'parsing_result': 90,
      'result_parsed': 95
    };

    // Update progress
    if (eventData.progress !== undefined) {
      // Use progress from event data if available (V2 Pipeline events include this)
      const progressValue = Math.round(eventData.progress * 100);
      console.log('📊 [handleEvent] Setting progress from event data:', progressValue);
      setProgress(progressValue);
    } else if (actualEventType === 'ai_generating' && eventData.progress !== undefined) {
      // Legacy AI progress (50% to 85%)
      const aiProgress = 50 + (eventData.progress * 35);
      console.log('📊 [handleEvent] Setting AI progress:', aiProgress);
      setProgress(aiProgress);
    } else if (stageProgress[actualEventType] !== undefined && stageProgress[actualEventType] !== null) {
      console.log('📊 [handleEvent] Setting progress from stageProgress:', stageProgress[actualEventType]);
      setProgress(stageProgress[actualEventType]);
    }

    // Handle specific event types
    switch (actualEventType) {
      case 'heartbeat':
        // ✅ P0 FIX: Silently handle heartbeat (connection keepalive)
        // Don't add to events history, just log
        console.debug('SSE heartbeat received:', eventData);
        break;

      // ========================================
      // V3 Pipeline Events (Oct 2025)
      // ========================================
      case 'started':
        console.log('🚀 [V3] Simulation started');
        setStatus('streaming');
        break;

      case 'loading_teams':
        console.log('📂 [V3] Loading team data...');
        break;

      case 'teams_loaded':
        console.log('✅ [V3] Teams loaded');
        break;

      case 'phase2_started':
        console.log('🤖 [V3] Phase 2: AI Scenario Generation started');
        setCurrentPhase(2);
        break;

      case 'phase2_complete':
        console.log('✅ [V3] Phase 2 complete:', eventData.scenario_count, 'scenarios');
        if (eventData.scenarios) {
          setScenarios(eventData.scenarios.map(s => ({
            id: s.id,
            name: s.name,
            probability: s.probability || s.expected_probability,
            status: 'generated'
          })));
          setSimulationStats(prev => ({ ...prev, scenariosCount: eventData.scenario_count }));
        }
        break;

      case 'phase3_started':
        console.log('🎲 [V3] Phase 3: Monte Carlo Validation started');
        setCurrentPhase(3);
        if (eventData.total_runs) {
          setSimulationStats(prev => ({ ...prev, totalSimulations: eventData.total_runs }));
        }
        break;

      case 'phase3_complete':
        console.log('✅ [V3] Phase 3 complete:', eventData.total_runs, 'simulations');
        if (eventData.convergence) {
          console.log('📊 [V3] Final probabilities:', eventData.convergence);
        }
        break;

      case 'match_event':
        // Add match event to the list
        setMatchEvents(prev => [...prev, {
          minute: eventData.minute,
          event_type: eventData.event_type,
          description: eventData.description,
          timestamp: eventData.timestamp
        }]);
        break;

      // V2 Pipeline: Phase 1
      case 'phase1_started':
        setCurrentPhase(1);
        setPhaseTimeline(prev => [...prev, { phase: 1, status: 'active', title: eventData.title, timestamp: eventData.timestamp }]);
        break;

      case 'phase1_complete':
        // Store scenarios from Phase 1
        if (eventData.scenarios) {
          setScenarios(eventData.scenarios.map(s => ({
            name: s.name,
            probability: s.probability,
            status: 'generated', // 'generated' | 'validating' | 'converged' | 'final'
            validationRuns: 0,
            expectedGoals: null
          })));
          setSimulationStats(prev => ({ ...prev, scenariosCount: eventData.scenarios_count }));
        }
        setPhaseTimeline(prev => prev.map(p => p.phase === 1 ? { ...p, status: 'completed' } : p));
        break;

      // V2 Pipeline: Phase 2-5 (Iterative Refinement)
      case 'phase2_5_started':
        setCurrentPhase(2);
        setMaxIterations(eventData.max_iterations || 5);
        setPhaseTimeline(prev => [...prev, { phase: '2-5', status: 'active', title: eventData.title, timestamp: eventData.timestamp }]);
        break;

      case 'iteration_started':
        setCurrentIteration(eventData.iteration);
        setSimulationStats(prev => ({ ...prev, iterations: eventData.iteration }));
        break;

      case 'phase2_validating':
        // Update scenarios status to validating
        setScenarios(prev => prev.map(s => ({ ...s, status: 'validating', validationRuns: eventData.runs_per_scenario })));
        if (eventData.total_runs) {
          setSimulationStats(prev => ({ ...prev, totalSimulations: prev.totalSimulations + eventData.total_runs }));
        }
        break;

      case 'phase3_analyzing':
        setCurrentPhase(3);
        break;

      case 'convergence_check':
        // Update convergence data
        setConvergenceData(prev => ({
          ...prev,
          confidence: eventData.confidence,
          threshold: eventData.threshold,
          converged: eventData.converged,
          history: [...prev.history, { iteration: eventData.iteration, confidence: eventData.confidence }]
        }));
        break;

      case 'convergence_reached':
        setConvergenceData(prev => ({ ...prev, converged: true }));
        setScenarios(prev => prev.map(s => ({ ...s, status: 'converged' })));
        setPhaseTimeline(prev => prev.map(p => p.phase === '2-5' ? { ...p, status: 'completed' } : p));
        break;

      case 'max_iterations_reached':
        // Convergence not reached, but moving forward
        setPhaseTimeline(prev => prev.map(p => p.phase === '2-5' ? { ...p, status: 'completed' } : p));
        break;

      // V2 Pipeline: Phase 6 (Final Simulation)
      case 'phase6_started':
        setCurrentPhase(6);
        setScenarios(prev => prev.map(s => ({ ...s, status: 'final' })));
        setPhaseTimeline(prev => [...prev, { phase: 6, status: 'active', title: eventData.title, timestamp: eventData.timestamp }]);
        if (eventData.total_runs) {
          setSimulationStats(prev => ({ ...prev, totalSimulations: prev.totalSimulations + eventData.total_runs }));
        }
        break;

      case 'phase6_complete':
        setPhaseTimeline(prev => prev.map(p => p.phase === 6 ? { ...p, status: 'completed' } : p));
        break;

      // V2 Pipeline: Phase 7 (Result Aggregation)
      case 'phase7_started':
        setCurrentPhase(7);
        setPhaseTimeline(prev => [...prev, { phase: 7, status: 'active', title: eventData.title, timestamp: eventData.timestamp }]);
        break;

      case 'phase7_complete':
        setPhaseTimeline(prev => prev.map(p => p.phase === 7 ? { ...p, status: 'completed' } : p));
        break;

      case 'completed':
        console.log('🎉 [V3] Simulation completed!', eventData);

        /**
         * V3 Pipeline Result Schema:
         * {
         *   match: { home_team: string, away_team: string },
         *   probabilities: { home_win: number, draw: number, away_win: number },
         *   scenarios: [
         *     { id: string, name: string, expected_probability: number, events_count: number }
         *   ],
         *   validation: {
         *     total_scenarios: number,
         *     total_runs: number,
         *     scenario_results: [
         *       {
         *         scenario_id: string,
         *         scenario_name: string,
         *         convergence_probability: { home_win: number, draw: number, away_win: number },
         *         avg_score: { home: number, away: number }  ⬅️ Object, not string!
         *       }
         *     ]
         *   },
         *   execution_time: number,
         *   pipeline: "v3",
         *   timestamp: number
         * }
         */

        const finalResult = {
          match: eventData.match,
          probabilities: eventData.probabilities,
          scenarios: eventData.scenarios,
          validation: eventData.validation,
          execution_time: eventData.execution_time,
          pipeline: eventData.pipeline || 'v3',
          timestamp: eventData.timestamp
        };
        console.log('📊 [V3] Final result:', finalResult);
        setResult(finalResult);
        setStatus('completed');
        setProgress(100);
        cleanup();
        break;

      case 'error':
        setError(eventData.error || eventData.message);
        setStatus('error');
        cleanup();
        break;

      case 'started':
        setStatus('streaming');
        break;

      default:
        // Continue streaming
        break;
    }
  };

  /**
   * Cancel simulation
   */
  const cancelSimulation = useCallback(() => {
    cleanup();
    setStatus('idle');
    setProgress(0);
  }, [cleanup]);

  /**
   * Get elapsed time
   */
  const getElapsedTime = () => {
    if (!startTimeRef.current) return 0;
    return Math.floor((Date.now() - startTimeRef.current) / 1000);
  };

  return {
    // State
    status,
    events,
    currentEvent,
    result,
    error,
    progress,
    matchEvents, // Real-time match events

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

    // Computed
    isStreaming: status === 'streaming',
    isCompleted: status === 'completed',
    hasError: status === 'error',
    isIdle: status === 'idle'
  };
};

export default useSSESimulation;
