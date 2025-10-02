import React from 'react';
import { motion } from 'framer-motion';

const ProbabilityBar = ({ label, value, color }) => {
  const safeValue = typeof value === 'string' ? parseFloat(value) : value;
  const displayValue = typeof safeValue === 'number' && !isNaN(safeValue) ? safeValue : 0;

  return (
    <div className="mb-4">
      <div className="flex justify-between mb-2">
        <span className="font-semibold text-sm md:text-base">{label}</span>
        <span className="font-bold text-sm md:text-base">{displayValue}%</span>
      </div>
      <div className="w-full h-8 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${displayValue}%` }}
          transition={{ duration: 1, ease: 'easeOut' }}
          className={`h-full ${color} flex items-center justify-end pr-3`}
        >
          <span className="text-white font-bold text-sm">{displayValue}%</span>
        </motion.div>
      </div>
    </div>
  );
};

export default ProbabilityBar;
