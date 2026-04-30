import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import type { ReactNode } from 'react';
import OwnerReviewsPage from '../page';

vi.mock('next/link', () => ({
  default: ({ children, href, ...props }: { children: ReactNode; href: string }) => (
    <a href={href} {...props}>
      {children}
    </a>
  ),
}));

vi.mock('@/hooks/useGovernance', () => ({
  useReviews: () => ({
    data: [],
    isLoading: false,
    error: null,
    refetch: vi.fn(),
    submitAction: vi.fn(),
  }),
}));

describe('OwnerReviewsPage', () => {
  it('renders a page-level return link back to overview', () => {
    render(<OwnerReviewsPage />);

    expect(screen.getByRole('link', { name: /back to overview/i })).toHaveAttribute('href', '/overview');
  });
});
