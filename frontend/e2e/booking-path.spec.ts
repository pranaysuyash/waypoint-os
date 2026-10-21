import { expect, test } from '@playwright/test';

/**
 * FND-0209 — first browser-level smoke of the canonical journey:
 *   signup → authenticated agency surface → intake entry point renders.
 *
 * This is a smoke, not a full booking run: the agentic intake→proposal leg is
 * long-running and provider-gated, so the smoke asserts the journey's front
 * half renders and acknowledges real input against the live local stack
 * (backend :8000, frontend :3005 per the Preview protocol).
 */

const uniqueSuffix = `${Date.now()}${Math.floor(Math.random() * 1000)}`;
// example.com passes the backend email validator (`.local` is rejected as a
// reserved TLD); each run creates a fresh additive test user.
const testEmail = `e2e-smoke-${uniqueSuffix}@example.com`;

test('signup lands in the agency workspace and the intake surface renders', async ({ page }) => {
  // 1. Public surface renders.
  await page.goto('/');
  await expect(page).toHaveTitle(/Waypoint/i);

  // 2. Signup → workspace.
  await page.goto('/signup');
  await page.getByLabel('Full name').fill('E2E Journey Smoke');
  await page.getByLabel('Email').fill(testEmail);
  await page.getByLabel('Password', { exact: true }).fill('e2e-smoke-password-8');
  await page.getByLabel('Confirm password').fill('e2e-smoke-password-8');
  // Agency name is optional (collapsed behind a toggle) — signup creates a
  // default agency, which is all the smoke needs.
  await page.getByRole('button', { name: /create workspace/i }).click();

  // Auth success lands on the protected default (workspace) — tolerate the
  // WelcomeCard onboarding overlay by asserting on document scope, not overlay.
  await expect(page).not.toHaveURL(/\/signup/, { timeout: 30_000 });

  // 3. Intake entry point renders and accepts a note (front half of the
  // booking path; the agentic run itself is provider-gated and long-running).
  await page.goto('/workbench?draft=new&tab=intake');
  const noteInput = page.locator('textarea').first();
  await expect(noteInput).toBeVisible({ timeout: 30_000 });
  await noteInput.fill(
    'Hi, planning a family trip — me and 2 friends want Japan in late March, ' +
      'budget around 3000 per person, 10 days.'
  );
});
