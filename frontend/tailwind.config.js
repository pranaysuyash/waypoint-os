/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./src/**/*.{js,ts,jsx,tsx,mdx}'],
  theme: {
    extend: {
      colors: {
        // Backgrounds
        canvas:    'var(--bg-canvas)',
        surface:   'var(--bg-surface)',
        elevated:  'var(--bg-elevated)',
        highlight: 'var(--bg-highlight)',
        input:     'var(--bg-input)',
        sidebar:     '#0a0d11',
        'count-badge': 'var(--bg-count-badge)',
        'rationale':   'var(--bg-rationale)',

        // Text
        'text-primary':    'var(--text-primary)',
        'text-secondary':  'var(--text-secondary)',
        'text-tertiary':   'var(--text-tertiary)',
        'text-muted':      'var(--text-muted)',
        'text-accent':     'var(--text-accent)',
        'text-placeholder':'var(--text-placeholder)',
        'text-on-accent':  'var(--text-on-accent)',
        'text-rationale':  'var(--text-rationale)',

        // Accents
        'accent-blue':       'var(--accent-blue)',
        'accent-blue-hover': 'var(--accent-blue-hover)',
        'accent-cyan':   'var(--accent-cyan)',
        'accent-green':  'var(--accent-green)',
        'accent-amber':  'var(--accent-amber)',
        'accent-red':    'var(--accent-red)',
        'accent-purple': 'var(--accent-purple)',
        'accent-orange': 'var(--accent-orange)',

        // Borders
        'border-default': 'var(--border-default)',
        'border-hover':   'var(--border-hover)',
        'border-active':  'var(--border-active)',
      },

      fontFamily: {
        display: 'var(--font-display)',
        body:    'var(--font-body)',
        mono:    'var(--font-mono)',
        data:    'var(--font-data)',
      },

        fontSize: {
          'fluid-xs':  'var(--text-xs)',
          'fluid-sm':  'var(--text-sm)',
          'fluid-base':'var(--text-base)',
          'fluid-lg':  'var(--text-lg)',
          'fluid-xl':  'var(--text-xl)',
          'fluid-2xl': 'var(--text-2xl)',
          'fluid-3xl': 'var(--text-3xl)',
          'fluid-4xl': 'var(--text-4xl)',
          'fluid-5xl': 'var(--text-5xl)',
          'fluid-6xl': 'var(--text-6xl)',
          // Fixed rem scale for App UI (dashboard, workspace, operations)
          'ui-xs':  'var(--ui-text-xs)',
          'ui-2xs':  'var(--ui-text-2xs)',
          'ui-sm':  'var(--ui-text-sm)',
          'ui-base': 'var(--ui-text-base)',
          'ui-lg':  'var(--ui-text-lg)',
          'ui-xl':  'var(--ui-text-xl)',
          'ui-2xl': 'var(--ui-text-2xl)',
          'ui-3xl': 'var(--ui-text-3xl)',
          'ui-4xl': 'var(--ui-text-4xl)',
        },

      spacing: {
        'space-1':  'var(--space-1)',
        'space-2':  'var(--space-2)',
        'space-3':  'var(--space-3)',
        'space-4':  'var(--space-4)',
        'space-5':  'var(--space-5)',
        'space-6':  'var(--space-6)',
        'space-8':  'var(--space-8)',
        'space-10': 'var(--space-10)',
        'space-12': 'var(--space-12)',
        'space-xs':  'var(--space-xs)',
        'space-sm':  'var(--space-sm)',
        'space-md':  'var(--space-md)',
        'space-lg':  'var(--space-lg)',
        'space-xl':  'var(--space-xl)',
        'space-2xl': 'var(--space-2xl)',
      },

      transitionTimingFunction: {
        spring: 'cubic-bezier(0.175, 0.885, 0.32, 1.275)',
      },

      boxShadow: {
        'glow-blue':  '0 0 20px rgba(88, 166, 255, 0.15)',
        'glow-amber': '0 0 20px rgba(217, 164, 32, 0.2)',
        'glow-green': '0 0 20px rgba(63, 185, 80, 0.15)',
        'glow-cyan':  '0 0 20px rgba(57, 208, 216, 0.15)',
        'glow-red':   '0 0 20px rgba(248, 81, 73, 0.15)',
        premium:      '0 12px 48px -12px rgba(0, 0, 0, 0.5)',
        soft:         '0 8px 32px 0 rgba(0, 0, 0, 0.37)',
      },

      borderRadius: {
        premium: '24px',
      },

      animation: {
        'pulse-dot':       'pulse-dot 2s infinite',
        'route-pulse':     'route-pulse 2s ease-in-out infinite',
        'fade-in':         'fade-in 0.2s ease-out',
        'slide-in':        'slide-in-left 0.2s ease-out',
        float:             'float 3s ease-in-out infinite',
        'agent-breathing': 'agent-breathing 4s infinite ease-in-out',
      },
    },
  },
  plugins: [],
};
