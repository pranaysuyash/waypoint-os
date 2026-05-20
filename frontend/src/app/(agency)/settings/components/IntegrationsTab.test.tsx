import { describe, expect, it, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { IntegrationsTab } from './IntegrationsTab';
import { useIntegrations } from '@/hooks/useIntegrations';

vi.mock('@/hooks/useIntegrations', () => ({
  useIntegrations: vi.fn(),
}));

const refetch = vi.fn(async () => undefined);

const integrations = [
  {
    provider: 'whatsapp',
    display_name: 'WhatsApp',
    enabled: false,
    status: 'disabled' as const,
    capabilities: ['outbound_messages', 'inbound_messages'],
    category: 'messaging',
    last_health_check_at: null,
    last_success_at: null,
    last_error_code: null,
    last_error_message_safe: null,
    updated_at: null,
  },
  {
    provider: 'gmail',
    display_name: 'Gmail',
    enabled: true,
    status: 'connected' as const,
    capabilities: ['email_read', 'email_send'],
    category: 'email',
    last_health_check_at: '2026-05-19T05:00:00Z',
    last_success_at: '2026-05-19T05:00:00Z',
    last_error_code: null,
    last_error_message_safe: null,
    updated_at: '2026-05-19T05:00:00Z',
  },
];

describe('IntegrationsTab', () => {
  beforeEach(() => {
    vi.mocked(useIntegrations).mockReturnValue({
      data: { integrations, total: integrations.length },
      isLoading: false,
      error: null,
      refetch,
    });
  });

  it('renders provider status without credential fields', () => {
    render(<IntegrationsTab />);

    expect(screen.getByRole('heading', { name: 'Integrations' })).toBeInTheDocument();
    expect(screen.getByText('WhatsApp')).toBeInTheDocument();
    expect(screen.getByText('Gmail')).toBeInTheDocument();
    expect(screen.getByText('Disabled')).toBeInTheDocument();
    expect(screen.getByText('Connected')).toBeInTheDocument();
    expect(screen.queryByText(/credential_ref/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/config_json/i)).not.toBeInTheDocument();
  });

  it('states that credential actions are intentionally not enabled yet', () => {
    render(<IntegrationsTab />);

    expect(screen.getByText(/credential boundary and audit events/i)).toBeInTheDocument();
    expect(screen.getByText(/do not paste api keys/i)).toBeInTheDocument();
  });
});
