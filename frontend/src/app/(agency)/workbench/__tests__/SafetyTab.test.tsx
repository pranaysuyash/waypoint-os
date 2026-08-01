import { describe, expect, it, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import type { ReactNode } from 'react';
import SafetyTab from '../SafetyTab';

// Mock the workbench store
const mockStore = {
  result_safety: null as unknown,
  result_traveler_bundle: {
    system_context: 'Session Goal: Prepare a clear options plan.',
    user_message: 'Here’s the options plan for Zanzibar.',
    follow_up_sequence: [],
    branch_prompts: [],
    internal_notes: '',
    constraints: [],
    audience: 'traveler',
  },
  result_internal_bundle: null,
  result_decision: null as unknown,
  debug_raw_json: false,
  setDebugRawJson: vi.fn(),
};

vi.mock('@/stores/workbench', () => ({
  useWorkbenchStore: () => mockStore,
}));

vi.mock('next/link', () => ({
  default: ({ children, href, ...props }: { children: ReactNode; href: string }) => (
    <a href={href} {...props}>
      {children}
    </a>
  ),
}));

// Mock CSS module
vi.mock('@/components/workbench/workbench.module.css', () => ({
  default: new Proxy(
    {},
    {
      get: (_: unknown, prop: string) => prop,
    },
  ),
}));

const SAFETY_RESULT = {
  leakage_passed: true,
  leakage_errors: [],
  strict_leakage: false,
};

const DECISION_WITH_SPECIALTY = {
  rationale: {
    frontier: {
      specialty_knowledge: [
        {
          niche: 'Medical Tourism & Post-Op Recovery',
          keywords: ['surgery'],
          checklists: ['Medical Records Transfer Protocol', 'Physician Fit-to-Fly Clearance'],
          compliance: ['HIPAA/GDPR Data Handling'],
          safety_notes: 'Verify proximity to emergency care.',
          urgency: 'HIGH',
        },
      ],
    },
  },
};

const DECISION_WITH_CRITICAL = {
  rationale: {
    frontier: {
      specialty_knowledge: [
        {
          niche: 'Human Remains Repatriation',
          keywords: ['repatriation'],
          checklists: ['Consular Clearance'],
          compliance: ['IATA TACT Rules'],
          safety_notes: 'High emotional sensitivity.',
          urgency: 'CRITICAL',
        },
      ],
    },
  },
};

const DECISION_WITH_EMPTY_SPECIALTY = {
  rationale: {
    frontier: {
      specialty_knowledge: [],
    },
  },
};

const DECISION_WITHOUT_FRONTIER = {
  rationale: {},
};

const DECISION_WITH_FOLLOWUP = {
  decision_state: 'ASK_FOLLOWUP',
  confidence: { overall: 0.72 },
  hard_blockers: ['resolved_destination'],
  soft_blockers: ['date_flexibility'],
  follow_up_questions: [
    {
      field_name: 'destination',
      question: 'Which island or region are you leaning toward?',
      priority: 'high',
    },
  ],
  rationale: {},
};

describe('SafetyTab - Special Handling Controls', () => {
  beforeEach(() => {
    mockStore.result_safety = null;
    mockStore.result_decision = null;
    mockStore.debug_raw_json = false;
    mockStore.setDebugRawJson = vi.fn();
  });

  it('renders Special Handling Controls when specialty_knowledge exists', () => {
    mockStore.result_safety = SAFETY_RESULT;
    mockStore.result_decision = DECISION_WITH_SPECIALTY;

    render(<SafetyTab />);

    expect(screen.getByText('Special Handling Controls')).toBeDefined();
    expect(screen.getByText('Medical Tourism & Post-Op Recovery')).toBeDefined();
    expect(screen.getByText('Medical Records Transfer Protocol')).toBeDefined();
    expect(screen.getByText('HIPAA/GDPR Data Handling')).toBeDefined();
    expect(screen.getByText('Verify proximity to emergency care.')).toBeDefined();
    expect(screen.getByText('HIGH')).toBeDefined();
  });

  it('hides Special Handling Controls when specialty_knowledge is empty', () => {
    mockStore.result_safety = SAFETY_RESULT;
    mockStore.result_decision = DECISION_WITH_EMPTY_SPECIALTY;

    render(<SafetyTab />);

    expect(screen.queryByText('Special Handling Controls')).toBeNull();
  });

  it('hides Special Handling Controls when no frontier in rationale', () => {
    mockStore.result_safety = SAFETY_RESULT;
    mockStore.result_decision = DECISION_WITHOUT_FRONTIER;

    render(<SafetyTab />);

    expect(screen.queryByText('Special Handling Controls')).toBeNull();
  });

  it('hides Special Handling Controls when no decision exists', () => {
    mockStore.result_safety = SAFETY_RESULT;
    mockStore.result_decision = null;

    render(<SafetyTab />);

    expect(screen.queryByText('Special Handling Controls')).toBeNull();
  });

  it('shows decision state even when safety bundle is absent', () => {
    mockStore.result_safety = null;
    mockStore.result_decision = DECISION_WITH_FOLLOWUP;

    render(<SafetyTab />);

    expect(screen.getByText('Trip readiness')).toBeDefined();
    expect(screen.getByText('Waiting on Customer')).toBeDefined();
    expect(screen.getByText('Confirm the final destination')).toBeDefined();
    expect(screen.getByText('Clarify how flexible the travel dates are')).toBeDefined();
    expect(screen.getByText('Which island or region are you leaning toward?')).toBeDefined();
    expect(screen.getByText('The message audit is not available for this run yet, so this view is showing the readiness summary instead.')).toBeDefined();
    expect(screen.getByText('Customer Message Preview')).toBeDefined();
    expect(screen.getByText('Here’s the options plan for Zanzibar.')).toBeDefined();
  });

  it('routes missing decision data to the trip repair surface when a trip exists', () => {
    render(
      <SafetyTab
        trip={{
          id: 'trip-safety-repair',
          destination: 'Bali',
          type: 'family leisure',
          state: 'green',
          age: '1h',
          createdAt: '2026-05-27T00:00:00Z',
          updatedAt: '2026-05-27T00:00:00Z',
          origin: 'Mumbai',
          budget: '₹4L',
          dateWindow: 'Jul 2026',
          party: 4,
        } as never}
      />
    );

    expect(screen.getByText(/No risk review data yet/i)).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Open Trip Details' })).toHaveAttribute(
      'href',
      '/trips/trip-safety-repair/intake',
    );
    expect(screen.queryByText(/New Inquiry/)).not.toBeInTheDocument();
  });

  it('renders CRITICAL urgency badge', () => {
    mockStore.result_safety = SAFETY_RESULT;
    mockStore.result_decision = DECISION_WITH_CRITICAL;

    render(<SafetyTab />);

    expect(screen.getByText('Human Remains Repatriation')).toBeDefined();
    expect(screen.getByText('CRITICAL')).toBeDefined();
  });

  it('renders compliance section', () => {
    mockStore.result_safety = SAFETY_RESULT;
    mockStore.result_decision = DECISION_WITH_SPECIALTY;

    render(<SafetyTab />);

    expect(screen.getByText('Compliance')).toBeDefined();
    expect(screen.getByText('HIPAA/GDPR Data Handling')).toBeDefined();
  });

  it('renders Risk Notes when present', () => {
    mockStore.result_safety = SAFETY_RESULT;
    mockStore.result_decision = DECISION_WITH_SPECIALTY;

    render(<SafetyTab />);

    expect(screen.getByText('Risk Notes')).toBeDefined();
    expect(screen.getByText('Verify proximity to emergency care.')).toBeDefined();
  });

  it('normalizes raw trip safety leaks when the store has not hydrated yet', () => {
    mockStore.result_safety = null;
    mockStore.result_decision = null;

    render(
      <SafetyTab
        trip={{
          id: 'trip-safety-raw',
          destination: 'Reykjavik',
          type: 'self drive',
          state: 'green',
          age: '1h',
          createdAt: '2026-05-27T00:00:00Z',
          updatedAt: '2026-05-27T00:00:00Z',
          origin: 'London',
          budget: '£4,000',
          dateWindow: 'Sep 2026',
          party: 2,
          safety: {
            leaks: ['internal_jargon'],
            traveler_bundle_leaks: ['MVB'],
            sanitized_view_leaks: [],
          } as never,
        } as never}
      />
    );

    expect(screen.getByText('What needs cleanup')).toBeDefined();
    expect(screen.getByText('2 internal-only references detected in the customer-facing reply.')).toBeDefined();
    expect(screen.getByText('Remove system labels, scores, and field names from the customer reply.')).toBeDefined();
    expect(screen.getByText('Keep operator notes and planning rationale in internal comments only.')).toBeDefined();
    expect(screen.queryByText('internal_jargon')).toBeNull();
    expect(screen.queryByText('MVB')).toBeNull();
  });
});
