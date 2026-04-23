/**
 * Centralized API Client
 *
 * Handles all HTTP requests to backend APIs with consistent error handling,
 * retry logic, and type safety.
 */

import { SpineRunRequest, SpineRunResponse } from "@/types/spine";
import type { ReviewStatus } from "@/types/governance";
import type { ValidationReport, FeeCalculationResult, DecisionOutput, StrategyOutput, PromptBundle } from "@/types/spine";

// ============================================================================
// TYPES
// ============================================================================

export interface ApiError {
  message: string;
  status?: number;
  code?: string;
  details?: unknown[];
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

    // Retry loop
    for (let attempt = 0; attempt <= retry; attempt++) {
      try {
        // Create abort controller for timeout
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), timeout);

        const response = await fetch(url, {
          ...fetchOptions,
          signal: controller.signal,
          headers: {
            "Content-Type": "application/json",
            ...fetchOptions.headers,
          },
        });

        clearTimeout(timeoutId);

        // Handle non-OK responses
        if (!response.ok) {
          let errorData: ApiError = { message: response.statusText };

          try {
            errorData = await response.json();
          } catch {
            // Use default error message if JSON parsing fails
          }

          throw new ApiException(
            errorData.message,
            response.status,
            errorData.code,
            errorData.details
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

        // Don't retry if this was the last attempt
        if (attempt < retry) {
          // Wait before retrying (with exponential backoff)
          await new Promise((resolve) =>
            setTimeout(resolve, retryDelay * Math.pow(2, attempt))
          );
        }
      }
    }

    // All retries exhausted
    throw lastError || new Error("Request failed");
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

// Export default instance (for relative URLs within the same origin)
export const api = new ApiClient({
  timeout: DEFAULT_TIMEOUT,
  retry: 2, // Retry failed requests twice
  retryDelay: DEFAULT_RETRY_DELAY,
});

// ============================================================================
// SPINE API
// ============================================================================

export async function runSpine(request: SpineRunRequest): Promise<SpineRunResponse> {
  return api.post<SpineRunResponse>("/api/spine/run", request, {
    timeout: 60000, // 60 seconds for spine runs (can be long)
  });
}

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
  // Pipeline result fields (returned by mock API, not yet in real API)
  packet?: unknown;
  validation?: ValidationReport;
  decision?: DecisionOutput;
  strategy?: StrategyOutput;
  internal_bundle?: PromptBundle;
  traveler_bundle?: PromptBundle;
  safety?: unknown;
  fees?: FeeCalculationResult;
  // Input fields (returned by mock API)
  customerMessage?: string;
  agentNotes?: string;
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
    feedback_reopen?: boolean;
    recovery_status?: string;
    recovery_started_at?: string;
    recovery_deadline?: string;
  };
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

export async function getTrips(params?: {
  state?: string;
  limit?: number;
  offset?: number;
}): Promise<{ items: Trip[]; total: number }> {
  const searchParams = new URLSearchParams();
  if (params?.state) searchParams.set("state", params.state);
  if (params?.limit) searchParams.set("limit", params.limit.toString());
  if (params?.offset) searchParams.set("offset", params.offset.toString());

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

export async function getOverride(overrideId: string): Promise<{ ok: boolean; override: any }> {
  return api.get(`/api/overrides/${overrideId}`);
}

// ============================================================================
// SCENARIOS API (already exists, just re-exporting)
// ============================================================================

export interface ScenarioListItem {
  id: string;
  title: string;
}

export interface ScenarioDetail {
  id: string;
  title: string;
  input: SpineRunRequest;
  expected: SpineRunResponse;
}

export async function getScenarios(): Promise<ScenarioListItem[]> {
  return api.get<ScenarioListItem[]>("/api/scenarios");
}

export async function getScenario(id: string): Promise<ScenarioDetail> {
  return api.get<ScenarioDetail>(`/api/scenarios/${id}`);
}
