import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { CheckCircle, XCircle, AlertCircle, Info, X } from 'lucide-react';

/**
 * Toast Component - Enhanced
 * 다양한 타입의 알림을 표시
 */
const Toast = ({ 
  id,
  message, 
  type = 'info', 
  duration = 3000, 
  onClose,
  action,
  actionLabel = '실행'
}) => {
  const [progress, setProgress] = useState(100);

  useEffect(() => {
    if (duration > 0) {
      // 프로그레스 바 애니메이션
      const interval = setInterval(() => {
        setProgress((prev) => {
          const next = prev - (100 / (duration / 50));
          return next <= 0 ? 0 : next;
        });
      }, 50);

      // 자동 닫기
      const timer = setTimeout(() => {
        onClose();
      }, duration);

      return () => {
        clearInterval(interval);
        clearTimeout(timer);
      };
    }
  }, [duration, onClose]);

  const config = {
    success: {
      icon: CheckCircle,
      gradient: 'from-success to-success/80',
      bg: 'bg-success/10',
      border: 'border-success/30',
      text: 'text-success',
      progressBg: 'bg-success'
    },
    error: {
      icon: XCircle,
      gradient: 'from-error to-error/80',
      bg: 'bg-error/10',
      border: 'border-error/30',
      text: 'text-error',
      progressBg: 'bg-error'
    },
    warning: {
      icon: AlertCircle,
      gradient: 'from-warning to-warning/80',
      bg: 'bg-warning/10',
      border: 'border-warning/30',
      text: 'text-warning',
      progressBg: 'bg-warning'
    },
    info: {
      icon: Info,
      gradient: 'from-info to-info/80',
      bg: 'bg-info/10',
      border: 'border-info/30',
      text: 'text-info',
      progressBg: 'bg-info'
    }
  };

  const { icon: Icon, gradient, bg, border, text, progressBg } = config[type];

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: -50, scale: 0.9, x: 100 }}
      animate={{ opacity: 1, y: 0, scale: 1, x: 0 }}
      exit={{ opacity: 0, x: 100, scale: 0.9 }}
      transition={{ 
        type: 'spring', 
        stiffness: 500, 
        damping: 30 
      }}
      className={`
        relative overflow-hidden backdrop-blur-lg rounded-sm shadow-glow
        border-2 ${border} ${bg}
        p-4 flex items-start gap-3 max-w-md min-w-[320px]
      `}
    >
      {/* Gradient Background */}
      <div className={`absolute inset-0 bg-gradient-to-r ${gradient} opacity-10`} />

      {/* Icon */}
      <motion.div
        className={`flex-shrink-0 ${text}`}
        initial={{ scale: 0, rotate: -180 }}
        animate={{ scale: 1, rotate: 0 }}
        transition={{ delay: 0.1, type: 'spring', stiffness: 300 }}
      >
        <Icon className="w-5 h-5" />
      </motion.div>

      {/* Content */}
      <div className="flex-1 relative z-10">
        <p className="text-sm font-medium text-white leading-relaxed">
          {message}
        </p>
        
        {/* Action Button */}
        {action && (
          <motion.button
            onClick={() => {
              action();
              onClose();
            }}
            className={`mt-2 text-xs font-semibold ${text} hover:underline`}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.2 }}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            {actionLabel} →
          </motion.button>
        )}
      </div>

      {/* Close Button */}
      <motion.button
        onClick={onClose}
        className="flex-shrink-0 text-white/60 hover:text-white hover:bg-white/10 rounded-sm p-1.5 transition-all relative z-10"
        whileHover={{ scale: 1.1, rotate: 90 }}
        whileTap={{ scale: 0.9 }}
      >
        <X className="w-4 h-4" />
      </motion.button>

      {/* Progress Bar */}
      {duration > 0 && (
        <motion.div
          className={`absolute bottom-0 left-0 h-1 ${progressBg}`}
          initial={{ width: '100%' }}
          animate={{ width: `${progress}%` }}
          transition={{ duration: 0.05, ease: 'linear' }}
        />
      )}
    </motion.div>
  );
};

/**
 * ToastContainer Component
 * Toast 메시지들을 관리하고 표시
 */
export const ToastContainer = ({ toasts, removeToast }) => {
  return (
    <div className="fixed top-20 right-4 z-50 space-y-3 max-h-screen overflow-hidden">
      <AnimatePresence mode="popLayout">
        {toasts.map((toast) => (
          <Toast
            key={toast.id}
            id={toast.id}
            message={toast.message}
            type={toast.type}
            duration={toast.duration}
            action={toast.action}
            actionLabel={toast.actionLabel}
            onClose={() => removeToast(toast.id)}
          />
        ))}
      </AnimatePresence>
    </div>
  );
};

/**
 * useToast Hook 강화
 */
export const createToast = {
  success: (message, options = {}) => ({
    message,
    type: 'success',
    duration: 3000,
    ...options
  }),
  error: (message, options = {}) => ({
    message,
    type: 'error',
    duration: 4000,
    ...options
  }),
  warning: (message, options = {}) => ({
    message,
    type: 'warning',
    duration: 3500,
    ...options
  }),
  info: (message, options = {}) => ({
    message,
    type: 'info',
    duration: 3000,
    ...options
  })
};

export default Toast;
