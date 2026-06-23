'use client';

import { useCallback, useEffect, useState } from 'react';

export interface ElementSize {
  width: number;
  height: number;
}

export function useElementSize<T extends HTMLElement>() {
  const [element, setElement] = useState<T | null>(null);
  const [size, setSize] = useState<ElementSize>({ width: 0, height: 0 });

  const ref = useCallback((node: T | null) => {
    setElement(node);
  }, []);

  useEffect(() => {
    if (!element) return;

    let frame = 0;
    const measure = () => {
      const rect = element.getBoundingClientRect();
      setSize((current) => {
        const next = {
          width: Math.max(0, Math.floor(rect.width)),
          height: Math.max(0, Math.floor(rect.height)),
        };
        if (current.width === next.width && current.height === next.height) {
          return current;
        }
        return next;
      });
    };

    measure();

    const runMeasure = () => {
      if (frame) cancelAnimationFrame(frame);
      frame = requestAnimationFrame(measure);
    };

    let observer: ResizeObserver | null = null;
    if (typeof ResizeObserver !== 'undefined') {
      observer = new ResizeObserver(runMeasure);
      observer.observe(element);
    } else if (typeof window !== 'undefined') {
      window.addEventListener('resize', runMeasure);
    }

    return () => {
      if (frame) cancelAnimationFrame(frame);
      observer?.disconnect();
      if (typeof window !== 'undefined') {
        window.removeEventListener('resize', runMeasure);
      }
    };
  }, [element]);

  return { ref, size };
}
