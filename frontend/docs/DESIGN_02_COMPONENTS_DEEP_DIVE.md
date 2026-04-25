# Design System — Component Library Deep Dive

> UI components, variants, composition, and component API

---

## Document Overview

**Series:** Design System | **Document:** 2 of 4 | **Focus:** Component Library

**Related Documents:**
- [01: Design Tokens Deep Dive](./DESIGN_01_TOKENS_DEEP_DIVE.md) — Foundation tokens
- [03: Patterns Deep Dive](./DESIGN_03_PATTERNS_DEEP_DIVE.md) — UX patterns
- [04: Accessibility Deep Dive](./DESIGN_04_ACCESSIBILITY_DEEP_DIVE.md) — WCAG compliance

---

## Table of Contents

1. [Component Architecture](#1-component-architecture)
2. [Primitive Components](#2-primitive-components)
3. [Form Components](#3-form-components)
4. [Feedback Components](#4-feedback-components)
5. [Layout Components](#5-layout-components)
6. [Navigation Components](#6-navigation-components)
7. [Data Display Components](#7-data-display-components)
8. [Overlay Components](#8-overlay-components)

---

## 1. Component Architecture

### 1.1 Component Hierarchy

```
┌────────────────────────────────────────────────────────────────────────────┐
│                         COMPONENT HIERARCHY                               │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  COMPOSITE COMPONENTS (Complex, multi-part)                              │
│  ┌──────────────────────────────────────────────────────────────────────┐ │
│  │  DataTable, Form, Modal, Sidebar, Header, DashboardWidget           │ │
│  └──────────────────────────────────────────────────────────────────────┘ │
│                                 │                                         │
│  ┌──────────────────────────────────────────────────────────────────────┐ │
│  │                        BASIC COMPONENTS                               │ │
│  │  Card, Badge, Chip, Tabs, Accordion, Dropdown, Tooltip              │ │
│  └──────────────────────────────────────────────────────────────────────┘ │
│                                 │                                         │
│  ┌──────────────────────────────────────────────────────────────────────┐ │
│  │                       PRIMITIVE COMPONENTS                            │ │
│  │  Button, Input, Text, Icon, Separator, Box                         │ │
│  └──────────────────────────────────────────────────────────────────────┘ │
│                                 │                                         │
│  ┌──────────────────────────────────────────────────────────────────────┐ │
│  │                         DESIGN TOKENS                                │ │
│  │  Colors, Spacing, Typography, Shadows, Radii                       │ │
│  └──────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Component API Convention

```typescript
// Standard component API pattern
interface ComponentProps {
  // Core content
  children?: React.ReactNode;

  // Visual variants
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg';

  // State
  disabled?: boolean;
  loading?: boolean;
  error?: boolean;

  // Behavior
  onClick?: (e: React.MouseEvent) => void;
  onFocus?: (e: React.FocusEvent) => void;
  onBlur?: (e: React.FocusEvent) => void;

  // Styling overrides (escape hatch)
  className?: string;
  style?: React.CSSProperties;

  // Layout
  fullWidth?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;

  // Accessibility
  id?: string;
  ariaLabel?: string;
  ariaDescribedBy?: string;
}

// Variant configuration type
type VariantConfig = {
  [K in keyof VariantProps]: CSS;
};

// Component definition with Stitches
export const Button = styled('button', {
  // Base styles
  variants: {
    variant: {
      primary: {
        backgroundColor: '$primary500',
        color: '$white',
        '&:hover': { backgroundColor: '$primary600' },
        '&:active': { backgroundColor: '$primary700' },
      },
      secondary: {
        backgroundColor: '$neutral100',
        color: '$neutral900',
        '&:hover': { backgroundColor: '$neutral200' },
      },
      ghost: {
        backgroundColor: 'transparent',
        color: '$primary500',
        '&:hover': { backgroundColor: '$primary50' },
      },
      danger: {
        backgroundColor: '$error500',
        color: '$white',
        '&:hover': { backgroundColor: '$error600' },
      },
    },
    size: {
      sm: {
        height: '$6',
        px: '$3',
        fontSize: '$sm',
      },
      md: {
        height: '$10',
        px: '$4',
        fontSize: '$base',
      },
      lg: {
        height: '$12',
        px: '$6',
        fontSize: '$lg',
      },
    },
  },

  defaultVariants: {
    variant: 'primary',
    size: 'md',
  },
});
```

### 1.3 Component Composition Pattern

```typescript
// Compound components pattern
export const Card = {
  Root: styled('div', {
    bg: '$white',
    borderRadius: '$lg',
    boxShadow: '$sm',
    overflow: 'hidden',
  }),

  Header: styled('div', {
    p: '$6',
    borderBottom: '1px solid $border',
  }),

  Title: styled('h3', {
    fontSize: '$lg',
    fontWeight: '$semibold',
    color: '$text',
  }),

  Subtitle: styled('p', {
    fontSize: '$sm',
    color: '$textSecondary',
    mt: '$1',
  }),

  Body: styled('div', {
    p: '$6',
  }),

  Footer: styled('div', {
    p: '$6',
    borderTop: '1px solid $border',
    bg: '$bgMuted',
  }),

  Actions: styled('div', {
    display: 'flex',
    gap: '$3',
    justifyContent: 'flex-end',
  }),
};

// Usage
<Card.Root>
  <Card.Header>
    <Card.Title>Card Title</Card.Title>
    <Card.Subtitle>Optional subtitle</Card.Subtitle>
  </Card.Header>
  <Card.Body>{/* Content */}</Card.Body>
  <Card.Footer>
    <Card.Actions>
      <Button variant="secondary">Cancel</Button>
      <Button>Save</Button>
    </Card.Actions>
  </Card.Footer>
</Card.Root>
```

---

## 2. Primitive Components

### 2.1 Button

```typescript
// Button component with variants
export const Button = styled('button', {
  // Base styles
  display: 'inline-flex',
  alignItems: 'center',
  justifyContent: 'center',
  gap: '$2',
  fontWeight: '$medium',
  lineHeight: '1',
  borderRadius: '$md',
  border: 'none',
  cursor: 'pointer',
  transition: 'all 150ms ease-out',

  '&:disabled': {
    opacity: 0.5,
    cursor: 'not-allowed',
    pointerEvents: 'none',
  },

  // Focus ring for accessibility
  '&:focus-visible': {
    outline: '2px solid $primary500',
    outlineOffset: '2px',
  },

  variants: {
    variant: {
      primary: {
        backgroundColor: '$primary500',
        color: '$white',
        '&:hover:not(:disabled)': { backgroundColor: '$primary600' },
        '&:active:not(:disabled)': { backgroundColor: '$primary700' },
      },
      secondary: {
        backgroundColor: '$neutral100',
        color: '$neutral900',
        '&:hover:not(:disabled)': { backgroundColor: '$neutral200' },
      },
      outline: {
        backgroundColor: 'transparent',
        border: '1px solid $border',
        color: '$text',
        '&:hover:not(:disabled)': {
          borderColor: '$neutral300',
          backgroundColor: '$neutral50',
        },
      },
      ghost: {
        backgroundColor: 'transparent',
        color: '$primary500',
        '&:hover:not(:disabled)': { backgroundColor: '$primary50' },
      },
      danger: {
        backgroundColor: '$error500',
        color: '$white',
        '&:hover:not(:disabled)': { backgroundColor: '$error600' },
      },
      link: {
        backgroundColor: 'transparent',
        color: '$primary500',
        padding: 0,
        height: 'auto',
        '&:hover:not(:disabled)': { textDecoration: 'underline' },
      },
    },
    size: {
      xs: {
        height: '$6',
        px: '$2',
        fontSize: '$xs',
      },
      sm: {
        height: '$8',
        px: '$3',
        fontSize: '$sm',
      },
      md: {
        height: '$10',
        px: '$4',
        fontSize: '$base',
      },
      lg: {
        height: '$12',
        px: '$6',
        fontSize: '$lg',
      },
      xl: {
        height: '$14',
        px: '$8',
        fontSize: '$xl',
      },
    },
  },

  defaultVariants: {
    variant: 'primary',
    size: 'md',
  },
});

// Button with loading state
interface ButtonWithLoadingProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  loading?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

export const ButtonWithLoading = React.forwardRef<HTMLButtonElement, ButtonWithLoadingProps>(
  ({ children, loading, leftIcon, rightIcon, disabled, ...props }, ref) => {
    return (
      <Button
        ref={ref}
        disabled={disabled || loading}
        {...props}
      >
        {loading && <Spinner size="sm" />}
        {!loading && leftIcon && <span className={styles.icon}>{leftIcon}</span>}
        {children}
        {!loading && rightIcon && <span className={styles.icon}>{rightIcon}</span>}
      </Button>
    );
  });
```

### 2.2 Icon

```typescript
// Icon component wrapper
interface IconProps {
  name: string;
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  color?: string;
  className?: string;
}

export const Icon: React.FC<IconProps> = ({ name, size = 'md', color, className }) => {
  const sizeMap = {
    xs: 14,
    sm: 16,
    md: 20,
    lg: 24,
    xl: 32,
  };

  return (
    <svg
      width={sizeMap[size]}
      height={sizeMap[size]}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={2}
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      style={color ? { color } : undefined}
    >
      <use href={`#${name}`} />
    </svg>
  );
};

// Icon sprite sheet (generated from icon library)
export const IconSprite: React.FC = () => (
  <svg style={{ display: 'none' }}>
    {/* All icon symbols defined here */}
  </svg>
);
```

### 2.3 Badge & Chip

```typescript
// Badge component
export const Badge = styled('span', {
  display: 'inline-flex',
  alignItems: 'center',
  px: '$2',
  py: '$1',
  fontSize: '$xs',
  fontWeight: '$medium',
  borderRadius: '$full',

  variants: {
    variant: {
      DEFAULT: {
        backgroundColor: '$primary100',
        color: '$primary700',
      },
      success: {
        backgroundColor: '$success50',
        color: '$success700',
      },
      warning: {
        backgroundColor: '$warning50',
        color: '$warning700',
      },
      error: {
        backgroundColor: '$error50',
        color: '$error700',
      },
      neutral: {
        backgroundColor: '$neutral100',
        color: '$neutral700',
      },
    },
    size: {
      sm: {
        fontSize: '$xs',
        px: '$1.5',
      },
      md: {
        fontSize: '$sm',
        px: '$2',
      },
      lg: {
        fontSize: '$base',
        px: '$3',
      },
    },
  },

  defaultVariants: {
    variant: 'DEFAULT',
    size: 'sm',
  },
});

// Chip component (dismissible)
export const Chip: React.FC<{
  label: string;
  onDismiss?: () => void;
  avatar?: React.ReactNode;
  variant?: 'default' | 'success' | 'warning' | 'error';
}> = ({ label, onDismiss, avatar, variant = 'default' }) => {
  return (
    <span className={cn(styles.chip, styles[variant])}>
      {avatar && <span className={styles.avatar}>{avatar}</span>}
      <span className={styles.label}>{label}</span>
      {onDismiss && (
        <button
          type="button"
          className={styles.dismiss}
          onClick={onDismiss}
          aria-label={`Remove ${label}`}
        >
          <CloseIcon size="xs" />
        </button>
      )}
    </span>
  );
};
```

---

## 3. Form Components

### 3.1 Input

```typescript
// Input component with states
interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  onRightIconClick?: () => void;
  fullWidth?: boolean;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, helperText, leftIcon, rightIcon, onRightIconClick, fullWidth, id, className, ...props }, ref
) => {
    const inputId = id || useId();

    return (
      <div className={cn(styles.inputWrapper, fullWidth && styles.fullWidth)}>
        {label && (
          <label htmlFor={inputId} className={styles.label}>
            {label}
          </label>
        )}

        <div className={cn(styles.inputContainer, error && styles.error)}>
          {leftIcon && <span className={styles.leftIcon}>{leftIcon}</span>}

          <input
            ref={ref}
            id={inputId}
            className={cn(styles.input, leftIcon && styles.hasLeftIcon, rightIcon && styles.hasRightIcon)}
            aria-invalid={!!error}
            aria-describedby={
              error ? `${inputId}-error` :
              helperText ? `${inputId}-helper` :
              undefined
            }
            {...props}
          />

          {rightIcon && (
            <button
              type="button"
              className={styles.rightIcon}
              onClick={onRightIconClick}
              tabIndex={-1}
            >
              {rightIcon}
            </button>
          )}
        </div>

        {error && (
          <span id={`${inputId}-error`} className={styles.errorText} role="alert">
            {error}
          </span>
        )}

        {helperText && !error && (
          <span id={`${inputId}-helper`} className={styles.helperText}>
            {helperText}
          </span>
        )}
      </div>
    );
  });
```

### 3.2 Select

```typescript
// Select component using Radix UI
import * as SelectPrimitive from '@radix-ui/react-select';

export const Select = SelectPrimitive.Root;
export const SelectTrigger = styled(SelectPrimitive.Trigger, {
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'space-between',
  height: '$10',
  px: '$3',
  fontSize: '$base',
  backgroundColor: '$white',
  border: '1px solid $border',
  borderRadius: '$md',
  cursor: 'pointer',
  transition: 'border-color 150ms',

  '&:focus': {
    outline: 'none',
    borderColor: '$primary500',
    boxShadow: '0 0 0 2px $primary100',
  },

  '&[data-disabled]': {
    opacity: 0.5,
    cursor: 'not-allowed',
  },

  '&[data-state=open]': {
    borderColor: '$primary500',
  },
});

export const SelectContent = styled(SelectPrimitive.Content, {
  overflow: 'hidden',
  backgroundColor: '$white',
  borderRadius: '$lg',
  boxShadow: '$lg',
  border: '1px solid $border',
  maxHeight: 256,
  zIndex: '$dropdown',
});

export const SelectItem = styled(SelectPrimitive.Item, {
  display: 'flex',
  alignItems: 'center',
  px: '$3',
  py: '$2',
  fontSize: '$sm',
  cursor: 'pointer',
  transition: 'background-color 100ms',

  '&:hover': {
    backgroundColor: '$neutral50',
  },

  '&[data-state=checked]': {
    backgroundColor: '$primary50',
    color: '$primary700',
  },

  '&[data-disabled]': {
    opacity: 0.5,
    cursor: 'not-allowed',
  },
});

// Usage example
export const SelectInput: React.FC<{
  label?: string;
  placeholder?: string;
  options: Array<{ value: string; label: string }>;
  value?: string;
  onChange?: (value: string) => void;
  error?: string;
}> = ({ label, placeholder, options, value, onChange, error }) => {
  return (
    <Select value={value} onValueChange={onChange}>
      {label && <SelectLabel>{label}</SelectLabel>}
      <SelectTrigger>
        <SelectValue placeholder={placeholder} />
        <SelectIcon />
      </SelectTrigger>
      <SelectContent>
        {options.map(option => (
          <SelectItem key={option.value} value={option.value}>
            {option.label}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
};
```

### 3.3 Checkbox & Radio

```typescript
// Checkbox component
import * as CheckboxPrimitive from '@radix-ui/react-checkbox';

export const Checkbox = styled(CheckboxPrimitive.Root, {
  display: 'flex',
  alignItems: 'center',
  width: '$4',
  height: '$4',
  borderRadius: '$sm',
  border: '2px solid $border',
  backgroundColor: '$white',
  cursor: 'pointer',
  transition: 'all 150ms',

  '&:hover': {
    borderColor: '$neutral400',
  },

  '&:focus': {
    outline: 'none',
    borderColor: '$primary500',
    boxShadow: '0 0 0 2px $primary100',
  },

  '&[data-state=checked]': {
    backgroundColor: '$primary500',
    borderColor: '$primary500',
    backgroundImage: `url("data:image/svg+xml,%3csvg viewBox='0 0 16 16' fill='white' xmlns='http://www.w3.org/2000/svg'%3e%3cpath d='M12.207 4.793a1 1 0 010 1.414l-5 5a1 1 0 01-1.414 0l-2-2a1 1 0 011.414-1.414L6.5 9.086l4.293-4.293a1 1 0 011.414 0z'/%3e%3c/svg%3e")`,
  },

  '&[data-disabled]': {
    opacity: 0.5,
    cursor: 'not-allowed',
  },
});

// Radio group component
import * as RadioGroupPrimitive from '@radix-ui/react-radio-group';

export const RadioGroup = styled(RadioGroupPrimitive.Root, {
  display: 'flex',
  flexDirection: 'column',
  gap: '$2',
});

export const Radio = styled(RadioGroupPrimitive.Item, {
  display: 'flex',
  alignItems: 'center',
  gap: '$2',
  px: '$3',
  py: '$2',
  borderRadius: '$md',
  cursor: 'pointer',
  transition: 'background-color 100ms',

  '&:hover': {
    backgroundColor: '$neutral50',
  },

  '&:focus': {
    outline: 'none',
    backgroundColor: '$neutral50',
  },

  '&[data-state=checked]': {
    backgroundColor: '$primary50',
  },
});

export const RadioIndicator = styled(RadioGroupPrimitive.Indicator, {
  width: '$4',
  height: '$4',
  borderRadius: '$full',
  border: '2px solid $border',
  position: 'relative',

  '&[data-state=checked]': {
    backgroundColor: '$primary500',
    borderColor: '$primary500',
    '&::after': {
      content: '""',
      position: 'absolute',
      top: '50%',
      left: '50%',
      transform: 'translate(-50%, -50%)',
      width: '$2',
      height: '$2',
      borderRadius: '$full',
      backgroundColor: '$white',
    },
  },
});
```

---

## 4. Feedback Components

### 4.1 Alert/Toast

```typescript
// Alert component
interface AlertProps {
  variant?: 'info' | 'success' | 'warning' | 'error';
  title?: string;
  children: React.ReactNode;
  onClose?: () => void;
}

export const Alert: React.FC<AlertProps> = ({ variant = 'info', title, children, onClose }) => {
  const icons = {
    info: <InfoIcon />,
    success: <CheckCircleIcon />,
    warning: <WarningIcon />,
    error: <ErrorIcon />,
  };

  return (
    <div className={cn(styles.alert, styles[variant])} role="alert">
      <span className={styles.icon}>{icons[variant]}</span>

      <div className={styles.content}>
        {title && <div className={styles.title}>{title}</div>}
        <div className={styles.message}>{children}</div>
      </div>

      {onClose && (
        <button
          type="button"
          className={styles.close}
          onClick={onClose}
          aria-label="Close alert"
        >
          <CloseIcon size="sm" />
        </button>
      )}
    </div>
  );
};

// Toast notification (with sonner)
import { toast } from 'sonner';

export const showToast = (
  message: string,
  variant: 'success' | 'error' | 'info' = 'info'
) => {
  toast[variant](message, {
    duration: 4000,
    position: 'bottom-right',
  });
};

// Toast with action
export const showToastWithAction = (
  message: string,
  action: {
    label: string;
    onClick: () => void;
  }
) => {
  toast(message, {
    action,
    duration: 6000,
  });
};
```

### 4.2 Progress & Loading

```typescript
// Spinner component
export const Spinner = styled('div', {
  width: '$4',
  height: '$4',
  borderRadius: '$full',
  border: '3px solid $neutral100',
  borderTopColor: '$primary500',
  animation: 'spin 1s linear infinite',

  '@keyframes spin': {
    '0%': { transform: 'rotate(0deg)' },
    '100%': { transform: 'rotate(360deg)' },
  },

  variants: {
    size: {
      xs: { width: '$3', height: '$3' },
      sm: { width: '$4', height: '$4' },
      md: { width: '$6', height: '$6' },
      lg: { width: '$8', height: '$8' },
    },
  },

  defaultVariants: {
    size: 'sm',
  },
});

// Progress bar
export const ProgressBar = styled('div', {
  width: '100%',
  height: '$2',
  backgroundColor: '$neutral100',
  borderRadius: '$full',
  overflow: 'hidden',

  variants: {
    value: {
      // 0-100%
    },
  },
});

export const ProgressFill = styled('div', {
  height: '100%',
  backgroundColor: '$primary500',
  borderRadius: '$full',
  transition: 'width 300ms ease-out',
});

// Skeleton loader
export const Skeleton = styled('div', {
  backgroundColor: '$neutral100',
  borderRadius: '$md',
  animation: 'pulse 2s ease-in-out infinite',

  '@keyframes pulse': {
    '0%, 100%': { opacity: 1 },
    '50%': { opacity: 0.5 },
  },

  variants: {
    variant: {
      text: {
        height: '$3',
        width: '100%',
      },
      circular: {
        borderRadius: '$full',
      },
    },
    width: {
      // Custom width
    },
    height: {
      // Custom height
    },
  },
});
```

---

## 5. Layout Components

### 5.1 Container & Stack

```typescript
// Container for content width
export const Container = styled('div', {
  width: '100%',
  mx: 'auto',
  px: '$4',

  variants: {
    size: {
      sm: { maxWidth: 640 },
      md: { maxWidth: 768 },
      lg: { maxWidth: 1024 },
      xl: { maxWidth: 1280 },
      full: { maxWidth: '100%' },
    },
  },

  defaultVariants: {
    size: 'lg',
  },
});

// Stack for vertical spacing
export const Stack = styled('div', {
  display: 'flex',
  flexDirection: 'column',

  variants: {
    gap: {
      xs: { gap: '$1' },
      sm: { gap: '$2' },
      md: { gap: '$3' },
      lg: { gap: '$4' },
      xl: { gap: '$6' },
    },
    align: {
      start: { alignItems: 'flex-start' },
      center: { alignItems: 'center' },
      end: { alignItems: 'flex-end' },
      stretch: { alignItems: 'stretch' },
    },
  },

  defaultVariants: {
    gap: 'md',
    align: 'stretch',
  },
});

// Inline stack for horizontal spacing
export const InlineStack = styled('div', {
  display: 'flex',
  flexDirection: 'row',
  flexWrap: 'wrap',

  variants: {
    gap: {
      xs: { gap: '$1' },
      sm: { gap: '$2' },
      md: { gap: '$3' },
      lg: { gap: '$4' },
      xl: { gap: '$6' },
    },
    align: {
      start: { alignItems: 'flex-start' },
      center: { alignItems: 'center' },
      end: { alignItems: 'flex-end' },
      stretch: { alignItems: 'stretch' },
    },
    justify: {
      start: { justifyContent: 'flex-start' },
      center: { justifyContent: 'center' },
      end: { justifyContent: 'flex-end' },
      between: { justifyContent: 'space-between' },
    },
  },

  defaultVariants: {
    gap: 'md',
    align: 'center',
    justify: 'start',
  },
});
```

### 5.2 Grid

```typescript
// Grid system
export const Grid = styled('div', {
  display: 'grid',
  gap: '$4',

  variants: {
    cols: {
      1: { gridTemplateColumns: 'repeat(1, minmax(0, 1fr))' },
      2: { gridTemplateColumns: 'repeat(2, minmax(0, 1fr))' },
      3: { gridTemplateColumns: 'repeat(3, minmax(0, 1fr))' },
      4: { gridTemplateColumns: 'repeat(4, minmax(0, 1fr))' },
      5: { gridTemplateColumns: 'repeat(5, minmax(0, 1fr))' },
      6: { gridTemplateColumns: 'repeat(6, minmax(0, 1fr))' },
      12: { gridTemplateColumns: 'repeat(12, minmax(0, 1fr))' },
    },
    gap: {
      xs: { gap: '$2' },
      sm: { gap: '$3' },
      md: { gap: '$4' },
      lg: { gap: '$6' },
    },
  },

  defaultVariants: {
    cols: 1,
    gap: 'md',
  },

  // Responsive columns
  mediaQueries: {
    '@sm': {
      cols: {
        2: { gridTemplateColumns: 'repeat(2, minmax(0, 1fr))' },
      },
    },
    '@md': {
      cols: {
        3: { gridTemplateColumns: 'repeat(3, minmax(0, 1fr))' },
      },
    },
    '@lg': {
      cols: {
        4: { gridTemplateColumns: 'repeat(4, minmax(0, 1fr))' },
      },
    },
  },
});

// Grid cell (for custom column spans)
export const Cell = styled('div', {
  variants: {
    span: {
      1: { gridColumn: 'span 1 / span 12' },
      2: { gridColumn: 'span 2 / span 12' },
      3: { gridColumn: 'span 3 / span 12' },
      4: { gridColumn: 'span 4 / span 12' },
      5: { gridColumn: 'span 5 / span 12' },
      6: { gridColumn: 'span 6 / span 12' },
      7: { gridColumn: 'span 7 / span 12' },
      8: { gridColumn: 'span 8 / span 12' },
      9: { gridColumn: 'span 9 / span 12' },
      10: { gridColumn: 'span 10 / span 12' },
      11: { gridColumn: 'span 11 / span 12' },
      12: { gridColumn: 'span 12 / span 12' },
    },
  },
});
```

### 5.3 Divider

```typescript
// Divider component
export const Divider = styled('div', {
  border: 'none',
  borderTop: '1px solid $border',
  my: '$4',

  variants: {
    orientation: {
      horizontal: {
        width: '100%',
        height: '1px',
      },
      vertical: {
        width: '1px',
        height: 'auto',
        borderTop: 'none',
        borderLeft: '1px solid $border',
      },
    },
    label: {
      // When labeled, use flex layout
    },
  },

  defaultVariants: {
    orientation: 'horizontal',
  },
});

// Labeled divider
export const LabeledDivider: React.FC<{ label: string }> = ({ label }) => {
  return (
    <div className={styles.labeledDivider}>
      <Divider />
      <span className={styles.label}>{label}</span>
      <Divider />
    </div>
  );
};
```

---

## 6. Navigation Components

### 6.1 Tabs

```typescript
// Tabs component using Radix UI
import * as TabsPrimitive from '@radix-ui/react-tabs';

export const Tabs = styled(TabsPrimitive.Root, {
  display: 'flex',
  flexDirection: 'column',
});

export const TabsList = styled(TabsPrimitive.List, {
  display: 'flex',
  gap: '$1',
  borderBottom: '1px solid $border',
  px: '$1',
});

export const TabsTrigger = styled(TabsPrimitive.Trigger, {
  px: '$4',
  py: '$3',
  fontSize: '$sm',
  fontWeight: '$medium',
  color: '$textSecondary',
  borderBottom: '2px solid transparent',
  cursor: 'pointer',
  transition: 'all 150ms',

  '&:hover': {
    color: '$text',
  },

  '&[data-state=active]': {
    color: '$primary500',
    borderBottomColor: '$primary500',
  },

  '&:focus': {
    outline: 'none',
    boxShadow: 'inset 0 -2px 0 0 $primary500',
  },
});

export const TabsContent = styled(TabsPrimitive.Content, {
  py: '$4',
});
```

### 6.2 Breadcrumb

```typescript
// Breadcrumb component
import * as BreadcrumbPrimitive from '@radix-ui/react-breadcrumb';

export const Breadcrumb = styled(BreadcrumbPrimitive.Root, {
  display: 'flex',
  alignItems: 'center',
  gap: '$2',
  fontSize: '$sm',
});

export const BreadcrumbItem = styled(BreadcrumbPrimitive.Item, {
  display: 'flex',
  alignItems: 'center',
  gap: '$2',
  color: '$textSecondary',

  '&:not(:last-child)': {
    '&:hover': {
      color: '$text',
    },
  },

  '&[aria-current="page"]': {
    color: '$text',
    fontWeight: '$medium',
  },
});

export const BreadcrumbSeparator = styled(BreadcrumbPrimitive.Separator, {
  color: '$textMuted',
});

export const Breadcrumbs: React.FC<{
  items: Array<{ label: string; href?: string }>;
}> = ({ items }) => {
  return (
    <Breadcrumb>
      {items.map((item, index) => (
        <React.Fragment key={index}>
          <BreadcrumbItem asChild>
            {item.href ? (
              <a href={item.href}>{item.label}</a>
            ) : (
              <span>{item.label}</span>
            )}
          </BreadcrumbItem>
          {index < items.length - 1 && (
            <BreadcrumbSeparator>/</BreadcrumbSeparator>
          )}
        </React.Fragment>
      ))}
    </Breadcrumb>
  );
};
```

---

## 7. Data Display Components

### 7.1 Table

```typescript
// Table component
export const Table = styled('table', {
  width: '100%',
  borderCollapse: 'collapse',
  fontSize: '$sm',
});

export const TableHeader = styled('thead', {
  borderBottom: '2px solid $border',
});

export const TableBody = styled('tbody', {
  '& > tr': {
    borderBottom: '1px solid $border',
    '&:last-child': {
      borderBottom: 'none',
    },
  },
});

export const TableRow = styled('tr', {
  transition: 'background-color 150ms',

  '&:hover': {
    backgroundColor: '$bgMuted',
  },
});

export const TableCell = styled('td', {
  py: '$3',
  px: '$4',
  textAlign: 'left',
});

export const TableHead = styled('th', {
  py: '$3',
  px: '$4',
  textAlign: 'left',
  fontWeight: '$medium',
  color: '$textSecondary',
  whiteSpace: 'nowrap',
});

export const TableFooter = styled('tfoot', {
  borderTop: '2px solid $border',
  backgroundColor: '$bgMuted',
});

// Usage example
export const DataTable: React.FC<{
  columns: Array<{ key: string; label: string }>;
  rows: Array<{ [key: string]: any }>;
}> = ({ columns, rows }) => {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          {columns.map(col => (
            <TableHead key={col.key}>{col.label}</TableHead>
          ))}
        </TableRow>
      </TableHeader>
      <TableBody>
        {rows.map((row, i) => (
          <TableRow key={i}>
            {columns.map(col => (
              <TableCell key={col.key}>{row[col.key]}</TableCell>
            ))}
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
};
```

### 7.2 Avatar

```typescript
// Avatar component
interface AvatarProps {
  src?: string;
  alt?: string;
  fallback?: string;
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl' | '2xl';
}

export const Avatar = styled('div', {
  display: 'inline-flex',
  alignItems: 'center',
  justifyContent: 'center',
  borderRadius: '$full',
  backgroundColor: '$primary100',
  color: '$primary700',
  fontWeight: '$medium',
  overflow: 'hidden',
  verticalAlign: 'middle',

  variants: {
    size: {
      xs: { width: '$5', height: '$5', fontSize: '$xs' },
      sm: { width: '$6', height: '$6', fontSize: '$xs' },
      md: { width: '$8', height: '$8', fontSize: '$sm' },
      lg: { width: '$10', height: '$10', fontSize: '$base' },
      xl: { width: '$12', height: '$12', fontSize: '$lg' },
      '2xl': { width: '$16', height: '$16', fontSize: '$xl' },
    },
  },

  defaultVariants: {
    size: 'md',
  },
});

export const AvatarImage = styled('img', {
  width: '100%',
  height: '100%',
  objectFit: 'cover',
});
```

---

## 8. Overlay Components

### 8.1 Modal/Dialog

```typescript
// Modal component using Radix UI
import * as DialogPrimitive from '@radix-ui/react-dialog';

export const Modal = DialogPrimitive.Root;
export const ModalTrigger = DialogPrimitive.Trigger;
export const ModalPortal = DialogPrimitive.Portal;
export const ModalClose = DialogPrimitive.Close;

export const ModalOverlay = styled(DialogPrimitive.Overlay, {
  position: 'fixed',
  inset: 0,
  backgroundColor: 'rgba(0, 0, 0, 0.5)',
  zIndex: '$modalBackdrop',
  animation: 'fadeIn 150ms ease-out',

  '@keyframes fadeIn': {
    '0%': { opacity: 0 },
    '100%': { opacity: 1 },
  },
});

export const ModalContent = styled(DialogPrimitive.Content, {
  position: 'fixed',
  left: '50%',
  top: '50%',
  transform: 'translate(-50%, -50%)',
  backgroundColor: '$white',
  borderRadius: '$lg',
  boxShadow: '$xl',
  zIndex: '$modal',
  maxWidth: '90vw',
  maxHeight: '90vh',
  overflow: 'auto',
  animation: 'scaleIn 150ms ease-out',

  '@keyframes scaleIn': {
    '0%': { opacity: 0, transform: 'translate(-50%, -50%) scale(0.95)' },
    '100%': { opacity: 1, transform: 'translate(-50%, -50%) scale(1)' },
  },

  variants: {
    size: {
      sm: { width: 400 },
      md: { width: 560 },
      lg: { width: 720 },
      xl: { width: 960 },
      full: { width: '100vw', height: '100vh', borderRadius: 0 },
    },
  },

  defaultVariants: {
    size: 'md',
  },
});

export const ModalHeader = styled(DialogPrimitive.Title, {
  px: '$6',
  py: '$4',
  fontSize: '$lg',
  fontWeight: '$semibold',
  borderBottom: '1px solid $border',
});

export const ModalBody = styled('div', {
  px: '$6',
  py: '$4',
});

export const ModalFooter = styled('div', {
  display: 'flex',
  gap: '$3',
  justifyContent: 'flex-end',
  px: '$6',
  py: '$4',
  borderTop: '1px solid $border',
  backgroundColor: '$bgMuted',
});
```

### 8.2 Tooltip

```typescript
// Tooltip component using Radix UI
import * as TooltipPrimitive from '@radix-ui/react-tooltip';

export const Tooltip = TooltipPrimitive.Root;
export const TooltipTrigger = TooltipPrimitive.Trigger;

export const TooltipContent = styled(TooltipPrimitive.Content, {
  px: '$3',
  py: '$2',
  fontSize: '$sm',
  fontWeight: '$medium',
  color: '$white',
  backgroundColor: '$neutral900',
  borderRadius: '$sm',
  maxWidth: 240,
  zIndex: '$tooltip',
  animation: 'fadeIn 100ms ease-out',

  '&[data-state="delayed-open"]': {
    animationDelay: '700ms',
  },
});
```

### 8.3 Popover

```typescript
// Popover component
import * as PopoverPrimitive from '@radix-ui/react-popover';

export const Popover = PopoverPrimitive.Root;
export const PopoverTrigger = PopoverPrimitive.Trigger;

export const PopoverContent = styled(PopoverPrimitive.Content, {
  backgroundColor: '$white',
  border: '1px solid $border',
  borderRadius: '$lg',
  boxShadow: '$lg',
  p: '$4',
  minWidth: 200,
  maxWidth: 320,
  zIndex: '$popover',
  animation: 'scaleIn 150ms ease-out',
});
```

---

## Summary

The component library provides a comprehensive set of reusable UI elements:

| Category | Components |
|----------|------------|
| **Primitives** | Button, Icon, Badge, Chip, Text, Separator |
| **Form** | Input, Select, Checkbox, Radio, Textarea, Switch |
| **Feedback** | Alert, Toast, Spinner, Progress, Skeleton |
| **Layout** | Container, Stack, InlineStack, Grid, Cell, Divider |
| **Navigation** | Tabs, Breadcrumb, Menu, Pagination |
| **Data Display** | Table, Avatar, Card, List, Badge |
| **Overlay** | Modal, Tooltip, Popover, Dropdown |

**Key Takeaways:**
- Use Radix UI primitives for accessibility
- Follow consistent API conventions
- Support variants (size, variant, state)
- Provide escape hatch with className/style
- Build composable components where appropriate
- Use design tokens for all values
- Support dark mode automatically via tokens
- Include proper ARIA attributes

---

**Related:** [03: Patterns Deep Dive](./DESIGN_03_PATTERNS_DEEP_DIVE.md) → UX patterns and layouts
