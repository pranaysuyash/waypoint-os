# DESIGN_03: Patterns Deep Dive

> Common UX patterns, layouts, forms, navigation, and state patterns

---

## Table of Contents

1. [Overview](#overview)
2. [Layout Patterns](#layout-patterns)
3. [Form Patterns](#form-patterns)
4. [Navigation Patterns](#navigation-patterns)
5. [Action Patterns](#action-patterns)
6. [Data Display Patterns](#data-display-patterns)
7. [Feedback Patterns](#feedback-patterns)
8. [Pattern Composition](#pattern-composition)
9. [Anti-Patterns](#anti-patterns)

---

## Overview

### What are Design Patterns?

Design patterns are reusable solutions to common UX problems. Unlike components (which are UI building blocks), patterns describe how components work together to solve specific user tasks.

### Pattern Categories

```
┌─────────────────────────────────────────────────────────────────┐
│                    DESIGN PATTERNS                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Layout     │  │    Form      │  │  Navigation  │          │
│  │  Patterns    │  │  Patterns    │  │  Patterns    │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │    Action    │  │    Data      │  │   Feedback   │          │
│  │  Patterns    │  │  Display     │  │  Patterns    │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Pattern Principles

| Principle | Description | Example |
|-----------|-------------|---------|
| **Consistency** | Same problem, same solution | All modals use same close behavior |
| **Predictability** | Users know what to expect | Primary action always right-aligned |
| **Efficiency** | Minimize steps to complete tasks | Smart defaults, progressive disclosure |
| **Forgiveness** | Easy to recover from errors | Undo, confirm destructive actions |
| **Accessibility** | Usable by everyone | Keyboard navigation, screen reader support |

---

## Layout Patterns

### Application Shell

The main application layout that persists across all pages.

```
┌─────────────────────────────────────────────────────────────────┐
│  Header                    Logo                    Search User │
├──────┬──────────────────────────────────────────────────────────┤
│      │  Breadcrumb                                            │
│      ├──────────────────────────────────────────────────────────┤
│ Nav  │                                                          │
│ Bar  │  Main Content Area                                       │
│      │                                                          │
│      │  ┌────────────┐  ┌────────────┐  ┌────────────┐        │
│      │  │  Card 1    │  │  Card 2    │  │  Card 3    │        │
│      │  └────────────┘  └────────────┘  └────────────┘        │
│      │                                                          │
├──────┴──────────────────────────────────────────────────────────┤
│  Footer                                             Version v1.0 │
└─────────────────────────────────────────────────────────────────┘
```

#### ApplicationShell Component

```typescript
// Application shell with collapsible sidebar
interface ApplicationShellProps {
  header?: React.ReactNode;
  sidebar?: React.ReactNode;
  sidebarCollapsed?: boolean;
  onSidebarToggle?: () => void;
  footer?: React.ReactNode;
  children: React.ReactNode;
}

export const ApplicationShell: React.FC<ApplicationShellProps> = ({
  header,
  sidebar,
  sidebarCollapsed = false,
  onSidebarToggle,
  footer,
  children,
}) => {
  return (
    <ShellContainer>
      {header && <ShellHeader>{header}</ShellHeader>}

      <ShellBody>
        {sidebar && (
          <ShellSidebar collapsed={sidebarCollapsed}>
            {sidebar}
          </ShellSidebar>
        )}

        <ShellContent withSidebar={!!sidebar} sidebarCollapsed={sidebarCollapsed}>
          {children}
        </ShellContent>
      </ShellBody>

      {footer && <ShellFooter>{footer}</ShellFooter>}
    </ShellContainer>
  );
};

const ShellContainer = styled('div', {
  display: 'flex',
  flexDirection: 'column',
  minHeight: '100vh',
  backgroundColor: '$neutral50',
});

const ShellHeader = styled('header', {
  position: 'sticky',
  top: 0,
  zIndex: 100,
  backgroundColor: '$white',
  borderBottom: '1px solid $neutral200',
  height: '$headerHeight',
  display: 'flex',
  alignItems: 'center',
  padding: '0 $space$6',
});

const ShellBody = styled('div', {
  display: 'flex',
  flex: 1,
  overflow: 'hidden',
});

const ShellSidebar = styled('aside', {
  width: '$sidebarWidth',
  backgroundColor: '$white',
  borderRight: '1px solid $neutral200',
  overflowY: 'auto',
  transition: 'width 200ms ease',

  variants: {
    collapsed: {
      true: {
        width: '$sidebarCollapsedWidth',
      },
    },
  },
});

const ShellContent = styled('main', {
  flex: 1,
  overflowY: 'auto',
  padding: '$space$6',

  variants: {
    withSidebar: {
      true: {
        maxWidth: 'calc(100vw - $sidebarWidth)',
      },
      false: {
        maxWidth: '100vw',
      },
    },
    sidebarCollapsed: {
      true: {
        maxWidth: 'calc(100vw - $sidebarCollapsedWidth)',
      },
    },
  },
});
```

### Two-Column Layout

Content with a persistent side panel for details, context, or actions.

```
┌─────────────────────────────────────────────────────────────────┐
│  ← Back    Trip Details                    Edit    Save         │
├─────────────────────────────────────────┬───────────────────────┤
│                                         │                       │
│  Main Content                           │   Side Panel          │
│                                         │                       │
│  • Customer info                        │   Quick Actions       │
│  • Destination                          │   • Send Quote        │
│  • Dates                                │   • Call Customer     │
│  • Travelers                            │   • Assign Agent      │
│                                         │                       │
│                                         │   Timeline            │
│                                         │   • Quote sent        │
│                                         │   • Follow-up         │
│                                         │                       │
├─────────────────────────────────────────┴───────────────────────┤
└─────────────────────────────────────────────────────────────────┘
```

#### TwoColumnLayout Component

```typescript
interface TwoColumnLayoutProps {
  main: React.ReactNode;
  side: React.ReactNode;
  sideWidth?: string;
  sidePosition?: 'left' | 'right';
  collapsible?: boolean;
  defaultCollapsed?: boolean;
}

export const TwoColumnLayout: React.FC<TwoColumnLayoutProps> = ({
  main,
  side,
  sideWidth = '320px',
  sidePosition = 'right',
  collapsible = false,
  defaultCollapsed = false,
}) => {
  const [collapsed, setCollapsed] = useState(defaultCollapsed);

  return (
    <LayoutContainer>
      <LayoutMain
        style={{
          [sidePosition === 'left' ? 'marginLeft' : 'marginRight']:
            collapsed ? 0 : sideWidth,
        }}
      >
        {main}
      </LayoutMain>

      <LayoutSide
        position={sidePosition}
        width={sideWidth}
        collapsed={collapsed}
      >
        {collapsible && (
          <CollapseButton onClick={() => setCollapsed(!collapsed)}>
            <Icon name={collapsed ? 'expand' : 'collapse'} />
          </CollapseButton>
        )}
        {side}
      </LayoutSide>
    </LayoutContainer>
  );
};

const LayoutContainer = styled('div', {
  display: 'flex',
  position: 'relative',
  minHeight: '100%',
});

const LayoutMain = styled('div', {
  flex: 1,
  minWidth: 0, // Prevent flex overflow
  transition: 'margin 200ms ease',
});

const LayoutSide = styled('aside', {
  position: 'sticky',
  top: 0,
  height: '100vh',
  overflowY: 'auto',
  backgroundColor: '$white',
  borderLeft: '1px solid $neutral200',
  padding: '$space$4',
  transition: 'all 200ms ease',

  variants: {
    position: {
      left: {
        borderLeft: 'none',
        borderRight: '1px solid $neutral200',
      },
      right: {
        borderLeft: '1px solid $neutral200',
        borderRight: 'none',
      },
    },
    collapsed: {
      true: {
        width: 0,
        padding: 0,
        overflow: 'hidden',
        border: 'none',
      },
    },
  },
});
```

### Split View

Two independent panels that can be scrolled and resized independently.

```
┌─────────────────────────────────────────────────────────────────┐
│  Trips (23)                           │  Trip Details           │
├───────────────────────────────────────┼─────────────────────────┤
│                                       │                         │
│  ┌─────────────────────────────────┐  │  Customer: John Doe    │
│  │ 🏖️ Goa Family Trip             │  │  Status: Quoted        │
│  │    John Doe • 5 travelers      │  │  Budget: ₹2,00,000     │
│  │    Mar 15-22, 2026             │  │                         │
│  ├─────────────────────────────────┤  │  ┌───────────────────┐ │
│  │ ✈️ Delhi to Singapore           │  │  │ Flights           │ │
│  │    Priya Sharma • 2 travelers  │  │  │ • Delhi → Singapore│ │
│  │    Apr 5-12, 2026              │  │  │ • Return flight    │ │
│  ├─────────────────────────────────┤  │  └───────────────────┘ │
│  │ 🏔️ Manali Honeymoon            │  │                         │
│  │    Rahul Verma • 2 travelers   │  │  ┌───────────────────┐ │
│  │    May 1-7, 2026               │  │  │ Hotels            │ │
│  └─────────────────────────────────┘  │  │ • Taj Resorts      │ │
│                                       │  └───────────────────┘ │
│  ┌─────────────────────────────────┐  │                         │
│  │ 🎓 Tokyo Grad Trip              │  │  ┌───────────────────┐ │
│  └─────────────────────────────────┘  │  │ Activities         │ │
│                                       │  └───────────────────┘ │
└───────────────────────────────────────┴─────────────────────────┘
              ↑ Resizable divider ↑
```

#### SplitView Component

```typescript
interface SplitViewProps {
  left: React.ReactNode;
  right: React.ReactNode;
  defaultSplitRatio?: number; // 0-1, 0.5 = equal
  minSplitRatio?: number;
  maxSplitRatio?: number;
  direction?: 'horizontal' | 'vertical';
}

export const SplitView: React.FC<SplitViewProps> = ({
  left,
  right,
  defaultSplitRatio = 0.4,
  minSplitRatio = 0.2,
  maxSplitRatio = 0.8,
  direction = 'horizontal',
}) => {
  const [splitRatio, setSplitRatio] = useState(defaultSplitRatio);
  const [isDragging, setIsDragging] = useState(false);
  containerRef = useRef<HTMLDivElement>(null);

  const handleMouseDown = useCallback(() => {
    setIsDragging(true);
  }, []);

  useEffect(() => {
    if (!isDragging) return;

    const handleMouseMove = (e: MouseEvent) => {
      if (!containerRef.current) return;

      const rect = containerRef.current.getBoundingClientRect();
      const ratio = direction === 'horizontal'
        ? (e.clientX - rect.left) / rect.width
        : (e.clientY - rect.top) / rect.height;

      setSplitRatio(Math.max(minSplitRatio, Math.min(maxSplitRatio, ratio)));
    };

    const handleMouseUp = () => {
      setIsDragging(false);
    };

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isDragging, direction, minSplitRatio, maxSplitRatio]);

  return (
    <SplitViewContainer ref={containerRef} direction={direction}>
      <SplitPanel style={{ flex: splitRatio }}>
        {left}
      </SplitPanel>

      <Resizer
        isDragging={isDragging}
        onMouseDown={handleMouseDown}
        direction={direction}
      />

      <SplitPanel style={{ flex: 1 - splitRatio }}>
        {right}
      </SplitPanel>
    </SplitViewContainer>
  );
};

const SplitViewContainer = styled('div', {
  display: 'flex',
  width: '100%',
  height: '100%',
  overflow: 'hidden',

  variants: {
    direction: {
      horizontal: {
        flexDirection: 'row',
      },
      vertical: {
        flexDirection: 'column',
      },
    },
  },
});

const SplitPanel = styled('div', {
  overflow: 'auto',
  minWidth: 0,
  minHeight: 0,
});

const Resizer = styled('div', {
  backgroundColor: '$neutral200',
  position: 'relative',
  zIndex: 10,
  transition: 'background-color 150ms',

  '&:hover': {
    backgroundColor: '$primary300',
  },

  variants: {
    isDragging: {
      true: {
        backgroundColor: '$primary500',
      },
    },
    direction: {
      horizontal: {
        width: '4px',
        cursor: 'col-resize',
      },
      vertical: {
        height: '4px',
        cursor: 'row-resize',
      },
    },
  },
});
```

### Dashboard Grid

Responsive grid for cards and widgets.

```
┌─────────────────────────────────────────────────────────────────┐
│  Dashboard                                             + Filter │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │    KPI      │  │    KPI      │  │    KPI      │             │
│  │   123       │  │   ₹45L      │  │   89%       │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
│                                                                  │
│  ┌─────────────────────────┐  ┌─────────────────────────┐      │
│  │                         │  │                         │      │
│  │     Chart Widget        │  │     List Widget         │      │
│  │                         │  │                         │      │
│  └─────────────────────────┘  └─────────────────────────┘      │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    Wide Widget                           │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

#### DashboardGrid Component

```typescript
type GridSpan = 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12;

interface DashboardWidget {
  id: string;
  content: React.ReactNode;
  columnSpan?: GridSpan;
  rowSpan?: number;
  minHeight?: number;
}

interface DashboardGridProps {
  widgets: DashboardWidget[];
  columns?: 12;
  gap?: string;
  editable?: boolean;
  onReorder?: (widgets: DashboardWidget[]) => void;
}

export const DashboardGrid: React.FC<DashboardGridProps> = ({
  widgets,
  columns = 12,
  gap = '$space$4',
  editable = false,
  onReorder,
}) => {
  const [order, setOrder] = useState(widgets);

  const handleReorder = useCallback((newOrder: DashboardWidget[]) => {
    setOrder(newOrder);
    onReorder?.(newOrder);
  }, [onReorder]);

  return (
    <GridContainer columns={columns} gap={gap}>
      {order.map((widget) => (
        <GridItem
          key={widget.id}
          columnSpan={widget.columnSpan ?? 4}
          rowSpan={widget.rowSpan ?? 1}
          minHeight={widget.minHeight}
        >
          {widget.content}
        </GridItem>
      ))}
    </GridContainer>
  );
};

const GridContainer = styled('div', {
  display: 'grid',
  width: '100%',
  gridAutoRows: 'minmax(200px, auto)',

  // Responsive breakpoints
  '@media (max-width: 768px)': {
    gridTemplateColumns: 'repeat(6, 1fr)',
  },
  '@media (max-width: 480px)': {
    gridTemplateColumns: '1fr',
  },

  variants: {
    columns: {
      12: { gridTemplateColumns: 'repeat(12, 1fr)' },
      8: { gridTemplateColumns: 'repeat(8, 1fr)' },
      6: { gridTemplateColumns: 'repeat(6, 1fr)' },
      4: { gridTemplateColumns: 'repeat(4, 1fr)' },
    },
    gap: {
      // Spread operator for gap values
    },
  },
});

const GridItem = styled('div', {
  backgroundColor: '$white',
  border: '1px solid $neutral200',
  borderRadius: '$radius$md',
  padding: '$space$4',
  overflow: 'hidden',

  variants: {
    columnSpan: {
      1: { gridColumn: 'span 1' },
      2: { gridColumn: 'span 2' },
      3: { gridColumn: 'span 3' },
      4: { gridColumn: 'span 4' },
      6: { gridColumn: 'span 6' },
      8: { gridColumn: 'span 8' },
      12: { gridColumn: 'span 12' },
    },
    rowSpan: {
      1: { gridRow: 'span 1' },
      2: { gridRow: 'span 2' },
    },
    minHeight: {
      // Spread operator for minHeight values
    },
  },
});
```

---

## Form Patterns

### Form Structure

Consistent organization of form elements.

```
┌─────────────────────────────────────────────────────────────────┐
│  Create Trip                                          Cancel X  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Section: Customer Information                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Customer Name *                                         │   │
│  │  ┌───────────────────────────────────────────────────┐   │   │
│  │  │                                                   │   │   │
│  │  └───────────────────────────────────────────────────┘   │   │
│  │                                                           │   │
│  │  Email *                          Phone                  │   │
│  │  ┌──────────────────────┐  ┌──────────────────────┐     │   │
│  │  │                      │  │                      │     │   │
│  │  └──────────────────────┘  └──────────────────────┘     │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  Section: Trip Details                                            │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Destination *       Dates *         Travelers *         │   │
│  │  ┌──────────────┐    ┌────────────┐   ┌──────────────┐   │   │
│  │  │              │    │            │   │              │   │   │
│  │  └──────────────┘    └────────────┘   └──────────────┘   │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│                          ┌──────────┐  ┌─────────┐             │
│                          │  Save    │  │ Cancel  │             │
│                          └──────────┘  └─────────┘             │
└─────────────────────────────────────────────────────────────────┘
```

#### FormSection Component

```typescript
interface FormSectionProps {
  title?: string;
  description?: string;
  children: React.ReactNode;
  collapsible?: boolean;
  defaultCollapsed?: boolean;
}

export const FormSection: React.FC<FormSectionProps> = ({
  title,
  description,
  children,
  collapsible = false,
  defaultCollapsed = false,
}) => {
  const [collapsed, setCollapsed] = useState(defaultCollapsed);

  return (
    <SectionContainer>
      {title && (
        <SectionHeader>
          <SectionTitle>
            {collapsible && (
              <CollapseIcon
                collapsed={collapsed}
                onClick={() => setCollapsed(!collapsed)}
              />
            )}
            {title}
          </SectionTitle>
          {description && <SectionDescription>{description}</SectionDescription>}
        </SectionHeader>
      )}

      {!collapsed && <SectionContent>{children}</SectionContent>}
    </SectionContainer>
  );
};

const SectionContainer = styled('div', {
  marginBottom: '$space$6',
});

const SectionHeader = styled('div', {
  marginBottom: '$space$4',
});

const SectionTitle = styled('h3', {
  fontSize: '$fontSizes$md',
  fontWeight: 600,
  color: '$neutral900',
  display: 'flex',
  alignItems: 'center',
  gap: '$space$2',
});

const SectionDescription = styled('p', {
  fontSize: '$fontSizes$sm',
  color: '$neutral600',
  marginTop: '$space$1',
});

const SectionContent = styled('div', {
  padding: '$space$4',
  backgroundColor: '$white',
  border: '1px solid $neutral200',
  borderRadius: '$radius$md',
});
```

### Field Grouping

Related fields grouped together.

```typescript
interface FieldGroupProps {
  label?: string;
  error?: string;
  required?: boolean;
  helperText?: string;
  children: React.ReactNode;
  orientation?: 'vertical' | 'horizontal';
}

export const FieldGroup: React.FC<FieldGroupProps> = ({
  label,
  error,
  required,
  helperText,
  children,
  orientation = 'vertical',
}) => {
  return (
    <GroupContainer orientation={orientation}>
      {label && (
        <GroupLabel>
          {label}
          {required && <RequiredIndicator>*</RequiredIndicator>}
        </GroupLabel>
      )}

      <GroupFields>{children}</GroupFields>

      {(error || helperText) && (
        <GroupHelperText error={!!error}>
          {error || helperText}
        </GroupHelperText>
      )}
    </GroupContainer>
  );
};

const GroupContainer = styled('div', {
  display: 'flex',
  marginBottom: '$space$4',

  variants: {
    orientation: {
      vertical: {
        flexDirection: 'column',
      },
      horizontal: {
        flexDirection: 'row',
        alignItems: 'flex-start',
        gap: '$space$4',
      },
    },
  },
});

const GroupLabel = styled('label', {
  fontSize: '$fontSizes$sm',
  fontWeight: 500,
  color: '$neutral700',
  marginBottom: '$space$2',
});

const RequiredIndicator = styled('span', {
  color: '$error500',
  marginLeft: '2px',
});

const GroupFields = styled('div', {
  display: 'flex',
  gap: '$space$3',
  flex: 1,
});

const GroupHelperText = styled('span', {
  fontSize: '$fontSizes$xs',
  marginTop: '$space$1',

  variants: {
    error: {
      true: {
        color: '$error500',
      },
      false: {
        color: '$neutral500',
      },
    },
  },
});
```

### Inline Editing

Edit content in place without a separate form.

```typescript
interface InlineEditProps {
  value: string;
  onSave: (value: string) => void | Promise<void>;
  placeholder?: string;
  multiline?: boolean;
  maxLength?: number;
  validate?: (value: string) => string | undefined;
}

export const InlineEdit: React.FC<InlineEditProps> = ({
  value,
  onSave,
  placeholder = 'Click to edit',
  multiline = false,
  maxLength,
  validate,
}) => {
  const [isEditing, setIsEditing] = useState(false);
  const [editValue, setEditValue] = useState(value);
  const [error, setError] = useState<string>();
  const [isSaving, setIsSaving] = useState(false);

  const inputRef = useRef<HTMLInputElement | HTMLTextAreaElement>(null);

  const handleStart = useCallback(() => {
    setEditValue(value);
    setIsEditing(true);
    setError(undefined);
  }, [value]);

  const handleCancel = useCallback(() => {
    setIsEditing(false);
    setEditValue(value);
    setError(undefined);
  }, [value]);

  const handleSave = useCallback(async () => {
    const validationError = validate?.(editValue);
    if (validationError) {
      setError(validationError);
      return;
    }

    setIsSaving(true);
    try {
      await onSave(editValue);
      setIsEditing(false);
    } catch (err) {
      setError('Failed to save. Please try again.');
    } finally {
      setIsSaving(false);
    }
  }, [editValue, onSave, validate]);

  // Focus input on edit start
  useEffect(() => {
    if (isEditing && inputRef.current) {
      inputRef.current.focus();
      inputRef.current.select();
    }
  }, [isEditing]);

  // Handle keyboard shortcuts
  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !multiline) {
      e.preventDefault();
      handleSave();
    } else if (e.key === 'Escape') {
      handleCancel();
    }
  }, [multiline, handleSave, handleCancel]);

  if (!isEditing) {
    return (
      <DisplayContainer onClick={handleStart}>
        {value || <Placeholder>{placeholder}</Placeholder>}
        <EditIcon name="edit" size="sm" />
      </DisplayContainer>
    );
  }

  return (
    <EditContainer>
      {multiline ? (
        <Textarea
          ref={inputRef as RefObject<HTMLTextAreaElement>}
          value={editValue}
          onChange={(e) => setEditValue(e.target.value)}
          onKeyDown={handleKeyDown}
          maxLength={maxLength}
          error={!!error}
        />
      ) : (
        <Input
          ref={inputRef as RefObject<HTMLInputElement>}
          value={editValue}
          onChange={(e) => setEditValue(e.target.value)}
          onKeyDown={handleKeyDown}
          maxLength={maxLength}
          error={!!error}
        />
      )}

      <EditActions>
        <Button
          variant="primary"
          size="sm"
          onClick={handleSave}
          disabled={isSaving || !editValue}
        >
          {isSaving ? 'Saving...' : 'Save'}
        </Button>
        <Button
          variant="secondary"
          size="sm"
          onClick={handleCancel}
          disabled={isSaving}
        >
          Cancel
        </Button>
      </EditActions>

      {error && <ErrorMessage>{error}</ErrorMessage>}
    </EditContainer>
  );
};

const DisplayContainer = styled('div', {
  display: 'flex',
  alignItems: 'center',
  gap: '$space$2',
  padding: '$space$2 $space$3',
  borderRadius: '$radius$sm',
  cursor: 'pointer',
  transition: 'background-color 150ms',

  '&:hover': {
    backgroundColor: '$neutral100',
  },

  '&:hover svg': {
    opacity: 1,
  },
});

const EditIcon = styled(Icon, {
  opacity: 0,
  color: '$neutral400',
  transition: 'opacity 150ms',
});

const Placeholder = styled('span', {
  color: '$neutral400',
  fontStyle: 'italic',
});

const EditContainer = styled('div', {
  display: 'flex',
  flexDirection: 'column',
  gap: '$space$2',
});

const EditActions = styled('div', {
  display: 'flex',
  gap: '$space$2',
  justifyContent: 'flex-end',
});

const ErrorMessage = styled('span', {
  fontSize: '$fontSizes$xs',
  color: '$error500',
});
```

### Validation States

Visual feedback for validation states.

```typescript
type ValidationState = 'idle' | 'validating' | 'valid' | 'invalid';

interface ValidationIconProps {
  state: ValidationState;
  message?: string;
}

export const ValidationIcon: React.FC<ValidationIconProps> = ({
  state,
  message,
}) => {
  if (state === 'idle') return null;

  const icons = {
    validating: <Spinner size="sm" />,
    valid: <Icon name="check-circle" color="$success500" />,
    invalid: <Icon name="alert-circle" color="$error500" />,
  };

  return (
    <ValidationIconContainer>
      {icons[state]}
      {message && state === 'invalid' && (
        <ValidationMessage>{message}</ValidationMessage>
      )}
    </ValidationIconContainer>
  );
};

const ValidationIconContainer = styled('div', {
  position: 'absolute',
  right: '$space$3',
  top: '50%',
  transform: 'translateY(-50%)',
  pointerEvents: 'none',
});

const ValidationMessage = styled('span', {
  position: 'absolute',
  top: '100%',
  right: 0,
  fontSize: '$fontSizes$xs',
  color: '$error500',
  marginTop: '$space$1',
  whiteSpace: 'nowrap',
});
```

---

## Navigation Patterns

### Breadcrumbs

Hierarchical navigation showing current location.

```
Trips > India > Goa > Goa Family Trip
```

```typescript
interface BreadcrumbItem {
  label: string;
  href?: string;
  icon?: string;
}

interface BreadcrumbsProps {
  items: BreadcrumbItem[];
  separator?: React.ReactNode;
  maxItems?: number;
}

export const Breadcrumbs: React.FC<BreadcrumbsProps> = ({
  items,
  separator = <ChevronRightIcon />,
  maxItems,
}) => {
  // Collapse middle items if too many
  const displayItems = useMemo(() => {
    if (!maxItems || items.length <= maxItems) return items;

    return [
      items[0],
      { label: '...', icon: 'more-horizontal' },
      ...items.slice(-(maxItems - 2)),
    ];
  }, [items, maxItems]);

  return (
    <BreadcrumbsContainer aria-label="Breadcrumb">
      {displayItems.map((item, index) => (
        <BreadcrumbItem key={index}>
          {index > 0 && <BreadcrumbSeparator>{separator}</BreadcrumbSeparator>}

          {item.href ? (
            <BreadcrumbLink href={item.href}>
              {item.icon && <Icon name={item.icon} size="xs" />}
              {item.label}
            </BreadcrumbLink>
          ) : (
            <BreadcrumbCurrent aria-current="page">
              {item.icon && <Icon name={item.icon} size="xs" />}
              {item.label}
            </BreadcrumbCurrent>
          )}
        </BreadcrumbItem>
      ))}
    </BreadcrumbsContainer>
  );
};

const BreadcrumbsContainer = styled('nav', {
  display: 'flex',
  alignItems: 'center',
  gap: '$space$2',
});

const BreadcrumbItem = styled('div', {
  display: 'flex',
  alignItems: 'center',
  gap: '$space$2',
});

const BreadcrumbSeparator = styled('span', {
  color: '$neutral400',
  display: 'flex',
  alignItems: 'center',
});

const BreadcrumbLink = styled('a', {
  display: 'flex',
  alignItems: 'center',
  gap: '$space$1',
  fontSize: '$fontSizes$sm',
  color: '$neutral600',
  textDecoration: 'none',
  transition: 'color 150ms',

  '&:hover': {
    color: '$primary500',
    textDecoration: 'underline',
  },
});

const BreadcrumbCurrent = styled('span', {
  display: 'flex',
  alignItems: 'center',
  gap: '$space$1',
  fontSize: '$fontSizes$sm',
  fontWeight: 500,
  color: '$neutral900',
});
```

### Tabs

Switch between related views within a context.

```typescript
interface Tab {
  id: string;
  label: string;
  icon?: string;
  content: React.ReactNode;
  disabled?: boolean;
  badge?: number | string;
}

interface TabsProps {
  tabs: Tab[];
  defaultTab?: string;
  variant?: 'line' | 'enclosed' | 'soft';
  orientation?: 'horizontal' | 'vertical';
  onChange?: (tabId: string) => void;
}

export const Tabs: React.FC<TabsProps> = ({
  tabs,
  defaultTab,
  variant = 'line',
  orientation = 'horizontal',
  onChange,
}) => {
  const [activeTab, setActiveTab] = useState(defaultTab ?? tabs[0]?.id);

  const handleTabChange = useCallback((tabId: string) => {
    if (tabs.find(t => t.id === tabId)?.disabled) return;
    setActiveTab(tabId);
    onChange?.(tabId);
  }, [tabs, onChange]);

  const currentTab = tabs.find(t => t.id === activeTab);

  return (
    <TabsContainer>
      <TabList
        role="tablist"
        orientation={orientation}
        variant={variant}
      >
        {tabs.map((tab) => (
          <TabTrigger
            key={tab.id}
            role="tab"
            aria-selected={activeTab === tab.id}
            aria-disabled={tab.disabled}
            active={activeTab === tab.id}
            disabled={tab.disabled}
            variant={variant}
            onClick={() => handleTabChange(tab.id)}
          >
            {tab.icon && <Icon name={tab.icon} />}
            <TabLabel>{tab.label}</TabLabel>
            {tab.badge && <TabBadge>{tab.badge}</TabBadge>}
          </TabTrigger>
        ))}
      </TabList>

      <TabPanel role="tabpanel" aria-labelledby={`tab-${activeTab}`}>
        {currentTab?.content}
      </TabPanel>
    </TabsContainer>
  );
};

const TabsContainer = styled('div', {
  display: 'flex',
  flexDirection: 'column',
});

const TabList = styled('div', {
  display: 'flex',
  marginBottom: '$space$4',

  variants: {
    orientation: {
      horizontal: {
        flexDirection: 'row',
        borderBottom: '1px solid $neutral200',
      },
      vertical: {
        flexDirection: 'column',
        borderBottom: 'none',
        borderRight: '1px solid $neutral200',
        width: '200px',
      },
    },
  },
});

const TabTrigger = styled('button', {
  display: 'flex',
  alignItems: 'center',
  gap: '$space$2',
  padding: '$space$3 $space$4',
  fontSize: '$fontSizes$sm',
  fontWeight: 500,
  color: '$neutral600',
  backgroundColor: 'transparent',
  border: 'none',
  cursor: 'pointer',
  transition: 'all 150ms',
  position: 'relative',

  '&:hover:not(:disabled)': {
    color: '$primary500',
  },

  '&:disabled': {
    opacity: 0.5,
    cursor: 'not-allowed',
  },

  variants: {
    active: {
      true: {
        color: '$primary600',
      },
    },
    variant: {
      line: {
        '&::after': {
          content: '""',
          position: 'absolute',
          bottom: -1,
          left: 0,
          right: 0,
          height: '2px',
          backgroundColor: '$primary500',
          opacity: 0,
          transition: 'opacity 150ms',
        },
      },
      enclosed: {
        borderRadius: '$radius$md $radius$md 0 0',
        backgroundColor: '$neutral100',
      },
      soft: {
        borderRadius: '$radius$md',
        backgroundColor: '$neutral50',
      },
    },
  },

  // Combine active variant styles
  compoundVariants: [
    {
      active: true,
      variant: 'line',
      css: {
        '&::after': { opacity: 1 },
      },
    },
    {
      active: true,
      variant: 'enclosed',
      css: {
        backgroundColor: '$white',
        border: '1px solid $neutral200',
        borderBottomColor: '$white',
      },
    },
    {
      active: true,
      variant: 'soft',
      css: {
        backgroundColor: '$primary100',
        color: '$primary700',
      },
    },
  ],
});

const TabLabel = styled('span', {
  whiteSpace: 'nowrap',
});

const TabBadge = styled('span', {
  backgroundColor: '$primary500',
  color: '$white',
  fontSize: '$fontSizes$xs',
  fontWeight: 600,
  padding: '2px 6px',
  borderRadius: '999px',
  minWidth: '20px',
  textAlign: 'center',
});

const TabPanel = styled('div', {
  flex: 1,
});
```

### Stepper

Multi-step progress indicator.

```
┌─────────────────────────────────────────────────────────────────┐
│  Create Quote                                                   │
│                                                                  │
│  ●───────●───────○───────○                                      │
│  Details  Pricing  Review  Complete                             │
│                                                                  │
│  Step 1 of 4: Trip Details                                      │
└─────────────────────────────────────────────────────────────────┘
```

```typescript
interface Step {
  id: string;
  label: string;
  description?: string;
  icon?: string;
  disabled?: boolean;
}

interface StepperProps {
  steps: Step[];
  currentStep: number;
  onStepClick?: (stepIndex: number) => void;
  variant?: 'numbers' | 'dots' | 'icons';
  orientation?: 'horizontal' | 'vertical';
}

export const Stepper: React.FC<StepperProps> = ({
  steps,
  currentStep,
  onStepClick,
  variant = 'numbers',
  orientation = 'horizontal',
}) => {
  const getStepState = (index: number): 'completed' | 'current' | 'pending' => {
    if (index < currentStep) return 'completed';
    if (index === currentStep) return 'current';
    return 'pending';
  };

  return (
    <StepperContainer orientation={orientation}>
      {steps.map((step, index) => {
        const state = getStepState(index);
        const isClickable = onStepClick && !step.disabled && state !== 'pending';

        return (
          <React.Fragment key={step.id}>
            <StepItem
              state={state}
              clickable={!!isClickable}
              onClick={() => isClickable && onStepClick!(index)}
              orientation={orientation}
            >
              <StepIndicator state={state} variant={variant}>
                {variant === 'numbers' && (
                  state === 'completed' ? (
                    <Icon name="check" />
                  ) : (
                    index + 1
                  )
                )}
                {variant === 'icons' && (
                  state === 'completed' ? (
                    <Icon name="check" />
                  ) : (
                    step.icon && <Icon name={step.icon} />
                  )
                )}
                {variant === 'dots' && null}
              </StepIndicator>

              <StepContent>
                <StepLabel>{step.label}</StepLabel>
                {step.description && (
                  <StepDescription>{step.description}</StepDescription>
                )}
              </StepContent>
            </StepItem>

            {index < steps.length - 1 && (
              <StepConnector state={state} orientation={orientation} />
            )}
          </React.Fragment>
        );
      })}
    </StepperContainer>
  );
};

const StepperContainer = styled('div', {
  display: 'flex',
  alignItems: 'flex-start',

  variants: {
    orientation: {
      horizontal: {
        flexDirection: 'row',
        justifyContent: 'space-between',
      },
      vertical: {
        flexDirection: 'column',
        gap: '$space$2',
      },
    },
  },
});

const StepItem = styled('div', {
  display: 'flex',
  alignItems: 'center',
  gap: '$space$3',

  variants: {
    clickable: {
      true: {
        cursor: 'pointer',
      },
    },
    orientation: {
      horizontal: {
        flexDirection: 'row',
      },
      vertical: {
        flexDirection: 'column',
        alignItems: 'flex-start',
      },
    },
  },
});

const StepIndicator = styled('div', {
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  width: '32px',
  height: '32px',
  borderRadius: '50%',
  fontSize: '$fontSizes$sm',
  fontWeight: 600,
  flexShrink: 0,

  variants: {
    state: {
      completed: {
        backgroundColor: '$primary500',
        color: '$white',
      },
      current: {
        backgroundColor: '$primary100',
        color: '$primary600',
        border: '2px solid $primary500',
      },
      pending: {
        backgroundColor: '$neutral100',
        color: '$neutral400',
      },
    },
    variant: {
      dots: {
        width: '12px',
        height: '12px',
      },
    },
  },
});

const StepContent = styled('div', {
  textAlign: 'center',
});

const StepLabel = styled('div', {
  fontSize: '$fontSizes$sm',
  fontWeight: 500,
});

const StepDescription = styled('div', {
  fontSize: '$fontSizes$xs',
  color: '$neutral500',
  marginTop: '2px',
});

const StepConnector = styled('div', {
  flex: 1,
  height: '2px',
  minWidth: '$space$6',

  variants: {
    state: {
      completed: {
        backgroundColor: '$primary500',
      },
      current: {
        backgroundColor: '$neutral200',
      },
      pending: {
        backgroundColor: '$neutral200',
      },
    },
    orientation: {
      horizontal: {
        marginTop: '16px',
      },
      vertical: {
        width: '2px',
        height: '$space$4',
        marginLeft: '15px',
        marginTop: 0,
      },
    },
  },
});
```

---

## Action Patterns

### Confirmation Dialogs

Require explicit confirmation before destructive actions.

```typescript
interface ConfirmationOptions {
  title: string;
  message: string | React.ReactNode;
  confirmLabel?: string;
  cancelLabel?: string;
  variant?: 'danger' | 'warning' | 'info';
  requireInput?: boolean;
  requiredInput?: string;
}

interface ConfirmDialogProps extends ConfirmationOptions {
  open: boolean;
  onConfirm: () => void | Promise<void>;
  onCancel: () => void;
  isConfirming?: boolean;
}

export const ConfirmDialog: React.FC<ConfirmDialogProps> = ({
  open,
  title,
  message,
  confirmLabel = 'Confirm',
  cancelLabel = 'Cancel',
  variant = 'danger',
  requireInput = false,
  requiredInput = 'DELETE',
  onConfirm,
  onCancel,
  isConfirming = false,
}) => {
  const [inputValue, setInputValue] = useState('');
  const isValid = !requireInput || inputValue === requiredInput;

  return (
    <Modal open={open} onClose={onCancel}>
      <ModalContent>
        <ModalHeader>
          <ModalIcon variant={variant}>
            <Icon
              name={variant === 'danger' ? 'alert-triangle' : 'info'}
              size="lg"
            />
          </ModalIcon>
          <ModalTitle>{title}</ModalTitle>
        </ModalHeader>

        <ModalBody>
          <Message variant={variant}>{message}</Message>

          {requireInput && (
            <RequiredInputSection>
              <RequiredInputLabel>
                Type <strong>{requiredInput}</strong> to confirm:
              </RequiredInputLabel>
              <Input
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                placeholder={requiredInput}
              />
            </RequiredInputSection>
          )}
        </ModalBody>

        <ModalFooter>
          <Button
            variant="secondary"
            onClick={onCancel}
            disabled={isConfirming}
          >
            {cancelLabel}
          </Button>
          <Button
            variant={variant === 'danger' ? 'error' : 'primary'}
            onClick={onConfirm}
            disabled={!isValid || isConfirming}
          >
            {isConfirming ? 'Confirming...' : confirmLabel}
          </Button>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
};

// Hook for showing confirmation dialogs
export const useConfirm = () => {
  const [options, setOptions] = useState<ConfirmationOptions | null>(null);
  const [resolveConfirm, setResolveConfirm] = useState<
    ((confirmed: boolean) => void) | null
  >(null);

  const confirm = useCallback(
    (opts: ConfirmationOptions): Promise<boolean> => {
      return new Promise((resolve) => {
        setOptions(opts);
        setResolveConfirm(() => resolve);
      });
    },
    []
  );

  const handleConfirm = useCallback(async () => {
    if (resolveConfirm) resolveConfirm(true);
    setOptions(null);
    setResolveConfirm(null);
  }, [resolveConfirm]);

  const handleCancel = useCallback(() => {
    if (resolveConfirm) resolveConfirm(false);
    setOptions(null);
    setResolveConfirm(null);
  }, [resolveConfirm]);

  const ConfirmationDialog = options ? (
    <ConfirmDialog
      {...options}
      open={!!options}
      onConfirm={handleConfirm}
      onCancel={handleCancel}
    />
  ) : null;

  return { confirm, ConfirmationDialog };
};
```

### Action Toolbar

Contextual actions based on selection state.

```typescript
interface Action {
  id: string;
  label: string;
  icon: string;
  onClick: () => void;
  variant?: 'primary' | 'secondary' | 'danger';
  disabled?: boolean;
}

interface ActionToolbarProps {
  selectedCount: number;
  actions: Action[];
  onClearSelection: () => void;
  maxVisible?: number;
}

export const ActionToolbar: React.FC<ActionToolbarProps> = ({
  selectedCount,
  actions,
  onClearSelection,
  maxVisible = 4,
}) => {
  const [overflowOpen, setOverflowOpen] = useState(false);

  const visibleActions = actions.slice(0, maxVisible);
  const overflowActions = actions.slice(maxVisible);

  return (
    <ToolbarContainer>
      <ToolbarSelection>
        <SelectionCount>{selectedCount} selected</SelectionCount>
        <ClearButton onClick={onClearSelection}>
          <Icon name="x" size="xs" />
        </ClearButton>
      </ToolbarSelection>

      <ToolbarActions>
        {visibleActions.map((action) => (
          <ToolbarButton
            key={action.id}
            variant={action.variant ?? 'secondary'}
            onClick={action.onClick}
            disabled={action.disabled}
          >
            {action.icon && <Icon name={action.icon} />}
            {action.label}
          </ToolbarButton>
        ))}

        {overflowActions.length > 0 && (
          <OverflowDropdown
            actions={overflowActions}
            open={overflowOpen}
            onOpenChange={setOverflowOpen}
          />
        )}
      </ToolbarActions>
    </ToolbarContainer>
  );
};

const ToolbarContainer = styled('div', {
  position: 'sticky',
  top: 0,
  zIndex: 50,
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'space-between',
  gap: '$space$4',
  padding: '$space$3 $space$4',
  backgroundColor: '$primary50',
  borderBottom: '1px solid $primary200',
  borderRadius: '$radius$md $radius$md 0 0',
});

const ToolbarSelection = styled('div', {
  display: 'flex',
  alignItems: 'center',
  gap: '$space$2',
});

const SelectionCount = styled('span', {
  fontSize: '$fontSizes$sm',
  fontWeight: 500,
  color: '$primary700',
});

const ClearButton = styled('button', {
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  width: '20px',
  height: '20px',
  borderRadius: '50%',
  border: 'none',
  backgroundColor: 'transparent',
  color: '$primary600',
  cursor: 'pointer',
  transition: 'background-color 150ms',

  '&:hover': {
    backgroundColor: '$primary200',
  },
});

const ToolbarActions = styled('div', {
  display: 'flex',
  gap: '$space$2',
});

const ToolbarButton = styled(Button, {
  gap: '$space$2',
});
```

---

## Data Display Patterns

### Empty States

Helpful guidance when there's no data to display.

```typescript
interface EmptyStateProps {
  illustration?: string;
  title: string;
  description?: string;
  action?: {
    label: string;
    onClick: () => void;
    variant?: 'primary' | 'secondary';
  };
  size?: 'sm' | 'md' | 'lg';
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  illustration,
  title,
  description,
  action,
  size = 'md',
}) => {
  return (
    <EmptyStateContainer size={size}>
      {illustration ? (
        <EmptyStateIllustration src={illustration} alt="" />
      ) : (
        <EmptyStateIcon>
          <Icon name="inbox" size={size === 'lg' ? 'xl' : 'lg'} />
        </EmptyStateIcon>
      )}

      <EmptyStateTitle>{title}</EmptyStateTitle>

      {description && (
        <EmptyStateDescription>{description}</EmptyStateDescription>
      )}

      {action && (
        <EmptyStateAction>
          <Button variant={action.variant ?? 'primary'} onClick={action.onClick}>
            {action.label}
          </Button>
        </EmptyStateAction>
      )}
    </EmptyStateContainer>
  );
};

const EmptyStateContainer = styled('div', {
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  justifyContent: 'center',
  padding: '$space$8',
  textAlign: 'center',

  variants: {
    size: {
      sm: {
        padding: '$space$6',
        gap: '$space$3',
      },
      md: {
        padding: '$space$10',
        gap: '$space$4',
      },
      lg: {
        padding: '$space$16',
        gap: '$space$6',
      },
    },
  },
});

const EmptyStateIllustration = styled('img', {
  width: '200px',
  height: '150px',
  objectFit: 'contain',
  marginBottom: '$space$4',
  opacity: 0.8,
});

const EmptyStateIcon = styled('div', {
  color: '$neutral300',
  marginBottom: '$space$4',
});

const EmptyStateTitle = styled('h3', {
  fontSize: '$fontSizes$lg',
  fontWeight: 600,
  color: '$neutral700',
  maxWidth: '400px',
});

const EmptyStateDescription = styled('p', {
  fontSize: '$fontSizes$sm',
  color: '$neutral500',
  maxWidth: '400px',
  lineHeight: 1.5,
});

const EmptyStateAction = styled('div', {
  marginTop: '$space$4',
});
```

### Loading States

Visual feedback during data fetching.

```typescript
interface LoadingStateProps {
  message?: string;
  size?: 'sm' | 'md' | 'lg';
  variant?: 'spinner' | 'skeleton' | 'dots';
}

export const LoadingState: React.FC<LoadingStateProps> = ({
  message,
  size = 'md',
  variant = 'spinner',
}) => {
  return (
    <LoadingContainer size={size}>
      {variant === 'spinner' && <Spinner size={size} />}
      {variant === 'dots' && <DotsSpinner />}
      {variant === 'skeleton' && <SkeletonLoader />}
      {message && <LoadingMessage>{message}</LoadingMessage>}
    </LoadingContainer>
  );
};

// Pulse animation for skeleton loading
export const SkeletonLoader: React.FC = () => {
  return (
    <SkeletonContainer>
      {[...Array(3)].map((_, i) => (
        <SkeletonRow key={i}>
          <SkeletonCircle />
          <SkeletonText />
        </SkeletonRow>
      ))}
    </SkeletonContainer>
  );
};

const LoadingContainer = styled('div', {
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  justifyContent: 'center',
  padding: '$space$8',
  gap: '$space$4',

  variants: {
    size: {
      sm: { minHeight: '200px' },
      md: { minHeight: '400px' },
      lg: { minHeight: '600px' },
    },
  },
});

const LoadingMessage = styled('span', {
  fontSize: '$fontSizes$sm',
  color: '$neutral500',
});

const SkeletonContainer = styled('div', {
  display: 'flex',
  flexDirection: 'column',
  gap: '$space$4',
  width: '100%',
});

const SkeletonRow = styled('div', {
  display: 'flex',
  alignItems: 'center',
  gap: '$space$4',
});

const SkeletonCircle = styled('div', {
  width: '40px',
  height: '40px',
  borderRadius: '50%',
  backgroundColor: '$neutral200',
  animation: 'pulse 1.5s ease-in-out infinite',
});

const SkeletonText = styled('div', {
  flex: 1,
  height: '16px',
  borderRadius: '$radius$sm',
  backgroundColor: '$neutral200',
  animation: 'pulse 1.5s ease-in-out infinite',
  animationDelay: '0.2s',
});
```

### Error States

Clear error messaging with recovery actions.

```typescript
interface ErrorStateProps {
  title?: string;
  message: string;
  error?: Error;
  actions?: Array<{
    label: string;
    onClick: () => void;
    variant?: 'primary' | 'secondary';
  }>;
  showDetails?: boolean;
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  title = 'Something went wrong',
  message,
  error,
  actions,
  showDetails = false,
}) => {
  const [showErrorDetails, setShowErrorDetails] = useState(false);

  return (
    <ErrorContainer>
      <ErrorIcon>
        <Icon name="alert-circle" size="xl" />
      </ErrorIcon>

      <ErrorTitle>{title}</ErrorTitle>
      <ErrorMessage>{message}</ErrorMessage>

      {actions && (
        <ErrorActions>
          {actions.map((action, i) => (
            <Button
              key={i}
              variant={action.variant ?? 'primary'}
              onClick={action.onClick}
            >
              {action.label}
            </Button>
          ))}
        </ErrorActions>
      )}

      {showDetails && error && (
        <>
          <ErrorDetailsToggle onClick={() => setShowErrorDetails(!showErrorDetails)}>
            {showErrorDetails ? 'Hide' : 'Show'} details
          </ErrorDetailsToggle>

          {showErrorDetails && (
            <ErrorDetails>
              <pre>{error.stack || error.message}</pre>
            </ErrorDetails>
          )}
        </>
      )}
    </ErrorContainer>
  );
};

const ErrorContainer = styled('div', {
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  justifyContent: 'center',
  padding: '$space$8',
  textAlign: 'center',
  gap: '$space$4',
});

const ErrorIcon = styled('div', {
  color: '$error500',
  marginBottom: '$space$2',
});

const ErrorTitle = styled('h3', {
  fontSize: '$fontSizes$lg',
  fontWeight: 600,
  color: '$neutral900',
});

const ErrorMessage = styled('p', {
  fontSize: '$fontSizes$sm',
  color: '$neutral600',
  maxWidth: '400px',
});

const ErrorActions = styled('div', {
  display: 'flex',
  gap: '$space$3',
  marginTop: '$space$2',
});

const ErrorDetailsToggle = styled('button', {
  fontSize: '$fontSizes$xs',
  color: '$neutral500',
  textDecoration: 'underline',
  border: 'none',
  background: 'none',
  cursor: 'pointer',
});

const ErrorDetails = styled('div', {
  marginTop: '$space$4',
  padding: '$space$4',
  backgroundColor: '$neutral900',
  borderRadius: '$radius$md',
  width: '100%',
  maxWidth: '600px',

  '& pre': {
    fontSize: '$fontSizes$xs',
    color: '$neutral100',
    overflow: 'auto',
    whiteSpace: 'pre-wrap',
    wordBreak: 'break-word',
  },
});
```

---

## Feedback Patterns

### Toast Notifications

Transient notifications for events.

```typescript
type ToastVariant = 'success' | 'error' | 'warning' | 'info';

interface Toast {
  id: string;
  title: string;
  message?: string;
  variant?: ToastVariant;
  duration?: number;
  action?: {
    label: string;
    onClick: () => void;
  };
}

interface ToastProps extends Toast {
  onClose: (id: string) => void;
}

export const Toast: React.FC<ToastProps> = ({
  id,
  title,
  message,
  variant = 'info',
  duration = 5000,
  action,
  onClose,
}) => {
  useEffect(() => {
    if (duration > 0) {
      const timer = setTimeout(() => onClose(id), duration);
      return () => clearTimeout(timer);
    }
  }, [id, duration, onClose]);

  const icons = {
    success: 'check-circle',
    error: 'alert-circle',
    warning: 'alert-triangle',
    info: 'info',
  };

  return (
    <ToastContainer variant={variant}>
      <ToastIcon>
        <Icon name={icons[variant]} />
      </ToastIcon>

      <ToastContent>
        <ToastTitle>{title}</ToastTitle>
        {message && <ToastMessage>{message}</ToastMessage>}
        {action && (
          <ToastAction onClick={action.onClick}>{action.label}</ToastAction>
        )}
      </ToastContent>

      <ToastClose onClick={() => onClose(id)}>
        <Icon name="x" size="sm" />
      </ToastClose>

      {duration > 0 && <ToastProgress duration={duration} />}
    </ToastContainer>
  );
};

// Toast manager
export const Toaster: React.FC = () => {
  const { toasts, removeToast } = useToastStore();

  return (
    <ToasterContainer>
      {toasts.map((toast) => (
        <Toast key={toast.id} {...toast} onClose={removeToast} />
      ))}
    </ToasterContainer>
  );
};

const ToasterContainer = styled('div', {
  position: 'fixed',
  bottom: '$space$6',
  right: '$space$6',
  display: 'flex',
  flexDirection: 'column',
  gap: '$space$3',
  zIndex: 9999,
  maxWidth: '400px',
  width: '100%',
});

const ToastContainer = styled('div', {
  display: 'flex',
  alignItems: 'flex-start',
  gap: '$space$3',
  padding: '$space$4',
  backgroundColor: '$white',
  borderRadius: '$radius$md',
  boxShadow: '$shadow$lg',
  position: 'relative',
  overflow: 'hidden',

  variants: {
    variant: {
      success: {
        borderLeft: '4px solid $success500',
      },
      error: {
        borderLeft: '4px solid $error500',
      },
      warning: {
        borderLeft: '4px solid $warning500',
      },
      info: {
        borderLeft: '4px solid $info500',
      },
    },
  },
});

const ToastProgress = styled('div', {
  position: 'absolute',
  bottom: 0,
  left: 0,
  height: '3px',
  backgroundColor: 'currentColor',
  opacity: 0.3,
  animation: 'toast-progress linear forwards',

  variants: {
    duration: {
      // Spread for duration values
    },
  },
});
```

---

## Pattern Composition

Patterns can be composed together:

```typescript
// A list page composed of multiple patterns
export const TripListPage: React.FC = () => {
  return (
    <ApplicationShell
      header={<PageHeader />}
      sidebar={<NavigationSidebar />}
    >
      {/* Layout pattern */}
      <TwoColumnLayout
        main={
          <>
            {/* Navigation pattern */}
            <Breadcrumbs
              items={[
                { label: 'Trips', href: '/trips' },
                { label: 'All Trips' },
              ]}
            />

            {/* Action pattern */}
            <ActionToolbar
              selectedCount={selectedTrips.length}
              actions={toolbarActions}
              onClearSelection={clearSelection}
            />

            {/* Data display pattern */}
            {isLoading ? (
              <LoadingState message="Loading trips..." />
            ) : trips.length === 0 ? (
              <EmptyState
                title="No trips yet"
                description="Create your first trip to get started"
                action={{ label: 'Create Trip', onClick: createTrip }}
              />
            ) : (
              <TripTable trips={trips} />
            )}
          </>
        }
        side={
          <>
            <FilterPanel />
            <TripStats />
          </>
        }
      />
    </ApplicationShell>
  );
};
```

---

## Anti-Patterns

### Common Mistakes to Avoid

| Anti-Pattern | Why It's Bad | Better Approach |
|--------------|--------------|-----------------|
| **Hidden actions** | Users can't find features | Visible, labeled buttons |
| **Modal chains** | Trapping users in modals | Inline editing or multi-step wizards |
| **Inconsistent terminology** | Confuses users | Shared vocabulary |
| **Overusing confirmations** | Users ignore warnings | Only for destructive actions |
| **Silent failures** | Users don't know what happened | Clear error messages |
| **Pagination without search** | Hard to find items | Add search/filter |
| **Generic error messages** | Not actionable | Specific, helpful errors |

---

**Last Updated:** 2026-04-25

**Next:** DESIGN_04 — Accessibility Deep Dive (WCAG compliance, keyboard navigation, screen readers)
