'use client';

import { useCallback, useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { ArrowRight, Building2, MessageSquare, Paperclip, Phone, Mail } from 'lucide-react';
import { useWorkbenchStore } from '@/stores/workbench';

// T6 (FND-0305): real channel-message feed for the inbox. Renders what the
// messaging webhook persisted (spine_api/services/message_store.py) — the
// traveler messages the system ingests but operators could never see. Honest
// empty state when no channel messages have arrived yet.
//
// Message→intake hand-off (operator-surface tranche 2026-11-03): inbound
// messages carry a "Use for intake" action that hands the message body to the
// workbench intake tab via the workbench store's pending_intake_prefill —
// closing the paste-only intake gap without a second intake door. Media-only
// messages (a filename with no extractable text) honestly disable the action.

export interface ChannelMessage {
  message_id: string;
  trip_id: string | null;
  channel: string;
  direction: 'inbound' | 'outbound';
  from_party: string;
  to_party: string;
  body: string;
  mime?: string | null;
  filename?: string | null;
  received_at: string;
}

const CHANNEL_ICON: Record<string, typeof MessageSquare> = {
  whatsapp: MessageSquare,
  sms: Phone,
  email: Mail,
  vendor_email: Building2,
};

const CHANNEL_LABEL: Record<string, string> = {
  whatsapp: 'WhatsApp',
  sms: 'SMS',
  vendor_email: 'Vendor quote',
  email: 'Email',
};

export default function ChannelMessagesPanel() {
  const [messages, setMessages] = useState<ChannelMessage[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const router = useRouter();
  const setPendingIntakePrefill = useWorkbenchStore((s) => s.setPendingIntakePrefill);

  const handleUseForIntake = (body: string) => {
    setPendingIntakePrefill(body);
    router.push('/inquiries/new?draft=new&tab=intake');
  };

  // FND-0406 (2026-11-07): the feed was one-shot on mount — new arrivals were
  // invisible until a page reload. Load function + manual refresh + 15s poll
  // keep the triage feed live without a second full-page mount.
  const loadMessages = useCallback(async (): Promise<void> => {
    try {
      const res = await fetch('/api/v1/messages?limit=50');
      if (!res.ok) throw new Error(`Message feed unavailable (${res.status})`);
      const data: { messages: ChannelMessage[] } = await res.json();
      setMessages(data.messages);
      setError(null);
    } catch (err: Error | unknown) {
      setError(err instanceof Error ? err.message : 'Message feed unavailable');
    }
  }, []);

  useEffect(() => {
    let cancelled = false;
    const run = async () => {
      await loadMessages();
      if (cancelled) return;
      setIsRefreshing(false);
    };
    setIsRefreshing(true);
    void run();
    return () => {
      cancelled = true;
    };
  }, [loadMessages]);

  useEffect(() => {
    const interval = setInterval(() => {
      void loadMessages();
    }, 15_000);
    return () => clearInterval(interval);
  }, [loadMessages]);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await loadMessages();
    setIsRefreshing(false);
  };

  if (error) {
    return (
      <div role='alert' data-testid='channel-messages-error' className='rounded-lg border border-red-500/20 bg-red-500/10 p-3 text-ui-xs text-red-400'>
        {error}
      </div>
    );
  }

  if (messages === null) {
    return (
      <div className='rounded-lg border border-[#30363d] bg-[#0f1115] p-4 text-ui-xs text-[#8b949e]'>
        Loading channel messages…
      </div>
    );
  }

  return (
    <div data-testid='channel-messages-panel' className='rounded-lg border border-[#30363d] bg-[#0f1115] overflow-hidden'>
      <div className='px-4 py-3 border-b border-[#30363d] bg-[#161b22] flex items-center justify-between'>
        <div className='flex items-center gap-2 text-ui-sm font-semibold text-[#e6edf3]'>
          <MessageSquare className='size-4 text-[#58a6ff]' />
          Channel Messages
        </div>
        <div className='flex items-center gap-2'>
          <span className='text-ui-xs text-[#484f58]'>{messages.length} recent</span>
          <button
            type='button'
            onClick={handleRefresh}
            disabled={isRefreshing}
            className='rounded-lg border border-[#30363d] bg-[#161b22] px-2 py-1 text-[11px] font-medium text-[#58a6ff] transition-colors hover:bg-[#1c2431] disabled:opacity-50'
            data-testid='channel-messages-refresh'
          >
            {isRefreshing ? 'Refreshing…' : 'Refresh'}
          </button>
        </div>
      </div>

      {messages.length === 0 ? (
        <p className='p-4 text-ui-sm text-[#8b949e]'>
          No channel messages have arrived yet. Inbound WhatsApp/SMS messages and vendor quote emails received through the
          messaging webhook appear here for triage.
        </p>
      ) : (
        <ul className='divide-y divide-[#21262d] max-h-96 overflow-y-auto'>
          {messages.map((m) => {
            const Icon = CHANNEL_ICON[m.channel] ?? MessageSquare;
            return (
              <li key={m.message_id} className='px-4 py-3 flex items-start gap-3' data-testid='channel-message-row'>
                <span
                  className={`mt-0.5 inline-flex items-center rounded-full px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${
                    m.direction === 'inbound' ? 'bg-[#58a6ff]/10 text-[#58a6ff]' : 'bg-[#3fb950]/10 text-[#3fb950]'
                  }`}
                >
                  <Icon className='size-3 mr-1' />
                  {CHANNEL_LABEL[m.channel] ?? m.channel} · {m.direction}
                </span>
                <div className='min-w-0 flex-1'>
                  <p className='text-ui-sm text-[#e6edf3] break-words'>
                    {m.body || <span className='text-[#484f58] italic'>media message{m.filename ? `: ${m.filename}` : ''}</span>}
                  </p>
                  {m.filename && (
                    <span
                      className='inline-flex items-center gap-1 mt-1 rounded-full bg-[#21262d] px-2 py-0.5 text-[10px] font-medium text-[#8b949e]'
                      data-testid='channel-message-attachment'
                      title={m.mime ?? undefined}
                    >
                      <Paperclip className='size-3' />
                      {m.filename}
                    </span>
                  )}
                  <p className='text-ui-xs text-[#484f58] mt-0.5'>
                    {m.from_party || 'unknown sender'}
                    {' · '}
                    {m.received_at ? new Date(m.received_at).toLocaleString() : ''}
                    {m.trip_id ? (
                      <>
                        {' · '}
                        <a href={`/trips/${m.trip_id}`} className='text-[#58a6ff] hover:underline'>
                          open trip
                        </a>
                      </>
                    ) : (
                      ' · unlinked'
                    )}
                  </p>
                </div>
                {m.direction === 'inbound' && m.body.trim() && (
                  <button
                    type='button'
                    onClick={() => handleUseForIntake(m.body)}
                    className='mt-0.5 inline-flex shrink-0 items-center gap-1 rounded-lg border border-[#30363d] bg-[#161b22] px-2 py-1 text-[11px] font-medium text-[#58a6ff] transition-colors hover:bg-[#1c2431]'
                    data-testid='channel-message-use-for-intake'
                    aria-label='Use this message for intake'
                  >
                    Use for intake
                    <ArrowRight className='size-3' />
                  </button>
                )}
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
