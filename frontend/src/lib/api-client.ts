/**
 * Centralized API Client
 *
 * Handles all HTTP requests to backend APIs with consistent error handling,
 * retry logic, and type safety.
 */

import type { ReviewStatus } from "@/types/governance";
import type { ValidationReport, FeeCalculationResult, DecisionOutput, StrategyOutput, PromptBundle } from "@/types/spine";
import type { IntegrityIssuesResponse } from "@/types/spine";

// ============================================================================
// TYPES
// ============================================================================

export interface ApiError {
  message: string;
  status?: number;
  code?: string;
  details?: unknown[];
  error?: unknown;
  detail?: unknown;
}

export class ApiException extends Error {
  status: number;
  code?: string;
  details?: unknown[];

  constructor(message: string, status: number, code?: string, details?: unknown[]) {
    super(message);
    this.name = "ApiException";
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

export interface RequestOptions extends RequestInit {
  timeout?: number;
  retry?: number;
  retryDelay?: number;
}

// ============================================================================
// CONFIG
// ============================================================================

const DEFAULT_TIMEOUT = 30000; // 30 seconds
const DEFAULT_RETRY = 0;
const DEFAULT_RETRY_DELAY = 1000;
const AUTH_UNAUTHORIZED_EVENT = "waypoint:auth-unauthorized";
let lastUnauthorizedEventAt = 0;

function notifyUnauthorized(): void {
  if (typeof window === "undefined") return;
  const now = Date.now();
  // Prevent event storms when several protected queries fail at once.
  if (now - lastUnauthorizedEventAt < 1500) return;
  lastUnauthorizedEventAt = now;
  window.dispatchEvent(new CustomEvent(AUTH_UNAUTHORIZED_EVENT));
}

// ============================================================================
// AUTH - cookie-based (httpOnly), no localStorage token needed
// ============================================================================

// ============================================================================
// CLIENT
// ============================================================================

class ApiClient {
  private baseUrl: string;
  private defaultTimeout: number;
  private defaultRetry: number;
  private defaultRetryDelay: number;

  constructor(options?: {
    baseUrl?: string;
    timeout?: number;
    retry?: number;
    retryDelay?: number;
  }) {
    this.baseUrl = options?.baseUrl ?? "";
    this.defaultTimeout = options?.timeout ?? DEFAULT_TIMEOUT;
    this.defaultRetry = options?.retry ?? DEFAULT_RETRY;
    this.defaultRetryDelay = options?.retryDelay ?? DEFAULT_RETRY_DELAY;
  }

  private async request<T>(
    endpoint: string,
    options: RequestOptions = {}
  ): Promise<T> {
    const {
      timeout = this.defaultTimeout,
      retry = this.defaultRetry,
      retryDelay = this.defaultRetryDelay,
      ...fetchOptions
    } = options;

    const url = `${this.baseUrl}${endpoint}`;
    let lastError: Error | null = null;

    const requestAttempt = async (attempt: number): Promise<T> => {
      try {
        // Create abort controller for timeout
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), timeout);

        // Build headers - auth is cookie-based (httpOnly), no Authorization header needed
        const incomingHeaders = fetchOptions.headers as Record<string, string> | undefined;
        const headers: Record<string, string> = {
          "Content-Type": "application/json",
          ...(incomingHeaders || {}),
        };

        const response = await fetch(url, {
          ...fetchOptions,
          signal: controller.signal,
          headers,
          credentials: "include",   // ensures cookies travel even after subdomain splits / CDN
        });

        clearTimeout(timeoutId);

        // Handle non-OK responses
        if (!response.ok) {
          if (response.status === 401) {
            notifyUnauthorized();
          }
          let errorData: ApiError = { message: response.statusText };

          try {
            errorData = await response.json();
          } catch {
            // Use default error message if JSON parsing fails
          }

          const normalized = this.normalizeErrorPayload(errorData, response.statusText);

          throw new ApiException(
            normalized.message,
            response.status,
            normalized.code,
            normalized.details
          );
        }

        // Parse and return response
        return await response.json();
      } catch (error) {
        lastError = error as Error;

        // Don't retry on certain errors
        if (
          error instanceof ApiException &&
          (error.status === 401 || error.status === 403 || error.status === 404)
        ) {
          throw error;
        }

        if (attempt < retry) {
          // Exponential backoff before the next retry attempt.
          await new Promise((resolve) =>
            setTimeout(resolve, retryDelay * Math.pow(2, attempt))
          );
          return requestAttempt(attempt + 1);
        }

        throw error;
      }
    };

    return requestAttempt(0).catch((error) => {
      if (error instanceof Error) {
        throw error;
      }
      throw lastError || new Error("Request failed");
    });
  }

