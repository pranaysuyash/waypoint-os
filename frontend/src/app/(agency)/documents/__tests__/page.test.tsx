import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import DocumentsPage from '../PageClient';

vi.mock('@/hooks/useTrips', () => ({
  useTrips: () => ({
    data: [
      { id: 'trip-1', destination: 'Paris', type: 'family' },
      { id: 'trip-2', destination: 'Tokyo', type: 'honeymoon' },
    ],
    isLoading: false,
  }),
  useTrip: (id: string | null) => ({
    data: id ? { id, stage: 'proposal', validation: { readiness: null } } : null,
  }),
}));

vi.mock('@/components/navigation/BackToOverviewLink', () => ({
  BackToOverviewLink: () => <div data-testid='back-link' />,
}));

vi.mock('@/app/(agency)/workbench/OpsPanel', () => ({
  default: ({ mode }: { mode: string }) => <div data-testid='ops-panel-mode'>{mode}</div>,
}));

describe('DocumentsPage', () => {
  it('renders documents shell and canonical ops panel documents mode', () => {
    render(<DocumentsPage />);
    expect(screen.getByText('Documents')).toBeInTheDocument();
    expect(screen.getByTestId('documents-trip-select')).toBeInTheDocument();
    expect(screen.getByTestId('ops-panel-mode')).toHaveTextContent('documents');
  });
});

