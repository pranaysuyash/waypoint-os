// @vitest-environment jsdom

import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import KnowledgePage from '../PageClient';

vi.mock('@/components/navigation/BackToOverviewLink', () => ({
  BackToOverviewLink: () => <div data-testid='back-link' />,
}));

describe('KnowledgePage', () => {
  it('renders the knowledge base and agency memory studio', () => {
    render(<KnowledgePage />);

    expect(screen.getByText(/Knowledge Base & Agency Memory/i)).toBeInTheDocument();
    expect(screen.getByText(/Canonical agency intelligence/i)).toBeInTheDocument();
    expect(screen.getAllByText(/South Africa Luxury Safari/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/Schengen Visa Processing/i)).toBeInTheDocument();
    expect(screen.getByText(/Create New Playbook/i)).toBeInTheDocument();
  });
});