  private normalizeErrorPayload(
    payload: ApiError,
    fallbackMessage: string
  ): { message: string; code?: string; details?: unknown[] } {
    let message = payload.message || fallbackMessage;
    let details = payload.details;
    const code = payload.code;

    if (!message && typeof payload.error === "string") {
      message = payload.error;
    }

    if (payload.error && typeof payload.error === "object") {
      const errObj = payload.error as Record<string, unknown>;
      if (typeof errObj.message === "string") message = errObj.message;
      if (Array.isArray(errObj.failures)) details = errObj.failures;
    }

    if (payload.detail && typeof payload.detail === "string") {
      message = payload.detail;
    } else if (payload.detail && typeof payload.detail === "object") {
      const detailObj = payload.detail as Record<string, unknown>;
      if (typeof detailObj.message === "string") message = detailObj.message;
      if (Array.isArray(detailObj.failures)) details = detailObj.failures;
    }

    return {
      message: message || fallbackMessage || "Request failed",
      code,
      details,
    };
  }

  // HTTP methods
  async get<T>(endpoint: string, options?: RequestOptions): Promise<T> {
    return this.request<T>(endpoint, { ...options, method: "GET" });
  }

  async post<T>(endpoint: string, data?: unknown, options?: RequestOptions): Promise<T> {
    return this.request<T>(endpoint, {
      ...options,
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async put<T>(endpoint: string, data?: unknown, options?: RequestOptions): Promise<T> {
    return this.request<T>(endpoint, {
      ...options,
      method: "PUT",
      body: JSON.stringify(data),
    });
  }

  async patch<T>(endpoint: string, data?: unknown, options?: RequestOptions): Promise<T> {
    return this.request<T>(endpoint, {
      ...options,
      method: "PATCH",
      body: JSON.stringify(data),
    });
  }

  async delete<T>(endpoint: string, options?: RequestOptions): Promise<T> {
    return this.request<T>(endpoint, { ...options, method: "DELETE" });
  }
}

// ============================================================================
// API INSTANCE
// ============================================================================

// Export default instance - point to own server for SSR/API routes
export const api = new ApiClient({
  baseUrl: '',  // Empty = relative URLs hit this origin
  timeout: DEFAULT_TIMEOUT,
  retry: 2,
  retryDelay: DEFAULT_RETRY_DELAY,
});

export { AUTH_UNAUTHORIZED_EVENT };

// ============================================================================
// TRIPS API
// ============================================================================

export interface Trip {
  id: string;
  destination: string;
  type: string;
  state: "green" | "amber" | "red" | "blue";
  age: string;
  createdAt: string;
  updatedAt: string;
  // Additional fields for UI display
  party?: number;
  dateWindow?: string;
  action?: string;
  overdue?: boolean;
  origin?: string;
  budget?: string;
  status?: string;
  stage?: string;
  // Pipeline result fields (returned by mock API, not yet in real API)
  packet?: unknown;
  validation?: ValidationReport;
  decision?: DecisionOutput;
  strategy?: StrategyOutput;
  internal_bundle?: PromptBundle;
  traveler_bundle?: PromptBundle;
  safety?: unknown;
  fees?: FeeCalculationResult;
  frontier_result?: unknown;
  agentOperations?: AgentOperationsMetadata;
  rawInput?: unknown;
  // Input fields (returned by mock API)
  customerMessage?: string;
  agentNotes?: string;
  followUpDueDate?: string;
  partyComposition?: string;
  pacePreference?: string;
  dateYearConfidence?: string;
  leadSource?: string;
  activityProvenance?: string;
  tripPriorities?: string;
  dateFlexibility?: string;
  // Contact / customer profile
  contactName?: string;
  // Review metadata (Wave 8)
  review_status?: ReviewStatus;
  assignee?: string;
  previousAssignee?: string;
  reviewedBy?: string;
  reviewedAt?: string;
  reviewNotes?: string;
  // Customer Feedback (Wave 9)
  feedback?: {
    rating: number;
    notes: string;
    is_simulated?: boolean;
    simulated_at?: string;
  };
  // Analytics (Wave 10)
  analytics?: {
    marginPct?: number;
    qualityScore?: number;
    qualityBreakdown?: {
      completeness: number;
      feasibility: number;
      risk: number;
      profitability: number;
    };
    requiresReview?: boolean;
    reviewReason?: string;
    feedback_reopen?: boolean;
    recovery_status?: string;
    recovery_started_at?: string;
    recovery_deadline?: string;
    approvalRequiredForSend?: boolean;
    sendPolicyReason?: string;
    ownerReviewDeadline?: string;
    escalationSeverity?: "high" | "critical";
    revisionCount?: number;
    // Suitability acknowledgment - persisted server-side when operator acknowledges Tier 1 flags
    acknowledged_flags?: string[];
    suitability_acknowledged_at?: string;
  };
}

export interface AgentOperationsMetadata {
  documentReadinessChecklist?: Record<string, unknown>;
  documentRiskLevel?: string;
  mustConfirmDocuments?: unknown[];
  destinationIntelligenceSnapshot?: Record<string, unknown>;
  destinationRiskLevel?: string;
  destinationIntelligenceRecommendations?: unknown[];
  weatherPivotPacket?: Record<string, unknown>;
  weatherPivotRiskLevel?: string;
  constraintFeasibilityAssessment?: Record<string, unknown>;
  feasibilityStatus?: string;
  proposalReadinessAssessment?: Record<string, unknown>;
  proposalReadinessStatus?: string;
  bookingReadinessAssessment?: Record<string, unknown>;
  bookingReadinessStatus?: string;
  flightStatusSnapshot?: Record<string, unknown>;
  flightDisruptionRiskLevel?: string;
  ticketPriceWatchAlert?: Record<string, unknown>;
  quoteRevalidationRequired?: boolean;
  priceWatchRiskLevel?: string;
  safetyAlertPacket?: Record<string, unknown>;
  safetyRiskLevel?: string;
  gdsSchemaBridge?: Record<string, unknown>;
  pnrShadowCheck?: Record<string, unknown>;
  pnrShadowRiskLevel?: string;
  supplierIntelligenceSnapshot?: Record<string, unknown>;
  supplierRiskLevel?: string;
  canonicalTravelObjects?: unknown[];
  lastAgentAction?: string;
  lastAgentActionAt?: string;
}

export interface TripStats {
  active: number;
  pendingReview: number;
  readyToBook: number;
  needsAttention: number;
}

export interface PipelineStage {
  label: string;
  count: number;
}

export interface StartPlanningResponse {
  success: boolean;
  trip_id: string;
  assigned_to: string;
}

/**
 * Analytics pipeline stage - returned by /analytics/pipeline.
 * Contains runtime metrics, not configuration.
 */
export interface AnalyticsPipelineStage {
  stageId: string;
  tripCount: number;
  exitRate: number;
  avgTimeInStage: number;
}

export async function getTrips(params?: {
  state?: string;
  limit?: number;
  offset?: number;
  view?: string;
}): Promise<{ items: Trip[]; total: number }> {
  const searchParams = new URLSearchParams();
  if (params?.state) searchParams.set("state", params.state);
  if (params?.limit) searchParams.set("limit", params.limit.toString());
  if (params?.offset) searchParams.set("offset", params.offset.toString());
  if (params?.view) searchParams.set("view", params.view);

  const query = searchParams.toString();
  return api.get<{ items: Trip[]; total: number }>(`/api/trips${query ? `?${query}` : ""}`);
}

export async function getTrip(id: string): Promise<Trip> {
  return api.get<Trip>(`/api/trips/${id}`);
}

export async function getTripStats(): Promise<TripStats> {
  return api.get<TripStats>("/api/stats");
}

export async function getPipeline(): Promise<PipelineStage[]> {
  return api.get<PipelineStage[]>("/api/pipeline");
}

export async function updateTrip(id: string, data: Partial<Trip>): Promise<Trip> {
  return api.patch<Trip>(`/api/trips/${id}`, data);
}

export async function startPlanningTrip(
  id: string,
  agentId: string,
  agentName: string
): Promise<StartPlanningResponse> {
  const params = new URLSearchParams({
    agent_id: agentId,
    agent_name: agentName,
  });
  return api.post<StartPlanningResponse>(`/api/trips/${id}/assign?${params.toString()}`, {});
}

export async function getIntegrityIssues(): Promise<IntegrityIssuesResponse> {
  return api.get<IntegrityIssuesResponse>("/api/system/integrity/issues");
}

export interface CreateTripRequest {
  raw_note: string;
  owner_note?: string;
  follow_up_due_date?: string;
  party_composition?: string;
  pace_preference?: string;
  date_year_confidence?: string;
  lead_source?: string;
  activity_provenance?: string;
}

export async function createTrip(data: CreateTripRequest): Promise<Trip> {
  return api.post<Trip>("/api/trips", data);
}

// ============================================================================
// AGENCY SETTINGS API
// ============================================================================

export interface AgencySettingsResponse {
  agency_id: string;
  profile: {
    agency_name: string;
    sub_brand: string;
    plan_label: string;
    contact_email: string;
    contact_phone: string;
    logo_url: string;
    website: string;
  };
  operational: {
    target_margin_pct: number;
    default_currency: string;
    operating_hours: {
      start: string;
      end: string;
    };
    operating_days: string[];
    preferred_channels: string[];
    brand_tone: string;
  };
  autonomy: AgencyAutonomyResponse;
}

export interface AgencyAutonomyResponse {
  approval_gates: Record<string, "auto" | "review" | "block">;
  mode_overrides: Record<string, Record<string, string>>;
  auto_proceed_with_warnings: boolean;
  learn_from_overrides: boolean;
  auto_reprocess_on_edit: boolean;
  allow_explicit_reassess: boolean;
  auto_reprocess_stages: Record<string, boolean>;
  min_proceed_confidence: number;
  min_draft_confidence: number;
}

export interface UpdateAgencyOperationalRequest {
  agency_name?: string;
  sub_brand?: string;
  plan_label?: string;
  contact_email?: string;
  contact_phone?: string;
  logo_url?: string;
  website?: string;
  target_margin_pct?: number;
  default_currency?: string;
  operating_hours_start?: string;
  operating_hours_end?: string;
  operating_days?: string[];
  preferred_channels?: string[];
  brand_tone?: string;
}

export interface UpdateAgencyAutonomyRequest {
  approval_gates?: Record<string, "auto" | "review" | "block">;
  mode_overrides?: Record<string, Record<string, string>>;
  auto_proceed_with_warnings?: boolean;
  learn_from_overrides?: boolean;
  auto_reprocess_on_edit?: boolean;
  allow_explicit_reassess?: boolean;
  auto_reprocess_stages?: Record<string, boolean>;
}

export type AgencySettings = AgencySettingsResponse;
export type AgencyAutonomy = AgencyAutonomyResponse;
export type UpdateOperationalPayload = UpdateAgencyOperationalRequest;
export type UpdateAutonomyPayload = UpdateAgencyAutonomyRequest;

export async function getAgencySettings(): Promise<AgencySettingsResponse> {
  return api.get<AgencySettingsResponse>("/api/settings");
}

export async function updateAgencyOperational(
  request: UpdateAgencyOperationalRequest
): Promise<AgencySettingsResponse> {
  return api.post<AgencySettingsResponse>("/api/settings/operational", request);
}

export async function updateAgencyAutonomy(
  request: UpdateAgencyAutonomyRequest
): Promise<AgencyAutonomyResponse> {
  return api.post<AgencyAutonomyResponse>("/api/settings/autonomy", request);
}

// ============================================================================
// TRIP REVIEW API
// ============================================================================

export async function submitTripReviewAction(
  tripId: string,
  action: string,
  notes?: string,
  errorCategory?: string
): Promise<{ success: boolean; review: any }> {
  return api.post(`/api/trips/${tripId}/review/action`, { action, notes, error_category: errorCategory });
}

// ============================================================================
// OVERRIDE API (P1-02: Agent Feedback Loop)
// ============================================================================

export interface OverrideRequest {
  flag: string;
  decision_type?: string;
  action: "suppress" | "downgrade" | "acknowledge";
  new_severity?: string;
  overridden_by: string;
  reason: string;
  scope: "this_trip" | "pattern";
  original_severity?: string;
}

export interface OverrideResponse {
  ok: boolean;
  override_id: string;
  trip_id: string;
  flag: string;
  action: string;
  new_severity?: string;
  cache_invalidated: boolean;
  rule_graduated: boolean;
  pattern_learning_queued: boolean;
  warnings: string[];
  audit_event_id: string;
}

export async function submitOverride(
  tripId: string,
  request: OverrideRequest
): Promise<OverrideResponse> {
  return api.post<OverrideResponse>(`/api/trips/${tripId}/override`, request);
}

export async function getOverrides(tripId: string): Promise<{ ok: boolean; trip_id: string; overrides: any[]; total: number }> {
  return api.get(`/api/trips/${tripId}/overrides`);
}

export async function acknowledgeSuitabilityFlags(
  tripId: string,
  flagTypes: string[],
): Promise<{ success: boolean; trip_id: string; acknowledged_flags: string[] }> {
  return api.post(`/api/trips/${tripId}/suitability/acknowledge`, { acknowledged_flags: flagTypes });
}

export interface StageTransitionResponse {
  trip_id: string;
  old_stage: string;
  new_stage: string;
  changed: boolean;
  readiness?: Record<string, unknown> | null;
}

export async function transitionTripStage(
  tripId: string,
  targetStage: string,
  reason?: string,
  expectedCurrentStage?: string,
): Promise<StageTransitionResponse> {
  return api.patch(`/trips/${tripId}/stage`, {
    target_stage: targetStage,
    reason,
    expected_current_stage: expectedCurrentStage,
  });
}

export interface ExplicitReassessRequest {
  reason?: string;
  stage?: string;
  operating_mode?: string;
  strict_leakage?: boolean;
}

export interface ExplicitReassessResponse {
  ok: boolean;
  trip_id: string;
  run_id: string;
  state: string;
  trigger: string;
}

export async function reassessTrip(
  tripId: string,
  request: ExplicitReassessRequest = {},
): Promise<ExplicitReassessResponse> {
  return api.post<ExplicitReassessResponse>(`/api/trips/${tripId}/reassess`, request);
}

export async function getOverride(overrideId: string): Promise<{ ok: boolean; override: any }> {
  return api.get(`/api/overrides/${overrideId}`);
}

// ============================================================================
// SCENARIOS API (already exists, just re-exporting)
// ============================================================================

export interface ScenarioListItem {
  id: string;
  title: string;
  source?: "fixture" | "doc";
  description?: string;
}

export interface ScenarioDetail {
  id: string;
  input: {
    raw_note: string | null;
    owner_note: string | null;
    structured_json: Record<string, unknown> | null;
    itinerary_text: string | null;
    stage: string;
    mode: string;
  };
  expected: {
    allowed_decision_states: string[];
    required_packet_fields: string[];
    forbidden_traveler_terms: string[];
    leakage_expected: boolean;
    assertions: Array<{
      type: string;
      message: string;
      field?: string;
      value?: string;
    }>;
  };
}

export async function getScenarios(): Promise<ScenarioListItem[]> {
  const response = await api.get<ScenarioListItem[] | { items?: ScenarioListItem[] }>("/api/scenarios");
  if (Array.isArray(response)) {
    return response;
  }
  return response.items ?? [];
}

export async function getScenario(id: string): Promise<ScenarioDetail> {
  return api.get<ScenarioDetail>(`/api/scenarios/${id}`);
}

// ============================================================================
// DRAFTS API (Phase 1)
// ============================================================================

export interface DraftSummary {
  draft_id: string;
  name: string;
  status: string;
  stage: string;
  operating_mode: string;
  last_run_state: string | null;
  promoted_trip_id: string | null;
  created_at: string;
  updated_at: string;
  created_by: string;
}

export interface CreateDraftRequest {
  name?: string;
  customer_message?: string | null;
  agent_notes?: string | null;
  stage?: string;
  operating_mode?: string;
  scenario_id?: string | null;
  strict_leakage?: boolean;
}

export interface CreateDraftResponse {
  draft_id: string;
  name: string;
  status: string;
  created_at: string;
}

export interface UpdateDraftRequest {
  name?: string;
  customer_message?: string | null;
  agent_notes?: string | null;
  structured_json?: Record<string, unknown> | null;
  itinerary_text?: string | null;
  stage?: string;
  operating_mode?: string;
  scenario_id?: string | null;
  strict_leakage?: boolean;
  expected_version?: number | null;
  is_auto_save?: boolean;
}

export async function createDraft(data: CreateDraftRequest): Promise<CreateDraftResponse> {
  return api.post<CreateDraftResponse>('/api/drafts', data);
}

export async function getDraft(draftId: string): Promise<Record<string, unknown>> {
  return api.get<Record<string, unknown>>(`/api/drafts/${draftId}`);
}

export async function patchDraft(draftId: string, data: UpdateDraftRequest): Promise<Record<string, unknown>> {
  return api.put<Record<string, unknown>>(`/api/drafts/${draftId}`, data);
}

export async function listDrafts(params?: { status?: string; limit?: number }): Promise<{ items: DraftSummary[]; total: number }> {
  const searchParams = new URLSearchParams();
  if (params?.status) searchParams.set('status', params.status);
  if (params?.limit) searchParams.set('limit', params.limit.toString());
  const query = searchParams.toString();
  return api.get<{ items: DraftSummary[]; total: number }>(`/api/drafts${query ? `?${query}` : ''}`);
}

export async function discardDraft(draftId: string): Promise<{ ok: boolean; draft_id: string; status: string }> {
  return api.delete<{ ok: boolean; draft_id: string; status: string }>(`/api/drafts/${draftId}`);
}

export async function promoteDraft(draftId: string, tripId: string): Promise<{ ok: boolean; draft_id: string; trip_id: string; status: string }> {
  return api.post<{ ok: boolean; draft_id: string; trip_id: string; status: string }>(`/api/drafts/${draftId}/promote`, { trip_id: tripId });
}

// ---------------------------------------------------------------------------
// Booking Data - lazy-loaded, not part of Trip interface
// ---------------------------------------------------------------------------

export interface BookingTraveler {
  traveler_id: string;
  full_name: string;
  date_of_birth: string;
  passport_number?: string | null;
  passport_expiry?: string | null;
  nationality?: string | null;
  emergency_contact?: string | null;
}

export interface BookingPayer {
  name: string;
  email?: string | null;
  phone?: string | null;
}

export interface BookingData {
  travelers: BookingTraveler[];
  payer?: BookingPayer | null;
  special_requirements?: string | null;
  booking_notes?: string | null;
}

export interface BookingDataResponse {
  trip_id: string;
  booking_data: BookingData | null;
  updated_at: string | null;
  stage: string;
  readiness: Record<string, unknown>;
}

export async function getBookingData(tripId: string): Promise<BookingDataResponse> {
  return api.get<BookingDataResponse>(`/api/trips/${tripId}/booking-data`);
}

export async function updateBookingData(
  tripId: string,
  data: BookingData,
  reason?: string,
  expectedUpdatedAt?: string,
): Promise<BookingDataResponse> {
  return api.patch<BookingDataResponse>(`/api/trips/${tripId}/booking-data`, {
    booking_data: data,
    reason: reason || undefined,
    expected_updated_at: expectedUpdatedAt || undefined,
  });
}

// ---------------------------------------------------------------------------
// Booking Collection Link (Phase 4A) - agent + public endpoints
// ---------------------------------------------------------------------------

export interface CollectionLinkInfo {
  token_id: string;
  collection_url: string;
  expires_at: string;
  trip_id: string;
  status: string;
}

export interface CollectionLinkStatus {
  has_active_token: boolean;
  token_id: string | null;
  expires_at: string | null;
  status: string | null;
  has_pending_submission: boolean;
}

export interface PendingBookingDataResponse {
  trip_id: string;
  pending_booking_data: BookingData | null;
  booking_data_source: string | null;
}

export interface PublicCollectionContext {
  valid: boolean;
  reason?: string;
  already_submitted?: boolean;
  trip_summary?: {
    destination?: string;
    date_window?: string;
    traveler_count?: number | string;
    agency_name?: string;
  };
  expires_at?: string;
}

const SPINE_API_URL = process.env.NEXT_PUBLIC_SPINE_API_URL || '';

// Agent endpoints (proxied through BFF)
export async function generateCollectionLink(
  tripId: string,
  expiresInHours?: number,
): Promise<CollectionLinkInfo> {
  return api.post<CollectionLinkInfo>(`/api/trips/${tripId}/collection-link`, {
    expires_in_hours: expiresInHours,
  });
}

export async function getCollectionLink(tripId: string): Promise<CollectionLinkStatus> {
  return api.get<CollectionLinkStatus>(`/api/trips/${tripId}/collection-link`);
}

export async function revokeCollectionLink(tripId: string): Promise<{ ok: boolean }> {
  return api.delete<{ ok: boolean }>(`/api/trips/${tripId}/collection-link`);
}

export async function getPendingBookingData(tripId: string): Promise<PendingBookingDataResponse> {
  return api.get<PendingBookingDataResponse>(`/api/trips/${tripId}/pending-booking-data`);
}

export async function acceptPendingBookingData(
  tripId: string,
): Promise<BookingDataResponse> {
  return api.post<BookingDataResponse>(`/api/trips/${tripId}/pending-booking-data/accept`);
}

export async function rejectPendingBookingData(
  tripId: string,
  reason?: string,
): Promise<{ ok: boolean }> {
  return api.post<{ ok: boolean }>(`/api/trips/${tripId}/pending-booking-data/reject`, {
    reason: reason || undefined,
  });
}

// Public endpoints (direct to backend, no auth)
export async function getPublicCollectionForm(token: string): Promise<PublicCollectionContext> {
  const url = `${SPINE_API_URL}/api/public/booking-collection/${encodeURIComponent(token)}`;
  const res = await fetch(url, { credentials: 'omit' });
  if (!res.ok) throw new Error(`Failed to load collection form (${res.status})`);
  return res.json();
}

export async function submitPublicBookingData(
  token: string,
  data: BookingData,
): Promise<{ ok: boolean; message: string }> {
  const url = `${SPINE_API_URL}/api/public/booking-collection/${encodeURIComponent(token)}/submit`;
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'omit',
    body: JSON.stringify({ booking_data: data }),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Submission failed (${res.status})`);
  }
  return res.json();
}

// ============================================================================
// DOCUMENT UPLOAD (Phase 4B)
// ============================================================================

export interface BookingDocument {
  id: string;
  trip_id: string;
  traveler_id: string | null;
  uploaded_by_type: 'agent' | 'customer';
  document_type: string;
  filename_present: boolean;
  filename_ext: string;
  mime_type: string;
  size_bytes: number;
  status: 'pending_review' | 'accepted' | 'rejected' | 'deleted';
  scan_status: 'skipped' | 'clean' | 'suspicious' | 'failed';
  review_notes_present: boolean;
  created_at: string;
  updated_at: string;
  reviewed_at: string | null;
  reviewed_by: string | null;
}

export interface DocumentListResponse {
  trip_id: string;
  documents: BookingDocument[];
}

export interface CustomerDocumentResponse {
  id: string;
  status: string;
}

export interface DownloadUrlResponse {
  url: string;
  expires_in: number;
}

// Agent document endpoints (proxied through BFF)

export async function uploadDocument(
  tripId: string,
  file: File,
  documentType: string,
  travelerId?: string,
): Promise<BookingDocument> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('document_type', documentType);
  if (travelerId) formData.append('traveler_id', travelerId);

  const res = await fetch(`/api/trips/${tripId}/documents`, {
    method: 'POST',
    credentials: 'include',
    body: formData,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Upload failed (${res.status})`);
  }
  return res.json();
}

export async function getDocuments(tripId: string): Promise<DocumentListResponse> {
  return api.get<DocumentListResponse>(`/api/trips/${tripId}/documents`);
}

export async function getDocumentDownloadUrl(
  tripId: string,
  documentId: string,
): Promise<DownloadUrlResponse> {
  return api.get<DownloadUrlResponse>(
    `/api/trips/${tripId}/documents/${documentId}/download-url`,
  );
}

export async function acceptDocument(
  tripId: string,
  documentId: string,
  notesPresent?: boolean,
): Promise<BookingDocument> {
  return api.post<BookingDocument>(
    `/api/trips/${tripId}/documents/${documentId}/accept`,
    { notes_present: notesPresent },
  );
}

export async function rejectDocument(
  tripId: string,
  documentId: string,
  notesPresent?: boolean,
): Promise<BookingDocument> {
  return api.post<BookingDocument>(
    `/api/trips/${tripId}/documents/${documentId}/reject`,
    { notes_present: notesPresent },
  );
}

export async function deleteDocument(
  tripId: string,
  documentId: string,
): Promise<{ ok: boolean; status: string }> {
  return api.delete<{ ok: boolean; status: string }>(
    `/api/trips/${tripId}/documents/${documentId}`,
  );
}

// Phase 4C: Document extraction

export interface ExtractionFieldView {
  field_name: string;
  value: string | null;
  confidence: number;
  present: boolean;
}

export interface ExtractionResponse {
  id: string;
  document_id: string;
  status: 'pending_review' | 'applied' | 'rejected' | 'failed' | 'running';
  extracted_by: string;
  overall_confidence: number | null;
  field_count: number;
  fields: ExtractionFieldView[];
  created_at: string;
  updated_at: string;
  reviewed_at: string | null;
  reviewed_by: string | null;
  provider_name: string | null;
  model_name: string | null;
  latency_ms: number | null;
  prompt_tokens: number | null;
  completion_tokens: number | null;
  total_tokens: number | null;
  cost_estimate_usd: number | null;
  error_code: string | null;
  error_summary: string | null;
  confidence_method: string | null;
  attempt_count: number;
  run_count: number;
  current_attempt_id: string | null;
  page_count: number | null;
}

export interface AttemptSummary {
  attempt_id: string;
  run_number: number;
  attempt_number: number;
  fallback_rank: number | null;
  provider_name: string;
  model_name: string | null;
  latency_ms: number | null;
  status: 'success' | 'failed';
  error_code: string | null;
  created_at: string | null;
}

export interface ApplyConflict {
  field_name: string;
  existing_value: string;
  extracted_value: string;
}

export interface ApplyExtractionResponse {
  applied: boolean;
  conflicts: ApplyConflict[];
  extraction: ExtractionResponse | null;
}

export async function extractDocument(
  tripId: string,
  documentId: string,
): Promise<ExtractionResponse> {
  return api.post<ExtractionResponse>(
    `/api/trips/${tripId}/documents/${documentId}/extract`,
  );
}

export async function getExtraction(
  tripId: string,
  documentId: string,
): Promise<ExtractionResponse> {
  return api.get<ExtractionResponse>(
    `/api/trips/${tripId}/documents/${documentId}/extraction`,
  );
}

export async function applyExtraction(
  tripId: string,
  documentId: string,
  body: {
    traveler_id: string;
    fields_to_apply: string[];
    allow_overwrite?: boolean;
    create_traveler_if_missing?: boolean;
  },
): Promise<ApplyExtractionResponse> {
  return api.post<ApplyExtractionResponse>(
    `/api/trips/${tripId}/documents/${documentId}/extraction/apply`,
    body,
  );
}

export async function rejectExtraction(
  tripId: string,
  documentId: string,
): Promise<ExtractionResponse> {
  return api.post<ExtractionResponse>(
    `/api/trips/${tripId}/documents/${documentId}/extraction/reject`,
  );
}

export async function listExtractionAttempts(
  tripId: string,
  documentId: string,
): Promise<AttemptSummary[]> {
  return api.get<AttemptSummary[]>(
    `/api/trips/${tripId}/documents/${documentId}/extraction/attempts`,
  );
}

export async function retryExtraction(
  tripId: string,
  documentId: string,
): Promise<ExtractionResponse> {
  return api.post<ExtractionResponse>(
    `/api/trips/${tripId}/documents/${documentId}/extraction/retry`,
  );
}

// Public customer document upload (direct to backend, no auth)

export async function uploadPublicDocument(
  token: string,
  file: File,
  documentType: string,
): Promise<CustomerDocumentResponse> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('document_type', documentType);

