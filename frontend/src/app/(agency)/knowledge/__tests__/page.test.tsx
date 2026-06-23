// @vitest-environment jsdom

import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import KnowledgePage from '../PageClient';

vi.mock('@/components/navigation/BackToOverviewLink', () => ({
  BackToOverviewLink: () => <div data-testid='back-link' />,
}));

describe('KnowledgePage', () => {
  it('renders the knowledge base shell', () => {
    render(<KnowledgePage />);

    expect(screen.getByText('Knowledge Base')).toBeInTheDocument();
    expect(screen.getByText(/Canonical agency memory shell/i)).toBeInTheDocument();
    expect(screen.getByText('Playbooks')).toBeInTheDocument();
    expect(screen.getByText('Preferences')).toBeInTheDocument();
    expect(screen.getByText('Memory')).toBeInTheDocument();
  });
});
