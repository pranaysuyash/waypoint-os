// @vitest-environment jsdom

/**
 * FND-0280 regression: the run-sync effect synthesized FOUR NaN literals into
 * DecisionOutput.confidence when a run returned decision fields without a
 * confidence payload. NaN is JSON-unsafe — JSON.stringify coerces it to null
 * downstream (poisoning persisted comparisons) while in-memory it lies as a
 * number. The fix synthesizes explicit nulls ("not measured"); this test pins
 * the JSON-safety contract so the NaN synthesis cannot return.
 */

import { describe, expect, it, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { useWorkbenchRunSync } from '../useWorkbenchRunSync';
import { useWorkbenchStore } from '@/stores/workbench';
import type { RunStatusResponse } from '@/types/spine';

vi.mock('@/lib/api-client', () => ({
  getDraft: vi.fn().mockResolvedValue({}),
}));

const fakeTabChange = vi.fn();

function renderSync(spineRunState: RunStatusResponse | null) {
  return renderHook(() =>
    useWorkbenchRunSync({
      spineRunState,
      activeTab: 'intake',
      handleTabChange: fakeTabChange,
    })
  );
}

function decisionWithoutConfidence(): RunStatusResponse {
  // Minimal blocked-run state: decision fields present, confidence payload
  // absent — exactly the branch that used to synthesize NaN.
  return {
    run_id: 'run_fnd0280',
    state: 'blocked',
    decision_state: 'ASK_FOLLOWUP',
    follow_up_questions: [
      { field_name: 'destination', question: 'Where to?', priority: 'high', suggested_values: [] },
    ],
    hard_blockers: [],
    soft_blockers: [],
  } as unknown as RunStatusResponse;
}

describe('useWorkbenchRunSync confidence synthesis (FND-0280)', () => {
  beforeEach(() => {
    useWorkbenchStore.setState({
      result_decision: null,
      result_validation: null,
      result_packet: null,
      result_frontier: null,
      draft_id: null,
    });
  });

  it('synthesizes explicit NULL confidences (never NaN) when the run lacks a confidence payload', async () => {
    renderSync(decisionWithoutConfidence());

    await waitFor(() =>
      expect(useWorkbenchStore.getState().result_decision).not.toBeNull()
    );
    const confidence = useWorkbenchStore.getState().result_decision?.confidence;
    expect(confidence).toBeDefined();
    expect(confidence?.overall).toBeNull();
    expect(confidence?.data_quality).toBeNull();
    expect(confidence?.judgment_confidence).toBeNull();
    expect(confidence?.commercial_confidence).toBeNull();
  });

  it('is JSON-safe: stringify round-trips the synthesized confidences without coercion', async () => {
    renderSync(decisionWithoutConfidence());

    await waitFor(() =>
      expect(useWorkbenchStore.getState().result_decision).not.toBeNull()
    );
    const serialized = JSON.stringify(
      useWorkbenchStore.getState().result_decision?.confidence
    );
    const round = JSON.parse(serialized) as Record<string, unknown>;
    // JSON.stringify(NaN) === "null" was the defect: the explicit nulls must
    // survive serialization IDENTICALLY (keys present, values null).
    expect(round).toEqual({
      overall: null,
      data_quality: null,
      judgment_confidence: null,
      commercial_confidence: null,
    });
  });

  // NOTE: there is deliberately no "preserves real confidence numbers" test —
  // RunStatusResponse carries NO confidence field in the backend contract, so
  // unconditional null synthesis is correct here. Real confidences flow into
  // DecisionOutput through the BFF trip adapter (decision.confidence ?? nulls).
});
