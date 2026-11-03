// @vitest-environment jsdom

import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import ChannelMessagesPanel from '../ChannelMessagesPanel';
import { useWorkbenchStore } from '@/stores/workbench';

// T6 (FND-0305): the inbox channel-messages panel renders the real webhook-
// stored feed with honest empty and error states — no sample content.
// Operator-surface tranche (2026-11-03): inbound messages hand off to intake;
// attachments render as explicit chips.

const { pushMock } = vi.hoisted(() => ({ pushMock: vi.fn() }));

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: pushMock, replace: vi.fn(), back: vi.fn(), pathname: '/inbox' }),
  usePathname: () => '/inbox',
  useSearchParams: () => new URLSearchParams(),
}));

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
  beforeEach(() => {
    pushMock.mockClear();
    useWorkbenchStore.setState({ pending_intake_prefill: null });
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    useWorkbenchStore.setState({ pending_intake_prefill: null });
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

  it('offers "Use for intake" on inbound messages with a body and hands the body to the workbench store', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(() => Promise.resolve({ ok: true, json: () => Promise.resolve({ messages: MESSAGES }) })),
    );
    render(<ChannelMessagesPanel />);

    const buttons = await waitFor(() => {
      const found = screen.getAllByTestId('channel-message-use-for-intake');
      expect(found.length).toBeGreaterThan(0);
      return found;
    });
    // Only the inbound message with a body offers the hand-off (msg_2 is
    // media-only; both fixture messages are inbound).
    expect(buttons).toHaveLength(1);

    buttons[0].click();
    expect(useWorkbenchStore.getState().pending_intake_prefill).toBe(
      'Mid December works for us — 4 travelers.',
    );
    expect(pushMock).toHaveBeenCalledWith('/inquiries/new?draft=new&tab=intake');
  });

  it('renders media attachments as explicit chips with filename metadata', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(() => Promise.resolve({ ok: true, json: () => Promise.resolve({ messages: MESSAGES }) })),
    );
    render(<ChannelMessagesPanel />);

    const chip = await screen.findByTestId('channel-message-attachment');
    expect(chip).toHaveTextContent('passport.jpg');
    expect(chip).toHaveAttribute('title', 'image/jpeg');
  });

  it('does not offer the intake hand-off for media-only messages (no extractable text)', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(() =>
        Promise.resolve({ ok: true, json: () => Promise.resolve({ messages: [MESSAGES[1]] }) }),
      ),
    );
    render(<ChannelMessagesPanel />);

    await screen.findByTestId('channel-message-row');
    expect(screen.queryByTestId('channel-message-use-for-intake')).not.toBeInTheDocument();
  });
});
