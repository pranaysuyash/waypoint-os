/**
 * URL State Management Utilities
 *
 * Helper functions for synchronizing state with URL search params.
 * This enables shareable links and browser history navigation.
 */

import { useSearchParams, useRouter, usePathname } from "next/navigation";

// ============================================================================
// TYPES
// ============================================================================

export type Serializable = string | number | boolean | null | undefined;
export type SerializedValue = string;

export interface UrlStateOptions {
  /**
   * Whether to replace the current history entry instead of pushing a new one
   * @default false
   */
  replace?: boolean;

  /**
   * Whether to scroll to top on navigation
   * @default false
   */
  scroll?: boolean;
}

// ============================================================================
// SERIALIZATION
// ============================================================================

function serialize(value: Serializable): SerializedValue | null {
  if (value === null || value === undefined) return null;
  if (typeof value === "boolean") return value ? "1" : "0";
  if (typeof value === "number") return value.toString();
  return value;
}

function deserialize(value: string | null): string | null {
  return value;
}

function deserializeBoolean(value: string | null): boolean {
  return value === "1";
}

function deserializeNumber(value: string | null): number | null {
  if (value === null) return null;
  const num = parseInt(value, 10);
  return isNaN(num) ? null : num;
}

// ============================================================================
// HOOKS
// ============================================================================

/**
 * Hook for managing a single URL search param as state
 *
 * @example
 * const [tab, setTab] = useUrlState("tab", "intake");
 */
export function useUrlState<T extends Serializable = string>(
  key: string,
  defaultValue: T,
  options?: UrlStateOptions
): [T, (value: T | ((prev: T) => T)) => void] {
  const searchParams = useSearchParams();
  const router = useRouter();
  const pathname = usePathname();

  // Read current value from URL
  const rawValue = searchParams.get(key);

  // Type-specific deserialization
  let currentValue: T;
  if (typeof defaultValue === "boolean") {
    currentValue = (rawValue === "1" ? true : rawValue === "0" ? false : defaultValue) as T;
  } else if (typeof defaultValue === "number") {
    currentValue = (deserializeNumber(rawValue) ?? defaultValue) as T;
  } else {
    currentValue = (rawValue ?? defaultValue) as T;
  }

  // Update function
  const setValue = (value: T | ((prev: T) => T)) => {
    const newValue = typeof value === "function" ? (value as (prev: T) => T)(currentValue) : value;
    const serialized = serialize(newValue);

    const params = new URLSearchParams(searchParams.toString());

    if (serialized === null) {
      params.delete(key);
    } else {
      params.set(key, serialized);
    }

    const url = `${pathname}?${params.toString()}`;
    const scroll = options?.scroll ?? false;

    if (options?.replace) {
      router.replace(url, { scroll });
    } else {
      router.push(url, { scroll });
    }
  };

  return [currentValue, setValue];
}

/**
 * Hook for managing multiple URL search params as state
 *
 * @example
 * const [state, setState] = useUrlStateMap({
 *   tab: "intake",
 *   view: "list",
 *   page: 1,
 * });
 */
export function useUrlStateMap<T extends Record<string, Serializable>>(
  defaultValues: T,
  options?: UrlStateOptions
): [T, (updates: Partial<T> | ((prev: T) => Partial<T>)) => void] {
  const searchParams = useSearchParams();
  const router = useRouter();
  const pathname = usePathname();

  // Read all values from URL
  const currentValues = Object.keys(defaultValues).reduce((acc, key) => {
    const rawValue = searchParams.get(key);
    const defaultValue = defaultValues[key as keyof T];

    if (typeof defaultValue === "boolean") {
      acc[key as keyof T] = (rawValue === "1" ? true : rawValue === "0" ? false : defaultValue) as T[keyof T];
    } else if (typeof defaultValue === "number") {
      acc[key as keyof T] = (deserializeNumber(rawValue) ?? defaultValue) as T[keyof T];
    } else {
      acc[key as keyof T] = (rawValue ?? defaultValue) as T[keyof T];
    }

    return acc;
  }, {} as T);

  // Update function
  const setValues = (updates: Partial<T> | ((prev: T) => Partial<T>)) => {
    const newUpdates = typeof updates === "function" ? updates(currentValues) : updates;
    const params = new URLSearchParams(searchParams.toString());

    // Apply updates
    Object.entries(newUpdates).forEach(([key, value]) => {
      const serialized = serialize(value);
      if (serialized === null) {
        params.delete(key);
      } else {
        params.set(key, serialized);
      }
    });

    const url = `${pathname}?${params.toString()}`;
    const scroll = options?.scroll ?? false;

    if (options?.replace) {
      router.replace(url, { scroll });
    } else {
      router.push(url, { scroll });
    }
  };

  return [currentValues, setValues];
}

