import { renderHook } from '@testing-library/react';
import { beforeEach, describe, expect, it } from 'vitest';
import { useComponentVariant, useThemeStore } from '../themeStore';

describe('theme store contract surface', () => {
  beforeEach(() => {
    localStorage.clear();
    useThemeStore.getState().resetVariants();
  });

  it('returns configured component variants and falls back to v2 for unknown components', () => {
    useThemeStore.getState().setComponentVariant('RouteMap', 'travel');

    const routeMap = renderHook(() => useComponentVariant('RouteMap'));
    expect(routeMap.result.current).toBe('travel');

    const unknown = renderHook(() => useComponentVariant('UnregisteredPanel'));
    expect(unknown.result.current).toBe('v2');
  });
});
