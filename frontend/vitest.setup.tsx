import '@testing-library/jest-dom';
import { cleanup } from '@testing-library/react';
import { createElement } from 'react';
import { afterEach, vi } from 'vitest';

const gsapTween = {
  kill: vi.fn(),
  pause: vi.fn(),
  play: vi.fn(),
  progress: vi.fn(),
};

const gsapTimeline = {
  kill: vi.fn(),
  pause: vi.fn(),
  play: vi.fn(),
  progress: vi.fn(),
  set: vi.fn().mockReturnThis(),
  to: vi.fn().mockReturnThis(),
  fromTo: vi.fn().mockReturnThis(),
};

const gsapMock = {
  context: vi.fn((fn?: () => void) => {
    if (typeof fn === 'function') {
      fn();
    }
    return { revert: vi.fn() };
  }),
  fromTo: vi.fn(() => gsapTween),
  registerPlugin: vi.fn(),
  set: vi.fn(() => gsapTween),
  timeline: vi.fn(() => gsapTimeline),
  to: vi.fn(() => gsapTween),
  utils: {
    toArray: vi.fn(() => []),
  },
};

const scrollTriggerMock = {
  create: vi.fn(() => ({ kill: vi.fn() })),
  getAll: vi.fn(() => []),
  killAll: vi.fn(),
  refresh: vi.fn(),
};

// Cleanup after each test
afterEach(() => {
  cleanup();
});

// GSAP ScrollTrigger calls window.matchMedia in jsdom where it doesn't exist
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation((query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});

Object.defineProperty(window, 'requestAnimationFrame', {
  writable: true,
  value: vi.fn((callback: FrameRequestCallback) => window.setTimeout(() => callback(Date.now()), 16)),
});

Object.defineProperty(window, 'cancelAnimationFrame', {
  writable: true,
  value: vi.fn((handle: number) => window.clearTimeout(handle)),
});

Object.defineProperty(globalThis, 'requestAnimationFrame', {
  writable: true,
  value: window.requestAnimationFrame,
});

Object.defineProperty(globalThis, 'cancelAnimationFrame', {
  writable: true,
  value: window.cancelAnimationFrame,
});

// Animation libraries are exercised in the browser, not in jsdom unit tests.
vi.mock('gsap', () => ({
  default: gsapMock,
  gsap: gsapMock,
}));

vi.mock('gsap/ScrollTrigger', () => ({
  default: scrollTriggerMock,
  ScrollTrigger: scrollTriggerMock,
}));

// Mock Next.js router
vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: vi.fn(),
    replace: vi.fn(),
    prefetch: vi.fn(),
    back: vi.fn(),
  }),
  useSearchParams: () => ({
    get: vi.fn(),
    getAll: vi.fn(),
    toString: vi.fn(),
  }),
  usePathname: () => '/',
}));

// Mock Next.js Image component
vi.mock('next/image', () => ({
  default: ({ alt, priority: _priority, ...props }: any) => createElement('img', { alt, ...props }),
}));
