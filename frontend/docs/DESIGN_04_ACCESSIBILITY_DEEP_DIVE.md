# DESIGN_04: Accessibility Deep Dive

> WCAG compliance, keyboard navigation, screen readers, and inclusive design

---

## Table of Contents

1. [Overview](#overview)
2. [WCAG Compliance](#wcag-compliance)
3. [Keyboard Navigation](#keyboard-navigation)
4. [Screen Reader Support](#screen-reader-support)
5. [Focus Management](#focus-management)
6. [Color and Contrast](#color-and-contrast)
7. [Text Scaling](#text-scaling)
8. [ARIA Attributes](#aria-attributes)
9. [Testing Checklist](#testing-checklist)

---

## Overview

### Accessibility Philosophy

Accessibility is not a feature — it's a fundamental aspect of good design. An accessible application works better for everyone:

```
┌─────────────────────────────────────────────────────────────────┐
│                     ACCESSIBILITY SPECTRUM                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Permanent  •  Temporary  •  Situational                        │
│  Disabilities   Conditions        Contexts                      │
│                                                                  │
│  ┌─────────┐   ┌─────────┐   ┌─────────┐                        │
│  │ Blind   │   │ Broken  │   │ Bright  │                        │
│  │         │   │ Arm     │   │ Sunlight│                        │
│  └─────────┘   └─────────┘   └─────────┘                        │
│        ↓              ↓              ↓                          │
│        └──────────────┴──────────────┘                          │
│                    ↓                                            │
│            Accessible Design                                   │
│            (Benefits Everyone)                                  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### The POUR Principles

WCAG 2.1 is built on four principles:

| Principle | Description | Examples |
|-----------|-------------|----------|
| **Perceivable** | Info must be presentable in ways users can perceive | Alt text, captions, color contrast |
| **Operable** | UI components must be operable | Keyboard navigation, no traps |
| **Understandable** | Info and UI must be understandable | Clear labels, consistent navigation |
| **Robust** | Content must be robust enough for all user agents | Semantic HTML, ARIA |

### Compliance Targets

```
┌─────────────────────────────────────────────────────────────────┐
│                    WCAG 2.1 COMPLIANCE LEVELS                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Level A (Minimum)                                               │
│  • Keyboard accessible                                          │
│  • Non-text content has alt text                                │
│  • Captions for video                                           │
│                                                                  │
│  Level AA (Target) ━━━━━━━━━━━━━━━━━━━━━━━━━━━━                 │
│  • Color contrast 4.5:1 for text                                 │
│  • Resizable text up to 200%                                    │
│  • No keyboard traps                                            │
│  • Focus visible                                                │
│                                                                  │
│  Level AAA (Enhanced)                                           │
│  • Sign language for video                                      │
│  • Color contrast 7:1 for text                                  │
│  • No time limits                                               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## WCAG Compliance

### Success Criteria Mapping

| Category | Criteria | Implementation |
|----------|----------|----------------|
| **Images** | 1.1.1 Non-text Content | Alt text, decorative images |
| **Audio/Video** | 1.2.1-5 Captions & Audio | Captions, transcripts, audio descriptions |
| **Adaptable** | 1.3.1-5 Info & Relationships | Semantic HTML, proper heading structure |
| **Distinguishable** | 1.4.1-12 Color, Contrast, Audio | Contrast ratios, no color-only meaning |
| **Keyboard** | 2.1.1-4 Keyboard Access | All functions available via keyboard |
| **Enough Time** | 2.2.1-3 Timing Adjustable | Adjustable timeouts, pause controls |
| **Seizures** | 2.3.1-3 Flashing Content | No >3 flashes/second |
| **Navigable** | 2.4.1-10 Help, Navigation | Skip links, breadcrumbs, focus order |
| **Readable** | 3.1.1-6 Language & Content | Lang attribute, consistent terminology |
| **Predictable** | 3.2.1-4 Consistent Behavior | Consistent layout, no context changes |
| **Input Assistance** | 3.3.1-8 Error Prevention | Labels, error suggestions, confirmations |
| **Compatible** | 4.1.1-3 Name, Role, Value | Semantic markup, ARIA, error handling |

### Accessibility Declaration

```typescript
// Accessibility statement page component
export const AccessibilityStatement: React.FC = () => {
  return (
    <Document>
      <H1>Accessibility Statement</H1>

      <Section>
        <H2>Our Commitment</H2>
        <P>
          We are committed to ensuring digital accessibility for people with
          disabilities. We are continually improving the user experience for
          everyone and applying the relevant accessibility standards.
        </P>
      </Section>

      <Section>
        <H2>Conformance Status</H2>
        <P>
          The Travel Agency Agent Workspace is partially conformant with
          <strong>WCAG 2.1 Level AA</strong>. Partially conformant means that
          some parts of the content do not fully conform to the accessibility
          standard.
        </P>

        <KnownIssues>
          <H3>Known Accessibility Issues</H3>
          <ul>
            <li>Some third-party integrations may have limited accessibility</li>
            <li>Legacy screens are being migrated to accessible components</li>
            <li>Some complex visualizations may lack alternative text</li>
          </ul>
        </KnownIssues>
      </Section>

      <Section>
        <H2>Feedback</H2>
        <P>
          We welcome your feedback on the accessibility of this application.
          Please let us know if you encounter accessibility barriers:
        </P>
        <Link href="mailto:accessibility@example.com">
          accessibility@example.com
        </Link>
      </Section>
    </Document>
  );
};
```

---

## Keyboard Navigation

### Tab Order and Focus

```
┌─────────────────────────────────────────────────────────────────┐
│                     KEYBOARD NAVIGATION                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Tab     → Move focus to next element                           │
│  Shift+Tab → Move focus to previous element                     │
│  Enter   → Activate button/link, submit form                    │
│  Space   → Toggle checkbox/radio, toggle button                 │
│  Arrow   → Navigate within composite (tabs, radio group)        │
│  Esc     → Close modal, dropdown, return focus                  │
│  Home/End → Jump to start/end of list                           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Skip Links

Allow keyboard users to skip repetitive navigation:

```typescript
export const SkipLinks: React.FC = () => {
  return (
    <>
      <SkipLink href="#main-content">Skip to main content</SkipLink>
      <SkipLink href="#navigation">Skip to navigation</SkipLink>

      <SkipLink href="#search" variant="secondary">
        Skip to search
      </SkipLink>
    </>
  );
};

const SkipLink = styled('a', {
  position: 'absolute',
  top: '-40px',
  left: 0,
  backgroundColor: '$primary600',
  color: '$white',
  padding: '$space$2 $space$4',
  zIndex: 100,

  '&:focus': {
    top: 0,
  },

  variants: {
    variant: {
      secondary: {
        left: '200px',
        backgroundColor: '$neutral600',
      },
    },
  },
};
```

### Keyboard Trap Prevention

Never trap keyboard focus in a component:

```typescript
// Ensure focus can always escape
export const useFocusTrap = (enabled: boolean) => {
  const containerRef = useRef<HTMLElement>(null);

  useEffect(() => {
    if (!enabled || !containerRef.current) return;

    const container = containerRef.current;
    const focusableElements = container.querySelectorAll<HTMLElement>(
      'a[href], button:not([disabled]), textarea:not([disabled]), ' +
      'input:not([disabled]), select:not([disabled]), ' +
      '[tabindex]:not([tabindex="-1"])'
    );

    if (focusableElements.length === 0) return;

    const firstElement = focusableElements[0];
    const lastElement = focusableElements[focusableElements.length - 1];

    const handleTab = (e: KeyboardEvent) => {
      if (e.key !== 'Tab') return;

      // Shift+Tab on first element → cycle to last
      if (e.shiftKey && document.activeElement === firstElement) {
        e.preventDefault();
        lastElement.focus();
      }
      // Tab on last element → cycle to first
      else if (!e.shiftKey && document.activeElement === lastElement) {
        e.preventDefault();
        firstElement.focus();
      }
    };

    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        // Return focus to trigger element
        const trigger = document.querySelector(
          '[aria-expanded="true"]'
        ) as HTMLElement;
        trigger?.focus();
      }
    };

    // Focus first element when trap activates
    firstElement.focus();

    container.addEventListener('keydown', handleTab);
    document.addEventListener('keydown', handleEscape);

    return () => {
      container.removeEventListener('keydown', handleTab);
      document.removeEventListener('keydown', handleEscape);
    };
  }, [enabled]);

  return containerRef;
};
```

### Focus Visible Styles

Always show focus indicator for keyboard navigation:

```css
/* Hide focus ring for mouse users */
:focus:not(:focus-visible) {
  outline: none;
}

/* Show focus ring for keyboard users */
:focus-visible {
  outline: 2px solid $primary500;
  outline-offset: 2px;
}
```

```typescript
// Stitches implementation
export const focusVisibleStyles = {
  '&:focus': {
    outline: 'none',
  },
  '&:focus-visible': {
    outline: '2px solid $primary500',
    outlineOffset: '2px',
  },
};
```

---

## Screen Reader Support

### Semantic HTML

Screen readers rely on proper HTML semantics:

```typescript
// ❌ Bad: Non-semantic divs
<div onClick={handleClick}>Click me</div>

// ✅ Good: Semantic button
<button onClick={handleClick}>Click me</button>

// ❌ Bad: Div as heading
<div className="text-xl font-bold">Heading</div>

// ✅ Good: Semantic heading
<h1>Heading</h1>

// ❌ Bad: Span as button
<span onClick={handleSubmit}>Submit</span>

// ✅ Good: Button with proper type
<button type="submit">Submit</button>
```

### Heading Structure

Maintain proper heading hierarchy:

```
┌─────────────────────────────────────────────────────────────────┐
│                      HEADING HIERARCHY                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  <h1> Trip Details         (Page title - one per page)          │
│    │                                                           │
│    ├─ <h2> Customer          (Major section)                    │
│    │    │                                                     │
│    │    └─ <h3> Contact Info   (Subsection)                    │
│    │                                                           │
│    ├─ <h2> Itinerary         (Major section)                    │
│    │    │                                                     │
│    │    └─ <h3> Flights         (Subsection)                    │
│    │         │                                                │
│    │         └─ <h4> Departure    (Sub-subsection)             │
│    │                                                           │
│    └─ <h2> Pricing           (Major section)                    │
│                                                                  │
│  Rules:                                                         │
│  • Never skip levels (h1 → h3)                                  │
│  • Don't use headings for styling                               │
│  • One h1 per page                                              │
│  • Headings should describe content                             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Live Regions

Announce dynamic content changes:

```typescript
interface LiveRegionProps {
  message: string;
  politeness?: 'polite' | 'assertive' | 'off';
  role?: 'status' | 'alert';
}

export const LiveRegion: React.FC<LiveRegionProps> = ({
  message,
  politeness = 'polite',
  role = 'status',
}) => {
  return (
    <div
      aria-live={politeness}
      aria-atomic="true"
      role={role}
      style={{ position: 'absolute', left: '-10000px', width: '1px', height: '1px' }}
    >
      {message}
    </div>
  );
};

// Usage: Announce form errors
export const FormErrors: React.FC<{ errors: string[] }> = ({ errors }) => {
  return (
    <>
      {errors.length > 0 && (
        <LiveRegion
          message={`Form has ${errors.length} errors: ${errors.join(', ')}`}
          role="alert"
          politeness="assertive"
        />
      )}
      <ErrorList>
        {errors.map((error, i) => (
          <ErrorItem key={i}>{error}</ErrorItem>
        ))}
      </ErrorList>
    </>
  );
};
```

### Screen Reader Only Text

Hide visual content but keep it accessible to screen readers:

```typescript
export const VisuallyHidden: React.FC<{
  children: React.ReactNode;
  focusable?: boolean;
}> = ({ children, focusable = false }) => {
  return (
    <span
      style={{
        position: 'absolute',
        width: '1px',
        height: '1px',
        padding: 0,
        margin: '-1px',
        overflow: 'hidden',
        clip: 'rect(0, 0, 0, 0)',
        whiteSpace: 'nowrap',
        border: 0,
        ...(focusable && {
          position: 'static',
          width: 'auto',
          height: 'auto',
          overflow: 'visible',
          clip: 'auto',
          whiteSpace: 'normal',
        }),
      }}
    >
      {children}
    </span>
  );
};

// Usage: Add context to icon-only buttons
<Button>
  <Icon name="search" />
  <VisuallyHidden>Search</VisuallyHidden>
</Button>
```

---

## Focus Management

### Modal Focus

Trap focus within modals and return it on close:

```typescript
export const useModalFocus = (
  open: boolean,
  close: () => void
) => {
  const modalRef = useRef<HTMLDivElement>(null);
  const previousActiveElement = useRef<HTMLElement | null>(null);

  // Save focus when modal opens
  useEffect(() => {
    if (open) {
      previousActiveElement.current = document.activeElement as HTMLElement;

      // Focus first focusable element in modal
      setTimeout(() => {
        const firstFocusable = modalRef.current?.querySelector<HTMLElement>(
          'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        firstFocusable?.focus();
      }, 0);
    } else {
      // Return focus to trigger when modal closes
      previousActiveElement.current?.focus();
    }
  }, [open]);

  // Handle Escape key
  useEffect(() => {
    if (!open) return;

    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        close();
      }
    };

    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [open, close]);

  return { modalRef, trap: useFocusTrap(open) };
};
```

### Programmatic Focus

Set focus after navigation or action:

```typescript
// Focus management after form submission
export const useFormFocus = () => {
  const firstErrorRef = useRef<HTMLInputElement>(null);

  const focusFirstError = useCallback(() => {
    setTimeout(() => {
      firstErrorRef.current?.focus();
      firstErrorRef.current?.scrollIntoView({
        behavior: 'smooth',
        block: 'center',
      });
    }, 100);
  }, []);

  return { firstErrorRef, focusFirstError };
};

// Usage in form
const Form: React.FC = () => {
  const { firstErrorRef, focusFirstError } = useFormFocus();

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    const errors = validate();
    if (errors.length > 0) {
      focusFirstError();
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <FormField
        ref={errors.name ? firstErrorRef : undefined}
        error={errors.name}
        label="Name"
        required
      />
    </form>
  );
};
```

---

## Color and Contrast

### WCAG AA Contrast Requirements

```
┌─────────────────────────────────────────────────────────────────┐
│                    CONTRAST RATIO REQUIREMENTS                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Normal Text (14px+)                                             │
│  • AA  : 4.5:1  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━                   │
│  • AAA : 7:1    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━              │
│                                                                  │
│  Large Text (18.66px+ / 14pt+ / Bold 16px+)                      │
│  • AA  : 3:1    ━━━━━━━━━━━━━━                                  │
│  • AAA : 4.5:1  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━                   │
│                                                                  │
│  UI Components (icons, borders)                                  │
│  • AA  : 3:1    ━━━━━━━━━━━━━━                                  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Token-Based Contrast

Define tokens with guaranteed contrast:

```typescript
// Design tokens with WCAG AA compliance
export const colors = {
  // Primary - 4.72:1 on white (passes AA)
  primary: {
    50: '#EEF2FF',
    100: '#E0E7FF',
    200: '#C7D2FE',
    300: '#A5B4FC',
    400: '#818CF8',
    500: '#6366F1',  // Primary
    600: '#4F46E5',  // 7.34:1 on white (passes AAA)
    700: '#4338CA',
    800: '#3730A3',
    900: '#312E81',
  },

  // Semantic colors
  success: {
    500: '#10B981',  // 3.87:1 on white (use white text)
    600: '#059669',  // 4.61:1 on white (passes AA)
  },
  error: {
    500: '#EF4444',  // 3.94:1 on white (use white text)
    600: '#DC2626',  // 4.56:1 on white (passes AA)
  },
  warning: {
    500: '#F59E0B',  // 2.99:1 on white (use dark text)
    600: '#D97706',  // 3.74:1 on white
  },

  // Neutral scale
  neutral: {
    50: '#FAFAFA',
    100: '#F5F5F5',
    200: '#E5E5E5',
    300: '#D4D4D4',
    400: '#A3A3A3',
    500: '#737373',  // 5.08:1 on white (passes AA)
    600: '#525252',  // 7.26:1 on white (passes AAA)
    700: '#404040',
    800: '#262626',
    900: '#171717',
  },
};
```

### Color Independence

Never rely on color alone to convey meaning:

```typescript
// ❌ Bad: Color only
<span style={{ color: 'red' }}>Required</span>
<span style={{ color: 'green' }}>Complete</span>

// ✅ Good: Color + text/icon
<span style={{ color: 'red' }}>
  <Icon name="asterisk" aria-label="required" />
  Required
</span>
<span style={{ color: 'green' }}>
  <Icon name="check-circle" aria-label="complete" />
  Complete
</span>

// Form validation example
interface ValidationMessageProps {
  type: 'error' | 'success' | 'warning';
  message: string;
}

export const ValidationMessage: React.FC<ValidationMessageProps> = ({
  type,
  message,
}) => {
  const icons = {
    error: 'alert-circle',
    success: 'check-circle',
    warning: 'alert-triangle',
  };

  return (
    <Message type={type} role="alert">
      <Icon name={icons[type]} aria-hidden="true" />
      <span>{message}</span>
    </Message>
  );
};
```

### Dark Mode Contrast

Ensure contrast in both themes:

```typescript
export const useAccessibleTheme = () => {
  const theme = useTheme();

  // Select text color based on background
  const getTextColor = (bg: string) => {
    const luminance = getLuminance(bg);
    return luminance > 0.5 ? theme.colors.neutral900 : theme.colors.neutral50;
  };

  // Get contrast-safe variant
  const getVariant = (variant: string, bg: string) => {
    const contrast = getContrast(
      theme.colors[variant]?.[500],
      bg
    );
    return contrast >= 4.5 ? 500 : 600;
  };

  return { getTextColor, getVariant };
};
```

---

## Text Scaling

### Responsive Typography

Text must be readable at 200% zoom:

```typescript
// Use relative units for text sizing
export const typography = {
  // Base size that user can override in browser
  base: '16px',  // 100% = 16px default

  // Scale using rem (relative to root)
  fontSizes: {
    xs: '0.75rem',    // 12px
    sm: '0.875rem',   // 14px
    base: '1rem',     // 16px
    lg: '1.125rem',   // 18px
    xl: '1.25rem',    // 20px
    '2xl': '1.5rem',  // 24px
    '3xl': '1.875rem', // 30px
    '4xl': '2.25rem', // 36px
  },

  // Line height scales with font size
  lineHeights: {
    tight: 1.25,
    normal: 1.5,
    relaxed: 1.75,
  },
};

// Allow horizontal scrolling at 200% zoom
export const ScalableText = styled('p', {
  fontSize: '1rem',
  lineHeight: 1.5,
  // Don't set fixed height or use text-overflow: ellipsis
  // Allow container to grow
  minHeight: '1.5em',
});
```

### Container Queries

Handle layout changes from text scaling:

```typescript
export const ScalableContainer = styled('div', {
  // Use container queries for responsive layout
  containerType: 'inline-size',

  // At small container sizes (from zoom), stack vertically
  '@container (max-width: 400px)': {
    flexDirection: 'column',
  },
});
```

---

## ARIA Attributes

### ARIA Roles

Map components to semantic roles:

```typescript
// Custom checkbox component
export const Checkbox: React.FC<CheckboxProps> = ({
  checked,
  onChange,
  disabled,
  children,
}) => {
  return (
    <CheckboxLabel>
      <HiddenCheckbox
        type="checkbox"
        checked={checked}
        onChange={onChange}
        disabled={disabled}
        aria-checked={checked}
      />
      <VisualCheckbox
        role="checkbox"
        aria-checked={checked}
        aria-disabled={disabled}
        tabIndex={disabled ? -1 : 0}
        onKeyDown={(e) => {
          if (e.key === ' ' || e.key === 'Enter') {
            e.preventDefault();
            onChange?.(!checked);
          }
        }}
      >
        {checked && <Icon name="check" size="sm" />}
      </VisualCheckbox>
      <CheckboxText>{children}</CheckboxText>
    </CheckboxLabel>
  );
};
```

### ARIA Labels and Descriptions

Provide accessible names:

```typescript
// Icon-only button needs accessible label
<Button
  aria-label="Close dialog"
  onClick={onClose}
>
  <Icon name="x" />
</Button>

// Complex widget needs description
<div role="region" aria-labelledby="search-title" aria-describedby="search-desc">
  <h2 id="search-title">Search Trips</h2>
  <p id="search-desc">Search by destination, customer name, or dates</p>
  <SearchInput />
</div>

// Input with error description
<div>
  <Input
    id="email"
    aria-invalid={!!error}
    aria-errormessage="email-error"
    aria-describedby={helper ? "email-helper" : undefined}
  />
  {helper && <span id="email-helper">{helper}</span>}
  {error && (
    <span id="email-error" role="alert">
      {error}
    </span>
  )}
</div>
```

### ARIA States and Properties

Common ARIA attributes:

| Attribute | Use Case | Values |
|-----------|----------|--------|
| `aria-expanded` | Toggle buttons, menus | true, false, undefined |
| `aria-pressed` | Toggle buttons | true, false, mixed |
| `aria-selected` | Tabs, list items | true, false, undefined |
| `aria-disabled` | Disabled state | true, false |
| `aria-hidden` | Hide from screen readers | true, false |
| `aria-invalid` | Form validation | true, false, grammar, spelling |
| `aria-required` | Required fields | true, false |
| `aria-live` | Dynamic content | polite, assertive, off |
| `aria-current` | Current page/step | page, step, location, date, time |

---

## Testing Checklist

### Automated Testing

```typescript
// Jest + jest-axe for accessibility testing
import { axe, toHaveNoViolations } from 'jest-axe';

expect.extend(toHaveNoViolations);

describe('TripList accessibility', () => {
  it('should not have accessibility violations', async () => {
    const { container } = render(<TripList />);
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});

// Storybook accessibility addon
// .storybook/test.tsx
import { composeStories } from '@storybook/testing-react';
import * as stories from './Button.stories';
import { axeTest } from './test-utils';

const storiesToTest = composeStories(stories);

describe('Button accessibility', () => {
  storiesToTest.forEach((Story) => {
    it(`${Story.storyName} should pass accessibility tests`, async () => {
      const { container } = render(<Story />);
      await axeTest(container);
    });
  });
});
```

### Manual Testing Checklist

```
┌─────────────────────────────────────────────────────────────────┐
│                   ACCESSIBILITY TESTING CHECKLIST                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Keyboard Navigation                                             │
│  □ Can navigate entire interface with Tab/Shift+Tab             │
│  □ Focus order is logical                                       │
│  □ Focus indicator is always visible                            │
│  □ Can activate all interactive elements with Enter/Space       │
│  □ Escape key closes modals/dropdowns                           │
│  □ Arrow keys work in composites (tabs, radios)                 │
│  □ No keyboard traps                                             │
│                                                                  │
│  Screen Reader                                                   │
│  □ Announces page title                                         │
│  □ Heading hierarchy is correct                                 │
│  □ Links and buttons have descriptive names                     │
│  □ Form inputs have associated labels                           │
│  □ Errors are announced                                         │
│  □ Dynamic content changes are announced                        │
│  □ Hidden content is not read                                   │
│                                                                  │
│  Visual                                                          │
│  □ Color contrast meets WCAG AA (4.5:1 for text)                │
│  □ Not color-dependent for meaning                              │
│  □ Text is readable at 200% zoom                                │
│  □ No horizontal scroll at 320px width                          │
│  □ Custom focus indicators are visible                          │
│                                                                  │
│  Forms                                                           │
│  □ All inputs have labels                                       │
│  □ Required fields are indicated                                │
│  □ Error messages are specific and helpful                      │
│  □ Validation happens on submit or after blur                   │
│  □ Success/error states are announced                           │
│                                                                  │
│  Content                                                         │
│  □ Images have alt text                                         │
│  □ Decorative images are marked aria-hidden                     │
│  □ Videos have captions                                         │
│  □ Tables have proper headers                                   │
│  □ Lists use semantic HTML                                      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Browser Testing Tools

| Tool | Purpose |
|------|---------|
| **axe DevTools** | Chrome extension for automated testing |
| **WAVE** | Visual accessibility feedback |
| **Lighthouse** | CI-friendly accessibility audit |
| **NVDA/JAWS** | Windows screen reader testing |
| **VoiceOver** | macOS screen reader testing |
| **Keyboard only** | Unplug mouse and test everything |

---

## Quick Reference

### Common Accessibility Mistakes

| Mistake | Fix |
|---------|-----|
| `div` with `onClick` | Use `<button>` or add `role="button"`, `tabIndex="0"` |
| `placeholder` as label | Use `<label>` element |
| Low contrast icons | Ensure 3:1 contrast against background |
| Color-only status | Add icon or text label |
| Empty alt text | Describe image content, use `alt=""` for decorative |
| Fixed container heights | Allow growth for text scaling |
| `outline: none` | Use `:focus:not(:focus-visible)` instead |

### Accessibility First Development

1. **Use semantic HTML first** - divs are a last resort
2. **Keyboard test early** - catch issues before they spread
3. **Include a11y in PR reviews** - make it part of definition of done
4. **Test with real users** - automated tools catch ~40% of issues
5. **Document component a11y** - note keyboard behavior, ARIA patterns

---

**Last Updated:** 2026-04-25

**Series Complete:** Design System Deep Dive Series (4/4 documents)
