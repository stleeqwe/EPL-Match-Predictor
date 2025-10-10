import React, { useState } from 'react';
import { AlertCircle, CheckCircle, Save, Download, Upload } from 'lucide-react';
import { calculateWeightedAverage, DEFAULT_SUB_POSITION } from '../config/positionAttributes';

/**
 * DataManager Component
 * 능력치 데이터 관리 (내보내기/가져오기/저장)
 */
const DataManager = ({
  selectedTeam,
  players = [],
  playerRatings,
  onSave,
  onExport,
  onImport,
  darkMode = false,
  nested = false  // 통합 사이드바 내부에 있을 때 true
}) => {
  const [importStatus, setImportStatus] = useState(null); // null, 'success', 'error'
  const [importMessage, setImportMessage] = useState('');

  // 팀 코멘트 가져오기 헬퍼
  const getTeamComment = (teamName) => {
    return localStorage.getItem(`team_comment_${teamName}`) || '';
  };

  // 로컬 저장
  const handleSave = () => {
    onSave();
  };

  // 내보내기
  const handleExport = () => {
    if (!selectedTeam || Object.keys(playerRatings).length === 0) {
      alert('저장된 능력치가 없습니다');
      return;
    }

    // 팀 코멘트도 함께 내보내기
    const teamComment = getTeamComment(selectedTeam);

    // 선수 정보를 포함한 능력치 데이터 생성
    const enrichedPlayerRatings = {};
    Object.keys(playerRatings).forEach(playerId => {
      const ratings = playerRatings[playerId];
      const player = players.find(p => p.id === parseInt(playerId));

      if (player) {
        // 평균 능력치 계산
        const subPosition = ratings._subPosition || DEFAULT_SUB_POSITION[player.position];
        const averageRating = calculateWeightedAverage(ratings, subPosition);

        enrichedPlayerRatings[playerId] = {
          _name: player.name,
          _position: player.position,
          _averageRating: averageRating ? parseFloat(averageRating.toFixed(2)) : null,
          ...ratings
        };
      } else {
        // 선수 정보를 찾을 수 없는 경우 원본 그대로
        enrichedPlayerRatings[playerId] = ratings;
      }
    });

    const exportData = {
      team: selectedTeam,
      exportDate: new Date().toISOString(),
      version: '2.1', // 버전 업데이트
      teamComment: teamComment,
      playerRatings: enrichedPlayerRatings
    };

    const dataStr = JSON.stringify(exportData, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${selectedTeam}_ratings_${new Date().toISOString().split('T')[0]}.json`;
    link.click();
    URL.revokeObjectURL(url);

    setImportStatus('success');
    setImportMessage(`${selectedTeam} 능력치 및 팀 코멘트가 내보내졌습니다`);
    setTimeout(() => setImportStatus(null), 3000);
  };

  // 가져오기
  const handleImport = (event) => {
    const file = event.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const imported = JSON.parse(e.target.result);

        // 데이터 검증
        if (!imported.playerRatings) {
          throw new Error('유효하지 않은 파일 형식입니다');
        }

        // 선수 능력치 가져오기
        onImport(imported.playerRatings);

        // 팀 코멘트도 함께 가져오기 (v2.0+)
        if (imported.teamComment && imported.team) {
          localStorage.setItem(`team_comment_${imported.team}`, imported.teamComment);
        }

        setImportStatus('success');
        const hasComment = imported.teamComment ? ' 및 팀 코멘트' : '';
        setImportMessage(`${imported.team || ''} 능력치${hasComment}를 불러왔습니다`);
        setTimeout(() => setImportStatus(null), 3000);
      } catch (error) {
        console.error('Import error:', error);
        setImportStatus('error');
        setImportMessage('파일을 읽을 수 없습니다: ' + error.message);
        setTimeout(() => setImportStatus(null), 5000);
      }
    };
    reader.readAsText(file);

    // 파일 입력 초기화
    event.target.value = '';
  };

  return (
    <div className="relative">
      {!nested && (
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
      )}

      {/* Icon Buttons - Horizontal Layout */}
      <div className="relative flex gap-2">
        {/* Save */}
        <button
          onClick={handleSave}
          disabled={!selectedTeam}
          title="로컬 저장"
          className={`
            flex-1 p-3 rounded-sm transition-all border flex items-center justify-center
            ${selectedTeam
              ? 'bg-slate-900/60 text-cyan-300 border-cyan-500/30 hover:bg-slate-900/80 hover:border-cyan-500/50'
              : 'bg-slate-900/20 text-white/30 border-cyan-500/10 cursor-not-allowed'}
          `}
        >
          <Save className="w-4 h-4" />
        </button>

        {/* Export */}
        <button
          onClick={handleExport}
          disabled={!selectedTeam}
          title="내보내기"
          className={`
            flex-1 p-3 rounded-sm transition-all border flex items-center justify-center
            ${selectedTeam
              ? 'bg-slate-900/60 text-cyan-300 border-cyan-500/30 hover:bg-slate-900/80 hover:border-cyan-500/50'
              : 'bg-slate-900/20 text-white/30 border-cyan-500/10 cursor-not-allowed'}
          `}
        >
          <Download className="w-4 h-4" />
        </button>

        {/* Import */}
        <label
          title="가져오기"
          className={`
            flex-1 p-3 rounded-sm transition-all border flex items-center justify-center
            ${selectedTeam
              ? 'bg-slate-900/60 text-cyan-300 border-cyan-500/30 hover:bg-slate-900/80 hover:border-cyan-500/50 cursor-pointer'
              : 'bg-slate-900/20 text-white/30 border-cyan-500/10 cursor-not-allowed'}
          `}
        >
          <Upload className="w-4 h-4" />
          <input
            type="file"
            accept=".json"
            onChange={handleImport}
            disabled={!selectedTeam}
            className="hidden"
          />
        </label>
      </div>

      {/* Status Message */}
      {importStatus && (
        <div className={`
          relative mt-4 p-3 rounded-sm flex items-center gap-2 border-2 transition-all
          ${importStatus === 'success'
            ? 'bg-success/20 text-success border-success/40 shadow-glow'
            : 'bg-error/20 text-error border-error/40'}
        `}>
          {importStatus === 'success' ? (
            <CheckCircle className="w-5 h-5 flex-shrink-0" />
          ) : (
            <AlertCircle className="w-5 h-5 flex-shrink-0" />
          )}
          <span className="text-sm font-medium font-mono">{importMessage}</span>
        </div>
      )}

    </div>
  );
};

export default DataManager;
