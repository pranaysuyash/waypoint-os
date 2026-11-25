import { expect, test } from '@playwright/test';
import path from 'node:path';

const demo = process.env.OVERVIEW_DEMO_URL;
const capture = process.env.COMMUNICATIONS_CAPTURE;
test.use({ channel: process.env.OVERVIEW_BROWSER_CHANNEL });

test('populated WhatsApp conversation retains controls and unsent reply through resize', async ({ page }) => {
  test.skip(!demo, 'Requires an isolated authenticated preview.');
  await page.addInitScript(() => localStorage.setItem('waypoint:welcome-seen:v1', '1'));
  await page.goto(new URL('/api/demo-session', demo).href);
  const session = await page.request.get(new URL('/api/auth/me', demo).href);
  expect(session.ok()).toBeTruthy();
  const { user } = await session.json();
  const conversationId = 'wa-responsive-fixture';
  const endpoint = '**/api/v1/messaging/whatsapp/' + conversationId;
  const reference = 'FixtureReference' + '1234567890'.repeat(12);
  const draft = 'I am checking the transfer for your group.';
  let owner: string | null = null;
  let feedUnavailable = false;
  await page.route(/\/api\/v1\/messages\?/, route => feedUnavailable
    ? route.fulfill({ status: 503 })
    : route.fulfill({ json: { messages: [{
      message_id: 'fixture-message', conversation_id: conversationId, channel: 'whatsapp',
      direction: 'inbound', from_party: '+15550100123', to_party: '+15550100999',
      body: reference, received_at: '2026-11-25T10:00:00Z', processing_state: 'processed',
    }] } }));
  await page.route(endpoint, route => route.fulfill({ json: {
    traveler: '+15550100123', staff_id: owner,
    replies: [{ id: 'fixture-reply', body: 'Thanks for your enquiry.', state: owner ? 'SUPPRESSED' : 'QUEUED' }],
  } }));
  await page.route(endpoint + '/ownership', route => {
    expect(route.request().postDataJSON()).toEqual({ action: 'takeover' });
    owner = user.id;
    return route.fulfill({ json: { staff_id: owner } });
  });
  await page.route(endpoint + '/replies**', route => route.abort('blockedbyclient'));
  await page.setViewportSize({ width: 320, height: 740 });
  await page.goto(new URL('/communications', demo).href);
  await page.getByRole('button', { name: /Open conversation with/ }).click();
  const conversation = page.getByRole('region', { name: 'WhatsApp conversation' });
  await expect(conversation.getByRole('button', { name: 'Approve and send draft' })).toBeVisible();
  await conversation.getByRole('button', { name: 'Take over replies' }).click();
  await expect(conversation.getByText('Suppressed by staff takeover')).toBeVisible();
  const reply = conversation.getByRole('textbox', { name: 'Staff reply' });
  await reply.fill(draft);
  if (capture) {
    await reply.scrollIntoViewIfNeeded();
    await page.screenshot({ path: path.join(capture, 'communications-320.png'), animations: 'disabled' });
  }
  for (const width of [320, 390, 639, 640, 767, 768, 854, 1024, 1440, 1920]) {
    await page.setViewportSize({ width, height: 740 });
    await expect(reply).toHaveValue(draft);
    await expect(conversation.getByRole('button', { name: 'Send staff reply' })).toBeEnabled();
    await expect(conversation.getByRole('list', { name: 'Recent conversation messages' }).getByText(reference, { exact: true })).toBeVisible();
    expect(await page.locator('#main-content').evaluate(el => el.scrollWidth - el.clientWidth)).toBeLessThanOrEqual(2);
  }
  feedUnavailable = true;
  await page.getByRole('button', { name: 'Refresh', exact: true }).click();
  await expect(page.getByText('Refresh failed. Showing the last loaded messages.')).toBeVisible();
  await expect(reply).toHaveValue(draft);
});
