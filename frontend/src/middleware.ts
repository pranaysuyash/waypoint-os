/**
 * Next.js Edge Middleware
 *
 * Canonical edge middleware convention for Next.js (under src/ directory).
 * Delegates to proxy handler in src/proxy.ts, ensuring edge auth and
 * navigation boundary runs during request lifecycle.
 */

export { default, config } from './proxy';
