import { describe, expect, it, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { AuthProvider } from '../AuthProvider';

const mockReplace = vi.fn();
const mockUseAuthStore = vi.fn();
let mockPathname = '/overview';

vi.mock('next/navigation', () => ({
  usePathname: () => mockPathname,
  useRouter: () => ({ replace: mockReplace }),
}));

vi.mock('@/stores/auth', () => ({
  useAuthStore: (selector: (state: any) => unknown) => selector(mockUseAuthStore()),
}));

describe('AuthProvider', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockPathname = '/overview';
    window.history.replaceState({}, '', '/overview');
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

  it('shows a redirecting message instead of a blank page on protected-route redirect', () => {
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

    expect(mockReplace).toHaveBeenCalledWith('/login?redirect=%2Foverview');
    expect(screen.getByText(/redirecting to login/i)).toBeInTheDocument();
    expect(screen.queryByText('protected app')).not.toBeInTheDocument();
  });

  it('preserves the full protected path and query string in the login redirect target', () => {
    const hydrate = vi.fn();
    mockPathname = '/trips/123';
    window.history.replaceState({}, '', '/trips/123?tab=reviews&mode=full');
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

    expect(mockReplace).toHaveBeenCalledWith(
      '/login?redirect=%2Ftrips%2F123%3Ftab%3Dreviews%26mode%3Dfull'
    );
  });

  it('stops showing the redirecting state after navigation reaches a public route', () => {
    const hydrate = vi.fn();
    mockUseAuthStore.mockReturnValue({
      hydrate,
      isLoading: false,
      isAuthenticated: false,
    });

    const { rerender } = render(
      <AuthProvider>
        <div>protected app</div>
      </AuthProvider>
    );

    expect(screen.getByText(/redirecting to login/i)).toBeInTheDocument();

    mockPathname = '/login';
    window.history.replaceState({}, '', '/login');

    rerender(
      <AuthProvider>
        <div>login page</div>
      </AuthProvider>
    );

    expect(screen.queryByText(/redirecting to login/i)).not.toBeInTheDocument();
    expect(screen.getByText('login page')).toBeInTheDocument();
  });
});
