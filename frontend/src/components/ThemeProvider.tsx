'use client';

import { useEffect } from 'react';
import { useThemeStore } from '@/stores/themeStore';

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const currentTheme = useThemeStore((state) => state.currentTheme);

  useEffect(() => {
    document.body.className = document.body.className
      .replace(/theme-\w+/g, '')
      .trim();
    document.body.classList.add(`theme-${currentTheme}`);
  }, [currentTheme]);

  return <>{children}</>;
}
