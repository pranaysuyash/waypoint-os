import { defineConfig } from '@playwright/test';

/**
 * FND-0209: first browser-level journey lane. Reuses the local dev servers
 * when they are already running (Preview protocol: backend :8000, frontend
 * :3005); CI starts them explicitly.
 */
export default defineConfig({
  testDir: './e2e',
  timeout: 120_000,
  expect: { timeout: 15_000 },
  fullyParallel: false,
  workers: 1,
  reporter: [['list']],
  use: {
    baseURL: process.env.E2E_BASE_URL ?? 'http://localhost:3005',
    trace: 'retain-on-failure',
  },
});
