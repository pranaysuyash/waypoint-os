/**
 * Accessibility Utilities
 *
 * Helper functions and constants for implementing accessible UI components.
 */

// ============================================================================
// ARIA ROLES
// ============================================================================

export const ARIA_ROLES = {
  navigation: "navigation",
  main: "main",
  complementary: "complementary",
  banner: "banner",
  contentinfo: "contentinfo",
  form: "form",
  search: "search",
  article: "article",
  region: "region",
  img: "img",
  button: "button",
  link: "link",
  dialog: "dialog",
  alertdialog: "alertdialog",
  alert: "alert",
  status: "status",
  log: "log",
  marquee: "marquee",
  timer: "timer",
  tooltip: "tooltip",
  tablist: "tablist",
  tab: "tab",
  tabpanel: "tabpanel",
  listbox: "listbox",
  option: "option",
  combobox: "combobox",
  menu: "menu",
  menuitem: "menuitem",
} as const;

const FOCUSABLE_ELEMENT_SELECTOR =
  'a[href], button:not([disabled]), textarea:not([disabled]), input:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])';

let bodyScrollLockCount = 0;
let previousBodyOverflow = '';

// ============================================================================
// ARIA PROPERTIES
// ============================================================================

/**
 * Generate ARIA props for a landmark region
 */
export function landmarkProps(label: string) {
  return {
    "aria-label": label,
    role: ARIA_ROLES.region,
  };
}

/**
 * Generate ARIA props for a navigation landmark
 */
export function navProps(label: string) {
  return {
    "aria-label": label,
    role: ARIA_ROLES.navigation,
  };
}

/**
 * Generate ARIA props for live region (announces changes to screen readers)
 */
export function liveRegionProps(polite: boolean = true) {
  return {
    "aria-live": polite ? "polite" : "assertive",
    "aria-atomic": "true",
  };
}

/**
 * Generate ARIA props for a button with an icon
 */
export function iconButtonProps(label: string) {
  return {
    "aria-label": label,
    role: ARIA_ROLES.button,
  };
}

/**
 * Generate ARIA props for a tab
 */
export function tabProps(id: string, selected: boolean, controlsId: string) {
  return {
    id,
    role: ARIA_ROLES.tab,
    "aria-selected": selected,
    "aria-controls": controlsId,
    tabIndex: selected ? 0 : -1,
  };
}

/**
 * Generate ARIA props for a tab panel
 */
export function tabPanelProps(id: string, labelledBy: string) {
  return {
    id,
    role: ARIA_ROLES.tabpanel,
    "aria-labelledby": labelledBy,
    tabIndex: 0,
  };
}

/**
 * Generate ARIA props for a status indicator
 */
export function statusProps(label: string) {
  return {
    role: ARIA_ROLES.status,
    "aria-live": "polite",
    "aria-label": label,
  };
}

// ============================================================================
// KEYBOARD INTERACTION HELPERS
// ============================================================================

/**
 * Handle keyboard navigation for a list of items (arrow keys)
 * Returns the new index after navigation
 */
export function handleListNavigation(
  event: React.KeyboardEvent,
  currentIndex: number,
  itemCount: number,
  orientation: "horizontal" | "vertical" = "horizontal"
): number | null {
  const isVertical = orientation === "vertical";
  const nextKey = isVertical ? "ArrowDown" : "ArrowRight";
  const prevKey = isVertical ? "ArrowUp" : "ArrowLeft";

  switch (event.key) {
    case nextKey:
      event.preventDefault();
      return (currentIndex + 1) % itemCount;
    case prevKey:
      event.preventDefault();
      return (currentIndex - 1 + itemCount) % itemCount;
    case "Home":
      event.preventDefault();
      return 0;
    case "End":
      event.preventDefault();
      return itemCount - 1;
    default:
      return null;
  }
}

/**
 * Handle keyboard activation (Enter or Space)
 */
export function handleActivation(event: React.KeyboardEvent, callback: () => void) {
  if (event.key === "Enter" || event.key === " ") {
    event.preventDefault();
    callback();
  }
}

/**
 * Handle escape key press
 */
export function handleEscape(event: React.KeyboardEvent, callback: () => void) {
  if (event.key === "Escape") {
    event.preventDefault();
    callback();
  }
}

// ============================================================================
// FOCUS MANAGEMENT
// ============================================================================

/**
 * Shared focus conventions:
 * - Use explicit role/labeling + keyboard handlers on the trigger/menu root.
 * - On Tab from popups/overlays, close then move to next focusable control
 *   outside the current surface to avoid traps.
 * - Use `getFocusableElements(document)` to discover candidates and keep
 *   ordering stable with DOM source order.
 */

/**
 * Get focusable elements within a container (excluding hidden/disabled controls).
 */
export function getFocusableElements(container: ParentNode | null): HTMLElement[] {
  if (!container) return [];

  return Array.from(container.querySelectorAll<HTMLElement>(FOCUSABLE_ELEMENT_SELECTOR)).filter(
    (focusable) => !focusable.hasAttribute("disabled") && focusable.tabIndex !== -1
  );
}

/**
 * Toggle body overflow lock for modal-like surfaces.
 */
export function lockBodyScroll(): () => void {
  if (typeof document === "undefined") return () => {};

  if (bodyScrollLockCount === 0) {
    previousBodyOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
  }

  bodyScrollLockCount += 1;

  return () => {
    bodyScrollLockCount = Math.max(0, bodyScrollLockCount - 1);
    if (bodyScrollLockCount === 0) {
      document.body.style.overflow = previousBodyOverflow;
    }
  };
}

/**
 * Trap focus within an element (for modals/dialogs)
 */
