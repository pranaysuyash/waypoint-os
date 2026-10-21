import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./vitest.setup.tsx'],
    include: ['**/__tests__/**/*.{test,spec}.{js,mjs,cjs,ts,mts,cts,jsx,tsx}'],
    exclude: ['node_modules', 'dist', '.next', '.next-dev', 'out', '.claude'],
    // Full-suite runs are heavy (React 19 + jsdom + async UI effects). A larger
    // timeout budget plus conservative worker fan-out reduces Vitest RPC stalls.
    testTimeout: 60000,
    hookTimeout: 30000,
    teardownTimeout: 30000,
    pool: 'forks',
    maxWorkers: 4,
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: [
        'node_modules/',
        'vitest.setup.ts',
        '**/__tests__/**',
        '**/*.config.{js,ts}',
        '**/types/**',
      ],
      // FND-0209 ratchet: floors pinned just under the 2026-09-16 baseline
      // (68.32 lines / 61.85 branch / 62.92 functions / 70.67 statements) so
      // coverage regressions fail CI while the suite is free to improve.
      // Raise these floors as coverage grows — never lower them.
      thresholds: {
        lines: 68,
        branches: 61,
        functions: 62,
        statements: 70,
      },
    },
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
});
