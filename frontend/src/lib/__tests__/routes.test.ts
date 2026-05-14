import { describe, it, expect } from 'vitest';
import { getTripRoute, getPostRunTripRoute, type WorkspaceStage } from '../routes';

describe('getTripRoute', () => {
  it('generates correct URL for ops stage', () => {
    expect(getTripRoute('trip_abc', 'ops')).toBe('/trips/trip_abc/ops');
  });

  it('accepts ops as a valid WorkspaceStage type', () => {
    const stage: WorkspaceStage = 'ops';
    expect(getTripRoute('trip_xyz', stage)).toBe('/trips/trip_xyz/ops');
  });

  it('generates correct URLs for all stages including ops', () => {
    const stages: WorkspaceStage[] = [
      'intake', 'packet', 'decision', 'strategy',
      'output', 'safety', 'suitability', 'timeline', 'ops',
    ];
    for (const stage of stages) {
      expect(getTripRoute('t1', stage)).toBe(`/trips/t1/${stage}`);
    }
  });

  it('falls back to /trips for falsy tripId', () => {
    expect(getTripRoute(null, 'ops')).toBe('/trips');
    expect(getTripRoute(undefined, 'ops')).toBe('/trips');
  });
});

describe('getPostRunTripRoute', () => {
  it('routes proposal + BLOCKED to /packet', () => {
    expect(getPostRunTripRoute({ tripId: 't1', tripStage: 'proposal', validationStatus: 'BLOCKED' }))
      .toBe('/trips/t1/packet');
  });

  it('routes booking + ESCALATED to /packet', () => {
    expect(getPostRunTripRoute({ tripId: 't1', tripStage: 'booking', validationStatus: 'ESCALATED' }))
      .toBe('/trips/t1/packet');
  });

  it('routes proposal + valid (no status) to /ops', () => {
    expect(getPostRunTripRoute({ tripId: 't1', tripStage: 'proposal', validationStatus: null }))
      .toBe('/trips/t1/ops');
  });

  it('routes booking + valid to /ops', () => {
    expect(getPostRunTripRoute({ tripId: 't1', tripStage: 'booking' }))
      .toBe('/trips/t1/ops');
  });

  it('routes intake stage to /intake', () => {
    expect(getPostRunTripRoute({ tripId: 't1', tripStage: 'intake' }))
      .toBe('/trips/t1/intake');
  });

  it('falls back to /intake when stage is missing', () => {
    expect(getPostRunTripRoute({ tripId: 't1' }))
      .toBe('/trips/t1/intake');
  });
});