export function trapFocus(
  element: HTMLElement,
  options: { initialFocus?: HTMLElement | null } = {}
): () => void {
  const handleTabKey = (e: KeyboardEvent) => {
    if (e.key !== "Tab") return;

    const focusableElements = getFocusableElements(element);
    if (focusableElements.length === 0) return;

    const firstFocusable = focusableElements[0] as HTMLElement;
    const lastFocusable = focusableElements[focusableElements.length - 1] as HTMLElement;

    if (e.shiftKey) {
      if (document.activeElement === firstFocusable) {
        e.preventDefault();
        lastFocusable.focus();
      }
    } else if (document.activeElement === lastFocusable) {
      e.preventDefault();
      firstFocusable.focus();
    }
  };

  const initialFocus = options.initialFocus && getFocusableElements(element).includes(options.initialFocus)
    ? options.initialFocus
    : getFocusableElements(element)[0];

  initialFocus?.focus();
  element.addEventListener("keydown", handleTabKey);

  // Return cleanup function
  return () => {
    element.removeEventListener("keydown", handleTabKey);
  };
}

/**
 * Move focus to next/previous element
 */
export function moveFocus(direction: "next" | "previous", container?: HTMLElement) {
  const focusable = getFocusableElements(document);
  const currentIndex = focusable.indexOf(document.activeElement as HTMLElement);
  const scoped = container
    ? focusable.filter((el) => container.contains(el))
    : focusable;

  if (direction === "next") {
    const nextEl = scoped[currentIndex + 1] || scoped[0];
    nextEl?.focus();
  } else {
    const prevEl = scoped[currentIndex - 1] || scoped[scoped.length - 1];
    prevEl?.focus();
  }
}

/**
 * Move focus to the next focusable element outside a container.
 */
export function focusNextOutside(
  container: ParentNode | null,
  options: {
    from?: Element | null;
    fallbackFrom?: Element | null;
  } = {}
): void {
  if (!container) return;

  const focusable = getFocusableElements(document);

  const preferred = options.from instanceof HTMLElement
    ? options.from
    : options.fallbackFrom instanceof HTMLElement
      ? options.fallbackFrom
      : null;

  let startIndex = preferred ? focusable.indexOf(preferred) : -1;

  if (startIndex === -1) {
    const inContainerIndexes = focusable
      .map((element, index) => ({ element, index }))
      .filter(({ element }) => container.contains(element))
      .map(({ index }) => index);
    if (inContainerIndexes.length > 0) {
      startIndex = Math.max(...inContainerIndexes);
    }
  }

  if (startIndex >= 0) {
    for (let i = startIndex + 1; i < focusable.length; i += 1) {
      const candidate = focusable[i];
      if (!container.contains(candidate)) {
        candidate.focus();
        return;
      }
    }
  }

  const firstOutside = focusable.find((element) => !container.contains(element));
  if (firstOutside) {
    firstOutside.focus();
    return;
  }

  preferred?.blur();
}

// ============================================================================
// ID GENERATION
// ============================================================================

let idCounter = 0;

/**
 * Generate a unique ID for accessibility relationships
 */
export function generateId(prefix: string = "id"): string {
  return `${prefix}-${++idCounter}`;
}

/**
 * Generate linked IDs for aria-labelledby/aria-describedby
 */
export function generateLinkedIds(prefix: string) {
  const base = generateId(prefix);
  return {
    label: `${base}-label`,
    description: `${base}-description`,
    error: `${base}-error`,
  };
}

/**
 * Generate linked IDs for dialog-like surfaces.
 */
export function surfaceIds(prefix: string) {
  const base = generateId(prefix);
  return {
    panel: `${base}-panel`,
    title: `${base}-title`,
    description: `${base}-description`,
    menu: `${base}-menu`,
  };
}

/**
 * Toggle aria-hidden/inert on siblings to keep non-active surfaces out of accessibility tree.
 */
export function withInertSiblings(layer: HTMLElement, active: boolean): () => void {
  if (typeof document === "undefined") return () => {};

  const parent = layer.parentElement;
  if (!parent) return () => {};

  const siblings = Array.from(parent.children)
    .filter((child) => child !== layer)
    .map((sibling) => {
      const previousAriaHidden = sibling.getAttribute("aria-hidden");
      const previousInert = (sibling as HTMLElement).inert;

      if (active) {
        sibling.setAttribute("aria-hidden", "true");
        (sibling as HTMLElement).inert = true;
      }

      return {
        sibling: sibling as HTMLElement,
        previousAriaHidden,
        previousInert,
      };
    });

  return () => {
    for (const { sibling, previousAriaHidden, previousInert } of siblings) {
      if (previousAriaHidden === null) {
        sibling.removeAttribute("aria-hidden");
      } else {
        sibling.setAttribute("aria-hidden", previousAriaHidden);
      }

      sibling.inert = previousInert;
    }
  };
}

// ============================================================================
// SCREEN READER ANNOUNCEMENTS
// ============================================================================

/**
 * Announce a message to screen readers
 * Requires a live region element in the DOM
 */
export function announceToScreenReader(message: string, priority: "polite" | "assertive" = "polite") {
  const liveRegion = document.getElementById(`sr-announcement-${priority}`);

  if (liveRegion) {
    liveRegion.textContent = message;
    // Clear after announcement to allow re-announcing same message
    setTimeout(() => {
      liveRegion.textContent = "";
    }, 1000);
  }
}

/**
 * Render the live region elements for announcements
 * Add this component once at the root of your app
 */
export function LiveRegion() {
  return (
    <>
      <div id="sr-announcement-polite" aria-live="polite" aria-atomic="true" className="sr-only" />
      <div id="sr-announcement-assertive" aria-live="assertive" aria-atomic="true" className="sr-only" />
    </>
  );
}
