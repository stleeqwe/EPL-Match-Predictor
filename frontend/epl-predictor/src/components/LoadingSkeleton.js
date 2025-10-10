import React from 'react';
import { motion } from 'framer-motion';

/**
 * LoadingSkeleton Component
 * 다양한 레이아웃을 위한 스켈레톤 로더
 */
const LoadingSkeleton = ({ 
  type = 'card', 
  count = 1,
  className = '' 
}) => {
  // 스켈레톤 애니메이션 - 부드럽고 미묘하게
  const shimmer = {
    hidden: { opacity: 0.5 },
    visible: {
      opacity: 0.8,
      transition: {
        repeat: Infinity,
        repeatType: 'reverse',
        duration: 2.5,
        ease: 'easeInOut'
      }
    }
  };

  // 순차 등장 애니메이션 - 더 부드럽게
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.05
      }
    }
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 8 },
    visible: {
      opacity: 1,
      y: 0,
      transition: {
        duration: 0.4,
        ease: 'easeOut'
      }
    }
  };

  // Card Skeleton
  if (type === 'card') {
    return (
      <motion.div
        className={`space-y-4 ${className}`}
        variants={containerVariants}
        initial="hidden"
        animate="visible"
      >
        {Array.from({ length: count }).map((_, i) => (
          <motion.div
            key={i}
            className="card p-6"
            variants={itemVariants}
          >
            <div className="flex items-start justify-between gap-4 mb-4">
              {/* Avatar */}
              <motion.div
                className="w-16 h-16 rounded-sm bg-white/10"
                variants={shimmer}
                initial="hidden"
                animate="visible"
              />
              {/* Badge */}
              <motion.div
                className="w-16 h-6 rounded-sm bg-white/10"
                variants={shimmer}
                initial="hidden"
                animate="visible"
              />
            </div>

            {/* Title */}
            <motion.div
              className="h-6 bg-white/10 rounded w-3/4 mb-2"
              variants={shimmer}
              initial="hidden"
              animate="visible"
            />

            {/* Subtitle */}
            <motion.div
              className="h-4 bg-white/10 rounded w-1/2 mb-4"
              variants={shimmer}
              initial="hidden"
              animate="visible"
            />

            {/* Stats Grid */}
            <div className="grid grid-cols-2 gap-3">
              {[1, 2, 3, 4].map((j) => (
                <motion.div
                  key={j}
                  className="h-16 bg-white/10 rounded-sm"
                  variants={shimmer}
                  initial="hidden"
                  animate="visible"
                  transition={{ delay: j * 0.1 }}
                />
              ))}
            </div>
          </motion.div>
        ))}
      </motion.div>
    );
  }

  // Table Skeleton
  if (type === 'table') {
    return (
      <div className={`card overflow-hidden ${className}`}>
        {/* Header */}
        <div className="p-6 border-b border-white/10">
          <motion.div
            className="h-6 bg-white/10 rounded w-1/3"
            variants={shimmer}
            initial="hidden"
            animate="visible"
          />
        </div>

        {/* Table Rows */}
        <div className="divide-y divide-white/5">
          {Array.from({ length: count }).map((_, i) => (
            <motion.div
              key={i}
              className="p-4 flex items-center gap-4"
              variants={itemVariants}
              initial="hidden"
              animate="visible"
              transition={{ delay: i * 0.05 }}
            >
              <motion.div
                className="w-8 h-8 rounded bg-white/10"
                variants={shimmer}
                initial="hidden"
                animate="visible"
              />
              <motion.div
                className="flex-1 h-4 bg-white/10 rounded"
                variants={shimmer}
                initial="hidden"
                animate="visible"
              />
              <motion.div
                className="w-16 h-4 bg-white/10 rounded"
                variants={shimmer}
                initial="hidden"
                animate="visible"
              />
            </motion.div>
          ))}
        </div>
      </div>
    );
  }

  // List Skeleton
  if (type === 'list') {
    return (
      <motion.div
        className={`space-y-3 ${className}`}
        variants={containerVariants}
        initial="hidden"
        animate="visible"
      >
        {Array.from({ length: count }).map((_, i) => (
          <motion.div
            key={i}
            className="card-hover p-4 flex items-center gap-4"
            variants={itemVariants}
          >
            <motion.div
              className="w-12 h-12 rounded-sm bg-white/10"
              variants={shimmer}
              initial="hidden"
              animate="visible"
            />
            <div className="flex-1 space-y-2">
              <motion.div
                className="h-4 bg-white/10 rounded w-3/4"
                variants={shimmer}
                initial="hidden"
                animate="visible"
              />
              <motion.div
                className="h-3 bg-white/10 rounded w-1/2"
                variants={shimmer}
                initial="hidden"
                animate="visible"
              />
            </div>
            <motion.div
              className="w-16 h-8 bg-white/10 rounded"
              variants={shimmer}
              initial="hidden"
              animate="visible"
            />
          </motion.div>
        ))}
      </motion.div>
    );
  }

  // Text Skeleton
  if (type === 'text') {
    return (
      <motion.div
        className={`space-y-2 ${className}`}
        variants={containerVariants}
        initial="hidden"
        animate="visible"
      >
        {Array.from({ length: count }).map((_, i) => (
          <motion.div
            key={i}
            className="h-4 bg-white/10 rounded"
            style={{ width: `${Math.random() * 40 + 60}%` }}
            variants={shimmer}
            initial="hidden"
            animate="visible"
            transition={{ delay: i * 0.1 }}
          />
        ))}
      </motion.div>
    );
  }

  // Grid Skeleton (PlayerCard grid)
  if (type === 'grid') {
    return (
      <motion.div
        className={`grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 ${className}`}
        variants={containerVariants}
        initial="hidden"
        animate="visible"
      >
        {Array.from({ length: count }).map((_, i) => (
          <motion.div
            key={i}
            className="card p-6"
            variants={itemVariants}
          >
            {/* Header */}
            <div className="flex items-start justify-between mb-4">
              <div className="flex-1 space-y-2">
                <motion.div
                  className="h-6 bg-white/10 rounded w-3/4"
                  variants={shimmer}
                  initial="hidden"
                  animate="visible"
                />
                <motion.div
                  className="h-4 bg-white/10 rounded w-1/2"
                  variants={shimmer}
                  initial="hidden"
                  animate="visible"
                />
              </div>
              <motion.div
                className="w-16 h-16 rounded-sm bg-white/10"
                variants={shimmer}
                initial="hidden"
                animate="visible"
              />
            </div>

            {/* Stats */}
            <div className="grid grid-cols-2 gap-3 mb-4">
              {[1, 2, 3, 4].map((j) => (
                <motion.div
                  key={j}
                  className="h-12 bg-white/10 rounded-sm"
                  variants={shimmer}
                  initial="hidden"
                  animate="visible"
                  transition={{ delay: j * 0.05 }}
                />
              ))}
            </div>

            {/* Rating */}
            <motion.div
              className="h-16 bg-white/10 rounded-sm"
              variants={shimmer}
              initial="hidden"
              animate="visible"
            />
          </motion.div>
        ))}
      </motion.div>
    );
  }

  // Default: Simple bar
  return (
    <motion.div
      className={`h-4 bg-white/10 rounded ${className}`}
      variants={shimmer}
      initial="hidden"
      animate="visible"
    />
  );
};

export default LoadingSkeleton;
