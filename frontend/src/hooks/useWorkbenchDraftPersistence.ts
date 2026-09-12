'use client';

/**
 * useWorkbenchDraftPersistence - draft create/patch/save lifecycle for the
 * workbench (manual save, ensure-saved-before-run, and the 5s debounced
 * auto-save with optimistic concurrency).
 *
 * Extracted from PageClient.tsx (council decision
 * Docs/architecture/WORKBENCH_MODULARIZATION_COUNCIL_DECISION_2026-09-12.md,
 * slice T2.2). Callback/effect bodies and dependency arrays are verbatim
 * except the FND-0277 consolidation: the three persistence strategies now
 * share one buildDraftPayload + one isConflictError predicate. Their FLOW
 * SHAPES are deliberately NOT unified — the three URL-write mechanisms and
 * the ensureDraftSaved setTimeout(0) deferral are load-bearing.
 *
 * Closure map (semantic-preservation requirement):
 * - refs owned here: autoSaveTimerRef (5s debounce timer, cleaned up on
 *   effect teardown), prevContentRef (content dedupe key; intentionally NOT
 *   advanced on save failure so the same content stays retryable)
 * - timers: the auto-save 5000ms setTimeout; ensureDraftSaved's deliberate
 *   window.setTimeout(…, 0) deferral after draft creation is load-bearing
 *   and intentionally has no cleanup
 * - store actions: store.setSaveState / store.setDraftMeta (explicit calls),
 *   destructured setSaveState / setDraftMeta (auto-save path)
 * - URL writes: window.history.replaceState (ensureDraftSaved + auto-save,
 *   deliberately bypassing the router) vs router.replace (handleSaveDraft) —
 *   the three mechanisms must stay distinct
 * - injected UI setters: setSaveSuccess / setSaveError (handleSaveDraft only)
 * - documented dep-array deviations: setSaveSuccess/setSaveError and later
 *   added where used — all identity-stable, semantics unchanged
 */
import { useCallback, useEffect, useRef } from 'react';
import type { ReadonlyURLSearchParams } from 'next/navigation';
import type { SpineStage, OperatingMode } from '@/types/spine';
import type { WorkbenchStore, DraftStatus } from '@/stores/workbench';
import { createDraft, patchDraft } from '@/lib/api-client';
import { safeParseJson } from '@/app/(agency)/workbench/workbench-state';
import { useTransientTimers } from '@/hooks/useTransientTimers';

function buildDraftPayload(
  store: WorkbenchStore,
  spineStage: SpineStage,
  currentMode: OperatingMode,
  currentScenario: string,
) {
  return {
    customer_message: store.input_raw_note || null,
    agent_notes: store.input_owner_note || null,
    structured_json: safeParseJson(store.input_structured_json),
    itinerary_text: store.input_itinerary_text || null,
    stage: spineStage,
    operating_mode: currentMode,
    scenario_id: currentScenario || null,
    strict_leakage: store.strict_leakage,
  };
}

function isConflictError(err: unknown): boolean {
  return (
    !!err && typeof err === 'object' && 'status' in err && (err as { status: number }).status === 409
  );
}

