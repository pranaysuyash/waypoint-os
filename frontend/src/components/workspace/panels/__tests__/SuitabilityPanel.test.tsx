import { describe, it, expect, vi } from "vitest";
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { SuitabilityPanel, type SuitabilityFlag } from '../SuitabilityPanel';

describe('SuitabilityPanel', () => {
  const mockFlags: SuitabilityFlag[] = [
    {
      flag: 'suitability_exclude_white_water_rafting',
      flag_type: 'suitability_exclude_white_water_rafting',
      severity: 'critical',
      reason: 'Toddler participant excluded from White Water Rafting: Height-based participation restriction excludes toddler cohort.',
      confidence: 0.95,
      details: {
        activity_id: 'white_water_rafting',
        activity_name: 'White Water Rafting',
        participant_label: 'toddler',
      },
      affected_travelers: ['child_1'],
    },
    {
      flag: 'suitability_discourage_hiking_difficult',
      flag_type: 'suitability_discourage_hiking_difficult',
      severity: 'high',
      reason: 'Elderly participant discouraged from Difficult Mountain Hike: Walking-heavy activity may not suit elderly mobility profile.',
      confidence: 0.88,
      details: {
        activity_id: 'hiking_difficult',
        activity_name: 'Difficult Mountain Hike',
        participant_label: 'elderly',
      },
      affected_travelers: ['elderly_1'],
    },
    {
      flag: 'suitability_pacing_toddler',
      flag_type: 'suitability_pacing_toddler',
      severity: 'medium',
      reason: 'High density: 4 activities in one day may exceed toddler stamina.',
      confidence: 0.75,
      details: {
        activity_count: 4,
      },
    },
  ];

  it('renders no flags message when flags array is empty', () => {
    render(<SuitabilityPanel flags={[]} />);
    expect(screen.getByText(/No suitability concerns detected/)).toBeInTheDocument();
  });

  it('renders critical flags with red background', () => {
    render(<SuitabilityPanel flags={mockFlags} />);
    const criticalText = screen.getByText(/Toddler participant excluded/);
    expect(criticalText).toBeInTheDocument();
    expect(criticalText.className).toMatch(/accent-red/);
  });

  it('renders high severity flags with orange background', () => {
    render(<SuitabilityPanel flags={mockFlags} />);
    const highText = screen.getByText(/Elderly participant discouraged/);
    expect(highText).toBeInTheDocument();
  });

  it('renders critical flags with acknowledgment checkbox', () => {
    render(<SuitabilityPanel flags={mockFlags} />);
    const checkboxes = screen.getAllByRole('checkbox');
    expect(checkboxes.length).toBeGreaterThan(0);
  });

  it('disables continue button when critical flags are not acknowledged', () => {
    const handleAcknowledge = vi.fn();
    render(<SuitabilityPanel flags={mockFlags} onAcknowledge={handleAcknowledge} />);

    const continueButton = screen.getByRole('button', { name: /Continue to Send/ });
    expect(continueButton).toBeDisabled();
  });

  it('enables continue button when all critical flags are acknowledged', () => {
    const handleAcknowledge = vi.fn();
    render(<SuitabilityPanel flags={mockFlags} onAcknowledge={handleAcknowledge} />);

    const checkboxes = screen.getAllByRole('checkbox');
    fireEvent.click(checkboxes[0]);

    const continueButton = screen.getByRole('button', { name: /Continue to Send/ });
    expect(continueButton).not.toBeDisabled();
  });

  it('calls onAcknowledge with flag IDs when continue is clicked', () => {
    const handleAcknowledge = vi.fn();
    render(<SuitabilityPanel flags={mockFlags} onAcknowledge={handleAcknowledge} />);

    const checkboxes = screen.getAllByRole('checkbox');
    fireEvent.click(checkboxes[0]);

    const continueButton = screen.getByRole('button', { name: /Continue to Send/ });
    fireEvent.click(continueButton);

    expect(handleAcknowledge).toHaveBeenCalledWith(
      expect.arrayContaining(['suitability_exclude_white_water_rafting'])
    );
  });

  it('displays confidence percentage for each flag', () => {
    render(<SuitabilityPanel flags={mockFlags} />);

    expect(screen.getByText('Confidence: 95%')).toBeInTheDocument();
    expect(screen.getByText('Confidence: 88%')).toBeInTheDocument();
  });

  it('displays activity name when available in details', () => {
    render(<SuitabilityPanel flags={mockFlags} />);

    expect(screen.getByText('Activity: White Water Rafting')).toBeInTheDocument();
    expect(screen.getByText('Activity: Difficult Mountain Hike')).toBeInTheDocument();
  });

  it('handles unchecking acknowledgment checkboxes', () => {
    const handleAcknowledge = vi.fn();
    render(<SuitabilityPanel flags={mockFlags} onAcknowledge={handleAcknowledge} />);

    const checkboxes = screen.getAllByRole('checkbox');
    fireEvent.click(checkboxes[0]);
    fireEvent.click(checkboxes[0]);

    const continueButton = screen.getByRole('button', { name: /Continue to Send/ });
    expect(continueButton).toBeDisabled();
  });

  it('renders operator review message for critical flags', () => {
    render(<SuitabilityPanel flags={mockFlags} />);
    expect(screen.getByText('Operator review required before sending to customer')).toBeInTheDocument();
  });

  it('only shows continue button when there are critical flags', () => {
    const lowFlagOnly: SuitabilityFlag[] = [
      {
        flag: 'test_low',
        flag_type: 'test_low',
        severity: 'low',
        reason: 'Minor concern',
        confidence: 0.8,
      },
    ];

    render(<SuitabilityPanel flags={lowFlagOnly} />);
    expect(screen.queryByRole('button', { name: /Continue to Send/ })).not.toBeInTheDocument();
  });

  it('sorts flags by severity correctly', () => {
    const unsortedFlags: SuitabilityFlag[] = [
      {
        flag: 'low1',
        flag_type: 'low1',
        severity: 'low',
        reason: 'Low severity',
        confidence: 0.7,
      },
      {
        flag: 'critical1',
        flag_type: 'critical1',
        severity: 'critical',
        reason: 'Critical severity',
        confidence: 0.95,
      },
      {
        flag: 'high1',
        flag_type: 'high1',
        severity: 'high',
        reason: 'High severity',
        confidence: 0.9,
      },
    ];

    render(<SuitabilityPanel flags={unsortedFlags} />);

    const criticalText = screen.getByText('Critical Concerns');
    const warningText = screen.getByText('Important Warnings');
    const infoText = screen.getByText('Additional Information');

    expect(criticalText.compareDocumentPosition(warningText)).toBe(4);
    expect(warningText.compareDocumentPosition(infoText)).toBe(4);
  });
});