/**
 * Hook for managing array values in URL (comma-separated)
 *
 * @example
 * const [tags, setTags] = useUrlArray("tags", []);
 */
export function useUrlArray(
  key: string,
  defaultValue: string[] = []
): [string[], (value: string[] | ((prev: string[]) => string[])) => void] {
  const searchParams = useSearchParams();
  const router = useRouter();
  const pathname = usePathname();

  const rawValue = searchParams.get(key);
  const currentValue = rawValue ? rawValue.split(",").filter(Boolean) : defaultValue;

  const setValue = (value: string[] | ((prev: string[]) => string[])) => {
    const newValue = typeof value === "function" ? value(currentValue) : value;
    const params = new URLSearchParams(searchParams.toString());

    if (newValue.length === 0) {
      params.delete(key);
    } else {
      params.set(key, newValue.join(","));
    }

    router.push(`${pathname}?${params.toString()}`, { scroll: false });
  };

  return [currentValue, setValue];
}

// ============================================================================
// URL BUILDERS
// ============================================================================

/**
 * Build a URL with search params from an object
 */
export function buildUrl(
  baseUrl: string,
  params: Record<string, Serializable>
): string {
  const searchParams = new URLSearchParams();

  Object.entries(params).forEach(([key, value]) => {
    const serialized = serialize(value);
    if (serialized !== null) {
      searchParams.set(key, serialized);
    }
  });

  const queryString = searchParams.toString();
  return queryString ? `${baseUrl}?${queryString}` : baseUrl;
}

/**
 * Parse search params into an object
 */
export function parseUrlParams(searchParams: URLSearchParams): Record<string, string> {
  const params: Record<string, string> = {};

  for (const [key, value] of searchParams.entries()) {
    params[key] = value;
  }

  return params;
}

// ============================================================================
// ZUSTAND MIDDLEWARE
// ============================================================================

/**
 * Zustand middleware to sync store state with URL
 *
 * @example
 * const useStore = create(
 *   urlStateMiddleware(
 *     (set) => ({ tab: "intake", view: "list" }),
 *     { tab: "tab", view: "view" }  // mapping: storeKey -> urlParam
 *   )
 * );
 */
export function urlStateMiddleware<T extends object>(
  stateMapping: Record<keyof T, string>
) {
  return (config: (set: any) => T) => (set: any, get: any, api: any) => {
    const store = config(set);

    // Listen to store changes and update URL
    api.subscribe((state: T, prevState: T) => {
      const url = new URL(window.location.href);

      Object.entries(stateMapping).forEach(([storeKey, urlKey]) => {
        const newValue = serialize(state[storeKey as keyof T] as Serializable);
        const prevValue = serialize(prevState[storeKey as keyof T] as Serializable);

        if (newValue !== prevValue) {
          if (newValue === null) {
            url.searchParams.delete(String(urlKey));
          } else {
            url.searchParams.set(String(urlKey), newValue);
          }
        }
      });

      const newUrl = url.toString();
      if (newUrl !== window.location.href) {
        window.history.replaceState(null, "", newUrl);
      }
    });

    return store;
  };
}
