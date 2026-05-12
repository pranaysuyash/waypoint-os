import { describe, expect, it } from 'vitest';
import {
  getTravelerPromptForPlanningDetail,
  getTravelerPromptForUnknownField,
} from '../traveler-prompts';

describe('traveler-prompts', () => {
  it('returns canonical prompts for unknown packet fields', () => {
    expect(getTravelerPromptForUnknownField('origin_city')).toBe(
      'Which city will the travelers depart from?',
    );
    expect(getTravelerPromptForUnknownField('budget_raw_text')).toBe(
      'What budget range should we plan within?',
    );
  });

  it('returns canonical prompts for intake planning details', () => {
    expect(getTravelerPromptForPlanningDetail('origin')).toBe(
      'Which city will the travelers depart from?',
    );
    expect(getTravelerPromptForPlanningDetail('priorities')).toContain('must-haves');
  });

  it('returns null for unsupported keys', () => {
    expect(getTravelerPromptForUnknownField('not_a_real_field')).toBeNull();
    expect(getTravelerPromptForPlanningDetail('not_a_real_detail')).toBeNull();
  });
});

