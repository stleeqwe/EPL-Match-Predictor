import React from 'react';
import { motion } from 'framer-motion';

const TabButton = ({ id, label, icon, activeTab, setActiveTab }) => {
  const isActive = activeTab === id;

  const getThemeColors = () => {
    switch(id) {
      case 'statistical':
        return {
          active: 'bg-gradient-to-br from-blue-500 to-blue-600',
          ring: 'ring-blue-500/30',
          text: 'text-blue-600 dark:text-blue-400'
        };
      case 'personal':
        return {
          active: 'bg-gradient-to-br from-purple-500 to-purple-600',
          ring: 'ring-purple-500/30',
          text: 'text-purple-600 dark:text-purple-400'
        };
      case 'hybrid':
        return {
          active: 'bg-gradient-to-br from-green-500 to-green-600',
          ring: 'ring-green-500/30',
          text: 'text-green-600 dark:text-green-400'
        };
      default:
        return {
          active: 'bg-gradient-to-br from-blue-500 to-blue-600',
          ring: 'ring-blue-500/30',
          text: 'text-blue-600 dark:text-blue-400'
        };
    }
  };

  const getDescription = () => {
    switch(id) {
      case 'statistical':
        return '통계 기반 분석';
      case 'personal':
        return '선수 능력치 기반';
      case 'hybrid':
        return '통합 분석';
      default:
        return '';
    }
  };

  const colors = getThemeColors();

  return (
    <motion.button
      onClick={() => setActiveTab(id)}
      className={`
        relative min-w-[140px] px-6 py-4 rounded-xl font-semibold transition-all
        ${isActive
          ? `${colors.active} text-white shadow-xl ring-4 ${colors.ring}`
          : 'bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 border-2 border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
        }
      `}
      whileHover={{ scale: 1.03, y: -2 }}
      whileTap={{ scale: 0.98 }}
    >
      <div className="flex flex-col items-center gap-2">
        <span className="text-2xl">{icon}</span>
        <div>
          <div className="font-bold">{label}</div>
          <div className={`text-xs mt-1 ${isActive ? 'text-white/90' : 'text-gray-500 dark:text-gray-400'}`}>
            {getDescription()}
          </div>
        </div>
      </div>

      {isActive && (
        <motion.div
          layoutId="activeIndicator"
          className="absolute -bottom-1 left-1/2 w-12 h-1 bg-white rounded-full"
          style={{ transform: 'translateX(-50%)' }}
          transition={{ type: "spring", bounce: 0.25, duration: 0.5 }}
        />
      )}
    </motion.button>
  );
};

export default TabButton;