export function useWorkbenchDraftPersistence({
  store,
  searchParams,
  replace,
  isSpineRunning,
  spineStage,
  currentMode,
  currentScenario,
  setSaveSuccess,
  setSaveError,
}: {
  store: WorkbenchStore;
  searchParams: ReadonlyURLSearchParams;
  replace: (href: string, options?: { scroll: boolean }) => void;
  isSpineRunning: boolean;
  spineStage: SpineStage;
  currentMode: OperatingMode;
  currentScenario: string;
  setSaveSuccess: (value: boolean) => void;
  setSaveError: (value: string | null) => void;
}) {
  const { setSaveState, setDraftMeta } = store;
  const { later } = useTransientTimers();

  const ensureDraftSaved = useCallback(async (): Promise<string | null> => {
    const hasContent =
      store.input_raw_note.trim() ||
      store.input_owner_note.trim() ||
      store.input_itinerary_text.trim() ||
      (store.input_structured_json.trim() ? safeParseJson(store.input_structured_json) !== null : false);

    if (!hasContent) return null;

    if (store.draft_id) {
      // Patch existing draft
      await patchDraft(store.draft_id, {
        ...buildDraftPayload(store, spineStage, currentMode, currentScenario),
        expected_version: store.draft_version,
        is_auto_save: false,
      });
      store.setSaveState('saved');
      return store.draft_id;
    }

    // Create new draft (create endpoint doesn't accept structured_json/itinerary_text)
    const payload = buildDraftPayload(store, spineStage, currentMode, currentScenario);
    const result = await createDraft({
      customer_message: payload.customer_message,
      agent_notes: payload.agent_notes,
      stage: payload.stage,
      operating_mode: payload.operating_mode,
      scenario_id: payload.scenario_id,
      strict_leakage: payload.strict_leakage,
    });
    // Defer hydration so the same submit turn can continue straight into the
    // Spine run. Immediate route/state churn here can pre-empt the first-submit
    // flow before the run request is issued in the browser.
    window.setTimeout(() => {
      store.setDraftMeta({
        draft_id: result.draft_id,
        name: result.name,
        status: result.status as DraftStatus,
        version: 1,
        created_at: result.created_at,
      });
      const params = new URLSearchParams(searchParams.toString());
      params.set('draft', result.draft_id);
      if (!params.get('tab')) params.set('tab', 'intake');
      window.history.replaceState(null, '', `?${params.toString()}`);
      store.setSaveState('saved');
    }, 0);
    return result.draft_id;
  }, [store, searchParams, spineStage, currentMode, currentScenario]);

  const handleSaveDraft = useCallback(async () => {
    const isAuto = false;
    if (store.save_state === 'saving') return;
    store.setSaveState('saving');

    try {
      const payload = buildDraftPayload(store, spineStage, currentMode, currentScenario);

      if (store.draft_id) {
        const updated = await patchDraft(store.draft_id, {
          ...payload,
          expected_version: store.draft_version,
          is_auto_save: isAuto,
        });
        store.setDraftMeta({
          draft_id: store.draft_id,
          name: (updated.name as string) || store.draft_name,
          status: (updated.status as DraftStatus) || 'open',
          version: (updated.version as number) || (store.draft_version ?? 0) + 1,
          created_at: updated.updated_at as string,
        });
      } else {
        const result = await createDraft({
          customer_message: payload.customer_message,
          agent_notes: payload.agent_notes,
          stage: payload.stage,
          operating_mode: payload.operating_mode,
          scenario_id: payload.scenario_id,
          strict_leakage: payload.strict_leakage,
        });
        store.setDraftMeta({
          draft_id: result.draft_id,
          name: result.name,
          status: result.status as DraftStatus,
          version: 1,
          created_at: result.created_at,
        });
        const params = new URLSearchParams(searchParams.toString());
        params.set('draft', result.draft_id);
        if (!params.get('tab')) params.set('tab', 'intake');
        replace(`?${params.toString()}`, { scroll: false });
      }

      store.setSaveState('saved');
      if (!isAuto) {
        setSaveSuccess(true);
        later(() => setSaveSuccess(false), 3000);
      }
    } catch (err) {
      const isConflict = isConflictError(err);
      if (isConflict) {
        store.setSaveState('conflict');
      } else {
        store.setSaveState('error');
      }
      if (!isAuto) {
        setSaveError(
          isConflict
            ? 'Save conflict - draft was modified elsewhere. Refresh and try again.'
            : 'Failed to save draft. Check connection and try again.',
        );
        later(() => setSaveError(null), 8000);
      }
    }
  }, [store, searchParams, replace, spineStage, currentMode, currentScenario, setSaveSuccess, setSaveError, later]);

  // ----- Auto-save (5s debounce, guarded) -----
  const autoSaveTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const prevContentRef = useRef<string>('');

  // Initialize prevContentRef after draft hydration so auto-save
  // doesn't immediately save loaded content as new.
  // FND-0279: stage/mode/scenario must come from the SAME derivation the
  // save payload uses (URL params), not from store copies — otherwise a
  // freshly hydrated draft with store.scenario_id = null diverges from the
  // arm key (null vs '') and spuriously autosaves ~5s after every load.
  useEffect(() => {
    if (store.draft_id && store.save_state === 'clean') {
      const contentKey = JSON.stringify({
        raw: store.input_raw_note,
        owner: store.input_owner_note,
        json: store.input_structured_json,
        itin: store.input_itinerary_text,
        stage: spineStage,
        mode: currentMode,
        scenario: currentScenario,
        strict: store.strict_leakage,
      });
      prevContentRef.current = contentKey;
    }
  }, [store.draft_id, store.save_state, store.input_raw_note, store.input_owner_note,
      store.input_structured_json, store.input_itinerary_text, store.strict_leakage,
      spineStage, currentMode, currentScenario]);

  const buildContentKey = useCallback(() => JSON.stringify({
    raw: store.input_raw_note,
    owner: store.input_owner_note,
    json: store.input_structured_json,
    itin: store.input_itinerary_text,
    stage: spineStage,
    mode: currentMode,
    scenario: currentScenario,
    strict: store.strict_leakage,
  }), [store.input_raw_note, store.input_owner_note, store.input_structured_json,
      store.input_itinerary_text, store.strict_leakage, spineStage, currentMode, currentScenario]);

  useEffect(() => {
    const hasContent =
      store.input_raw_note.trim() ||
      store.input_owner_note.trim() ||
      store.input_structured_json.trim() ||
      store.input_itinerary_text.trim();

    if (!hasContent) return;
    if (store.draft_status === 'processing' || store.draft_status === 'promoted') return;
    if (isSpineRunning) return;
    if (store.save_state === 'saving') return;

    const contentKey = buildContentKey();
    if (contentKey === prevContentRef.current) return;

    if (autoSaveTimerRef.current) clearTimeout(autoSaveTimerRef.current);

    autoSaveTimerRef.current = setTimeout(() => {
      (async () => {
        setSaveState('saving');
        try {
          const payload = buildDraftPayload(store, spineStage, currentMode, currentScenario);

          if (store.draft_id) {
            const updated = await patchDraft(store.draft_id, {
              ...payload,
              expected_version: store.draft_version,
              is_auto_save: true,
            });
            setDraftMeta({
              draft_id: store.draft_id,
              name: (updated.name as string) || store.draft_name,
              status: (updated.status as DraftStatus) || 'open',
              version: (updated.version as number) || (store.draft_version ?? 0) + 1,
              created_at: updated.updated_at as string,
            });
          } else {
            const result = await createDraft({
              customer_message: payload.customer_message,
              agent_notes: payload.agent_notes,
              stage: payload.stage,
              operating_mode: payload.operating_mode,
              scenario_id: payload.scenario_id,
              strict_leakage: payload.strict_leakage,
            });
            setDraftMeta({
              draft_id: result.draft_id,
              name: result.name,
              status: result.status as DraftStatus,
              version: 1,
              created_at: result.created_at,
            });
            const params = new URLSearchParams(searchParams.toString());
            params.set('draft', result.draft_id);
            if (!params.get('tab')) params.set('tab', 'intake');
            window.history.replaceState(null, '', `?${params.toString()}`);
          }
          // Mark as saved only after successful API call
          setSaveState('saved');
          prevContentRef.current = buildContentKey();
        } catch (err) {
          setSaveState(isConflictError(err) ? 'conflict' : 'error');
          // Do NOT update prevContentRef on failure - same content is retryable
        }
      })();
    }, 5000);

    return () => {
      if (autoSaveTimerRef.current) clearTimeout(autoSaveTimerRef.current);
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps -- dep list is a verbatim preservation contract; buildDraftPayload reads exactly the enumerated store fields (adding whole-`store` would widen re-arm semantics)
  }, [
    store.input_raw_note,
    store.input_owner_note,
    store.input_structured_json,
    store.input_itinerary_text,
    store.draft_id,
    store.draft_name,
    store.draft_status,
    store.draft_version,
    store.save_state,
    isSpineRunning,
    spineStage,
    currentMode,
    currentScenario,
    store.strict_leakage,
    searchParams,
    buildContentKey,
    setSaveState,
    setDraftMeta,
  ]);

  return { ensureDraftSaved, handleSaveDraft };
}
