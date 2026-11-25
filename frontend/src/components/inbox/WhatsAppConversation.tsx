'use client';

import { useEffect, useRef, useState } from 'react';
import { api } from '@/lib/api-client';
import { useAuthStore } from '@/stores/auth';
import type { ChannelMessage } from './ChannelMessagesPanel';

interface Reply {
  id: string;
  body: string;
  state: string;
  created_at?: number;
  delivery_status?: string | null;
}

interface Conversation {
  traveler: string;
  staff_id: string | null;
  replies: Reply[];
}

const BUTTON = 'rounded-lg border border-[#30363d] px-2.5 py-1 text-ui-xs text-[#58a6ff] hover:bg-[#1c2431] disabled:opacity-50';
export const REPLY_STATUS: Record<string, string> = {
  QUEUED: 'Draft awaiting approval',
  SUPPRESSED: 'Suppressed by staff takeover',
  SENDING: 'Waiting for provider response',
  SENT: 'Accepted by WhatsApp',
  sent: 'Sent by WhatsApp',
  delivered: 'Delivered',
  read: 'Read',
  failed: 'WhatsApp reported delivery failure',
  FAILED: 'Provider rejected the reply',
  DELIVERY_UNKNOWN: 'Delivery unknown. Check WhatsApp before sending again.',
  NOT_CONFIGURED: 'WhatsApp transport is disconnected',
  STAFF_REVIEW_REQUIRED: 'Staff review needed before sending',
};

