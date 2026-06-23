import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import type { ReactNode } from 'react';
import IntakeTab from '../IntakeTab';

vi.mock('next/navigation', () => ({
  useSearchParams: () => new URLSearchParams(),
  useRouter: () => ({ replace: vi.fn() }),
}));

vi.mock('@/stores/workbench', () => ({
  useWorkbenchStore: () => ({
    input_raw_note: '',
    input_owner_note: '',
    setInputRawNote: vi.fn(),
    setInputOwnerNote: vi.fn(),
  }),
}));

describe('IntakeTab', () => {
  it('shows the canonical trip purpose prompt in the intake helper copy', () => {
    render(<IntakeTab trip={null} />);

    expect(screen.getByText(/What is the purpose of this trip/i)).toBeInTheDocument();
    expect(screen.getByText(/Need the purpose fast\?/i)).toBeInTheDocument();
  });
});
