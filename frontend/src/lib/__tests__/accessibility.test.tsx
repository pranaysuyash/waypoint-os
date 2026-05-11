import { render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import {
  ARIA_ROLES,
  landmarkProps,
  navProps,
  liveRegionProps,
  iconButtonProps,
  tabProps,
  tabPanelProps,
  statusProps,
  handleListNavigation,
  handleActivation,
  handleEscape,
  trapFocus,
  moveFocus,
  generateId,
  generateLinkedIds,
  announceToScreenReader,
  LiveRegion,
} from '../accessibility';

function keyboardEvent(key: string) {
  return {
    key,
    preventDefault: vi.fn(),
  } as unknown as React.KeyboardEvent;
}

describe('accessibility utilities', () => {
  beforeEach(() => {
    document.body.innerHTML = '';
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('returns semantic ARIA prop sets for landmarks, controls, and status regions', () => {
    expect(ARIA_ROLES.navigation).toBe('navigation');
    expect(landmarkProps('Trip details')).toEqual({ role: 'region', 'aria-label': 'Trip details' });
    expect(navProps('Primary')).toEqual({ role: 'navigation', 'aria-label': 'Primary' });
    expect(liveRegionProps()).toEqual({ 'aria-live': 'polite', 'aria-atomic': 'true' });
    expect(liveRegionProps(false)).toEqual({ 'aria-live': 'assertive', 'aria-atomic': 'true' });
    expect(iconButtonProps('Open filters')).toEqual({ role: 'button', 'aria-label': 'Open filters' });
    expect(statusProps('Saved')).toEqual({ role: 'status', 'aria-live': 'polite', 'aria-label': 'Saved' });
  });

  it('returns linked tab and panel attributes with roving tab index semantics', () => {
    expect(tabProps('tab-summary', true, 'panel-summary')).toMatchObject({
      id: 'tab-summary',
      role: 'tab',
      'aria-selected': true,
      'aria-controls': 'panel-summary',
      tabIndex: 0,
    });
    expect(tabProps('tab-history', false, 'panel-history')).toMatchObject({ tabIndex: -1 });
    expect(tabPanelProps('panel-summary', 'tab-summary')).toEqual({
      id: 'panel-summary',
      role: 'tabpanel',
      'aria-labelledby': 'tab-summary',
      tabIndex: 0,
    });
  });

  it('normalizes list navigation and activation keyboard behavior', () => {
    const next = keyboardEvent('ArrowRight');
    expect(handleListNavigation(next, 1, 3)).toBe(2);
    expect(next.preventDefault).toHaveBeenCalledOnce();

    const wrapPrevious = keyboardEvent('ArrowUp');
    expect(handleListNavigation(wrapPrevious, 0, 3, 'vertical')).toBe(2);

    expect(handleListNavigation(keyboardEvent('Home'), 2, 4)).toBe(0);
    expect(handleListNavigation(keyboardEvent('End'), 0, 4)).toBe(3);
    expect(handleListNavigation(keyboardEvent('Tab'), 0, 4)).toBeNull();

    const activate = vi.fn();
    handleActivation(keyboardEvent('Enter'), activate);
    handleActivation(keyboardEvent(' '), activate);
    expect(activate).toHaveBeenCalledTimes(2);

    const close = vi.fn();
    handleEscape(keyboardEvent('Escape'), close);
    expect(close).toHaveBeenCalledOnce();
  });

  it('traps and moves focus within document controls', () => {
    const container = document.createElement('div');
    container.innerHTML = '<button id="first">First</button><button id="last">Last</button>';
    document.body.append(container);

    const cleanup = trapFocus(container);
    expect(document.activeElement).toBe(document.getElementById('first'));

    document.getElementById('last')?.focus();
    const tabFromLast = new KeyboardEvent('keydown', { key: 'Tab', bubbles: true });
    const preventTab = vi.spyOn(tabFromLast, 'preventDefault');
    container.dispatchEvent(tabFromLast);
    expect(preventTab).toHaveBeenCalledOnce();
    expect(document.activeElement).toBe(document.getElementById('first'));

    moveFocus('next', container);
    expect(document.activeElement).toBe(document.getElementById('last'));
    moveFocus('previous', container);
    expect(document.activeElement).toBe(document.getElementById('first'));

    cleanup();
  });

  it('generates linked ids and announces messages through live regions', () => {
    vi.useFakeTimers();
    const id = generateId('trip-panel');
    expect(id).toMatch(/^trip-panel-\d+$/);
    expect(generateLinkedIds('field')).toMatchObject({
      label: expect.stringMatching(/^field-\d+-label$/),
      description: expect.stringMatching(/^field-\d+-description$/),
      error: expect.stringMatching(/^field-\d+-error$/),
    });

    render(<LiveRegion />);
    announceToScreenReader('Saved itinerary', 'assertive');
    expect(screen.getByText('Saved itinerary')).toHaveAttribute('aria-live', 'assertive');

    vi.advanceTimersByTime(1000);
    expect(document.getElementById('sr-announcement-assertive')).toHaveTextContent('');
  });
});
