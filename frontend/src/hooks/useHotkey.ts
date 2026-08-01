'use client';

/**
 * useHotkey - Lightweight keyboard shortcut hook.
 *
 * Binds a key combo (e.g. 'n') with optional modifier (ctrl/cmd) to a callback.
 * Cleans up the listener on unmount.
 *
 * Usage:
 *   useHotkey('n', true, () => navigate('/workbench?draft=new&tab=intake'));
 *   // Ctrl+N or Cmd+N navigates to new inquiry
 */

import { useEffect, useCallback } from 'react';

type HotkeyHandler = (event: KeyboardEvent) => void;

export function useHotkey(
  key: string,
  withModifier: boolean,
  handler: HotkeyHandler,
  enabled: boolean = true,
): void {
  const stableHandler = useCallback((event: KeyboardEvent) => handler(event), [handler]);

  useEffect(() => {
    if (!enabled) return;

    const listener = (event: KeyboardEvent) => {
      // Ignore when typing in inputs/textareas
      if (
        event.target instanceof HTMLInputElement ||
        event.target instanceof HTMLTextAreaElement ||
        event.target instanceof HTMLSelectElement ||
        (event.target as HTMLElement)?.isContentEditable
      ) {
        return;
      }

      const isModifier = event.ctrlKey || event.metaKey;

      if (withModifier && !isModifier) return;
      if (!withModifier && isModifier) return;

      if (event.key.toLowerCase() === key.toLowerCase()) {
        event.preventDefault();
        event.stopPropagation();
        stableHandler(event);
      }
    };

    document.addEventListener('keydown', listener);
    return () => document.removeEventListener('keydown', listener);
  }, [key, withModifier, enabled, stableHandler]);
}
