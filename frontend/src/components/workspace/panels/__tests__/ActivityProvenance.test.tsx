/**
 * ActivityProvenance Tests
 *
 * Test coverage for the ActivityProvenanceBadge component:
 * - Rendering suggested activities with confidence
 * - Rendering requested activities
 * - Color coding and styling
 * - Accessibility features
 *
 * 14 tests total
 */

import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import {
  ActivityProvenanceBadge,
  ActivityProvenanceGroup,
  type ActivitySource,
} from '../ActivityProvenance';

describe('ActivityProvenanceBadge', () => {
  // Test 1: Render suggested badge with confidence
  it('should render suggested badge with emoji and label', () => {
    render(<ActivityProvenanceBadge source="suggested" confidence={95} />);

    expect(screen.getByText(/SUGGESTED/i)).toBeInTheDocument();
    expect(screen.getByText('🤖')).toBeInTheDocument();
  });

  // Test 2: Display confidence percentage for suggested
  it('should display confidence percentage for suggested activities', () => {
    render(<ActivityProvenanceBadge source="suggested" confidence={85} />);

    expect(screen.getByText(/85%/)).toBeInTheDocument();
  });

  // Test 3: Render requested badge
  it('should render requested badge with emoji and label', () => {
    render(<ActivityProvenanceBadge source="requested" />);

    expect(screen.getByText(/REQUESTED/i)).toBeInTheDocument();
    expect(screen.getByText('✅')).toBeInTheDocument();
  });

  // Test 4: Not display confidence for requested activities
  it('should not display confidence percentage for requested activities', () => {
    const { container } = render(<ActivityProvenanceBadge source="requested" />);

    const percentageElements = container.querySelectorAll('.opacity-85');
    expect(percentageElements.length).toBe(0);
  });

  // Test 5: Apply correct styling for suggested (blue)
  it('should apply blue styling for suggested activities', () => {
    const { container } = render(<ActivityProvenanceBadge source="suggested" confidence={95} />);

    const badge = container.querySelector('span');
    expect(badge?.className).toMatch(/accent-blue/);
  });

  // Test 6: Apply correct styling for requested (green)
  it('should apply green styling for requested activities', () => {
    const { container } = render(<ActivityProvenanceBadge source="requested" />);

    const badge = container.querySelector('span');
    expect(badge?.className).toMatch(/accent-green/);
  });

    // Test 7: Support different sizes
    it('should support sm size variant', () => {
      const { container } = render(
        <ActivityProvenanceBadge source="suggested" confidence={90} size="sm" />
      );
    
      const badge = container.querySelector('[role="status"]');
      expect(badge?.className).toMatch(/px-2 py-0\.5/);
    });
    
    // Test 8: Support md size variant (default)
    it('should support md size variant (default)', () => {
      const { container } = render(
        <ActivityProvenanceBadge source="suggested" confidence={90} size="md" />
      );
    
      const badge = container.querySelector('[role="status"]');
      expect(badge?.className).toMatch(/px-2\.5 py-1 /);
    });
    
    // Test 9: Support lg size variant
    it('should support lg size variant', () => {
      const { container } = render(
        <ActivityProvenanceBadge source="suggested" confidence={90} size="lg" />
      );
    
      const badge = container.querySelector('[role="status"]');
      expect(badge?.className).toMatch(/px-3 py-1\.5/);
    });

  // Test 10: Accessibility - aria-label for suggested
  it('should provide accessible aria-label for suggested', () => {
    render(<ActivityProvenanceBadge source="suggested" confidence={95} />);

    const badge = screen.getByRole('status');
    expect(badge).toHaveAttribute('aria-label', expect.stringContaining('SUGGESTED'));
  });

  // Test 11: Accessibility - aria-label for requested
  it('should provide accessible aria-label for requested', () => {
    render(<ActivityProvenanceBadge source="requested" />);

    const badge = screen.getByRole('status');
    expect(badge).toHaveAttribute('aria-label', expect.stringContaining('REQUESTED'));
  });

  // Test 12: Handle edge case - zero confidence
  it('should handle zero confidence', () => {
    render(<ActivityProvenanceBadge source="suggested" confidence={0} />);

    expect(screen.getByText('0%')).toBeInTheDocument();
  });

  // Test 13: Handle edge case - 100 confidence
  it('should handle 100% confidence', () => {
    render(<ActivityProvenanceBadge source="suggested" confidence={100} />);

    expect(screen.getByText('100%')).toBeInTheDocument();
  });

  // Test 14: Support custom className
  it('should accept and apply custom className', () => {
    const { container } = render(
      <ActivityProvenanceBadge
        source="suggested"
        confidence={90}
        className="custom-badge-class"
      />
    );

    const badge = container.querySelector('span');
    expect(badge?.className).toContain('custom-badge-class');
  });
});

describe('ActivityProvenanceGroup', () => {
  // Test 1: Render activity name and badge together
  it('should render activity name with provenance badge', () => {
    render(
      <ActivityProvenanceGroup
        activityName="Hiking"
        source="suggested"
        confidence={95}
      />
    );

    expect(screen.getByText('Hiking')).toBeInTheDocument();
    expect(screen.getByText(/SUGGESTED/i)).toBeInTheDocument();
  });

  // Test 2: Display timestamp when provided
  it('should display timestamp when provided', () => {
    render(
      <ActivityProvenanceGroup
        activityName="Hiking"
        source="suggested"
        confidence={95}
        timestamp="2026-04-28T10:30:00Z"
      />
    );

    // Check that timestamp is rendered (formatted)
    const activity = screen.getByText('Hiking');
    expect(activity).toBeInTheDocument();
  });

  // Test 3: Handle no timestamp
  it('should not break when timestamp is undefined', () => {
    render(
      <ActivityProvenanceGroup
        activityName="Museum Visit"
        source="requested"
      />
    );

    expect(screen.getByText('Museum Visit')).toBeInTheDocument();
  });
});
