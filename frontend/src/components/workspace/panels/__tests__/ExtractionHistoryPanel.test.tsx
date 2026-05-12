import { describe, it, expect, vi, beforeEach } from "vitest";
import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";
import { ExtractionHistoryPanel } from "../ExtractionHistoryPanel";
import * as apiClient from "@/lib/api-client";
import type { ExtractionResponse, AttemptSummary } from "@/lib/api-client";

vi.mock("@/lib/api-client", async () => {
  const actual = await vi.importActual("@/lib/api-client");
  return {
    ...actual,
    listExtractionAttempts: vi.fn(),
    retryExtraction: vi.fn(),
  };
});

const mockListAttempts = vi.mocked(apiClient.listExtractionAttempts);
const mockRetryExtraction = vi.mocked(apiClient.retryExtraction);

const tripId = "trip-123";
const documentId = "doc-456";

function makeExtraction(overrides: Partial<ExtractionResponse> = {}): ExtractionResponse {
  return {
    id: "ext-789",
    document_id: documentId,
    status: "pending_review",
    extracted_by: "openai",
    overall_confidence: 0.9,
    field_count: 3,
    fields: [
      { field_name: "full_name", value: "TEST", confidence: 0.9, present: true },
      { field_name: "passport_number", value: "AB123", confidence: 0.85, present: true },
      { field_name: "nationality", value: "US", confidence: 0.95, present: true },
    ],
    created_at: "2026-05-08T10:00:00Z",
    updated_at: "2026-05-08T10:00:01Z",
    reviewed_at: null,
    reviewed_by: null,
    provider_name: "openai",
    model_name: "gpt-5.4-nano",
    latency_ms: 142,
    prompt_tokens: 100,
    completion_tokens: 50,
    total_tokens: 150,
    cost_estimate_usd: 0.00008,
    error_code: null,
    error_summary: null,
    confidence_method: "heuristic_presence",
    attempt_count: 2,
    run_count: 1,
    current_attempt_id: "attempt-2",
    page_count: null,
    ...overrides,
  };
}

function makeAttempt(overrides: Partial<AttemptSummary> = {}): AttemptSummary {
  return {
    attempt_id: "attempt-1",
    run_number: 1,
    attempt_number: 1,
    fallback_rank: 0,
    provider_name: "openai",
    model_name: "gpt-5.4-nano",
    latency_ms: 142,
    status: "success",
    error_code: null,
    created_at: "2026-05-08T10:00:00Z",
    ...overrides,
  };
}

