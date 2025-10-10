import React from 'react';
import { motion } from 'framer-motion';
import { 
  AlertCircle, 
  WifiOff, 
  Database, 
  FileQuestion, 
  RefreshCw,
  Home,
  ArrowLeft
} from 'lucide-react';

/**
 * ErrorState Component
 * 다양한 에러 상황을 위한 일관된 UI
 */
const ErrorState = ({
  type = 'general',
  title,
  message,
  onRetry,
  onBack,
  onHome,
  customIcon,
  className = ''
}) => {
  // 에러 타입별 설정
  const errorTypes = {
    general: {
      icon: AlertCircle,
      defaultTitle: '오류가 발생했습니다',
      defaultMessage: '일시적인 문제가 발생했습니다. 잠시 후 다시 시도해주세요.',
      color: 'text-error',
      bgColor: 'bg-error/20'
    },
    network: {
      icon: WifiOff,
      defaultTitle: '네트워크 연결 오류',
      defaultMessage: '인터넷 연결을 확인하고 다시 시도해주세요.',
      color: 'text-warning',
      bgColor: 'bg-warning/20'
    },
    server: {
      icon: Database,
      defaultTitle: '서버 연결 실패',
      defaultMessage: '서버에 연결할 수 없습니다. 잠시 후 다시 시도해주세요.',
      color: 'text-error',
      bgColor: 'bg-error/20'
    },
    notFound: {
      icon: FileQuestion,
      defaultTitle: '찾을 수 없습니다',
      defaultMessage: '요청하신 데이터를 찾을 수 없습니다.',
      color: 'text-info',
      bgColor: 'bg-info/20'
    },
    empty: {
      icon: FileQuestion,
      defaultTitle: '데이터가 없습니다',
      defaultMessage: '표시할 데이터가 없습니다.',
      color: 'text-white/60',
      bgColor: 'bg-white/10'
    }
  };

  const config = errorTypes[type] || errorTypes.general;
  const Icon = customIcon || config.icon;

  return (
    <motion.div
      className={`flex flex-col items-center justify-center p-8 md:p-12 text-center ${className}`}
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.3 }}
    >
      {/* Icon */}
      <motion.div
        className={`w-20 h-20 md:w-24 md:h-24 rounded-full ${config.bgColor} flex items-center justify-center mb-6`}
        initial={{ scale: 0, rotate: -180 }}
        animate={{ scale: 1, rotate: 0 }}
        transition={{ 
          type: 'spring', 
          stiffness: 200, 
          delay: 0.1 
        }}
      >
        <Icon className={`w-10 h-10 md:w-12 md:h-12 ${config.color}`} />
      </motion.div>

      {/* Title */}
      <motion.h3
        className="text-xl md:text-2xl font-bold text-white mb-3"
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
      >
        {title || config.defaultTitle}
      </motion.h3>

      {/* Message */}
      <motion.p
        className="text-sm md:text-base text-white/60 mb-8 max-w-md"
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
      >
        {message || config.defaultMessage}
      </motion.p>

      {/* Actions */}
      <motion.div
        className="flex flex-col sm:flex-row gap-3 w-full max-w-sm"
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
      >
        {onRetry && (
          <motion.button
            onClick={onRetry}
            className="btn btn-primary flex items-center justify-center gap-2"
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            <RefreshCw className="w-4 h-4" />
            다시 시도
          </motion.button>
        )}

        {onBack && (
          <motion.button
            onClick={onBack}
            className="btn btn-secondary flex items-center justify-center gap-2"
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            <ArrowLeft className="w-4 h-4" />
            뒤로 가기
          </motion.button>
        )}

        {onHome && (
          <motion.button
            onClick={onHome}
            className="btn btn-ghost flex items-center justify-center gap-2"
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            <Home className="w-4 h-4" />
            홈으로
          </motion.button>
        )}
      </motion.div>

      {/* Decorative animation */}
      <motion.div
        className="absolute inset-0 pointer-events-none overflow-hidden -z-10"
        initial={{ opacity: 0 }}
        animate={{ opacity: 0.3 }}
        transition={{ delay: 0.5 }}
      >
        {Array.from({ length: 3 }).map((_, i) => (
          <motion.div
            key={i}
            className={`absolute w-64 h-64 rounded-full ${config.bgColor} blur-3xl`}
            style={{
              left: `${Math.random() * 100}%`,
              top: `${Math.random() * 100}%`,
            }}
            animate={{
              x: [0, Math.random() * 100 - 50, 0],
              y: [0, Math.random() * 100 - 50, 0],
              scale: [1, 1.2, 1],
            }}
            transition={{
              duration: 10 + i * 2,
              repeat: Infinity,
              ease: 'easeInOut',
            }}
          />
        ))}
      </motion.div>
    </motion.div>
  );
};

/**
 * EmptyState Component
 * 데이터가 없을 때 사용
 */
export const EmptyState = ({ 
  icon = '📭',
  title = '데이터가 없습니다',
  message = '표시할 내용이 없습니다.',
  action,
  actionLabel = '새로고침',
  className = ''
}) => {
  return (
    <motion.div
      className={`flex flex-col items-center justify-center p-12 text-center ${className}`}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
    >
      {/* Icon/Emoji */}
      <motion.div
        className="text-6xl md:text-7xl mb-6"
        initial={{ scale: 0, rotate: -30 }}
        animate={{ scale: 1, rotate: 0 }}
        transition={{ 
          type: 'spring', 
          stiffness: 200,
          delay: 0.1 
        }}
      >
        {icon}
      </motion.div>

      {/* Title */}
      <motion.h3
        className="text-xl md:text-2xl font-bold text-white mb-3"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.2 }}
      >
        {title}
      </motion.h3>

      {/* Message */}
      <motion.p
        className="text-white/60 mb-6 max-w-md"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.3 }}
      >
        {message}
      </motion.p>

      {/* Action */}
      {action && (
        <motion.button
          onClick={action}
          className="btn btn-primary"
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
        >
          {actionLabel}
        </motion.button>
      )}
    </motion.div>
  );
};

export default ErrorState;
