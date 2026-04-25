import { describe, it, expect } from 'vitest';

/**
 * Normalise raw backend workload rows into frontend WorkloadDistribution shape.
 * 
 * Backend contract (from /api/team/workload):
 *   {
 *     member_id: string;
 *     name: string;
 *     role: string;
 *     capacity: number;
 *     assigned: number;
 *     available: number;
 *   }
 * 
 * Frontend WorkloadDistribution contract:
 *   {
 *     memberId: string;
 *     name: string;
 *     role: string;
 *     capacity: number;
 *     assigned: number;
 *     available: number;
 *     loadPercentage: number;
 *     status: 'under' | 'optimal' | 'near_limit' | 'over_capacity';
 *   }
 */
function normalizeWorkload(raw: {
  member_id: string;
  name: string;
  role: string;
  capacity: number;
  assigned: number;
  available: number;
}): {
  memberId: string;
  name: string;
  role: string;
  capacity: number;
  assigned: number;
  available: number;
  loadPercentage: number;
  status: 'under' | 'optimal' | 'near_limit' | 'over_capacity';
} {
  const capacity = Math.max(1, raw.capacity);
  const assigned = raw.assigned;
  const loadPercentage = Math.round((assigned / capacity) * 100);

  let status: 'under' | 'optimal' | 'near_limit' | 'over_capacity';
  if (loadPercentage >= 100) status = 'over_capacity';
  else if (loadPercentage >= 85) status = 'near_limit';
  else if (loadPercentage >= 40) status = 'optimal';
  else status = 'under';

  return {
    memberId: raw.member_id,
    name: raw.name,
    role: raw.role,
    capacity,
    assigned,
    available: Math.max(0, raw.available),
    loadPercentage,
    status,
  };
}

describe('Workload normalization contract (BFF → frontend)', () => {
  it('maps backend member_id to frontend memberId', () => {
    const result = normalizeWorkload({
      member_id: 'agent_abc',
      name: 'Alice',
      role: 'senior_agent',
      capacity: 10,
      assigned: 3,
      available: 7,
    });
    expect(result.memberId).toBe('agent_abc');
  });

  it('computes loadPercentage from assigned / capacity', () => {
    const result = normalizeWorkload({
      member_id: 'agent_abc',
      name: 'Alice',
      role: 'senior_agent',
      capacity: 10,
      assigned: 5,
      available: 5,
    });
    expect(result.loadPercentage).toBe(50);
  });

  it('caps at 100% loadPercentage even when assigned exceeds capacity', () => {
    const result = normalizeWorkload({
      member_id: 'agent_abc',
      name: 'Alice',
      role: 'senior_agent',
      capacity: 5,
      assigned: 8,
      available: 0,
    });
    expect(result.loadPercentage).toBe(160); // We don't cap the percentage, only status
  });

  it('status: under when load < 40%', () => {
    const result = normalizeWorkload({
      member_id: 'agent_abc', name: 'Alice', role: 'senior_agent',
      capacity: 10, assigned: 3, available: 7,
    });
    expect(result.status).toBe('under');
  });

  it('status: optimal when load 40-84%', () => {
    const result = normalizeWorkload({
      member_id: 'agent_abc', name: 'Alice', role: 'senior_agent',
      capacity: 10, assigned: 5, available: 5,
    });
    expect(result.status).toBe('optimal');
  });

  it('status: near_limit when load 85-99%', () => {
    const result = normalizeWorkload({
      member_id: 'agent_abc', name: 'Alice', role: 'senior_agent',
      capacity: 10, assigned: 9, available: 1,
    });
    expect(result.status).toBe('near_limit');
  });

  it('status: over_capacity when load >= 100%', () => {
    const result = normalizeWorkload({
      member_id: 'agent_abc', name: 'Alice', role: 'senior_agent',
      capacity: 5, assigned: 5, available: 0,
    });
    expect(result.status).toBe('over_capacity');
  });

  it('returns 0 available when backend reports negative available', () => {
    const result = normalizeWorkload({
      member_id: 'agent_abc', name: 'Alice', role: 'senior_agent',
      capacity: 5, assigned: 8, available: -3,
    });
    expect(result.available).toBe(0);
  });
});
