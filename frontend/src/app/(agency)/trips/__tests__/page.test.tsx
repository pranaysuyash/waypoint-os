import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import type { ReactNode } from 'react';
import WorkspacesPage from '../page';

vi.mock('next/link', () => ({
  default: ({ children, href, ...props }: { children: ReactNode; href: string }) => (
    <a href={href} {...props}>
      {children}
    </a>
  ),
}));

vi.mock('@/hooks/useTrips', () => ({
  useTrips: vi.fn(),
}));

import { useTrips } from '@/hooks/useTrips';

describe('WorkspacesPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(useTrips).mockReturnValue({
      data: [],
      total: 0,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    } as never);
  });

  it('renders a page-level return link back to overview', () => {
    render(<WorkspacesPage />);

    expect(screen.getByRole('link', { name: /back to overview/i })).toHaveAttribute('href', '/overview');
  });
});
