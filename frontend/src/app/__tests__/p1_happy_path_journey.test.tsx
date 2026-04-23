import { describe, it, expect, vi, beforeEach } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import InboxPage from "@/app/inbox/page";
import WorkspacesPage from "@/app/workspace/page";
import { IntakePanel } from "@/components/workspace/panels/IntakePanel";
import type { InboxTrip } from "@/types/governance";
import type { Trip } from "@/lib/api-client";
import * as governanceHooks from "@/hooks/useGovernance";
import * as tripHooks from "@/hooks/useTrips";
import * as workbenchStore from "@/stores/workbench";
import * as spineHook from "@/hooks/useSpineRun";
import * as nextNavigation from "next/navigation";

vi.mock("@/hooks/useGovernance", () => ({
  useInboxTrips: vi.fn(),
}));

vi.mock("@/hooks/useTrips", () => ({
  useTrips: vi.fn(),
  useUpdateTrip: vi.fn(),
}));

vi.mock("@/stores/workbench", () => ({
  useWorkbenchStore: vi.fn(),
}));

vi.mock("@/hooks/useSpineRun", () => ({
  useSpineRun: vi.fn(),
}));

vi.mock("next/navigation", () => ({
  useRouter: vi.fn(),
}));

describe("P1 Happy Path Journey", () => {
  const pushMock = vi.fn();
  const executeMock = vi.fn();
  const mutateMock = vi.fn();
  const setOperatingModeMock = vi.fn();

  const inboxTrip: InboxTrip = {
    id: "TRIP-123",
    reference: "REF-123",
    destination: "Singapore",
    tripType: "Family",
    partySize: 4,
    dateWindow: "June 2026",
    value: 220000,
    priority: "high",
    priorityScore: 90,
    stage: "intake",
    stageNumber: 1,
    assignedTo: "agent-1",
    assignedToName: "Alex Agent",
    submittedAt: "2026-04-23T08:00:00.000Z",
    lastUpdated: "2026-04-23T08:15:00.000Z",
    daysInCurrentStage: 1,
    slaStatus: "at_risk",
    customerName: "Sharma Family",
    flags: [],
  };

  const workspaceTrip: Trip = {
    id: "TRIP-123",
    destination: "Singapore",
    type: "Family",
    state: "amber",
    age: "1d",
    dateWindow: "June 2026",
    party: 4,
    budget: "INR 220000",
    customerMessage: "Need family trip options",
    agentNotes: "Priority lead",
    createdAt: "2026-04-23T08:00:00.000Z",
    updatedAt: "2026-04-23T08:15:00.000Z",
  };

  beforeEach(() => {
    vi.clearAllMocks();

    vi.mocked(nextNavigation.useRouter).mockReturnValue({
      push: pushMock,
    } as any);

    vi.mocked(governanceHooks.useInboxTrips).mockReturnValue({
      data: [inboxTrip],
      total: 1,
      hasMore: false,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
      assignTrips: vi.fn(),
      bulkAction: vi.fn(),
      snoozeTrip: vi.fn(),
    } as any);

    vi.mocked(tripHooks.useTrips).mockReturnValue({
      data: [workspaceTrip],
      total: 1,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    } as any);

    vi.mocked(tripHooks.useUpdateTrip).mockReturnValue({
      mutate: mutateMock,
      isSaving: false,
      error: null,
    } as any);

    vi.mocked(workbenchStore.useWorkbenchStore).mockReturnValue({
      input_raw_note: "Customer asks for June family trip with kid activities",
      input_owner_note: "Repeat traveler. Prioritize Sentosa options.",
      input_structured_json: "",
      input_itinerary_text: "",
      stage: "discovery",
      operating_mode: "normal_intake",
      strict_leakage: false,
      scenario_id: "",
      setInputRawNote: vi.fn(),
      setInputOwnerNote: vi.fn(),
      setStage: vi.fn(),
      setOperatingMode: setOperatingModeMock,
      setResultPacket: vi.fn(),
      setResultValidation: vi.fn(),
      setResultDecision: vi.fn(),
      setResultStrategy: vi.fn(),
      setResultInternalBundle: vi.fn(),
      setResultTravelerBundle: vi.fn(),
      setResultSafety: vi.fn(),
      setResultFees: vi.fn(),
      setResultRunTs: vi.fn(),
    } as any);

    vi.mocked(spineHook.useSpineRun).mockReturnValue({
      execute: executeMock,
      isLoading: false,
      error: null,
      reset: vi.fn(),
      data: null,
    } as any);

    executeMock.mockResolvedValue({
      packet: { packet_id: "pkt_123" },
      validation: { ok: true },
      decision: { decision_state: "ASK_FOLLOWUP" },
      strategy: { session_goal: "Resolve gaps" },
      internal_bundle: { user_message: "internal" },
      traveler_bundle: { user_message: "traveler" },
      safety: { leakage_passed: true },
      fees: null,
    });

    mutateMock.mockResolvedValue({ ...workspaceTrip });
  });

  it("supports inbox -> workspace process -> return link flow", async () => {
    render(<InboxPage />);

    const openLink = screen.getByRole("link", { name: /Singapore/i });
    expect(openLink).toHaveAttribute("href", "/workspace/TRIP-123/intake");

    render(<IntakePanel tripId="TRIP-123" trip={workspaceTrip} />);

    fireEvent.change(screen.getByDisplayValue("New Request"), {
      target: { value: "emergency" },
    });
    expect(setOperatingModeMock).toHaveBeenCalledWith("emergency");

    fireEvent.click(screen.getByRole("button", { name: /Process trip/i }));

    await waitFor(() => {
      expect(executeMock).toHaveBeenCalledTimes(1);
    });

    const sentPayload = executeMock.mock.calls[0][0];
    expect(sentPayload.raw_note).toContain("June family trip");
    expect(sentPayload.owner_note).toContain("Repeat traveler");
    expect(sentPayload.operating_mode).toBe("normal_intake");
    expect(sentPayload.stage).toBe("discovery");

    await waitFor(() => {
      expect(pushMock).toHaveBeenCalledWith("/workspace/TRIP-123/packet");
    });

    fireEvent.click(screen.getByRole("button", { name: /Save changes/i }));
    await waitFor(() => {
      expect(mutateMock).toHaveBeenCalledWith(
        "TRIP-123",
        expect.objectContaining({
          customerMessage: "Customer asks for June family trip with kid activities",
          agentNotes: "Repeat traveler. Prioritize Sentosa options.",
        }),
      );
    });

    vi.mocked(tripHooks.useTrips).mockReturnValue({
      data: [],
      total: 0,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    } as any);

    render(<WorkspacesPage />);
    const returnInbox = screen.getByRole("link", { name: /Go to Inbox/i });
    expect(returnInbox).toHaveAttribute("href", "/inbox");
  });
});
