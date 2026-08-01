import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import type { ReactNode } from 'react';
import { WelcomeModal } from '../WelcomeModal';

const mockPush = vi.fn();
let mockPathname = '/overview';

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: mockPush }),
  usePathname: () => mockPathname,
}));

describe('WelcomeModal', () => {
  beforeEach(() => {
    mockPush.mockReset();
    localStorage.clear();
    mockPathname = '/overview';
  });

  it('renders as a non-blocking welcome card for authenticated users', () => {
    render(<WelcomeModal isAuthenticated />);

    expect(screen.getByText('Welcome to Waypoint')).toBeInTheDocument();
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: /process your first inquiry/i })).toBeInTheDocument();
  });

  it('dismisses the welcome card and records the seen flag', () => {
    render(<WelcomeModal isAuthenticated />);

    fireEvent.click(screen.getByRole('button', { name: /get started/i }));

    expect(localStorage.getItem('waypoint:welcome-seen:v1')).toBe('1');
    expect(screen.queryByText('Welcome to Waypoint')).not.toBeInTheDocument();
  });

  it('navigates when a quick link is chosen', () => {
    render(<WelcomeModal isAuthenticated />);

    fireEvent.click(screen.getByRole('button', { name: /process your first inquiry/i }));

    expect(mockPush).toHaveBeenCalledWith('/workbench?draft=new&tab=intake');
    expect(localStorage.getItem('waypoint:welcome-seen:v1')).toBe('1');
  });

  it('uses a compact banner on narrow viewports', async () => {
    const originalWidth = window.innerWidth;
    Object.defineProperty(window, 'innerWidth', { configurable: true, value: 390 });

    render(<WelcomeModal isAuthenticated />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /open intake/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /get started/i })).toBeInTheDocument();
    });

    Object.defineProperty(window, 'innerWidth', { configurable: true, value: originalWidth });
    window.dispatchEvent(new Event('resize'));
  });

  it('stays hidden on the workbench surface', () => {
    mockPathname = '/workbench';

    const { container } = render(<WelcomeModal isAuthenticated />);

    expect(container).toBeEmptyDOMElement();
  });
});
