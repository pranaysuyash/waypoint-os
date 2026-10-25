/**
 * work-items-api — typed client for the classified incoming-work queue
 * (GET /api/v1/work-items + PATCH /api/v1/work-items/{id} lifecycle;
 * backend spine_api/routers/work_items.py, canonical classifier
 * spine_api/services/work_intake.py — INCOMING_WORK_CLASSIFICATION_MAP
 * 2026-10-24 §5 C1, lifecycle §14).
 */

import { api } from '@/lib/api-client';

export interface WorkItemEntry {
  item_id: string;
  received_at: string;
  door: string;
  origin: 'demand' | 'supply' | 'operator' | 'system' | 'world';
  intent: string;
  authority: string;
  urgency: 'high' | 'normal' | 'low';
  state: 'open' | 'claimed' | 'resolved' | 'dismissed';
  claimed_by: string | null;
  /** Operator-facing row title composed at read time (work_intake.display_for). */
  headline: string;
  /** Human context line: channel / bound-entity label / actor. */
  meta: string[];
  /** N identical entity-bound open items collapsed into this row (1 = uncollapsed). */
  group_count: number;
  channel: string | null;
  trip_id: string | null;
  run_id: string | null;
  draft_id: string | null;
  actor: string | null;
  identity_known: boolean;
  identity_key: string | null;
  returning_customer: boolean;
  memory_entity_id: string | null;
  memory_fact_count: number;
  duplicate_of: string | null;
  money_touch: boolean;
  pii_present: boolean;
  payload_summary: Record<string, unknown>;
}

export interface WorkItemQueueResponse {
  ok: boolean;
  items: WorkItemEntry[];
  total: number;
  actionable: number;
  duplicates_flagged: number;
  returning_customers: number;
  counts: {
    by_origin: Record<string, number>;
    by_intent: Record<string, number>;
    by_urgency: Record<string, number>;
    by_state: Record<string, number>;
  };
  count_basis: string;
}

export type WorkItemAction = 'claim' | 'unclaim' | 'dismiss' | 'resolve';

export async function getWorkItems(limit = 8, includeDone = false): Promise<WorkItemQueueResponse> {
  return api.get(`/api/v1/work-items?limit=${limit}&include_done=${includeDone}`);
}

export async function actOnWorkItem(
  itemId: string,
  action: WorkItemAction,
  note?: string
): Promise<{ ok: boolean; item_id: string; state: string }> {
  return api.patch(`/api/v1/work-items/${itemId}`, { action, note });
}
