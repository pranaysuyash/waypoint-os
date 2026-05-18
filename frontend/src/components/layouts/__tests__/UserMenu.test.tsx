import { beforeEach, describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import { UserMenu } from '../UserMenu';
import { waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

const { mockPush, mockLogout, mockUseAuthStore, mockApiPost } = vi.hoisted(() => ({
  mockPush: vi.fn(),
  mockLogout: vi.fn(),
  mockUseAuthStore: vi.fn(),
  mockApiPost: vi.fn(),
}));

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: mockPush }),
}));

vi.mock('@/lib/api-client', () => ({
  api: { post: mockApiPost },
}));

vi.mock('@/stores/auth', () => ({
  useAuthStore: (selector: (state: unknown) => unknown) => selector(mockUseAuthStore()),
}));

describe('UserMenu', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUseAuthStore.mockReturnValue({
      user: { name: 'Alex Doe', email: 'alex@example.com' },
      agency: { name: 'Atlas Travel', slug: 'atlas' },
      membership: { role: 'admin', isPrimary: true },
      logout: mockLogout,
    });
  });

  it('opens and closes with keyboard with proper menu role and focus handling', () => {
    render(<UserMenu />);

    const trigger = screen.getByRole('button', { name: 'User menu' });
    expect(screen.queryByRole('menu')).not.toBeInTheDocument();
    expect(trigger).toHaveAttribute('aria-expanded', 'false');

    fireEvent.keyDown(trigger, { key: 'ArrowDown' });

    const menu = screen.getByRole('menu');
    expect(menu).toBeInTheDocument();
    expect(trigger).toHaveAttribute('aria-expanded', 'true');
    expect(screen.getByRole('menuitem', { name: /settings/i })).toHaveAttribute('tabindex', '0');

    fireEvent.keyDown(menu, { key: 'ArrowDown' });
    expect(screen.getByRole('menuitem', { name: /sign out/i })).toHaveFocus();

    fireEvent.keyDown(menu, { key: 'Home' });
    expect(screen.getByRole('menuitem', { name: /settings/i })).toHaveFocus();

    fireEvent.keyDown(menu, { key: 'Escape' });
    expect(menu).not.toBeInTheDocument();
    expect(trigger).toHaveFocus();
  });

  it('closes on Tab and advances focus to the next field', async () => {
    const user = userEvent.setup();
    render(
      <>
        <UserMenu />
        <button type='button'>Next control</button>
      </>
    );

    await user.click(screen.getByRole('button', { name: 'User menu' }));
    await user.keyboard('{Tab}');

    expect(screen.queryByRole('menu')).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Next control' })).toHaveFocus();
  });

  it('navigates to settings from menu activation and updates focus predictably', () => {
    render(<UserMenu />);

    const trigger = screen.getByRole('button', { name: 'User menu' });
    fireEvent.click(trigger);
    const settingsItem = screen.getByRole('menuitem', { name: /settings/i });

    expect(trigger).toHaveAttribute('aria-expanded', 'true');

    fireEvent.keyDown(settingsItem, { key: 'Enter' });

    expect(mockPush).toHaveBeenCalledWith('/settings');
  });

  it('logs out and navigates on Sign out activation', async () => {
    render(<UserMenu />);

    fireEvent.click(screen.getByRole('button', { name: 'User menu' }));
    const signOutItem = screen.getByRole('menuitem', { name: /sign out/i });
    fireEvent.keyDown(signOutItem, { key: ' ' });

    await waitFor(() => expect(mockApiPost).toHaveBeenCalledWith('/api/auth/logout'));
    expect(mockLogout).toHaveBeenCalled();
    expect(mockPush).toHaveBeenCalledWith('/login');
  });
});
