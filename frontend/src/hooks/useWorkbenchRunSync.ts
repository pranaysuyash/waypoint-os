'use client';

/**
 * useWorkbenchRunSync - merge live Spine run state into the workbench store
 * and auto-navigate to the operator-relevant tab on terminal transitions.
 *
 * Contains three effects in their original declaration order (ordering is a
 * behavioral contract — see council decision
 * Docs/architecture/WORKBENCH_MODULARIZATION_COUNCIL_DECISION_2026-09-12.md,
 * slice T2.1):
 *   1. run state -> store merge (validation/packet/decision/frontier)
 *   2. draft status update + refetch on terminal states
 *   3. edge-detected tab auto-switch on blocked/failed/completed
 *
 * Closure map (semantic-preservation requirement):
 * - refs owned here: prevRunStateRef, prevCompletedRunFrontierRef
 *   (previously owned by WorkbenchContent; no other consumer existed)
 * - store actions via useWorkbenchStore(): setResultValidation,
 *   setResultPacket, setResultDecision, setResultFrontier, setDraftStatus,
 *   hydrateFromDraft; store.draft_id read per render
 * - no timers created or cleaned up here
 * - effect bodies and dependency arrays are verbatim from the origin
 */
import { useEffect, useRef } from 'react';
import type { RunStatusResponse } from '@/types/spine';
import { useWorkbenchStore } from '@/stores/workbench';
import { getDraft } from '@/lib/api-client';
import type { DecisionOutput } from '@/types/spine';

export function useWorkbenchRunSync({
  spineRunState,
  activeTab,
  handleTabChange,
}: {
  spineRunState: RunStatusResponse | null;
  activeTab: string;
  handleTabChange: (tab: string) => void;
}) {
  const store = useWorkbenchStore();
  const {
    setResultValidation,
    setResultPacket,
    setResultDecision,
    setResultFrontier,
    setDraftStatus,
    hydrateFromDraft,
  } = store;
  const runFrontier = spineRunState?.frontier_result;
  const prevRunStateRef = useRef<string | null>(null);
  const prevCompletedRunFrontierRef = useRef(false);

  // Populate store with validation/packet from run status so blocked runs
  // still show specific field-level errors in the UI.
  useEffect(() => {
    if (spineRunState?.validation) {
      setResultValidation(spineRunState.validation);
    }
    if (spineRunState?.packet) {
      setResultPacket(spineRunState.packet);
    }
    if (
      spineRunState?.decision_state ||
      spineRunState?.follow_up_questions ||
      spineRunState?.hard_blockers ||
      spineRunState?.soft_blockers
    ) {
      const normalizedFollowUps = Array.isArray(spineRunState.follow_up_questions)
        ? spineRunState.follow_up_questions.map((question) => {
            const record = question as Record<string, unknown>;
            return {
              field_name: typeof record.field_name === 'string' ? record.field_name : '',
              question: typeof record.question === 'string' ? record.question : '',
              priority: typeof record.priority === 'string' ? record.priority : 'medium',
              suggested_values: Array.isArray(record.suggested_values) ? record.suggested_values : [],
            };
          })
        : [];
      setResultDecision({
        decision_state: spineRunState.decision_state ?? 'ASK_FOLLOWUP',
        hard_blockers: spineRunState.hard_blockers ?? [],
        soft_blockers: spineRunState.soft_blockers ?? [],
        contradictions: [],
        risk_flags: [],
        follow_up_questions: normalizedFollowUps as DecisionOutput['follow_up_questions'],
        rationale: {
          hard_blockers: [],
          soft_blockers: [],
          contradictions: [],
          confidence: 0,
          confidence_scorecard: { data: 0, judgment: 0, commercial: 0 },
          feasibility: '',
        },
        confidence: {
          overall: NaN,
          data_quality: NaN,
          judgment_confidence: NaN,
          commercial_confidence: NaN,
        },
        branch_options: [],
        commercial_decision: 'NONE',
        budget_breakdown: null,
      });
    }
    setResultFrontier(spineRunState?.frontier_result ?? null);
  }, [
    spineRunState,
    setResultValidation,
    setResultPacket,
    setResultDecision,
    setResultFrontier,
  ]);

  // Update draft status based on run state, and refetch after terminal states
  // to pick up backend lifecycle changes (version bumps, status updates).
// react-doctor-disable-next-line react-doctor/no-cascading-set-state — multiple independent state slices updated
  useEffect(() => {
    if (!store.draft_id || !spineRunState?.state) return;
    const runState = spineRunState.state;
    if (runState === 'running' || runState === 'queued') {
      setDraftStatus('processing');
    } else if (runState === 'blocked') {
      setDraftStatus('blocked');
      // Refetch draft to get updated version from backend lifecycle
      getDraft(store.draft_id).then((draft) => hydrateFromDraft(draft)).catch(() => {});
    } else if (runState === 'failed') {
      setDraftStatus('failed');
      getDraft(store.draft_id).then((draft) => hydrateFromDraft(draft)).catch(() => {});
    } else if (runState === 'completed') {
      setDraftStatus('open');
      getDraft(store.draft_id).then((draft) => hydrateFromDraft(draft)).catch(() => {});
    }
  }, [spineRunState?.state, store.draft_id, setDraftStatus, hydrateFromDraft]);

  // Auto-switch to the tab containing errors when a run ends in blocked/failed state.
  // This prevents the user from missing field-level validation errors that are rendered
  // in the Trip Details (packet) tab or other stage-specific tabs.
  useEffect(() => {
    const currentState = spineRunState?.state ?? null;
    const prevState = prevRunStateRef.current;
    const completedWithRunFrontier = currentState === 'completed' && Boolean(runFrontier);
    const needsFollowUpReview =
      currentState === 'completed' &&
      (
        spineRunState?.decision_state === 'ASK_FOLLOWUP' ||
        (spineRunState?.hard_blockers?.length ?? 0) > 0 ||
        (spineRunState?.soft_blockers?.length ?? 0) > 0
      );

    // Navigate the most useful tab after terminal transitions.
    // Blocked/failed flows still land on Trip Details for immediate validation context.
    // Completed runs with follow-up blockers land on Risk Review first unless the operator is already on Trip Details.
    // Otherwise, completed runs with frontier output land on Frontier for immediate intelligence visibility.
    if (
      currentState !== prevState &&
      (currentState === 'blocked' || currentState === 'failed')
    ) {
      handleTabChange('packet');
    } else if (currentState !== prevState && needsFollowUpReview && activeTab !== 'packet') {
      handleTabChange('safety');
    } else if (
      currentState === 'completed' &&
      completedWithRunFrontier &&
      currentState !== prevState &&
      (!prevCompletedRunFrontierRef.current || prevState !== 'completed')
    ) {
      handleTabChange('frontier');
    }

    if (currentState !== 'completed') {
      prevCompletedRunFrontierRef.current = false;
    } else if (needsFollowUpReview) {
      prevCompletedRunFrontierRef.current = false;
    } else if (completedWithRunFrontier) {
      prevCompletedRunFrontierRef.current = true;
    }

    prevRunStateRef.current = currentState;
  }, [spineRunState, handleTabChange, runFrontier, activeTab]);
}
