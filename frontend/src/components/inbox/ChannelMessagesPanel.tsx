'use client';

import { useEffect, useState } from 'react';
import { MessageSquare, Phone, Mail } from 'lucide-react';

// T6 (FND-0305): real channel-message feed for the inbox. Renders what the
// messaging webhook persisted (spine_api/services/message_store.py) — the
// traveler messages the system ingests but operators could never see. Honest
// empty state when no channel messages have arrived yet.

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
};

const CHANNEL_LABEL: Record<string, string> = {
  whatsapp: 'WhatsApp',
  sms: 'SMS',
  email: 'Email',
};

export default function ChannelMessagesPanel() {
  const [messages, setMessages] = useState<ChannelMessage[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetch('/api/v1/messages?limit=50')
      .then(async (res) => {
        if (!res.ok) throw new Error(`Message feed unavailable (${res.status})`);
        return res.json();
      })
      .then((data: { messages: ChannelMessage[] }) => {
        if (!cancelled) setMessages(data.messages);
      })
      .catch((err: Error) => {
        if (!cancelled) setError(err.message);
      });
    return () => {
      cancelled = true;
    };
  }, []);

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
        <span className='text-ui-xs text-[#484f58]'>{messages.length} recent</span>
      </div>

      {messages.length === 0 ? (
        <p className='p-4 text-ui-sm text-[#8b949e]'>
          No channel messages have arrived yet. Inbound WhatsApp/SMS messages received through the
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
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
