import { beforeEach, describe, expect, it, vi } from 'vitest';
import { useWorkbenchStore } from '../workbench';

function resetWorkbenchDebugState() {
  useWorkbenchStore.setState({ debug_raw_json: false });
}

describe('workbench privacy contract', () => {
  beforeEach(() => {
    vi.unstubAllEnvs();
    resetWorkbenchDebugState();
  });

  it('blocks debug_raw_json when secure debug mode is disabled', () => {
    vi.stubEnv('NEXT_PUBLIC_ALLOW_DEBUG_JSON', 'false');

    useWorkbenchStore.getState().setDebugRawJson(true);

    expect(useWorkbenchStore.getState().debug_raw_json).toBe(false);
  });

  it('allows debug_raw_json only in explicit secure mode', () => {
    vi.stubEnv('NEXT_PUBLIC_ALLOW_DEBUG_JSON', 'true');

    useWorkbenchStore.getState().setDebugRawJson(true);
    expect(useWorkbenchStore.getState().debug_raw_json).toBe(true);

    useWorkbenchStore.getState().setDebugRawJson(false);
    expect(useWorkbenchStore.getState().debug_raw_json).toBe(false);
  });
});

