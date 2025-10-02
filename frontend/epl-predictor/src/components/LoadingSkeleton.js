import React from 'react';
import { motion } from 'framer-motion';

const LoadingSkeleton = ({ darkMode }) => {
  const cardBg = darkMode ? 'bg-gray-800' : 'bg-white';

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className={`${cardBg} border rounded-xl p-8 shadow-lg`}
    >
      <div className="space-y-6">
        {/* Header skeleton */}
        <div className="flex items-center gap-3">
          <motion.div
            animate={{ opacity: [0.5, 1, 0.5] }}
            transition={{ duration: 1.5, repeat: Infinity }}
            className="w-8 h-8 bg-gray-300 dark:bg-gray-600 rounded-full"
          />
          <motion.div
            animate={{ opacity: [0.5, 1, 0.5] }}
            transition={{ duration: 1.5, repeat: Infinity, delay: 0.1 }}
            className="h-8 w-48 bg-gray-300 dark:bg-gray-600 rounded"
          />
        </div>

        {/* Score skeleton */}
        <div className="p-6 bg-gray-100 dark:bg-gray-700 rounded-xl">
          <motion.div
            animate={{ opacity: [0.5, 1, 0.5] }}
            transition={{ duration: 1.5, repeat: Infinity, delay: 0.2 }}
            className="h-4 w-24 bg-gray-300 dark:bg-gray-600 rounded mx-auto mb-4"
          />
          <div className="flex items-center justify-center gap-6">
            <motion.div
              animate={{ opacity: [0.5, 1, 0.5] }}
              transition={{ duration: 1.5, repeat: Infinity, delay: 0.3 }}
              className="h-16 w-16 bg-gray-300 dark:bg-gray-600 rounded"
            />
            <div className="text-4xl font-bold text-gray-400">-</div>
            <motion.div
              animate={{ opacity: [0.5, 1, 0.5] }}
              transition={{ duration: 1.5, repeat: Infinity, delay: 0.4 }}
              className="h-16 w-16 bg-gray-300 dark:bg-gray-600 rounded"
            />
          </div>
        </div>

        {/* Probability bars skeleton */}
        {[0, 1, 2].map((i) => (
          <div key={i} className="space-y-2">
            <motion.div
              animate={{ opacity: [0.5, 1, 0.5] }}
              transition={{ duration: 1.5, repeat: Infinity, delay: 0.5 + i * 0.1 }}
              className="h-4 w-32 bg-gray-300 dark:bg-gray-600 rounded"
            />
            <motion.div
              animate={{ opacity: [0.5, 1, 0.5] }}
              transition={{ duration: 1.5, repeat: Infinity, delay: 0.6 + i * 0.1 }}
              className="h-8 w-full bg-gray-300 dark:bg-gray-600 rounded-full"
            />
          </div>
        ))}
      </div>

      <div className="text-center mt-6 text-gray-500 dark:text-gray-400">
        예측 분석 중...
      </div>
    </motion.div>
  );
};

export default LoadingSkeleton;
