import { describe, expect, it, vi, beforeEach } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import { AuthProvider } from '../AuthProvider';

const mockUseAuthStore = vi.fn();
const mockRouterPush = vi.fn();
let mockPathname = '/overview';

vi.mock('next/navigation', () => ({
  usePathname: () => mockPathname,
  useRouter: () => ({ push: mockRouterPush }),
}));

vi.mock('@/lib/api-client', () => ({
  AUTH_UNAUTHORIZED_EVENT: 'waypoint:auth-unauthorized',
  api: { post: vi.fn() },
  ApiException: class ApiException extends Error {
    status: number;
    constructor(message: string, status: number = 400) {
      super(message);
      this.status = status;
    }
  },
}));

vi.mock('@/stores/auth', () => ({
  useAuthStore: (selector: (state: any) => unknown) => selector(mockUseAuthStore()),
}));

describe('AuthProvider', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockRouterPush.mockReset();
    mockPathname = '/overview';
    // Component reads window.location.search for query string
    Object.defineProperty(window, 'location', {
      value: { ...window.location, search: '' },
      writable: true,
    });
  });

  it('shows a session-checking message while auth is hydrating', () => {
    const hydrate = vi.fn();
    mockUseAuthStore.mockReturnValue({
      hydrate,
      isLoading: true,
      isAuthenticated: false,
    });

    render(
      <AuthProvider>
        <div>protected app</div>
      </AuthProvider>
    );

    expect(screen.getByText(/checking your session/i)).toBeInTheDocument();
    expect(screen.queryByText('protected app')).not.toBeInTheDocument();
  });

  it('shows login modal on protected-route when unauthenticated', () => {
    const hydrate = vi.fn();
    mockUseAuthStore.mockReturnValue({
      hydrate,
      isLoading: false,
      isAuthenticated: false,
    });

    render(
      <AuthProvider>
        <div>protected app</div>
      </AuthProvider>
    );

    expect(screen.getByText(/sign in required/i)).toBeInTheDocument();
    expect(screen.getByText(/continue to/i)).toBeInTheDocument();
    expect(screen.getByText('protected app')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /open full sign-in page/i })).toHaveAttribute(
      'href',
      '/login?redirect=%2Foverview'
    );
  });

  it('preserves the full protected path and query string in modal context', () => {
    const hydrate = vi.fn();
    mockPathname = '/trips/123';
    Object.defineProperty(window, 'location', {
      value: { ...window.location, search: '?tab=reviews&mode=full' },
      writable: true,
    });
    mockUseAuthStore.mockReturnValue({
      hydrate,
      isLoading: false,
      isAuthenticated: false,
    });

    render(
      <AuthProvider>
        <div>protected app</div>
      </AuthProvider>
    );

    expect(screen.getByText('/trips/123?tab=reviews&mode=full')).toBeInTheDocument();
  });

  it('does not show login modal on public routes', () => {
    const hydrate = vi.fn();
    mockPathname = '/login';
    mockUseAuthStore.mockReturnValue({
      hydrate,
      isLoading: false,
      isAuthenticated: false,
    });

    render(
      <AuthProvider>
        <div>login page</div>
      </AuthProvider>
    );

    expect(screen.queryByText(/sign in required/i)).not.toBeInTheDocument();
    expect(screen.getByText('login page')).toBeInTheDocument();
  });

  it('navigates to full-page login when Escape is pressed', () => {
    const hydrate = vi.fn();
    mockPathname = '/trips';
    mockUseAuthStore.mockReturnValue({
      hydrate,
      isLoading: false,
      isAuthenticated: false,
    });

    render(
      <AuthProvider>
        <div>protected app</div>
      </AuthProvider>
    );

    fireEvent.keyDown(document, { key: 'Escape' });
    expect(mockRouterPush).toHaveBeenCalledWith('/login?redirect=%2Ftrips');
  });
});
