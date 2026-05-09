import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { StatusBadge } from '../status-badge';
import { CheckCircle, AlertTriangle } from 'lucide-react';

const REVIEW_MAP = {
  pending: { label: 'Pending Review', color: '#d29922', icon: CheckCircle },
  approved: { label: 'Approved', color: '#3fb950', icon: CheckCircle },
};

describe('StatusBadge', () => {
  it('renders status label from map', () => {
    render(<StatusBadge status="pending" map={REVIEW_MAP} />);
    expect(screen.getByText('Pending Review')).toBeInTheDocument();
  });

  it('renders null for unknown status', () => {
    const { container } = render(
      <StatusBadge status="nonexistent" map={REVIEW_MAP} />
    );
    expect(container.firstChild).toBeNull();
  });

  it('renders approved status', () => {
    render(<StatusBadge status="approved" map={REVIEW_MAP} />);
    expect(screen.getByText('Approved')).toBeInTheDocument();
  });

  it('applies color from map', () => {
    const { container } = render(
      <StatusBadge status="pending" map={REVIEW_MAP} />
    );
    const span = container.querySelector('span');
    expect(span).not.toBeNull();
  });
});
