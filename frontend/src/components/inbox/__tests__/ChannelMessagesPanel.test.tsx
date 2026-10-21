// @vitest-environment jsdom

import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import ChannelMessagesPanel from '../ChannelMessagesPanel';

// T6 (FND-0305): the inbox channel-messages panel renders the real webhook-
// stored feed with honest empty and error states — no sample content.

const MESSAGES = [
  {
    message_id: 'msg_1',
    trip_id: 'trip_9',
    channel: 'whatsapp',
    direction: 'inbound',
    from_party: '+919820000111',
    to_party: '919820000000',
    body: 'Mid December works for us — 4 travelers.',
    received_at: '2026-09-29T10:00:00Z',
  },
  {
    message_id: 'msg_2',
    trip_id: null,
    channel: 'sms',
    direction: 'inbound',
    from_party: '+919777770000',
    to_party: '919820000000',
    body: '',
    mime: 'image/jpeg',
    filename: 'passport.jpg',
    received_at: '2026-09-29T09:00:00Z',
  },
];

describe('ChannelMessagesPanel (T6)', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('renders stored messages with channel, direction, and trip links', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(() => Promise.resolve({ ok: true, json: () => Promise.resolve({ messages: MESSAGES }) })),
    );
    render(<ChannelMessagesPanel />);

    await waitFor(() => {
      expect(screen.getByTestId('channel-messages-panel')).toBeInTheDocument();
    });
    expect(screen.getByText(/Mid December works for us/)).toBeInTheDocument();
    expect(screen.getByText(/WHATSAPP · inbound/i)).toBeInTheDocument();
    expect(screen.getByText(/SMS · inbound/i)).toBeInTheDocument();
    // Media message shows filename metadata, never a fabricated body.
    expect(screen.getByText(/media message: passport.jpg/)).toBeInTheDocument();
    // Unlinked messages say so honestly; linked ones offer the trip.
    expect(screen.getByText(/unlinked/)).toBeInTheDocument();
    expect(screen.getByText('open trip')).toHaveAttribute('href', '/trips/trip_9');
  });

  it('renders an honest empty state when no channel messages exist', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(() => Promise.resolve({ ok: true, json: () => Promise.resolve({ messages: [] }) })),
    );
    render(<ChannelMessagesPanel />);

    await waitFor(() => {
      expect(screen.getByText(/No channel messages have arrived yet/)).toBeInTheDocument();
    });
    expect(screen.queryByTestId('channel-message-row')).not.toBeInTheDocument();
  });

  it('renders an inline error when the feed is unavailable', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(() => Promise.resolve({ ok: false, status: 503, json: () => Promise.resolve({}) })),
    );
    render(<ChannelMessagesPanel />);

    await waitFor(() => {
      expect(screen.getByTestId('channel-messages-error')).toBeInTheDocument();
    });
    expect(screen.getByText(/Message feed unavailable \(503\)/)).toBeInTheDocument();
  });
});
