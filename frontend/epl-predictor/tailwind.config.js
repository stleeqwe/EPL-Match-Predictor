/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      // 🎨 브랜드 컬러 시스템
      colors: {
        // 브랜드 기본 컬러
        brand: {
          primary: '#06B6D4',      // Cyan
          secondary: '#0891B2',    // Cyan Dark
          accent: '#22D3EE',       // Cyan Light
          dark: '#1e293b',         // Slate Dark
          darker: '#0f172a',       // Slate Darker
        },
        // 의미적 컬러
        success: {
          DEFAULT: '#10B981',
          light: '#34D399',
          dark: '#059669',
        },
        warning: {
          DEFAULT: '#F59E0B',
          light: '#FBBF24',
          dark: '#D97706',
        },
        error: {
          DEFAULT: '#EF4444',
          light: '#F87171',
          dark: '#DC2626',
        },
        info: {
          DEFAULT: '#3B82F6',
          light: '#60A5FA',
          dark: '#2563EB',
        },
        // EPL 특화 컬러
        epl: {
          ucl: '#00FF7F',         // Champions League
          uel: '#FF00FF',         // Europa League
          relegation: '#FF1493',  // Relegation
          clean: '#00FFFF',       // Clean sheets
        },
        // 포지션별 컬러
        position: {
          gk: '#FFD700',          // Gold - 골키퍼
          df: '#00FFFF',          // Cyan - 수비수
          mf: '#00FF7F',          // Spring Green - 미드필더
          fw: '#FF1493',          // Deep Pink - 공격수
        }
      },
      
      // 📝 타이포그래피
      fontFamily: {
        sans: ['Inter', 'Noto Sans KR', '-apple-system', 'BlinkMacSystemFont', 'sans-serif'],
        mono: ['SF Mono', 'Roboto Mono', 'Courier New', 'monospace'],
        orbitron: ['Orbitron', 'sans-serif'],
        grotesk: ['Space Grotesk', 'sans-serif'],
      },
      fontSize: {
        'hero': ['3.75rem', { lineHeight: '1', fontWeight: '900' }],      // 60px
        '4xl': ['2.25rem', { lineHeight: '2.5rem', fontWeight: '700' }],  // 36px
        '3xl': ['1.875rem', { lineHeight: '2.25rem', fontWeight: '700' }],// 30px
        '2xl': ['1.5rem', { lineHeight: '2rem', fontWeight: '700' }],     // 24px
        'xl': ['1.25rem', { lineHeight: '1.75rem', fontWeight: '600' }],  // 20px
        'lg': ['1.125rem', { lineHeight: '1.75rem', fontWeight: '500' }], // 18px
        'base': ['1rem', { lineHeight: '1.5rem', fontWeight: '400' }],    // 16px
        'sm': ['0.875rem', { lineHeight: '1.25rem', fontWeight: '400' }], // 14px
        'xs': ['0.75rem', { lineHeight: '1rem', fontWeight: '400' }],     // 12px
      },
      letterSpacing: {
        tighter: '-0.02em',
        tight: '-0.01em',
        normal: '0',
        wide: '0.01em',
        wider: '0.02em',
      },
      
      // 📏 간격 시스템
      spacing: {
        '18': '4.5rem',
        '88': '22rem',
        '128': '32rem',
      },
      
      // 🎭 애니메이션
      animation: {
        'fade-in': 'fadeIn 0.5s ease-in-out',
        'fade-in-up': 'fadeInUp 0.6s ease-out',
        'slide-up': 'slideUp 0.5s ease-in-out',
        'slide-down': 'slideDown 0.5s ease-in-out',
        'slide-left': 'slideLeft 0.5s ease-in-out',
        'slide-right': 'slideRight 0.5s ease-in-out',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'pulse-fast': 'pulse 1s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'bounce-slow': 'bounce 2s infinite',
        'spin-slow': 'spin 3s linear infinite',
        'scale': 'scale 0.3s ease-in-out',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        fadeInUp: {
          '0%': { 
            opacity: '0',
            transform: 'translateY(20px)',
          },
          '100%': { 
            opacity: '1',
            transform: 'translateY(0)',
          },
        },
        slideUp: {
          '0%': { transform: 'translateY(20px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        slideDown: {
          '0%': { transform: 'translateY(-20px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        slideLeft: {
          '0%': { transform: 'translateX(20px)', opacity: '0' },
          '100%': { transform: 'translateX(0)', opacity: '1' },
        },
        slideRight: {
          '0%': { transform: 'translateX(-20px)', opacity: '0' },
          '100%': { transform: 'translateX(0)', opacity: '1' },
        },
        scale: {
          '0%': { transform: 'scale(0.95)', opacity: '0' },
          '100%': { transform: 'scale(1)', opacity: '1' },
        },
      },
      
      // 🌈 그라데이션
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'gradient-conic': 'conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))',
        'gradient-primary': 'linear-gradient(135deg, #06B6D4 0%, #22D3EE 100%)',
        'gradient-success': 'linear-gradient(135deg, #10B981 0%, #22D3EE 100%)',
        'gradient-warning': 'linear-gradient(135deg, #F59E0B 0%, #FBBF24 100%)',
      },
      
      // 🎯 박스 그림자
      boxShadow: {
        'glow-sm': '0 0 10px rgba(6, 182, 212, 0.5)',
        'glow': '0 0 20px rgba(6, 182, 212, 0.6)',
        'glow-lg': '0 0 30px rgba(6, 182, 212, 0.7)',
        'neon': '0 0 5px theme("colors.brand.accent"), 0 0 20px theme("colors.brand.accent")',
      },
      
      // 🔲 테두리 반경
      borderRadius: {
        'xl': '1rem',
        '2xl': '1.5rem',
        '3xl': '2rem',
      },
      
      // 🎨 백드롭 필터
      backdropBlur: {
        xs: '2px',
      },
    },
  },
  plugins: [],
}
