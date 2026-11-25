'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import { ArrowRight, Building2, ChevronDown, ChevronUp, MessageSquare, Paperclip, Phone, Mail } from 'lucide-react';
import { useWorkbenchStore } from '@/stores/workbench';
import { api, ApiException } from '@/lib/api-client';
import WhatsAppConversation, { REPLY_STATUS } from './WhatsAppConversation';

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
  conversation_id?: string | null;
  conversation_owner?: 'staff' | 'assistant' | null;
  processing_state?: string | null;
  dispatch_status?: string | null;
  delivery_status?: string | null;
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

export interface ChannelMessagesPanelProps {
  /** Collapse the multi-row feed into a compact header + latest-message bar. */
  defaultCollapsed?: boolean;
  scope?: 'all' | 'whatsapp' | 'other';
}

export default function ChannelMessagesPanel({ defaultCollapsed = false, scope = 'all' }: ChannelMessagesPanelProps = {}) {
  const [messages, setMessages] = useState<ChannelMessage[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isExpanded, setIsExpanded] = useState(!defaultCollapsed);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const selectedRow = useRef<HTMLButtonElement | null>(null);
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
      const query = scope === 'whatsapp' ? 'limit=50&channel=whatsapp' : 'limit=50';
      const data = await api.get<{ messages: ChannelMessage[] }>(`/api/v1/messages?${query}`);
      setMessages(scope === 'other' ? data.messages.filter((message) => message.channel !== 'whatsapp') : data.messages);
      setError(null);
    } catch (err: Error | unknown) {
      setError(err instanceof ApiException ? `Message feed unavailable (${err.status})` : 'Message feed unavailable');
    }
  }, [scope]);

  useEffect(() => {
    let cancelled = false;
    const run = async () => {
      await loadMessages();
      if (cancelled) return;
      setIsRefreshing(false);
    };
    const timer = window.setTimeout(() => {
      if (!cancelled) {
        setIsRefreshing(true);
        void run();
      }
    }, 0);
    return () => {
      cancelled = true;
      window.clearTimeout(timer);
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

  if (error && messages === null) {
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

  const threads = new Map<string, ChannelMessage[]>();
  if (scope === 'whatsapp') {
    for (const message of messages) {
      if (!message.conversation_id) continue;
      const thread = threads.get(message.conversation_id);
      if (thread) thread.push(message);
      else threads.set(message.conversation_id, [message]);
    }
  }
  const feedMessages = threads.size ? messages.filter((message) => !message.conversation_id) : messages;
  const currentThread = conversationId ? threads.get(conversationId) : undefined;
  const closeThread = () => {
    setConversationId(null);
    window.requestAnimationFrame(() => selectedRow.current?.focus());
  };
  const latestMessage = feedMessages.find((m) => m.direction === 'inbound' && m.body.trim()) ?? feedMessages[0] ?? null;
  const emptyMessage = {
    all: 'No channel messages have arrived yet. Incoming WhatsApp, SMS and vendor messages appear here.',
    whatsapp: 'No WhatsApp messages have arrived yet.',
    other: 'No other channel messages in the recent feed.',
  }[scope];

  return (
    <>
      {error && <p role='status' className='px-1 text-ui-xs text-amber-300'>Refresh failed. Showing the last loaded messages.</p>}
      {threads.size > 0 && (
        <div className='grid overflow-hidden rounded-lg border border-[#30363d] bg-[#0f1115] md:grid-cols-[minmax(14rem,19rem)_minmax(0,1fr)]'>
          <section aria-label='Recent WhatsApp conversations' className={`${currentThread ? 'hidden md:block' : ''} min-w-0 md:border-r md:border-[#30363d]`}>
            <div className='flex items-center justify-between gap-2 border-b border-[#30363d] px-4 py-3'>
              <h3 className='text-ui-sm font-medium text-[#e6edf3]'>Recent conversations</h3>
              <button type='button' disabled={isRefreshing} onClick={() => void handleRefresh()} className='rounded px-2 py-1 text-ui-xs text-[#58a6ff] hover:bg-[#21262d]'>
                {isRefreshing ? 'Refreshing…' : 'Refresh'}
              </button>
            </div>
            <ul className='max-h-[65vh] divide-y divide-[#21262d] overflow-y-auto'>
              {Array.from(threads, ([id, thread]) => {
                const latest = thread[0];
                const traveler = latest.direction === 'inbound' ? latest.from_party : latest.to_party;
                const owner = latest.conversation_owner === 'staff' ? 'Staff owns replies' : latest.conversation_owner === 'assistant' ? 'Assistant can draft' : '';
                return (
                  <li key={id}>
                    <button
                      type='button'
                      aria-label={`Open conversation with ${traveler || 'unknown traveler'}`}
                      aria-current={conversationId === id ? 'true' : undefined}
                      onClick={(event) => {
                        selectedRow.current = event.currentTarget;
                        setConversationId(id);
                      }}
                      className='grid w-full gap-1 border-l-2 border-transparent px-3 py-3 text-left hover:bg-[#161b22] focus-visible:outline focus-visible:-outline-offset-2 focus-visible:outline-[#58a6ff] aria-[current=true]:border-[#58a6ff] aria-[current=true]:bg-[#161b22]'
                    >
                      <span className='flex items-baseline justify-between gap-2'>
                        <span className='truncate text-ui-sm font-medium text-[#e6edf3]'>{traveler || 'Unknown traveler'}</span>
                        {latest.received_at && <time dateTime={latest.received_at} className='shrink-0 text-ui-xs text-[#8b949e]'>{new Date(latest.received_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}</time>}
                      </span>
                      <span className='truncate text-ui-xs text-[#aab4bf]'>{latest.body || latest.filename || 'Media message'}</span>
                      <span className='text-ui-xs text-[#8b949e]'>
                        {REPLY_STATUS[latest.delivery_status ?? latest.dispatch_status ?? ''] ?? (latest.processing_state === 'review_required' ? 'Staff review needed' : owner)}
                      </span>
                    </button>
                  </li>
                );
              })}
            </ul>
          </section>
          {currentThread && conversationId ? (
            <WhatsAppConversation
              key={conversationId}
              conversationId={conversationId}
              inboundMessages={currentThread.filter((message) => message.direction === 'inbound')}
              onUseForIntake={handleUseForIntake}
              onClose={closeThread}
              onChange={loadMessages}
            />
          ) : (
            <p className='hidden min-h-72 place-items-center p-6 text-ui-sm text-[#8b949e] md:grid'>Select a conversation to see messages and reply controls.</p>
          )}
        </div>
      )}
      {(!threads.size || feedMessages.length > 0) && (
      <div data-testid='channel-messages-panel' className='rounded-lg border border-[#30363d] bg-[#0f1115] overflow-hidden'>
        <div className={`px-4 py-2.5 bg-[#161b22] flex items-center justify-between gap-3 ${isExpanded || latestMessage ? 'border-b border-[#30363d]' : ''}`}>
          <div className='flex items-center gap-2 text-ui-sm font-semibold text-[#e6edf3]'>
            <MessageSquare className='size-4 text-[#58a6ff]' />
            <span>{scope === 'whatsapp' ? 'Recent messages' : 'Channel Messages'}</span>
            <span className='text-ui-xs font-normal text-[#8b949e]'>
              · {feedMessages.length.toLocaleString('en-IN')} recent
            </span>
          </div>
          <div className='flex items-center gap-2'>
            <button
              type='button'
              onClick={handleRefresh}
              disabled={isRefreshing}
              className='rounded-lg border border-[#30363d] bg-[#0f1115] px-2.5 py-1 text-[11px] font-medium text-[#58a6ff] transition-colors hover:bg-[#1c2431] disabled:opacity-50'
              data-testid='channel-messages-refresh'
            >
              {isRefreshing ? 'Refreshing…' : 'Refresh'}
            </button>
            <button
              type='button'
              onClick={() => setIsExpanded((prev) => !prev)}
              aria-expanded={isExpanded}
              data-testid='channel-messages-toggle'
              className='inline-flex items-center gap-1 rounded-lg border border-[#30363d] bg-[#0f1115] px-2.5 py-1 text-[11px] font-medium text-[#e6edf3] transition-colors hover:bg-[#1c2431]'
            >
              {isExpanded ? (
                <>
                  Hide feed
                  <ChevronUp className='size-3.5 text-[#8b949e]' />
              </>
            ) : (
              <>
                {feedMessages.length > 0 ? `Show feed (${feedMessages.length.toLocaleString('en-IN')})` : 'Show feed'}
                <ChevronDown className='size-3.5 text-[#8b949e]' />
              </>
            )}
          </button>
        </div>
      </div>

      {!isExpanded ? (
        latestMessage ? (
          <div
            data-testid='channel-messages-collapsed-summary'
            className='px-4 py-2 flex items-center justify-between gap-3 bg-[#0f1115]'
          >
            <div className='min-w-0 flex items-center gap-2.5 text-ui-xs'>
              <span
                className={`inline-flex shrink-0 items-center rounded-full px-2 py-0.5 text-[10px] font-medium ${
                  latestMessage.direction === 'inbound' ? 'bg-[#58a6ff]/10 text-[#58a6ff]' : 'bg-[#3fb950]/10 text-[#3fb950]'
                }`}
              >
                {CHANNEL_LABEL[latestMessage.channel] ?? latestMessage.channel} · {latestMessage.direction}
              </span>
              <span className='text-[#8b949e] shrink-0'>
                {latestMessage.from_party || 'unknown sender'}
              </span>
              <span className='text-[#e6edf3] truncate'>
                {latestMessage.body || (latestMessage.filename ? `media message: ${latestMessage.filename}` : 'media message')}
              </span>
            </div>
            {latestMessage.direction === 'inbound' && latestMessage.conversation_id ? (
              <button
                type='button'
                onClick={() => { setIsExpanded(true); setConversationId(latestMessage.conversation_id ?? null); }}
                className='shrink-0 rounded-lg border border-[#30363d] px-2 py-1 text-ui-xs text-[#58a6ff] hover:bg-[#1c2431]'
              >
                Open conversation
              </button>
            ) : latestMessage.direction === 'inbound' && latestMessage.body.trim() && (
              <button
                type='button'
                onClick={() => handleUseForIntake(latestMessage.body)}
                className='inline-flex shrink-0 items-center gap-1 rounded-lg border border-[#30363d] bg-[#161b22] px-2.5 py-1 text-[11px] font-medium text-[#58a6ff] transition-colors hover:bg-[#1c2431]'
                data-testid='channel-message-use-for-intake'
                aria-label='Use latest message for intake'
              >
                Use for intake
                <ArrowRight className='size-3' />
              </button>
            )}
          </div>
        ) : (
          <p className='px-4 py-2 text-ui-xs text-[#8b949e]'>
            {emptyMessage}
          </p>
        )
      ) : feedMessages.length === 0 ? (
        <p className='p-4 text-ui-sm text-[#8b949e]'>
          {emptyMessage}
        </p>
      ) : (
        <ul className='divide-y divide-[#21262d] max-h-96 overflow-y-auto'>
          {feedMessages.map((m) => {
            const Icon = CHANNEL_ICON[m.channel] ?? MessageSquare;
            const replyStatus = REPLY_STATUS[m.delivery_status ?? m.dispatch_status ?? ''];
            const draft = m.dispatch_status === 'QUEUED' || m.dispatch_status === 'SUPPRESSED';
            return (
              <li key={m.message_id} className='px-4 py-3 flex items-start gap-3' data-testid='channel-message-row'>
                <span
                  className={`mt-0.5 inline-flex items-center rounded-full px-1.5 py-0.5 text-[10px] font-medium ${
                    m.direction === 'inbound' ? 'bg-[#58a6ff]/10 text-[#58a6ff]' : 'bg-[#21262d] text-[#8b949e]'
                  }`}
                >
                  <Icon className='size-3 mr-1' />
                  {CHANNEL_LABEL[m.channel] ?? m.channel} · {draft ? 'draft' : m.direction}
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
                  {m.processing_state === 'review_required' && (
                    <p className='mt-1 text-ui-xs text-amber-300'>Staff review needed</p>
                  )}
                  {replyStatus && <p className='mt-1 text-ui-xs text-[#8b949e]'>{replyStatus}</p>}
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
                {m.direction === 'inbound' && m.conversation_id && (
                  <button
                    type='button'
                    onClick={() => setConversationId(m.conversation_id ?? null)}
                    className='mt-0.5 shrink-0 rounded-lg border border-[#30363d] px-2 py-1 text-ui-xs text-[#58a6ff] hover:bg-[#1c2431]'
                  >
                    Open conversation
                  </button>
                )}
                {m.direction === 'inbound' && m.body.trim() && (!m.conversation_id || (m.processing_state === 'review_required' && !m.trip_id)) && (
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
      {conversationId && !currentThread && (
        <WhatsAppConversation
          key={conversationId}
          conversationId={conversationId}
          onClose={closeThread}
          onChange={loadMessages}
        />
      )}
    </div>
    )}
    </>
  );
}
