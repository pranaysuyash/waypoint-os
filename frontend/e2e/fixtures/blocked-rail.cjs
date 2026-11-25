const rail = require('../../../Docs/evidence/workbench-rail-unslop-2026-11-24/fixture.json');

/** @param {import('@playwright/test').Page} page */
async function installBlockedRailFixture(page) {
  const intakeQuestions = [
    { field_name: 'origin_city', question: 'Which city will you be departing from?' },
    { field_name: 'date_window', question: 'When are you planning to travel? Are the dates fixed or flexible?' },
    { field_name: 'party_size', question: 'How many people will be traveling?' },
    { field_name: 'budget', question: "What's your approximate budget for this trip?" },
    { field_name: 'trip_purpose', question: "What's the main purpose of this trip? (leisure, business, pilgrimage, etc.)" },
  ];
  const draft = 'draft_rail_responsive';
  const run = 'run_rail_responsive';
  let blocked = false;
  await page.route('**/api/triage/message', route => route.fulfill({ json: {} }));
  await page.route('**/api/drafts/' + draft, route => route.fulfill({ json: {
    draft_id: draft, name: 'Overnight train and separately booked transfer',
    customer_message: rail.note + ' Correction from the traveler: ' + rail.update,
    version: blocked ? 2 : 1, status: blocked ? 'blocked' : 'open',
  } }));
  await page.route('**/api/spine/run', route => route.fulfill({ json: { run_id: run, state: 'queued' } }));
  await page.route('**/api/runs/' + run, route => {
    blocked = true;
    return route.fulfill({ json: {
      run_id: run, state: 'blocked', trip_id: null, stage: 'discovery',
      validation: { status: 'ESCALATED', gate: 'NB01', reasons: ['Structural validation failed'] },
      block_reason: 'Trip details are incomplete', packet: rail.packet,
      decision_state: 'STOP_NEEDS_REVIEW', follow_up_questions: intakeQuestions,
      hard_blockers: ['extraction_quality'], steps_completed: ['packet'], events: [],
    } });
  });
  return { rail, intakeQuestions, route: '/inquiries/new?draft=' + draft + '&tab=intake' };
}

module.exports = { installBlockedRailFixture };
