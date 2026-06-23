import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import type { ReactNode } from 'react';
import SettingsPage from '../page';

let mockAuthState = {
  isLoading: false,
  isAuthenticated: false,
};

vi.mock('next/navigation', () => ({
  useSearchParams: () => new URLSearchParams(),
  useRouter: () => ({ push: vi.fn() }),
  usePathname: () => '/settings',
}));

vi.mock('@/stores/auth', () => ({
  useAuthStore: (selector: (state: typeof mockAuthState) => unknown) => selector(mockAuthState),
}));

vi.mock('@/hooks/useAgencySettings', () => ({
  useAgencySettings: () => ({
    data: null,
    isLoading: false,
    error: null,
    refetch: vi.fn(),
  }),
  useUpdateOperationalSettings: () => ({
    mutate: vi.fn(),
    isSaving: false,
    error: null,
  }),
  useUpdateAutonomyPolicy: () => ({
    mutate: vi.fn(),
    isSaving: false,
    error: null,
  }),
  useUpdateSeasonalPolicy: () => ({
    mutate: vi.fn(),
    isSaving: false,
    error: null,
  }),
}));

vi.mock('../components/ProfileTab', () => ({ ProfileTab: () => <div /> }));
vi.mock('../components/OperationalTab', () => ({ OperationalTab: () => <div /> }));
vi.mock('../components/AutonomyTab', () => ({ AutonomyTab: () => <div /> }));
vi.mock('../components/PeopleTab', () => ({ PeopleTab: () => <div /> }));
vi.mock('../components/IntegrationsTab', () => ({ IntegrationsTab: () => <div /> }));
vi.mock('../components/SeasonalTab', () => ({ SeasonalTab: () => <div /> }));
vi.mock('../components/GuardTab', () => ({ GuardTab: () => <div /> }));
vi.mock('../components/AlertDestinationsTab', () => ({ AlertDestinationsTab: () => <div /> }));
vi.mock('../components/AiAgentTab', () => ({ AiAgentTab: () => <div /> }));
vi.mock('../components/SupportSettingsTab', () => ({ SupportSettingsTab: () => <div /> }));
vi.mock('../components/CommSettingsTab', () => ({ CommSettingsTab: () => <div /> }));

describe('Settings page auth fallback', () => {
  beforeEach(() => {
    mockAuthState = {
      isLoading: false,
      isAuthenticated: false,
    };
  });

  it('shows a sign-in notice when the browser session is unauthenticated', () => {
    render(<SettingsPage />);

    expect(screen.getByRole('heading', { name: /agency settings/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /sign in to continue/i })).toHaveAttribute(
      'href',
      '/login?redirect=%2Fsettings'
    );
  });
});
