import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { WorkspaceTripLayoutShell } from "../layout";
import { ApiException } from "@/lib/api-client";
import * as apiClient from "@/lib/api-client";
import * as navigation from "next/navigation";

vi.mock("next/navigation", () => ({
  useParams: vi.fn(),
  usePathname: vi.fn(),
}));

vi.mock("@/lib/api-client", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api-client")>("@/lib/api-client");
  return {
    ...actual,
    api: {
      ...actual.api,
      get: vi.fn(),
    },
  };
});

vi.mock("@/components/error-boundary", () => ({
  ErrorBoundary: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  InlineError: ({ title, message }: { title?: string; message: string }) => (
    <div role="alert">
      {title && <span>{title}</span>}
      {message}
    </div>
  ),
}));

describe("trips/[tripId]/layout stale-link fallback", () => {
  it("explains that a missing trip link is stale and points back to Trips in Planning", async () => {
    vi.mocked(navigation.useParams).mockReturnValue({ tripId: "trip_missing_123" });
    vi.mocked(navigation.usePathname).mockReturnValue("/trips/trip_missing_123/intake");
    vi.mocked(apiClient.api.get).mockRejectedValue(new ApiException("Trip not found", 404));

    render(
      <WorkspaceTripLayoutShell>
        <div>Stage content</div>
      </WorkspaceTripLayoutShell>,
    );

    expect(await screen.findByText("Workspace unavailable")).toBeInTheDocument();
    await waitFor(() => {
      expect(
        screen.getByText("This trip link is stale or missing. Return to Trips in Planning and reopen it."),
      ).toBeInTheDocument();
    });
    expect(screen.getByRole("link", { name: "Back to Trips in Planning" })).toHaveAttribute("href", "/trips");
  });
});
