import React, { useState, useEffect } from 'react';
import { Moon, Sun, Menu, X } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const Header = ({ darkMode, setDarkMode }) => {
  const [isScrolled, setIsScrolled] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  // 스크롤 감지 - throttle 및 hysteresis 적용
  useEffect(() => {
    let ticking = false;
    let lastScrollY = 0;

    const handleScroll = () => {
      if (!ticking) {
        window.requestAnimationFrame(() => {
          const currentScrollY = window.scrollY;

          // Hysteresis: 올라갈 때와 내려갈 때 다른 임계값 사용
          if (currentScrollY > lastScrollY) {
            // 아래로 스크롤 중
            if (currentScrollY > 50) {
              setIsScrolled(true);
            }
          } else {
            // 위로 스크롤 중
            if (currentScrollY < 20) {
              setIsScrolled(false);
            }
          }

          lastScrollY = currentScrollY;
          ticking = false;
        });
        ticking = true;
      }
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <>
      {/* Header */}
      <motion.header
        className={`
          sticky top-0 z-50
          ${isScrolled
            ? 'py-3 backdrop-blur-xl bg-brand-darker/95 border-b border-white/10 shadow-glow-sm'
            : 'py-4 bg-transparent'
          }
        `}
        style={{
          transition: 'padding 0.3s ease, background-color 0.3s ease, backdrop-filter 0.3s ease, border-color 0.3s ease, box-shadow 0.3s ease',
          willChange: 'padding, background-color, backdrop-filter'
        }}
        initial={{ y: -100 }}
        animate={{ y: 0 }}
        transition={{ type: 'spring', stiffness: 100, damping: 20 }}
      >
        <div className="container-custom">
          <div className="flex items-center justify-between gap-4">
            {/* Left: Logo & Title */}
            <div className="flex items-center gap-3">
              {/* Logo */}
              <motion.img
                src="/visionary-ai-logo.png"
                alt="Visionary AI"
                className={`
                  flex-shrink-0 object-contain
                  ${isScrolled ? 'h-14 md:h-16' : 'h-16 md:h-20'}
                `}
                style={{
                  transition: 'height 0.3s ease',
                  willChange: 'height',
                  filter: 'drop-shadow(0 0 10px rgba(139, 92, 246, 0.3))'
                }}
                whileHover={{ scale: 1.05 }}
                transition={{ type: 'spring', stiffness: 300 }}
              />

              {/* Title */}
              <div>
                <h1
                  className={`
                    font-extrabold tracking-wider
                    ${isScrolled ? 'text-lg md:text-xl' : 'text-xl md:text-3xl'}
                  `}
                  style={{
                    fontFamily: "'Space Grotesk', sans-serif",
                    transition: 'font-size 0.3s ease',
                    willChange: 'font-size',
                    textShadow: '0 0 20px rgba(139, 92, 246, 0.3)'
                  }}
                >
                  <span className="bg-gradient-to-r from-purple-400 via-pink-300 to-purple-200 bg-clip-text text-transparent">
                    Visionary
                  </span>
                  {' '}
                  <span className="text-brand-accent font-black">AI</span>
                  {' '}
                  <span className="bg-gradient-to-r from-cyan-400 via-blue-300 to-cyan-200 bg-clip-text text-transparent">
                    Analytics
                  </span>
                </h1>
                <p
                  className={`
                    text-white/70 font-medium tracking-wide
                    ${isScrolled ? 'text-xs hidden md:block' : 'text-sm md:text-base mt-0.5'}
                  `}
                  style={{
                    transition: 'font-size 0.3s ease, margin-top 0.3s ease, opacity 0.3s ease',
                    willChange: 'font-size, margin-top, opacity'
                  }}
                >
                  Personal Analysis & <span className="text-brand-accent">AI</span> Simulation
                </p>
              </div>
            </div>

            {/* Right: Desktop Features & Actions */}
            <div className="hidden md:flex items-center gap-3">
              {/* AI Engine Indicator */}
              <motion.div
                className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-white/5 border border-white/10"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.2 }}
              >
                <span className="text-xs text-white/70">Powered by</span>
                <div className="flex items-center gap-1">
                  <span className="text-xs font-bold text-emerald-300">ChatGPT</span>
                  <span className="text-white/50">&</span>
                  <span className="text-xs font-bold text-orange-300">Claude</span>
                </div>
              </motion.div>

              {/* Dark Mode Toggle */}
              <motion.button
                onClick={() => setDarkMode(!darkMode)}
                className="btn-ghost p-2.5 rounded-lg hover:bg-white/10 transition-all"
                aria-label="다크모드 토글"
                whileHover={{ scale: 1.1, rotate: 15 }}
                whileTap={{ scale: 0.9 }}
              >
                <AnimatePresence mode="wait" initial={false}>
                  <motion.div
                    key={darkMode ? 'dark' : 'light'}
                    initial={{ y: -20, opacity: 0, rotate: -90 }}
                    animate={{ y: 0, opacity: 1, rotate: 0 }}
                    exit={{ y: 20, opacity: 0, rotate: 90 }}
                    transition={{ duration: 0.2 }}
                  >
                    {darkMode ? (
                      <Sun className="w-5 h-5 text-brand-accent" />
                    ) : (
                      <Moon className="w-5 h-5 text-brand-accent" />
                    )}
                  </motion.div>
                </AnimatePresence>
              </motion.button>
            </div>

            {/* Mobile: Menu Button */}
            <div className="flex md:hidden items-center gap-2">
              <motion.button
                onClick={() => setDarkMode(!darkMode)}
                className="btn-ghost p-2 rounded-lg"
                aria-label="다크모드 토글"
                whileTap={{ scale: 0.9 }}
              >
                {darkMode ? (
                  <Sun className="w-5 h-5 text-brand-accent" />
                ) : (
                  <Moon className="w-5 h-5 text-brand-accent" />
                )}
              </motion.button>

              <motion.button
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                className="btn-ghost p-2 rounded-lg"
                aria-label="메뉴"
                whileTap={{ scale: 0.9 }}
              >
                {mobileMenuOpen ? (
                  <X className="w-5 h-5 text-white" />
                ) : (
                  <Menu className="w-5 h-5 text-white" />
                )}
              </motion.button>
            </div>
          </div>
        </div>
      </motion.header>

      {/* Mobile Menu */}
      <AnimatePresence>
        {mobileMenuOpen && (
          <motion.div
            className="fixed inset-0 z-40 md:hidden"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            {/* Backdrop */}
            <motion.div
              className="absolute inset-0 bg-black/50 backdrop-blur-sm"
              onClick={() => setMobileMenuOpen(false)}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            />

            {/* Menu Content */}
            <motion.div
              className="absolute top-[72px] right-0 left-0 mx-4 card p-6"
              initial={{ opacity: 0, y: -20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ type: 'spring', stiffness: 300, damping: 30 }}
            >
              <div className="space-y-4">
                {/* AI Engine Indicator */}
                <div className="w-full px-4 py-3 rounded-lg bg-white/5 border border-white/10 flex flex-col items-center gap-2">
                  <span className="text-sm text-white/70">Powered by AI</span>
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-bold text-emerald-300">ChatGPT</span>
                    <span className="text-white/50">&</span>
                    <span className="text-sm font-bold text-orange-300">Claude</span>
                  </div>
                </div>

                {/* Divider */}
                <div className="border-t border-white/10"></div>

                {/* Additional Info */}
                <div className="text-center text-sm text-white/60">
                  <p>Visionary AI Analytics</p>
                  <p className="text-xs mt-1">Version 1.0</p>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
};

export default Header;
