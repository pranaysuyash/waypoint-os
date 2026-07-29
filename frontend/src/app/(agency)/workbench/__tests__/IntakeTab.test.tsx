import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import type { ReactNode } from 'react';
import IntakeTab from '../IntakeTab';

const mockReplace = vi.fn();

vi.mock('next/navigation', () => ({
  useSearchParams: () => new URLSearchParams(),
  useRouter: () => ({ replace: mockReplace }),
  usePathname: () => '/workbench',
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
  beforeEach(() => {
    mockReplace.mockReset();
  });

  it('shows the canonical trip purpose prompt in the intake helper copy', () => {
    render(<IntakeTab trip={null} />);

    expect(screen.getByText(/What is the purpose of this trip/i)).toBeInTheDocument();
    expect(screen.getByText(/Need the purpose fast\?/i)).toBeInTheDocument();
  });

  it('updates the full workbench pathname when the stage changes', async () => {
    render(<IntakeTab trip={null} />);

    await userEvent.selectOptions(screen.getByLabelText('Stage'), 'booking');

    expect(mockReplace).toHaveBeenCalledWith('/workbench?stage=booking', { scroll: false });
  });
});