  const url = `${SPINE_API_URL}/api/public/booking-collection/${encodeURIComponent(token)}/documents`;
  const res = await fetch(url, {
    method: 'POST',
    credentials: 'omit',
    body: formData,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Upload failed (${res.status})`);
  }
  return res.json();
}

// Phase 5A: Booking tasks

export interface BookingTask {
  id: string;
  trip_id: string;
  agency_id: string;
  task_type: string;
  title: string;
  description: string | null;
  status: string;
  priority: string;
  owner_id: string | null;
  due_at: string | null;
  blocker_code: string | null;
  blocker_refs: Record<string, unknown> | null;
  source: string;
  generation_hash: string | null;
  created_by: string;
  completed_by: string | null;
  completed_at: string | null;
  cancelled_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface BookingTaskSummary {
  total: number;
  not_started: number;
  blocked: number;
  ready: number;
  in_progress: number;
  waiting_on_customer: number;
  completed: number;
  cancelled: number;
}

export interface BookingTaskListResponse {
  ok: boolean;
  tasks: BookingTask[];
  summary: BookingTaskSummary;
}

export interface BookingTaskCreateRequest {
  task_type: string;
  title: string;
  description?: string;
  priority?: string;
  owner_id?: string;
  due_at?: string;
}

export interface BookingTaskUpdateRequest {
  status?: string;
  priority?: string;
  owner_id?: string;
  due_at?: string;
  title?: string;
}

export interface ReconciliationEntry {
  task_id: string;
  old_status: string;
  new_status: string;
}

export interface GenerateTasksResponse {
  ok: boolean;
  created: BookingTask[];
  skipped: string[];
  reconciled: ReconciliationEntry[];
}

export async function listBookingTasks(tripId: string): Promise<BookingTaskListResponse> {
  return api.get<BookingTaskListResponse>(`/api/booking-tasks/${tripId}`);
}

export async function createBookingTask(
  tripId: string,
  data: BookingTaskCreateRequest,
): Promise<{ ok: boolean; task: BookingTask }> {
  return api.post(`/api/booking-tasks/${tripId}`, data);
}

export async function generateBookingTasks(
  tripId: string,
  force = false,
): Promise<GenerateTasksResponse> {
  return api.post<GenerateTasksResponse>(`/api/booking-tasks/${tripId}/generate`, { force });
}

export async function updateBookingTask(
  tripId: string,
  taskId: string,
  data: BookingTaskUpdateRequest,
): Promise<{ ok: boolean; task: BookingTask }> {
  return api.patch(`/api/booking-tasks/${tripId}/${taskId}`, data);
}

export async function completeBookingTask(
  tripId: string,
  taskId: string,
): Promise<{ ok: boolean; task: BookingTask }> {
  return api.post(`/api/booking-tasks/${tripId}/${taskId}/complete`);
}

export async function cancelBookingTask(
  tripId: string,
  taskId: string,
): Promise<{ ok: boolean; task: BookingTask }> {
  return api.post(`/api/booking-tasks/${tripId}/${taskId}/cancel`);
}

// ── Phase 5B: Confirmations + Execution Timeline ────────────────────────────

export interface ConfirmationSummary {
  id: string;
  trip_id: string;
  task_id: string | null;
  confirmation_type: string;
  confirmation_status: string;
  has_supplier: boolean;
  has_confirmation_number: boolean;
  external_ref_present: boolean;
  notes_present: boolean;
  evidence_ref_count: number;
  recorded_at: string | null;
  verified_at: string | null;
  voided_at: string | null;
  created_by: string;
  created_at: string;
}

export interface ConfirmationDetail extends ConfirmationSummary {
  evidence_refs: { type: string; id: string }[] | null;
  supplier_name: string | null;
  confirmation_number: string | null;
  notes: string | null;
  external_ref: string | null;
  recorded_by: string | null;
  verified_by: string | null;
  voided_by: string | null;
  updated_at: string;
}

export interface CreateConfirmationRequest {
  confirmation_type: string;
  task_id?: string;
  supplier_name?: string;
  confirmation_number?: string;
  notes?: string;
  external_ref?: string;
  evidence_refs?: { type: string; id: string }[];
}

export interface UpdateConfirmationRequest {
  confirmation_type?: string;
  task_id?: string;
  supplier_name?: string;
  confirmation_number?: string;
  notes?: string;
  external_ref?: string;
  evidence_refs?: { type: string; id: string }[];
}

export interface ExecutionTimelineEvent {
  event_type: string;
  event_category: string;
  subject_type: string;
  subject_id: string;
  status_from: string | null;
  status_to: string;
  actor_type: string;
  actor_id: string | null;
  source: string;
  event_metadata: Record<string, unknown> | null;
  timestamp: string;
}

export async function listConfirmations(
  tripId: string,
): Promise<{ ok: boolean; confirmations: ConfirmationSummary[] }> {
  return api.get(`/api/trips/${tripId}/confirmations`);
}

export async function getConfirmation(
  tripId: string,
  confirmationId: string,
): Promise<{ ok: boolean; confirmation: ConfirmationDetail }> {
  return api.get(`/api/trips/${tripId}/confirmations/${confirmationId}`);
}

export async function createConfirmation(
  tripId: string,
  data: CreateConfirmationRequest,
): Promise<{ ok: boolean; confirmation: ConfirmationDetail }> {
  return api.post(`/api/trips/${tripId}/confirmations`, data);
}

export async function updateConfirmation(
  tripId: string,
  confirmationId: string,
  data: UpdateConfirmationRequest,
): Promise<{ ok: boolean; confirmation: ConfirmationDetail }> {
  return api.patch(`/api/trips/${tripId}/confirmations/${confirmationId}`, data);
}

export async function recordConfirmation(
  tripId: string,
  confirmationId: string,
): Promise<{ ok: boolean; confirmation: ConfirmationSummary }> {
  return api.post(`/api/trips/${tripId}/confirmations/${confirmationId}/record`);
}

export async function verifyConfirmation(
  tripId: string,
  confirmationId: string,
): Promise<{ ok: boolean; confirmation: ConfirmationSummary }> {
  return api.post(`/api/trips/${tripId}/confirmations/${confirmationId}/verify`);
}

export async function voidConfirmation(
  tripId: string,
  confirmationId: string,
): Promise<{ ok: boolean; confirmation: ConfirmationSummary }> {
  return api.post(`/api/trips/${tripId}/confirmations/${confirmationId}/void`);
}

export async function getExecutionTimeline(
  tripId: string,
  category?: string,
): Promise<{
  ok: boolean;
  events: ExecutionTimelineEvent[];
  summary: Record<string, number>;
}> {
  const params = category ? `?category=${category}` : "";
  return api.get(`/api/trips/${tripId}/execution-timeline${params}`);
}
