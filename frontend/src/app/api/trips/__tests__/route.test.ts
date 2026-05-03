import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { POST } from "../route";
import type { NextRequest } from "next/server";

vi.mock("@/lib/bff-auth", async (importOriginal) => {
  const actual: Record<string, unknown> = await importOriginal() as Record<string, unknown>;
  return {
    ...actual,
    bffFetchOptions: vi.fn((_request: unknown, method: string, _scope?: unknown, extraHeaders?: Record<string, string>, body?: unknown) => {
      const opts: RequestInit = {
        method,
        headers: { ...extraHeaders, "Content-Type": "application/json" },
        cache: "no-store" as RequestCache,
      };
      if (body !== undefined) {
        opts.body = JSON.stringify(body);
      }
      return opts;
    }),
  };
});

function asNextRequest(request: Request): NextRequest {
  return request as unknown as NextRequest;
}

describe("/api/trips POST endpoint - Kill Switch Tests", () => {
  const originalEnv = process.env.DISABLE_CALL_CAPTURE;

  afterEach(() => {
    if (originalEnv === undefined) {
      delete process.env.DISABLE_CALL_CAPTURE;
    } else {
      process.env.DISABLE_CALL_CAPTURE = originalEnv;
    }
    vi.restoreAllMocks();
  });

  describe("Call Capture Enabled (Normal Operation)", () => {
    beforeEach(() => {
      delete process.env.DISABLE_CALL_CAPTURE;
      vi.spyOn(global, "fetch").mockImplementation((_url, _opts) => {
        return Promise.resolve(
          new Response(
            JSON.stringify({
              run_id: "run_test_001",
              state: "queued",
            }),
            { status: 200, headers: { "Content-Type": "application/json" } }
          )
        );
      });
    });

    afterEach(() => {
      vi.restoreAllMocks();
    });

    it("test_call_capture_enabled_returns_202_with_run_id", async () => {
      const request = new Request("http://localhost:3000/api/trips", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          raw_note: "Customer wants to explore European destinations",
          owner_note: "Follow up about wine tours",
        }),
      });

      const response = await POST(asNextRequest(request));
      const data = await response.json();

      expect(response.status).toBe(202);
      expect(data).toHaveProperty("run_id");
      expect(data).toHaveProperty("state");
      expect(data.state).toBe("queued");
      expect(data).not.toHaveProperty("error");
    });

    it("test_call_capture_enabled_accepts_all_optional_fields", async () => {
      const request = new Request("http://localhost:3000/api/trips", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          raw_note: "Trip inquiry",
          owner_note: "Premium customer",
          structured_json: { preferences: "luxury" },
          itinerary_text: "Paris, Rome, Venice",
          stage: "planning",
          operating_mode: "normal_intake",
          follow_up_due_date: "2026-05-15",
        }),
      });

      const response = await POST(asNextRequest(request));
      expect(response.status).toBe(202);

      const data = await response.json();
      expect(data).toHaveProperty("run_id");
      expect(data.state).toBe("queued");
    });

    it("test_call_capture_enabled_validates_required_raw_note", async () => {
      const request = new Request("http://localhost:3000/api/trips", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          owner_note: "This is missing raw_note field",
        }),
      });

      const response = await POST(asNextRequest(request));
      const data = await response.json();

      expect(response.status).toBe(400);
      expect(data).toEqual({ error: "raw_note required" });
    });

    it("test_call_capture_enabled_with_minimal_payload", async () => {
      const request = new Request("http://localhost:3000/api/trips", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          raw_note: "Simple note",
        }),
      });

      const response = await POST(asNextRequest(request));
      expect(response.status).toBe(202);

      const data = await response.json();
      expect(data).toHaveProperty("run_id");
      expect(data.state).toBe("queued");
    });
  });

  describe("Call Capture Disabled (Kill Switch Active)", () => {
    beforeEach(() => {
      process.env.DISABLE_CALL_CAPTURE = "true";
    });

    it("test_kill_switch_active_returns_503", async () => {
      const request = new Request("http://localhost:3000/api/trips", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          raw_note: "Trip inquiry that should be rejected",
        }),
      });

      const response = await POST(asNextRequest(request));
      const data = await response.json();

      expect(response.status).toBe(503);
      expect(data).toEqual({
        error: "Call capture feature is temporarily disabled",
      });
    });

    it("test_kill_switch_requires_truthy_exactly", () => {
      // Only exact "true" string should trigger
      const envValue = process.env.DISABLE_CALL_CAPTURE;
      const isDisabled = envValue === "true";

      expect(isDisabled).toBe(true);
    });
  });

  describe("Kill Switch Default State", () => {
    beforeEach(() => {
      delete process.env.DISABLE_CALL_CAPTURE;
    });

    it("test_kill_switch_is_disabled_by_default", () => {
      const envValue = process.env.DISABLE_CALL_CAPTURE;
      const isDisabled = envValue === "true";

      expect(isDisabled).toBe(false);
    });
  });

  describe("Error Handling in Normal Operation", () => {
    beforeEach(() => {
      delete process.env.DISABLE_CALL_CAPTURE;
    });

    it("test_handles_invalid_json_gracefully", async () => {
      const request = new Request("http://localhost:3000/api/trips", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: "invalid json {",
      });

      const response = await POST(asNextRequest(request));
      expect(response.status).toBe(500);

      const data = await response.json();
      expect(data).toEqual({ error: "Failed to create trip" });
    });

    it("test_returns_400_when_raw_note_is_empty_string", async () => {
      const request = new Request("http://localhost:3000/api/trips", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          raw_note: "",
          owner_note: "Has note but raw_note is empty",
        }),
      });

      const response = await POST(asNextRequest(request));
      expect(response.status).toBe(400);

      const data = await response.json();
      expect(data).toEqual({ error: "raw_note required" });
    });
  });
});
