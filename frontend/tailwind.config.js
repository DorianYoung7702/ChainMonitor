/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // 主色调
        primary: {
          DEFAULT: '#3B82F6',
          hover: '#60A5FA',
          dark: '#1E40AF',
        },
        // 背景色系
        bg: {
          dark: '#0A0E1A',
          surface: '#111827',
          light: '#1F2937',
        },
        // 边框
        border: {
          DEFAULT: '#374151',
          light: '#4B5563',
        },
        // 文本色系
        text: {
          primary: '#F9FAFB',
          secondary: '#D1D5DB',
          tertiary: '#9CA3AF',
        },
        // 风险等级语义色
        risk: {
          0: '#10B981', // 正常 - 绿色
          1: '#F59E0B', // 注意 - 黄色
          2: '#F97316', // 警告 - 橙色
          3: '#EF4444', // 高危 - 红色
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'fade-in': 'fadeIn 0.5s ease-in-out',
        'slide-up': 'slideUp 0.3s ease-out',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
      },
    },
  },
  plugins: [],
}
