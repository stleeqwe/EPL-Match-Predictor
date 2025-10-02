import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Brain, Check, Loader } from 'lucide-react';

const STEPS = [
  { icon: '📊', label: '통계 데이터 수집', duration: 800 },
  { icon: '🧮', label: 'Dixon-Coles 계산', duration: 1200 },
  { icon: '🎯', label: 'XGBoost 모델 실행', duration: 1000 },
  { icon: '✨', label: '결과 생성', duration: 600 }
];

const ProgressStep = ({ icon, label, status, darkMode }) => (
  <motion.div
    initial={{ opacity: 0, x: -20 }}
    animate={{ opacity: 1, x: 0 }}
    className={`flex items-center gap-3 p-3 rounded-lg transition-all ${
      status === "complete"
        ? darkMode ? "bg-green-900/20" : "bg-green-50"
        : status === "active"
        ? darkMode ? "bg-blue-900/20" : "bg-blue-50"
        : darkMode ? "bg-gray-800/50" : "bg-gray-50"
    }`}
  >
    <span className="text-2xl">{icon}</span>
    <span
      className={`flex-1 font-medium ${
        status === "complete"
          ? "text-green-700 dark:text-green-300"
          : status === "active"
          ? "text-blue-700 dark:text-blue-300"
          : "text-gray-500 dark:text-gray-400"
      }`}
    >
      {label}
    </span>
    {status === "complete" && <Check className="w-5 h-5 text-green-500" />}
    {status === "active" && (
      <motion.div
        animate={{ rotate: 360 }}
        transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
      >
        <Loader className="w-5 h-5 text-blue-500" />
      </motion.div>
    )}
  </motion.div>
);

const PredictionLoadingState = ({ darkMode }) => {
  const [currentStep, setCurrentStep] = useState(0);

  useEffect(() => {
    if (currentStep < STEPS.length) {
      const timer = setTimeout(() => {
        setCurrentStep((prev) => prev + 1);
      }, STEPS[currentStep]?.duration || 1000);

      return () => clearTimeout(timer);
    }
  }, [currentStep]);

  const cardBg = darkMode ? 'bg-gray-800' : 'bg-white';
  const borderColor = darkMode ? 'border-gray-700' : 'border-gray-200';

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={`${cardBg} border ${borderColor} rounded-2xl p-8 shadow-xl`}
    >
      {/* 헤더 */}
      <div className="flex items-center gap-4 mb-6">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
          className="p-3 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl"
        >
          <Brain className="w-8 h-8 text-white" />
        </motion.div>
        <div>
          <h3 className={`text-xl font-bold ${darkMode ? 'text-white' : 'text-gray-900'}`}>
            AI 분석 중...
          </h3>
          <p className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>
            {currentStep < STEPS.length ? STEPS[currentStep].label : '완료 중...'}
          </p>
        </div>
      </div>

      {/* 진행 바 */}
      <div className="mb-6">
        <div className="flex justify-between mb-2">
          <span className={`text-sm font-medium ${darkMode ? 'text-gray-300' : 'text-gray-700'}`}>
            진행률
          </span>
          <span className={`text-sm font-bold ${darkMode ? 'text-blue-400' : 'text-blue-600'}`}>
            {Math.round((currentStep / STEPS.length) * 100)}%
          </span>
        </div>
        <div className={`h-3 rounded-full overflow-hidden ${darkMode ? 'bg-gray-700' : 'bg-gray-200'}`}>
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${(currentStep / STEPS.length) * 100}%` }}
            transition={{ duration: 0.5 }}
            className="h-full bg-gradient-to-r from-blue-500 to-purple-600"
          />
        </div>
      </div>

      {/* 진행 단계 */}
      <div className="space-y-3">
        {STEPS.map((step, index) => (
          <ProgressStep
            key={index}
            icon={step.icon}
            label={step.label}
            status={
              index < currentStep
                ? "complete"
                : index === currentStep
                ? "active"
                : "pending"
            }
            darkMode={darkMode}
          />
        ))}
      </div>

      {/* 스켈레톤 프리뷰 */}
      <div className="mt-8 space-y-4">
        <div className="flex items-center justify-center gap-8">
          <div className={`h-24 w-24 rounded-xl animate-pulse ${darkMode ? 'bg-gray-700' : 'bg-gray-200'}`} />
          <div className={`h-12 w-12 rounded-full animate-pulse ${darkMode ? 'bg-gray-700' : 'bg-gray-200'}`} />
          <div className={`h-24 w-24 rounded-xl animate-pulse ${darkMode ? 'bg-gray-700' : 'bg-gray-200'}`} />
        </div>
        <div className="space-y-2">
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className={`h-4 rounded animate-pulse ${darkMode ? 'bg-gray-700' : 'bg-gray-200'}`}
              style={{ width: `${100 - i * 15}%` }}
            />
          ))}
        </div>
      </div>
    </motion.div>
  );
};

export default PredictionLoadingState;