export default function WhatsAppConversation({ conversationId, inboundMessages = [], onUseForIntake, onClose, onChange }: {
  conversationId: string;
  inboundMessages?: ChannelMessage[];
  onUseForIntake?: (body: string) => void;
  onClose: () => void;
  onChange: () => Promise<void>;
}) {
  const url = `/api/v1/messaging/whatsapp/${encodeURIComponent(conversationId)}`;
  const [conversation, setConversation] = useState<Conversation | null>(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [content, setContent] = useState('');
  const actorId = useAuthStore((state) => state.user?.id);
  const closeButton = useRef<HTMLButtonElement>(null);
  const pending = useRef<{ content: string; id: string } | null>(null);

  useEffect(() => {
    closeButton.current?.focus();
  }, [conversationId]);

  useEffect(() => {
    let active = true;
    void api.get<Conversation>(url, { cache: 'no-store' }).then((value) => {
      if (active) setConversation(value);
    }).catch((err: unknown) => {
      if (active) setError(err instanceof Error ? err.message : 'Could not open the conversation');
    });
    return () => { active = false; };
  }, [url]);

  async function perform(action?: () => Promise<unknown>) {
    setBusy(true);
    setError('');
    try {
      await action?.();
      setConversation(await api.get<Conversation>(url, { cache: 'no-store' }));
      await onChange();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'WhatsApp action unavailable');
    } finally {
      setBusy(false);
    }
  }

  async function send() {
    const text = content.trim();
    if (!text) return;
    const attempt = pending.current?.content === text ? pending.current : { content: text, id: crypto.randomUUID() };
    pending.current = attempt;
    await api.post<Reply>(`${url}/replies`, { content: text, request_id: attempt.id });
    pending.current = null;
    setContent('');
  }

  const isOwner = Boolean(actorId && conversation?.staff_id === actorId);
  const timeline = [
    ...inboundMessages.map((message) => ({ id: message.message_id, timestamp: Date.parse(message.received_at), message })),
    ...(conversation?.replies ?? []).map((reply) => ({ id: reply.id, timestamp: (reply.created_at ?? 0) * 1000, reply })),
  ].sort((left, right) => left.timestamp - right.timestamp);

  return (
    <section aria-label='WhatsApp conversation' className='min-w-0 space-y-3 border-t border-[#30363d] p-4 text-[#e6edf3]'>
      <div className='flex flex-wrap items-center justify-between gap-2'>
        <h3 className='text-ui-sm font-semibold'>WhatsApp conversation{conversation ? ` · ${conversation.traveler}` : ''}</h3>
        <button type='button' ref={closeButton} className={BUTTON} onClick={onClose} disabled={busy}>Back to conversations</button>
      </div>
      {error && <p role='alert' className='text-ui-xs text-red-400'>{error}</p>}
      {!conversation && !error && <p className='text-ui-xs'>Loading conversation…</p>}
      {conversation && (
        <>
          <div className='flex flex-wrap items-center gap-2'>
            <p role='status' className='text-ui-xs'>{conversation.staff_id ? (isOwner ? 'You own replies' : 'Another staff member owns replies') : 'Assistant can draft replies'}</p>
            {(!conversation.staff_id || isOwner) && (
              <button type='button' className={BUTTON} disabled={busy} onClick={() => void perform(() => api.post(`${url}/ownership`, { action: conversation.staff_id ? 'release' : 'takeover' }))}>
                {conversation.staff_id ? 'Release to assistant' : 'Take over replies'}
              </button>
            )}
            <button type='button' className={BUTTON} disabled={busy} onClick={() => void perform()}>Refresh conversation</button>
          </div>
          {timeline.length > 0 && (
            <ol aria-label='Recent conversation messages' className='max-h-[45vh] space-y-3 overflow-y-auto px-1 py-2'>
              {timeline.map((entry) => {
                if ('message' in entry) {
                  const { message } = entry;
                  return (
                    <li key={entry.id} className='mr-auto w-fit max-w-[90%] space-y-1 rounded-lg bg-[#161b22] px-3 py-2'>
                      <p className='text-ui-xs text-[#aab4bf]'>
                        Traveler{message.received_at && <> · <time dateTime={message.received_at}>{new Date(message.received_at).toLocaleString()}</time></>}
                      </p>
                      <p className='whitespace-pre-wrap break-words text-ui-sm'>{message.body || 'Media message'}</p>
                      {message.filename && <p className='break-words text-ui-xs text-[#aab4bf]'>{message.filename}</p>}
                      {message.processing_state === 'review_required' && <p className='text-ui-xs text-amber-300'>Staff review needed</p>}
                      {message.trip_id ? (
                        <a className={BUTTON} href={`/trips/${message.trip_id}`}>Open trip</a>
                      ) : message.processing_state === 'review_required' && message.body.trim() && onUseForIntake && (
                        <button type='button' className={BUTTON} onClick={() => onUseForIntake(message.body)}>Use for intake</button>
                      )}
                    </li>
                  );
                }
                const { reply } = entry;
                return (
                  <li key={reply.id} className='ml-auto w-fit max-w-[90%] space-y-1 rounded-lg border border-[#30363d] bg-[#151e2a] px-3 py-2'>
                    <p className='text-ui-xs text-[#aab4bf]'>
                      Waypoint{reply.created_at ? <> · <time dateTime={new Date(reply.created_at * 1000).toISOString()}>{new Date(reply.created_at * 1000).toLocaleString()}</time></> : null}
                    </p>
                    <p className='whitespace-pre-wrap break-words text-ui-sm'>{reply.body}</p>
                    <p className='text-ui-xs text-[#8b949e]'>{REPLY_STATUS[reply.delivery_status ?? reply.state] ?? 'Status unavailable'}</p>
                    {reply.state === 'QUEUED' && !conversation.staff_id && (
                      <button type='button' className={BUTTON} disabled={busy} onClick={() => void perform(() => api.post(`${url}/replies/${encodeURIComponent(reply.id)}/dispatch`, {}))}>
                        Approve and send draft
                      </button>
                    )}
                  </li>
                );
              })}
            </ol>
          )}
          {isOwner && (
            <form className='space-y-2' onSubmit={(event) => { event.preventDefault(); void perform(send); }}>
              <label className='block text-ui-xs' htmlFor='whatsapp-staff-reply'>Staff reply</label>
              <textarea id='whatsapp-staff-reply' className='w-full rounded-lg border border-[#30363d] bg-[#0f1115] p-2 text-ui-sm' maxLength={4096} value={content} disabled={busy} onChange={(event) => setContent(event.target.value)} />
              <button type='submit' className={BUTTON} disabled={busy || !content.trim()}>Send staff reply</button>
            </form>
          )}
        </>
      )}
    </section>
  );
}
