/**
 * Centralized API Client
 *
 * Handles all HTTP requests to backend APIs with consistent error handling,
 * retry logic, and type safety.
 */

import type { ReviewStatus } from "@/types/governance";
import type {
  ValidationReport,
  FeeCalculationResult,
  DecisionOutput,
  StrategyOutput,
  PromptBundle,
  FrontierOrchestrationResult,
} from "@/types/spine";
import type { IntegrityIssuesResponse } from "@/types/spine";
import type {
  CreateSeasonalCampaignRequest as BackendCreateSeasonalCampaignRequest,
  SeasonDispatchResponse as BackendSeasonDispatchResponse,
  SeasonalCampaignListResponse as BackendSeasonalCampaignListResponse,
  SeasonalCampaignPlan,
  SeasonPreflightResponse as BackendSeasonPreflightResponse,
  SeasonSimulationResponse as BackendSeasonSimulationResponse,
  UpdateSeasonalCampaignRequest as BackendUpdateSeasonalCampaignRequest,
} from "@/types/generated/spine-api";

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
  frontier_result?: FrontierOrchestrationResult | null;
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

export type AgencyTier = "starter" | "pro" | "enterprise";

export interface AgencySettingsResponse {
  agency_id: string;
  tier: AgencyTier;
  seasonal: AgencySeasonalSettings;
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

export interface AgencySeasonalSettings {
  active_seasons_enabled: boolean;
  default_quarter_window_months: number;
  channel_mix: Record<string, number>;
  weather_risk_threshold: number;
  budget_guardrail_multiplier: number;
  micro_seasonality_window_days: number;
  quarterly_recalibration_enabled: boolean;
  prelaunch_blocklist: string[];
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

export interface UpdateAgencySeasonalRequest {
  active_seasons_enabled?: boolean;
  default_quarter_window_months?: number;
  channel_mix?: Record<string, number>;
  weather_risk_threshold?: number;
  budget_guardrail_multiplier?: number;
  micro_seasonality_window_days?: number;
  quarterly_recalibration_enabled?: boolean;
  prelaunch_blocklist?: string[];
}

export type SeasonalCampaign = SeasonalCampaignPlan;
export type SeasonalCampaignListResponse = BackendSeasonalCampaignListResponse;
export type CreateSeasonalCampaignRequest = BackendCreateSeasonalCampaignRequest;
export type UpdateSeasonalCampaignRequest = BackendUpdateSeasonalCampaignRequest;
export type SimulateSeasonalCampaignResponse = BackendSeasonSimulationResponse;
export type SeasonPreflightResponse = BackendSeasonPreflightResponse;
export type SeasonDispatchResponse = BackendSeasonDispatchResponse;

export type AgencySettings = AgencySettingsResponse;
export type AgencyAutonomy = AgencyAutonomyResponse;
export type AgencySeasonal = AgencySeasonalSettings;
export type UpdateOperationalPayload = UpdateAgencyOperationalRequest;
export type UpdateAutonomyPayload = UpdateAgencyAutonomyRequest;
export type UpdateSeasonalPayload = UpdateAgencySeasonalRequest;
export type CreateSeasonalCampaignPayload = CreateSeasonalCampaignRequest;
export type UpdateSeasonalCampaignPayload = UpdateSeasonalCampaignRequest;

export async function getAgencySettings(): Promise<AgencySettingsResponse> {
  return api.get<AgencySettingsResponse>("/api/settings");
}

export async function updateAgencyOperational(
  request: UpdateAgencyOperationalRequest
): Promise<AgencySettingsResponse> {
  return api.post<AgencySettingsResponse>("/api/settings/operational", request);
}

export async function getAgencySeasonalSettings(): Promise<AgencySeasonalSettings> {
  return api.get<AgencySeasonalSettings>("/api/settings/seasonal");
}

export async function updateAgencySeasonal(
  request: UpdateAgencySeasonalRequest
): Promise<AgencySettingsResponse> {
  return api.put<AgencySettingsResponse>("/api/settings/seasonal", request);
}

export async function listSeasonalCampaigns(): Promise<SeasonalCampaignListResponse> {
  return api.get<SeasonalCampaignListResponse>("/api/settings/seasonal/campaigns");
}

export async function getSeasonalCampaign(planId: string): Promise<SeasonalCampaign> {
  return api.get<SeasonalCampaign>(`/api/settings/seasonal/campaigns/${encodeURIComponent(planId)}`);
}

export async function createSeasonalCampaign(
  request: CreateSeasonalCampaignRequest
): Promise<SeasonalCampaign> {
  return api.post<SeasonalCampaign>("/api/settings/seasonal/campaigns", request);
}

export async function updateSeasonalCampaign(
  planId: string,
  request: UpdateSeasonalCampaignRequest
): Promise<SeasonalCampaign> {
  return api.put<SeasonalCampaign>(`/api/settings/seasonal/campaigns/${encodeURIComponent(planId)}`, request);
}

export async function deleteSeasonalCampaign(planId: string): Promise<{ ok: boolean; plan_id: string }> {
  return api.delete<{ ok: boolean; plan_id: string }>(`/api/settings/seasonal/campaigns/${encodeURIComponent(planId)}`);
}

export async function simulateSeasonalCampaign(
  planId: string,
  scenario = "baseline"
): Promise<SimulateSeasonalCampaignResponse> {
  return api.post<SimulateSeasonalCampaignResponse>(
    `/api/settings/seasonal/campaigns/${encodeURIComponent(planId)}/simulate`,
    { scenario },
  );
}

export async function preflightSeasonalCampaign(planId: string): Promise<SeasonPreflightResponse> {
  return api.post<SeasonPreflightResponse>(`/api/settings/seasonal/campaigns/${encodeURIComponent(planId)}/preflight`);
}

export async function dispatchSeasonalCampaign(
  planId: string,
  dryRun = true
): Promise<SeasonDispatchResponse> {
  return api.post<SeasonDispatchResponse>(
    `/api/settings/seasonal/campaigns/${encodeURIComponent(planId)}/dispatch`,
    { dry_run: dryRun },
  );
}

export async function updateAgencyAutonomy(
  request: UpdateAgencyAutonomyRequest
): Promise<AgencySettingsResponse> {
  return api.post<AgencySettingsResponse>("/api/settings/autonomy", request);
}

// ============================================================================
// LLM GUARD API
// ============================================================================

export interface LlmGuardState {
  enabled: boolean;
  agency_id: string;
  max_calls_per_hour: number | null;
  max_calls_per_model: Record<string, number>;
  daily_budget: number | null;
  budget_mode: string;
  current_hourly_calls: number;
  current_daily_cost: number;
}

export async function getLlmGuardState(): Promise<LlmGuardState> {
  return api.get<LlmGuardState>("/api/settings/llm-guard");
}

// ============================================================================
// ALERT DESTINATIONS API
// ============================================================================

export interface AlertDestinationConfig {
  id: string;
  label: string;
  enabled: boolean;
  type: "webhook" | "email";
  url: string;
  email_to: string;
  email_cc: string;
  smtp_host: string;
  smtp_port: number;
  smtp_user: string;
  smtp_use_tls: boolean;
  sender: string;
  min_severity: "warning" | "critical";
  event_types: string[];
  has_smtp_password: boolean;
}

export interface AlertDestinationsResponse {
  enabled: boolean;
  destinations: AlertDestinationConfig[];
}

export interface TestAlertRequest {
  type: "webhook" | "email";
  url?: string;
  email_to?: string;
  smtp_host?: string;
  smtp_port?: number;
  smtp_user?: string;
  smtp_password?: string;
  sender?: string;
}

export async function getAlertDestinations(): Promise<AlertDestinationsResponse> {
  return api.get<AlertDestinationsResponse>("/api/settings/alert-destinations");
}

export async function updateAlertDestinations(data: {
  enabled: boolean;
  destinations: AlertDestinationConfig[];
}): Promise<{ ok: boolean }> {
  return api.post<{ ok: boolean }>("/api/settings/alert-destinations", data);
}

export async function testAlertDestination(data: TestAlertRequest): Promise<{ ok: boolean; detail: string }> {
  return api.post<{ ok: boolean; detail: string }>("/api/settings/alert-destinations/test", data);
}

// ============================================================================
// AI AGENT SETTINGS API (P4-07)
// ============================================================================

export interface AiAgentSettings {
  agency_id: string;
  enable_auto_intake: boolean;
  enable_auto_shortlist: boolean;
  enable_auto_proposal: boolean;
  enable_auto_negotiation: boolean;
  enable_frontier_orchestration: boolean;
  enable_checker_agent: boolean;
  enable_call_capture: boolean;
  enable_document_extraction: boolean;
  preferred_model: string;
  fallback_model: string;
  extraction_model: string;
  checker_model: string;
  max_negotiation_rounds: number;
  proposal_confidence_threshold: number;
  auto_advance_stages: boolean;
  require_owner_review_above_value: number;
  brand_voice: "professional" | "friendly" | "luxury" | "budget";
  response_language: string;
  max_follow_up_questions: number;
}

export type UpdateAiAgentPayload = Partial<Omit<AiAgentSettings, "agency_id">>;

export async function getAiAgentSettings(): Promise<AiAgentSettings> {
  return api.get<AiAgentSettings>("/api/settings/ai-agent");
}

export async function updateAiAgentSettings(data: UpdateAiAgentPayload): Promise<{ ok: boolean }> {
  return api.post<{ ok: boolean }>("/api/settings/ai-agent", data);
}

// ============================================================================
// SUPPORT SETTINGS API (P4-08)
// ============================================================================

export interface SupportSettings {
  agency_id: string;
  enable_email_support: boolean;
  enable_chat_support: boolean;
  enable_phone_support: boolean;
  enable_whatsapp_support: boolean;
  default_response_sla_hours: number;
  urgent_response_sla_hours: number;
  auto_route_by_destination: boolean;
  auto_route_by_language: boolean;
  escalation_after_sla_breach: boolean;
  escalation_contact_email: string;
  escalation_contact_phone: string;
  support_hours_start: string;
  support_hours_end: string;
  support_days: string[];
  timezone: string;
  enable_auto_acknowledgement: boolean;
  auto_acknowledgement_message: string;
  out_of_hours_message: string;
  enable_csat_survey: boolean;
  csat_trigger: "after_resolution" | "after_first_response" | "never";
}

export type UpdateSupportPayload = Partial<Omit<SupportSettings, "agency_id">>;

export async function getSupportSettings(): Promise<SupportSettings> {
  return api.get<SupportSettings>("/api/settings/support");
}

export async function updateSupportSettings(data: UpdateSupportPayload): Promise<{ ok: boolean }> {
  return api.post<{ ok: boolean }>("/api/settings/support", data);
}

// ============================================================================
// COMMUNICATION SETTINGS API (P4-09)
// ============================================================================

export interface CommSettings {
  agency_id: string;
  default_outbound_channel: "email" | "whatsapp" | "sms";
  allow_channel_switching: boolean;
  enable_template_library: boolean;
  default_greeting: string;
  default_sign_off: string;
  respect_operating_hours: boolean;
  send_immediately_during_hours: boolean;
  queue_outside_hours: boolean;
  max_emails_per_day_per_trip: number;
  max_whatsapp_per_day_per_trip: number;
  auto_detect_language: boolean;
  default_language: string;
  supported_languages: string[];
  translate_outbound: boolean;
  enable_auto_followup: boolean;
  auto_followup_delay_days: number;
  max_auto_followups: number;
  followup_escalate_after_max: boolean;
  notify_on_customer_reply: boolean;
  notify_on_sla_warning: boolean;
  notify_on_escalation: boolean;
  digest_frequency: "realtime" | "hourly" | "daily" | "never";
  include_agency_signature: boolean;
  include_unsubscribe_link: boolean;
  compliance_footer: string;
}

export type UpdateCommPayload = Partial<Omit<CommSettings, "agency_id">>;

export async function getCommSettings(): Promise<CommSettings> {
  return api.get<CommSettings>("/api/settings/comm");
}

export async function updateCommSettings(data: UpdateCommPayload): Promise<{ ok: boolean }> {
  return api.post<{ ok: boolean }>("/api/settings/comm", data);
}

// ============================================================================
// TRIP REVIEW API
// ============================================================================

export async function submitTripReviewAction(
  tripId: string,
  action: string,
  notes?: string,
  errorCategory?: string,
  escalationOutcome?: "false_escalation" | "missed_escalation" | "correct_escalation" | "not_applicable",
  reviewWorkflowUnitId?: string,
): Promise<{ success: boolean; review: any }> {
  const payload: Record<string, unknown> = {
    action,
    notes,
    error_category: errorCategory,
    escalation_outcome: escalationOutcome,
  };
  if (reviewWorkflowUnitId) {
    payload.review_workflow_unit_id = reviewWorkflowUnitId;
  }
  return api.post(`/api/trips/${tripId}/review/action`, payload);
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

export type PaymentStatus =
  | 'not_started'
  | 'deposit_paid'
  | 'partially_paid'
  | 'paid'
  | 'overdue'
  | 'waived'
  | 'refunded'
  | 'unknown';

export type RefundStatus =
  | 'not_applicable'
  | 'not_requested'
  | 'pending_review'
  | 'approved'
  | 'processing'
  | 'paid'
  | 'rejected'
  | 'cancelled';

export interface PaymentTracking {
  agreed_amount?: number | null;
  currency?: string | null;
  amount_paid?: number | null;
  balance_due?: number | null;
  payment_status?: PaymentStatus;
  payment_method?: string | null;
  payment_reference?: string | null;
  payment_proof_url?: string | null;
  refund_status?: RefundStatus;
  refund_amount_agreed?: number | null;
  refund_method?: string | null;
  refund_reference?: string | null;
  refund_paid_by_agency?: boolean;
  notes?: string | null;
  tracking_only?: boolean;
  final_payment_due?: string | null;
}

export interface BookingData {
  travelers: BookingTraveler[];
  payer?: BookingPayer | null;
  special_requirements?: string | null;
  booking_notes?: string | null;
  payment_tracking?: PaymentTracking | null;
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

export async function updatePaymentTracking(
  tripId: string,
  paymentTracking: PaymentTracking,
  expectedUpdatedAt?: string,
): Promise<BookingDataResponse> {
  return api.patch<BookingDataResponse>(`/api/trips/${tripId}/booking-data/payment`, {
    payment_tracking: paymentTracking,
    expected_updated_at: expectedUpdatedAt || undefined,
  });
}

// ---------------------------------------------------------------------------
// Payments Queue (v1 read-model, queue/read-only)
// ---------------------------------------------------------------------------

export type QueueStatus =
  | 'not_configured'
  | 'unknown'
  | 'due_later'
  | 'due_soon'
  | 'overdue'
  | 'paid_complete'
  | 'refund_in_progress';

export interface PaymentQueueItem {
  trip_id: string;
  trip_name: string;
  destination?: string | null;
  start_date?: string | null;
  status?: string | null;
  queue_status: QueueStatus;
  payment_status: PaymentStatus;
  refund_status: RefundStatus;
  agreed_amount?: number | null;
  amount_paid?: number | null;
  balance_due?: number | null;
  currency: string;
  final_payment_due?: string | null;
  payment_reference_present: boolean;
  payment_proof_url_present: boolean;
  refund_paid_by_agency: boolean;
  updated_at?: string | null;
}

export interface PaymentQueueSummary {
  total: number;
  by_queue_status: Record<string, number>;
  overdue_count: number;
  due_soon_count: number;
  not_configured_count: number;
  paid_complete_count: number;
  refund_in_progress_count: number;
  due_within_7_days_count: number;
}

export interface PaymentQueuePagination {
  limit: number;
  offset: number;
  returned: number;
  total: number;
  has_more: boolean;
}

export interface PaymentQueueResponse {
  summary: PaymentQueueSummary;
  pagination: PaymentQueuePagination;
  items: PaymentQueueItem[];
}

export interface PaymentQueueParams {
  limit?: number;
  offset?: number;
  queue_status?: QueueStatus;
  payment_status?: PaymentStatus;
  refund_status?: RefundStatus;
  due_bucket?: 'none' | 'overdue' | 'due_0_3' | 'due_4_7' | 'due_8_14';
}

export async function getPaymentsQueue(params?: PaymentQueueParams): Promise<PaymentQueueResponse> {
  const searchParams = new URLSearchParams();
  if (params?.limit != null) searchParams.set('limit', String(params.limit));
  if (params?.offset != null) searchParams.set('offset', String(params.offset));
  if (params?.queue_status) searchParams.set('queue_status', params.queue_status);
  if (params?.payment_status) searchParams.set('payment_status', params.payment_status);
  if (params?.refund_status) searchParams.set('refund_status', params.refund_status);
  if (params?.due_bucket) searchParams.set('due_bucket', params.due_bucket);
  const qs = searchParams.toString();
  return api.get<PaymentQueueResponse>(`/api/payments${qs ? `?${qs}` : ''}`);
}

// ---------------------------------------------------------------------------
// Integrations — agency-scoped provider status (read-only v1)
// ---------------------------------------------------------------------------

export type IntegrationStatus =
  | 'disabled'
  | 'connected'
  | 'degraded'
  | 'auth_expired'
  | 'misconfigured';

export interface Integration {
  provider: string;
  display_name: string;
  enabled: boolean;
  status: IntegrationStatus;
  capabilities: string[];
  category: string;
  last_health_check_at: string | null;
  last_success_at: string | null;
  last_error_code: string | null;
  last_error_message_safe: string | null;
  updated_at: string | null;
}

export interface IntegrationListResponse {
  integrations: Integration[];
  total: number;
}

export async function getIntegrations(): Promise<IntegrationListResponse> {
  return api.get<IntegrationListResponse>('/api/integrations');
}

export async function getIntegration(provider: string): Promise<Integration> {
  return api.get<Integration>(`/api/integrations/${encodeURIComponent(provider)}`);
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
  /** Populated by authenticated GET when an active, non-expired token exists.
   *  null for absent/revoked/used/expired tokens and pre-migration rows. */
  collection_url?: string | null;
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
export async function getPublicCollectionForm(agencyId: string, token: string): Promise<PublicCollectionContext> {
  const url = `${SPINE_API_URL}/api/public/booking-collection/${encodeURIComponent(agencyId)}/${encodeURIComponent(token)}`;
  const res = await fetch(url, { credentials: 'omit' });
  if (!res.ok) throw new Error(`Failed to load collection form (${res.status})`);
  return res.json();
}

export async function submitPublicBookingData(
  agencyId: string,
  token: string,
  data: BookingData,
): Promise<{ ok: boolean; message: string }> {
  const url = `${SPINE_API_URL}/api/public/booking-collection/${encodeURIComponent(agencyId)}/${encodeURIComponent(token)}/submit`;
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
  agencyId: string,
  token: string,
  file: File,
  documentType: string,
): Promise<CustomerDocumentResponse> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('document_type', documentType);

  const url = `${SPINE_API_URL}/api/public/booking-collection/${encodeURIComponent(agencyId)}/${encodeURIComponent(token)}/documents`;
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
  actorType?: string,
): Promise<{
  ok: boolean;
  events: ExecutionTimelineEvent[];
  summary: Record<string, number>;
}> {
  const sp = new URLSearchParams();
  if (category) sp.set("category", category);
  if (actorType) sp.set("actor_type", actorType);
  const qs = sp.toString();
  const params = qs ? `?${qs}` : "";
  return api.get(`/api/trips/${tripId}/execution-timeline${params}`);
}
