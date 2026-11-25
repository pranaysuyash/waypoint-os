const { chromium } = require('playwright');
const { expect } = require('@playwright/test');
const fs = require('node:fs/promises');
const os = require('node:os');
const path = require('node:path');
const { installBlockedRailFixture } = require('../e2e/fixtures/blocked-rail.cjs');

const base = process.env.RESPONSIVE_AUDIT_BASE || 'http://127.0.0.1:3018';
const capture = process.env.RESPONSIVE_AUDIT_CAPTURE;

async function audit() {
  const scratch = await fs.mkdtemp(path.join(os.tmpdir(), 'waypoint-browser-zoom-'));
  let context;
  try {
    const extension = path.join(scratch, 'extension');
    await fs.mkdir(extension);
    await fs.writeFile(path.join(extension, 'manifest.json'), JSON.stringify({
      manifest_version: 3,
      name: 'Local browser zoom audit',
      version: '1.0',
      permissions: ['tabs'],
      background: { service_worker: 'worker.js' },
    }));
    await fs.writeFile(path.join(extension, 'worker.js'), 'chrome.runtime.onInstalled.addListener(() => {});');
    context = await chromium.launchPersistentContext(path.join(scratch, 'profile'), {
      channel: 'chromium', headless: true, viewport: null,
      args: ['--window-size=1280,960', '--disable-extensions-except=' + extension, '--load-extension=' + extension],
    });
    const worker = context.serviceWorkers()[0] || await context.waitForEvent('serviceworker');
    const page = context.pages()[0];
    const cdp = capture && await context.newCDPSession(page);
    await page.addInitScript(() => localStorage.setItem('waypoint:welcome-seen:v1', '1'));
    await page.goto(base + '/api/demo-session');
    const blocked = await installBlockedRailFixture(page);
    for (const [route, name, role, required] of [
      ['/overview', 'overview', 'link', 'Open oldest enquiry'],
      ['/inquiries/new?draft=new&tab=intake', 'workbench', 'button', 'Process inquiry'],
      [blocked.route, 'blocked-risk', 'tab', 'Trip Details'],
    ]) {
      await page.goto(base + route);
      if (name === 'blocked-risk') {
        await page.getByRole('button', { name: 'Process inquiry', exact: true }).click();
        await expect(page.getByText('Blocked', { exact: true }).first()).toBeVisible();
        await page.getByRole('tab', { name: 'Risk Review' }).click();
      }
      const action = page.getByRole(role, { name: required, exact: true }).first();
      await expect(action).toBeVisible();
      for (const zoom of [1, 2, 4]) {
        const reportedZoom = await worker.evaluate(async ({ origin, zoom }) => {
          const tabs = await chrome.tabs.query({});
          const tab = tabs.find(tab => tab.url?.startsWith(origin + '/'));
          if (tab?.id === undefined) throw new Error('Audit tab not found');
          await chrome.tabs.setZoom(tab.id, zoom);
          return chrome.tabs.getZoom(tab.id);
        }, { origin: new URL(base).origin, zoom });
        expect(reportedZoom).toBeCloseTo(zoom, 4);
        await expect.poll(() => page.evaluate(() => devicePixelRatio)).toBeCloseTo(zoom, 1);
        await expect(action).toBeVisible();
        await action.scrollIntoViewIfNeeded();
        await expect(action).toBeInViewport();
        if (name === 'blocked-risk') {
          await expect(page.getByRole('tab', { name: 'Risk Review' })).toHaveAttribute('aria-selected', 'true');
          const feasibility = page.getByRole('region', { name: 'Itinerary feasibility' });
          const prompt = feasibility.getByText(blocked.rail.packet.itinerary_feasibility_question, { exact: true });
          const questions = page.getByText('Additional intake questions', { exact: true }).locator('..').getByRole('listitem');
          await expect(questions).toHaveText(blocked.intakeQuestions.map(item => item.question));
          for (const item of [prompt, ...await questions.all()]) {
            await item.evaluate(el => el.scrollIntoView({ block: 'center', behavior: 'instant' }));
            const readable = await item.evaluate(el => {
              const item = el.getBoundingClientRect();
              const navigation = document.querySelector('[aria-label="Mobile bottom navigation"]');
              const bottom = navigation?.getBoundingClientRect().height
                ? navigation.getBoundingClientRect().top
                : innerHeight;
              return item.top >= 0 && item.bottom <= bottom + 1;
            });
            expect(readable, 'Full question must be readable above bottom navigation').toBe(true);
          }
        }
        const dimensions = await page.locator('#main-content').evaluate(main => ({
          viewport: innerWidth, window: outerWidth, dpr: devicePixelRatio,
          overflow: Math.max(main.scrollWidth - main.clientWidth, document.documentElement.scrollWidth - innerWidth),
        }));
        expect(dimensions.dpr).toBeCloseTo(zoom, 1);
        expect(dimensions.overflow, name + ' at ' + zoom * 100 + '% zoom').toBeLessThanOrEqual(2);
        console.log(JSON.stringify({ name, zoom, ...dimensions }));
        if (cdp) {
          await fs.mkdir(capture, { recursive: true });
          const screenshot = await cdp.send('Page.captureScreenshot', { format: 'png', captureBeyondViewport: false });
          await fs.writeFile(path.join(capture, name + '-zoom-' + zoom * 100 + '.png'), Buffer.from(screenshot.data, 'base64'));
        }
      }
      if (name === 'blocked-risk') {
        await action.click();
        await expect(action).toHaveAttribute('aria-selected', 'true');
      }
    }
  } finally {
    await context?.close();
    await fs.rm(scratch, { recursive: true });
  }
}

audit().catch(error => { console.error(error); process.exitCode = 1; });
