// @vitest-environment jsdom

import { describe, expect, it, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import React from 'react';
import { QuickIngestPalette } from '../QuickIngestPalette';

describe('QuickIngestPalette (Stream 2 - Daily Utility)', () => {
  it('renders closed trigger button initially', () => {
    render(<QuickIngestPalette onApply={vi.fn()} />);
    expect(screen.getByText('Quick Ingest (WhatsApp / Email Scrub)')).toBeDefined();
  });

  it('opens panel and parses WhatsApp sample slots', () => {
    const handleApply = vi.fn();
    render(<QuickIngestPalette onApply={handleApply} />);

    // Click trigger to open
    fireEvent.click(screen.getByText('Quick Ingest (WhatsApp / Email Scrub)'));

    // Should see header and sample buttons
    expect(screen.getByText('Quick Ingest & Transcript Scrub')).toBeDefined();
    expect(screen.getByText('WhatsApp Family Chat')).toBeDefined();

    // Click sample
    fireEvent.click(screen.getByText('WhatsApp Family Chat'));

    // Verify parsed slot badges appear
    expect(screen.getByText(/📍 Dubai & Abu Dhabi/)).toBeDefined();
    expect(screen.getByText(/🛫 Ex: DEL/)).toBeDefined();
    expect(screen.getByText(/👥 Couple \+ 2 children/)).toBeDefined();
    expect(screen.getByText(/🏨 Atlantis The Palm/)).toBeDefined();
    expect(screen.getByText(/✨ Vegetarian meals/)).toBeDefined();

    // Click apply button
    const applyBtn = screen.getByText('Apply Structured Brief to Draft');
    fireEvent.click(applyBtn);

    expect(handleApply).toHaveBeenCalledTimes(1);
    const appliedText = handleApply.mock.calls[0][0];
    expect(appliedText).toContain('Trip Request: Dubai & Abu Dhabi');
    expect(appliedText).toContain('Origin: DEL');
    expect(appliedText).toContain('Vegetarian meals');
  });
});
