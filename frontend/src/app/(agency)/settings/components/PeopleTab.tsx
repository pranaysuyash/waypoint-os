'use client';

import { useState } from 'react';
import { Copy, RefreshCw, Users, Check, AlertCircle, Shield } from 'lucide-react';
import { useWorkspace } from '@/hooks/useGovernance';
import { useTeamMembers } from '@/hooks/useGovernance';

// ── WorkspaceCodePanel ────────────────────────────────────────────────────────

function WorkspaceCodePanel() {
  const {
    data: workspace,
    isLoading,
    error,
    workspaceState,
    canViewWorkspaceInvites,
    canGenerateWorkspaceInvite,
    workspaceUnavailableTransient,
    generateCode,
    refetch,
  } = useWorkspace();
  const [copied, setCopied] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [generateError, setGenerateError] = useState<string | null>(null);
  const [generatedCode, setGeneratedCode] = useState<string | null>(null);

  const code = generatedCode ?? workspace?.workspace_code ?? null;
  const joinUrl = code ? `${window.location.origin}/join/${code}` : null;
  const isPermissionError = workspaceState === "forbidden" || !canViewWorkspaceInvites;

  async function handleCopy() {
    if (!joinUrl) return;
    try {
      await navigator.clipboard.writeText(joinUrl);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Clipboard API unavailable - fall back to selection
    }
  }

  async function handleRegenerate() {
    setIsGenerating(true);
    setGenerateError(null);
    try {
      const newCode = await generateCode('internal');
      setGeneratedCode(newCode);
    } catch (err) {
      setGenerateError(err instanceof Error ? err.message : 'Failed to regenerate code');
    } finally {
      setIsGenerating(false);
    }
  }

  if (isLoading) {
    return (
      <div className="rounded-xl border border-[#1c2128] bg-[#0f1115] p-6">
        <div className="h-4 w-32 rounded bg-[#1c2128] animate-pulse mb-3" />
        <div className="h-10 w-full rounded bg-[#1c2128] animate-pulse" />
      </div>
    );
  }

  if (workspaceState === "unauthenticated" && !joinUrl) {
    return (
      <div className="rounded-xl border border-[#d29922]/30 bg-[#d29922]/10 p-4 space-y-3">
        <div className="flex items-center gap-2 text-ui-sm text-[#d29922]">
          <AlertCircle className="size-4 shrink-0" />
          Your session expired. Sign in again to manage workspace invites.
        </div>
        <button
          onClick={() => refetch()}
          className="px-3 py-1.5 rounded border border-[#30363d] text-ui-xs text-[#e6edf3] hover:bg-[#1c2128] transition-colors"
        >
          Retry
        </button>
      </div>
    );
  }

  if ((workspaceState === "forbidden" || workspaceState === "error") && !joinUrl) {
    return (
      <div className="rounded-xl border border-[#f85149]/30 bg-[#f85149]/10 p-4 space-y-3">
        <div className="flex items-center gap-2 text-ui-sm text-[#f85149]">
          <AlertCircle className="size-4 shrink-0" />
          {isPermissionError
            ? 'You do not have permission to view workspace invites.'
            : `Failed to load workspace: ${error?.message ?? "Unknown error"}`}
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => refetch()}
            className="px-3 py-1.5 rounded border border-[#30363d] text-ui-xs text-[#e6edf3] hover:bg-[#1c2128] transition-colors"
          >
            Retry
          </button>
          {!isPermissionError && canGenerateWorkspaceInvite && (
            <button
              onClick={handleRegenerate}
              disabled={isGenerating}
              className="px-3 py-1.5 rounded border border-[#30363d] text-ui-xs text-[#e6edf3] hover:bg-[#1c2128] transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
            >
              {isGenerating ? 'Generating…' : 'Generate invite link'}
            </button>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-[#1c2128] bg-[#0f1115] p-6 space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-ui-base font-semibold text-[#e6edf3]">Invitation Link</h3>
          <p className="text-ui-sm text-[#8b949e] mt-0.5">
            Share this link so agents can join your workspace. Generating a new link revokes the old one.
          </p>
        </div>
      </div>

      {(workspaceUnavailableTransient || workspaceState === "forbidden" || workspaceState === "unauthenticated") && joinUrl && (
        <div className="flex items-center gap-2 rounded-lg border border-[#d29922]/30 bg-[#d29922]/10 p-3 text-ui-sm text-[#d29922]">
          <AlertCircle className="size-4 shrink-0" />
          Workspace details could not be refreshed. Your current invite link still works.
        </div>
      )}

      {generateError && (
        <div className="flex items-center gap-2 rounded-lg border border-[#f85149]/30 bg-[#f85149]/10 p-3 text-ui-sm text-[#f85149]">
          <AlertCircle className="size-4 shrink-0" />
          {generateError}
        </div>
      )}

      {joinUrl ? (
        <div className="flex items-center gap-2">
          <div className="flex-1 rounded-lg border border-[#30363d] bg-[#161b22] px-3 py-2 text-ui-sm text-[#8b949e] font-mono truncate">
            {joinUrl}
          </div>
          <button
            onClick={handleCopy}
            className="flex items-center gap-1.5 px-3 py-2 rounded-lg border border-[#30363d] text-ui-sm text-[#e6edf3] hover:bg-[#1c2128] transition-colors shrink-0"
            title="Copy invitation link"
          >
            {copied ? <Check className="size-4 text-[#3fb950]" /> : <Copy className="size-4" />}
            {copied ? 'Copied' : 'Copy'}
          </button>
          <button
            onClick={handleRegenerate}
            disabled={isGenerating || !canGenerateWorkspaceInvite}
            className="flex items-center gap-1.5 px-3 py-2 rounded-lg border border-[#30363d] text-ui-sm text-[#e6edf3] hover:bg-[#1c2128] transition-colors shrink-0 disabled:opacity-40 disabled:cursor-not-allowed"
            title="Generate new invitation link (revokes current)"
          >
            <RefreshCw className={`size-4 ${isGenerating ? 'animate-spin' : ''}`} />
            {isGenerating ? 'Regenerating…' : 'New link'}
          </button>
        </div>
      ) : (
        <div className="flex items-center gap-3">
          <p className="text-ui-sm text-[#8b949e] flex-1">No active invitation link. Generate one to start onboarding agents.</p>
          <button
            onClick={handleRegenerate}
            disabled={isGenerating || !canGenerateWorkspaceInvite}
            className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-[#58a6ff] text-[#0d1117] text-ui-sm font-medium hover:bg-[#79b8ff] transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
          >
            <RefreshCw className={`size-4 ${isGenerating ? 'animate-spin' : ''}`} />
            Generate link
          </button>
        </div>
      )}
    </div>
  );
}

// ── TeamMemberList ────────────────────────────────────────────────────────────

const ROLE_LABELS: Record<string, string> = {
  owner: 'Owner',
  admin: 'Admin',
  senior_agent: 'Senior Agent',
  junior_agent: 'Junior Agent',
  viewer: 'Viewer',
};

const ROLE_COLORS: Record<string, string> = {
  owner: 'text-[#d2a8ff] bg-[#d2a8ff]/10 border-[#d2a8ff]/20',
  admin: 'text-[#58a6ff] bg-[#58a6ff]/10 border-[#58a6ff]/20',
  senior_agent: 'text-[#3fb950] bg-[#3fb950]/10 border-[#3fb950]/20',
  junior_agent: 'text-[#8b949e] bg-[#8b949e]/10 border-[#8b949e]/20',
  viewer: 'text-[#8b949e] bg-[#8b949e]/10 border-[#8b949e]/20',
};

function TeamMemberList() {
  const { data: members, isLoading, error, teamMembersState, canViewTeamMembers, refetch } = useTeamMembers();

  if (isLoading) {
    return (
      <div className="space-y-2">
        {['team-skeleton-1', 'team-skeleton-2', 'team-skeleton-3'].map((skeletonKey) => (
          <div key={skeletonKey} className="h-14 rounded-lg bg-[#161b22] animate-pulse" />
        ))}
      </div>
    );
  }

  if (teamMembersState === "unauthenticated") {
    return (
      <div className="rounded-lg border border-[#d29922]/30 bg-[#d29922]/10 p-3 space-y-2">
        <div className="flex items-center gap-2 text-ui-sm text-[#d29922]">
          <AlertCircle className="size-4" />
          Your session expired. Sign in again to view team members.
        </div>
        <button
          onClick={() => refetch()}
          className="px-3 py-1.5 rounded border border-[#30363d] text-ui-xs text-[#e6edf3] hover:bg-[#1c2128] transition-colors"
        >
          Retry
        </button>
      </div>
    );
  }

  if (teamMembersState === "forbidden" || !canViewTeamMembers) {
    return (
      <div className="flex items-center gap-2 text-ui-sm text-[#f85149]">
        <AlertCircle className="size-4" />
        You do not have permission to view team members.
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-lg border border-[#f85149]/30 bg-[#f85149]/10 p-3 space-y-2">
        <div className="flex items-center gap-2 text-ui-sm text-[#f85149]">
          <AlertCircle className="size-4" />
          Failed to load team members: {error.message}
        </div>
        <button
          onClick={() => refetch()}
          className="px-3 py-1.5 rounded border border-[#30363d] text-ui-xs text-[#e6edf3] hover:bg-[#1c2128] transition-colors"
        >
          Retry
        </button>
      </div>
    );
  }

  if (members.length === 0) {
    return (
      <div className="flex flex-col items-center gap-2 py-8 text-center">
        <Users className="size-8 text-[#30363d]" />
        <p className="text-ui-sm text-[#8b949e]">No team members yet.</p>
        <p className="text-ui-xs text-[#6e7681]">Share the invitation link above to onboard your first agent.</p>
      </div>
    );
  }

  return (
    <div className="space-y-1">
      {members.map((member) => {
        const roleKey = member.role?.toLowerCase() ?? 'viewer';
        const roleLabel = ROLE_LABELS[roleKey] ?? member.role;
        const roleColor = ROLE_COLORS[roleKey] ?? ROLE_COLORS.viewer;
        return (
          <div
            key={member.id}
            className="flex items-center gap-3 p-3 rounded-lg hover:bg-[#161b22] transition-colors"
          >
            <div className="size-8 rounded-full bg-[#1c2128] border border-[#30363d] flex items-center justify-center shrink-0">
              <span className="text-ui-xs font-semibold text-[#8b949e]">
                {(member.name ?? member.email ?? '?')[0].toUpperCase()}
              </span>
            </div>
            <div className="flex-1 min-w-0">
              <div className="text-ui-sm font-medium text-[#e6edf3] truncate">{member.name ?? member.email}</div>
              {member.name && (
                <div className="text-ui-xs text-[#8b949e] truncate">{member.email}</div>
              )}
            </div>
            <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded border text-ui-xs font-medium ${roleColor}`}>
              {roleKey === 'owner' || roleKey === 'admin' ? (
                <Shield className="size-3" />
              ) : null}
              {roleLabel}
            </span>
          </div>
        );
      })}
    </div>
  );
}

// ── PeopleTab (exported) ──────────────────────────────────────────────────────

export function PeopleTab() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-ui-base font-semibold text-[#e6edf3]">Onboarding</h2>
        <p className="text-ui-sm text-[#8b949e] mt-1">
          Invite agents to join your workspace using a shareable link.
        </p>
      </div>

      <WorkspaceCodePanel />

      <div>
        <h2 className="text-ui-base font-semibold text-[#e6edf3] mb-4">Team Members</h2>
        <TeamMemberList />
      </div>
    </div>
  );
}
