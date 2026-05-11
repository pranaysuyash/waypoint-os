import { describe, expect, it, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import SafetyTab from '../SafetyTab';

// Mock the workbench store
const mockStore = {
  result_safety: null as unknown,
  result_traveler_bundle: null,
  result_internal_bundle: null,
  result_decision: null as unknown,
  debug_raw_json: false,
  setDebugRawJson: vi.fn(),
};

vi.mock('@/stores/workbench', () => ({
  useWorkbenchStore: () => mockStore,
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
});