describe("ExtractionHistoryPanel", () => {
  const onRetryComplete = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders attempt history with provider/model/status/latency metadata", async () => {
    mockListAttempts.mockResolvedValue([
      makeAttempt({
        attempt_id: "attempt-1",
        attempt_number: 1,
        provider_name: "gemini",
        model_name: "gemini-2.5-flash",
        latency_ms: 30021,
        status: "failed",
        error_code: "api_timeout",
      }),
      makeAttempt({
        attempt_id: "attempt-2",
        attempt_number: 2,
        fallback_rank: 1,
        provider_name: "openai",
        model_name: "gpt-5.4-nano",
        latency_ms: 142,
        status: "success",
      }),
    ]);

    render(
      <ExtractionHistoryPanel
        tripId={tripId}
        documentId={documentId}
        extraction={makeExtraction()}
        onRetryComplete={onRetryComplete}
      />,
    );

    await waitFor(() => {
      expect(screen.getByText("Extraction History")).toBeInTheDocument();
    });

    // Check metadata is displayed - provider/model may appear in multiple elements
    expect(screen.getAllByText(/gemini/).length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText(/gemini-2.5-flash/).length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText(/openai/).length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText(/gpt-5.4-nano/).length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("30.0s")).toBeInTheDocument(); // 30021ms
    expect(screen.getByText("142ms")).toBeInTheDocument();
  });

  it("marks current attempt without emoji", async () => {
    mockListAttempts.mockResolvedValue([
      makeAttempt({
        attempt_id: "attempt-1",
        status: "failed",
        error_code: "api_timeout",
      }),
      makeAttempt({
        attempt_id: "attempt-2",
        status: "success",
      }),
    ]);

    render(
      <ExtractionHistoryPanel
        tripId={tripId}
        documentId={documentId}
        extraction={makeExtraction({ current_attempt_id: "attempt-2" })}
        onRetryComplete={onRetryComplete}
      />,
    );

    await waitFor(() => {
      // "Current" text marker, not emoji
      const currentMarkers = screen.getAllByText("Current");
      expect(currentMarkers.length).toBeGreaterThanOrEqual(1);
    });

    // No emoji characters in the document
    const pageText = document.body.textContent ?? "";
    expect(pageText).not.toContain("★");
    expect(pageText).not.toContain("⭐");
  });

  it("hides retry button when extraction is not failed", async () => {
    mockListAttempts.mockResolvedValue([makeAttempt()]);

    render(
      <ExtractionHistoryPanel
        tripId={tripId}
        documentId={documentId}
        extraction={makeExtraction({ status: "pending_review" })}
        onRetryComplete={onRetryComplete}
      />,
    );

    await waitFor(() => {
      expect(screen.getByText("Extraction History")).toBeInTheDocument();
    });

    // Retry button should not exist for pending_review
    expect(screen.queryByText(/Retry/)).not.toBeInTheDocument();
  });

  it("shows retry button when extraction is failed", async () => {
    mockListAttempts.mockResolvedValue([
      makeAttempt({ status: "failed", error_code: "api_timeout" }),
    ]);

    render(
      <ExtractionHistoryPanel
        tripId={tripId}
        documentId={documentId}
        extraction={makeExtraction({
          status: "failed",
          current_attempt_id: null,
          error_code: "api_timeout",
        })}
        onRetryComplete={onRetryComplete}
      />,
    );

    await waitFor(() => {
      expect(screen.getByText("Retry")).toBeInTheDocument();
    });
  });

  it("calls retry API and refreshes on retry click", async () => {
    const updatedExtraction = makeExtraction({ status: "pending_review", run_count: 2 });

    mockListAttempts
      .mockResolvedValueOnce([makeAttempt({ status: "failed", error_code: "api_timeout" })])
      .mockResolvedValueOnce([
        makeAttempt({ status: "failed", error_code: "api_timeout" }),
        makeAttempt({ attempt_id: "attempt-2", status: "success" }),
      ]);

    mockRetryExtraction.mockResolvedValue(updatedExtraction);

    render(
      <ExtractionHistoryPanel
        tripId={tripId}
        documentId={documentId}
        extraction={makeExtraction({
          status: "failed",
          current_attempt_id: null,
          error_code: "api_timeout",
        })}
        onRetryComplete={onRetryComplete}
      />,
    );

    await waitFor(() => {
      expect(screen.getByText("Retry")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("Retry"));

    await waitFor(() => {
      expect(mockRetryExtraction).toHaveBeenCalledWith(tripId, documentId);
      expect(onRetryComplete).toHaveBeenCalledWith(updatedExtraction);
      // Attempts refreshed after retry
      expect(mockListAttempts).toHaveBeenCalledTimes(2);
    });
  });

  it("displays error_code only, never error_summary", async () => {
    mockListAttempts.mockResolvedValue([
      makeAttempt({
        status: "failed",
        error_code: "api_timeout",
      }),
    ]);

    const { container } = render(
      <ExtractionHistoryPanel
        tripId={tripId}
        documentId={documentId}
        extraction={makeExtraction({
          status: "failed",
          error_code: "api_timeout",
          error_summary: "Provider call timed out after 30s",
          current_attempt_id: null,
        })}
        onRetryComplete={onRetryComplete}
      />,
    );

    await waitFor(() => {
      // error_code is displayed
      expect(screen.getByText("api_timeout")).toBeInTheDocument();
    });

    // error_summary is NOT displayed
    expect(container.textContent).not.toContain("Provider call timed out after 30s");
  });

  it("does not render PII fields from attempt data", async () => {
    mockListAttempts.mockResolvedValue([
      makeAttempt({ status: "success" }),
    ]);

    const { container } = render(
      <ExtractionHistoryPanel
        tripId={tripId}
        documentId={documentId}
        extraction={makeExtraction()}
        onRetryComplete={onRetryComplete}
      />,
    );

    await waitFor(() => {
      expect(screen.getByText("Extraction History")).toBeInTheDocument();
    });

    const text = container.textContent ?? "";

    // PII fields that must NOT appear
    expect(text).not.toContain("extracted_fields_encrypted");
    expect(text).not.toContain("fields_present");
    expect(text).not.toContain("confidence_scores");
    expect(text).not.toContain("error_summary");
    expect(text).not.toContain("storage_key");
    expect(text).not.toContain("filename");

    // Attempt metadata that SHOULD appear
    expect(text).toContain("openai");
    expect(text).toContain("142ms");
  });

  it("shows fallback rank labels correctly", async () => {
    mockListAttempts.mockResolvedValue([
      makeAttempt({ fallback_rank: 0, provider_name: "gemini", model_name: "gemini-2.5-flash" }),
      makeAttempt({
        attempt_id: "attempt-2",
        attempt_number: 2,
        fallback_rank: 1,
        provider_name: "openai",
        model_name: "gpt-5.4-nano",
      }),
    ]);

    render(
      <ExtractionHistoryPanel
        tripId={tripId}
        documentId={documentId}
        extraction={makeExtraction({ current_attempt_id: "attempt-2" })}
        onRetryComplete={onRetryComplete}
      />,
    );

    await waitFor(() => {
      // Fallback labels are inside parentheses: "(Primary)", "(Fallback 1)"
      expect(screen.getByText(/Primary/)).toBeInTheDocument();
      expect(screen.getByText(/Fallback 1/)).toBeInTheDocument();
    });
  });

  it("shows page count badge when extraction has pages", async () => {
    mockListAttempts.mockResolvedValue([makeAttempt()]);

    render(
      <ExtractionHistoryPanel
        tripId={tripId}
        documentId={documentId}
        extraction={makeExtraction({ page_count: 3 })}
        onRetryComplete={onRetryComplete}
      />,
    );

    await waitFor(() => {
      expect(screen.getByText("3 pages")).toBeInTheDocument();
    });
  });
});
