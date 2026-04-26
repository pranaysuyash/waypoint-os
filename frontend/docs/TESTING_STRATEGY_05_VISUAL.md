# Testing Strategy Part 5: Visual Regression

> Chromatic, Storybook, and screenshot testing

**Series:** Testing Strategy
**Previous:** [Part 4: E2E Testing](./TESTING_STRATEGY_04_E2E.md)
**Next:** [Part 6: Performance Testing](./TESTING_STRATEGY_06_PERFORMANCE.md)

---

## Table of Contents

1. [Visual Testing Philosophy](#visual-testing-philosophy)
2. [Storybook Setup](#storybook-setup)
3. [Chromatic Integration](#chromatic-integration)
4. [Writing Visual Stories](#writing-visual-stories)
5. [Interaction Testing](#interaction-testing)
6. [Cross-Browser Testing](#cross-browser-testing)
7. [Review Workflow](#review-workflow)

---

## Visual Testing Philosophy

### What is Visual Testing?

Visual regression testing catches **UI changes** that functional tests miss:

- Layout shifts
- Style regressions
- Responsive design issues
- Cross-browser differences
- Accessibility regressions

### Visual Testing Matrix

```
┌────────────────────────────────────────────────────────┐
│                    Visual Testing                      │
├────────────────────────────────────────────────────────┤
│ Storybook + Chromatic    │  Playwright Screenshots     │
│ - Component-level        │  - Flow-level               │
│ - Fast feedback          │  - Real browser rendering   │
│ - All variants           │  - Critical pages           │
│ - PR review integration  │  - Cross-browser validation  │
└────────────────────────────────────────────────────────┘
```

### What to Test Visually

| Category | Examples | Priority |
|----------|----------|----------|
| **Core Components** | Buttons, Inputs, Cards | P0 |
| **Booking UI** | Forms, Timelines, Status | P0 |
| **Responsive** | Mobile, Tablet, Desktop | P0 |
| **States** | Loading, Error, Empty | P1 |
| **Theming** | Light, Dark modes | P1 |
| **i18n** | RTL languages, long text | P2 |

---

## Storybook Setup

### Installation

```bash
npx storybook@latest init
```

### Configuration

```typescript
// .storybook/main.ts

import type { StorybookConfig } from '@storybook/react-vite';

const config: StorybookConfig = {
  stories: [
    '../src/**/*.mdx',
    '../src/**/*.stories.@(js|jsx|ts|tsx|mdx)',
  ],
  addons: [
    '@storybook/addon-links',
    '@storybook/addon-essentials',
    '@storybook/addon-interactions',
    '@storybook/addon-a11y', // Accessibility testing
    '@storybook/addon-themes', // Theme switching
    '@storybook/addon-viewport', // Responsive testing
  ],
  framework: {
    name: '@storybook/react-vite',
    options: {},
  },
  docs: {
    autodocs: 'tag',
  },
  typescript: {
    check: false,
    reactDocgen: 'react-docgen-typescript',
    reactDocgenTypescriptOptions: {
      shouldExtractLiteralValuesFromEnum: true,
      propFilter: (prop) => {
        return !prop.name.startsWith('__');
      },
    },
  },
};

export default config;
```

### Preview Configuration

```typescript
// .storybook/preview.ts

import type { Preview } from '@storybook/react';
import { withThemeByDataAttribute } from '@storybook/addon-themes';
import { withDevices } from '@storybook/addon-viewport';
import '../src/index.css';

const preview: Preview = {
  parameters: {
    actions: { argTypesRegex: '^on.*' },
    controls: {
      matchers: {
        color: /(background|color)$/i,
        date: /Date$/,
      },
    },
    backgrounds: {
      default: 'light',
      values: [
        { name: 'light', value: '#ffffff' },
        { name: 'dark', value: '#1a1a1a' },
        { name: 'gray', value: '#f3f4f6' },
      ],
    },
    viewport: {
      viewports: {
        mobile: {
          name: 'Mobile',
          styles: { width: '375px', height: '667px' },
        },
        tablet: {
          name: 'Tablet',
          styles: { width: '768px', height: '1024px' },
        },
        desktop: {
          name: 'Desktop',
          styles: { width: '1440px', height: '900px' },
        },
      },
    },
  },
  globalTypes: {
    theme: {
      description: 'Global theme for components',
      defaultValue: 'light',
      toolbar: {
        title: 'Theme',
        icon: 'circlehollow',
        items: [
          { value: 'light', icon: 'sun', title: 'Light' },
          { value: 'dark', icon: 'moon', title: 'Dark' },
        ],
        dynamicTitle: true,
      },
    },
    locale: {
      description: 'Internationalization locale',
      defaultValue: 'en-US',
      toolbar: {
        title: 'Locale',
        icon: 'globe',
        items: [
          { value: 'en-US', title: 'English (US)' },
          { value: 'es-ES', title: 'Spanish' },
          { value: 'fr-FR', title: 'French' },
          { value: 'ar-SA', title: 'Arabic (RTL)' },
          { value: 'hi-IN', title: 'Hindi' },
        ],
      },
    },
  },
  decorators: [
    withThemeByDataAttribute({
      themes: {
        light: 'light',
        dark: 'dark',
      },
      defaultTheme: 'light',
      attributeName: 'data-theme',
    }),
    (Story) => (
      <div style={{ padding: '20px' }}>
        <Story />
      </div>
    ),
  ],
};

export default preview;
```

---

## Chromatic Integration

### Setup

```bash
npx chromatic init
```

### Configuration

```json
// package.json scripts
{
  "scripts": {
    "storybook": "storybook dev -p 6006",
    "build-storybook": "storybook build",
    "chromatic": "chromatic"
  }
}
```

```bash
# .github/workflows/chromatic.yml

name: Chromatic

on:
  push:
    branches: [main, master]
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  chromatic:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - uses: actions/setup-node@v4
        with:
          node-version: 20

      - name: Install dependencies
        run: npm ci

      - name: Publish to Chromatic
        uses: chromaui/action@v1
        with:
          token: ${{ secrets.GITHUB_TOKEN }}
          projectToken: ${{ secrets.CHROMATIC_PROJECT_TOKEN }}
          storybookBuildDir: storybook-static
          autoAcceptChanges: main # Only on main branch
```

### Chromatic Options

```javascript
// chromatic.config.js

module.exports = {
  // Storybook build output directory
  storybookBuildDir: 'storybook-static',

  // Automatically accept changes on main branch
  autoAcceptChanges: 'main',

  // Build only stories that changed
  onlyChanged: true,

  // Exit with error on changes (blocks PR merge)
  exitZeroOnChanges: false,

  // Number of parallel workers
  concurrentJobs: 4,

  // Ignore specific files/paths
  ignoreGlobs: ['**/*.test.ts', '**/*.test.tsx'],

  // Script to run before build
  buildScript: 'npm run build-storybook',
};
```

---

## Writing Visual Stories

### Component Story Structure

```typescript
// src/components/Button/Button.stories.tsx

import type { Meta, StoryObj } from '@storybook/react';
import { Button } from './Button';

const meta: Meta<typeof Button> = {
  title: 'Components/Button',
  component: Button,
  tags: ['autodocs'],
  argTypes: {
    variant: {
      control: 'select',
      options: ['primary', 'secondary', 'outline', 'ghost'],
    },
    size: {
      control: 'select',
      options: ['sm', 'md', 'lg'],
    },
    disabled: {
      control: 'boolean',
    },
    loading: {
      control: 'boolean',
    },
  },
};

export default meta;
type Story = StoryObj<typeof Button>;

// Default state
export const Primary: Story = {
  args: {
    variant: 'primary',
    children: 'Button',
  },
};

// All variants
export const Variants: Story = {
  render: () => (
    <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
      <Button variant="primary">Primary</Button>
      <Button variant="secondary">Secondary</Button>
      <Button variant="outline">Outline</Button>
      <Button variant="ghost">Ghost</Button>
    </div>
  ),
};

// All sizes
export const Sizes: Story = {
  render: () => (
    <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
      <Button size="sm">Small</Button>
      <Button size="md">Medium</Button>
      <Button size="lg">Large</Button>
    </div>
  ),
};

// States
export const States: Story = {
  render: () => (
    <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
      <Button>Default</Button>
      <Button disabled>Disabled</Button>
      <Button loading>Loading</Button>
    </div>
  ),
};

// With icons
export const WithIcon: Story = {
  args: {
    variant: 'primary',
    leftIcon: 'search',
    children: 'Search',
  },
};

// Dark mode
export const DarkMode: Story = {
  args: {
    variant: 'primary',
    children: 'Button',
  },
  parameters: {
    themes: {
      themeOverride: 'dark',
    },
  },
};

// RTL (Arabic)
export const RTL: Story = {
  args: {
    variant: 'primary',
    children: 'بحث',
  },
  parameters: {
    locale: 'ar-SA',
  },
};
```

### Complex Component Stories

```typescript
// src/components/BookingCard/BookingCard.stories.tsx

import type { Meta, StoryObj } from '@storybook/react';
import { BookingCard } from './BookingCard';

const meta: Meta<typeof BookingCard> = {
  title: 'Components/BookingCard',
  component: BookingCard,
  tags: ['autodocs'],
};

export default meta;
type Story = StoryObj<typeof BookingCard>;

// Confirmed booking
export const Confirmed: Story = {
  args: {
    booking: {
      id: 'BK-12345',
      destination: 'Paris, France',
      dates: { start: '2025-06-01', end: '2025-06-07' },
      guests: 2,
      status: 'confirmed',
      totalPrice: 2400,
      currency: 'USD',
      thumbnail: 'https://images.unsplash.com/photo-1502602898657-3e91760cbb34',
    },
  },
};

// Pending booking
export const Pending: Story = {
  args: {
    booking: {
      id: 'BK-12346',
      destination: 'London, UK',
      dates: { start: '2025-07-01', end: '2025-07-05' },
      guests: 4,
      status: 'pending',
      totalPrice: 1800,
      currency: 'USD',
    },
  },
};

// Cancelled booking
export const Cancelled: Story = {
  args: {
    booking: {
      id: 'BK-12347',
      destination: 'Tokyo, Japan',
      dates: { start: '2025-08-01', end: '2025-08-10' },
      guests: 2,
      status: 'cancelled',
      totalPrice: 3500,
      currency: 'USD',
    },
  },
};

// Loading state
export const Loading: Story = {
  args: {
    loading: true,
  },
};

// Error state
export const Error: Story = {
  args: {
    error: 'Failed to load booking details',
  },
};

// Long destination name (i18n test)
export const LongContent: Story = {
  args: {
    booking: {
      id: 'BK-12348',
      destination: 'Krasnodar Krai, Sochi, Black Sea Coast, Russia',
      dates: { start: '2025-09-01', end: '2025-09-14' },
      guests: 6,
      status: 'confirmed',
      totalPrice: 8400,
      currency: 'USD',
    },
  },
};

// Different currencies
export const Currencies: Story = {
  render: () => (
    <div style={{ display: 'grid', gap: '16px', maxWidth: '400px' }}>
      <BookingCard booking={mockBookingUSD} />
      <BookingCard booking={mockBookingEUR} />
      <BookingCard booking={mockBookingGBP} />
      <BookingCard booking={mockBookingINR} />
      <BookingCard booking={mockBookingJPY} />
    </div>
  ),
};
```

### Responsive Stories

```typescript
// src/components/Navigation/Navigation.stories.tsx

export const Responsive: Story = {
  render: () => <Navigation />,
  parameters: {
    viewport: {
      defaultViewport: 'mobile',
    },
  },
};

// Show multiple viewports
export const AllViewports: Story = {
  render: () => <Navigation />,
  parameters: {
    viewport: {
      viewports: ['mobile', 'tablet', 'desktop'],
    },
  },
};
```

---

## Interaction Testing

### Testing User Interactions

```typescript
// src/components/DatePicker/DatePicker.stories.tsx

import type { Meta, StoryObj } from '@storybook/react';
import { within, userEvent } from '@storybook/test';
import { DatePicker } from './DatePicker';

const meta: Meta<typeof DatePicker> = {
  title: 'Components/DatePicker',
  component: DatePicker,
};

export default meta;
type Story = StoryObj<typeof DatePicker>;

export const OpenAndClose: Story = {
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);

    // Click to open
    const input = canvas.getByLabelText(/date/i);
    await userEvent.click(input);

    // Calendar should be visible
    const calendar = canvas.getByRole('dialog');
    expect(calendar).toBeVisible();

    // Select a date
    const dateButton = canvas.getByRole('button', { name: '15' });
    await userEvent.click(dateButton);

    // Calendar should close
    expect(calendar).not.toBeInTheDocument();

    // Input should have value
    expect(input).toHaveValue('2025-06-15');
  },
};

export const DateRangeSelection: Story = {
  args: {
    range: true,
  },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);

    const input = canvas.getByLabelText(/date range/i);
    await userEvent.click(input);

    // Select start date
    await userEvent.click(canvas.getByRole('button', { name: '1' }));

    // Select end date
    await userEvent.click(canvas.getByRole('button', { name: '7' }));

    // Verify range
    expect(input).toHaveValue('Jun 1 - 7, 2025');
  },
};

export const Validation: Story = {
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);

    const input = canvas.getByLabelText(/date/i);

    // Try to select past date
    await userEvent.click(input);
    const pastDate = canvas.getByRole('button', { name: '1' });
    expect(pastDate).toHaveAttribute('aria-disabled', 'true');
  },
};
```

### Testing Async Interactions

```typescript
// src/components/Autocomplete/Autocomplete.stories.tsx

import type { Meta, StoryObj } from '@storybook/react';
import { within, userEvent, waitFor } from '@storybook/test';
import { Autocomplete } from './Autocomplete';

export const SearchAndSelect: Story = {
  args: {
    placeholder: 'Search destinations',
    onSearch: async (query) => {
      // Simulate API delay
      await new Promise(resolve => setTimeout(resolve, 500));
      return [
        { id: '1', name: 'Paris, France' },
        { id: '2', name: 'Paris, Texas' },
      ];
    },
  },
  play: async ({ canvasElement, args }) => {
    const canvas = within(canvasElement);

    const input = canvas.getByRole('combobox');

    // Type search
    await userEvent.type(input, 'Paris');

    // Wait for results
    await waitFor(() => {
      const listbox = canvas.getByRole('listbox');
      expect(listbox).toBeVisible();
    });

    // Select option
    await userEvent.click(canvas.getByRole('option', { name: 'Paris, France' }));

    // Verify selection
    expect(input).toHaveValue('Paris, France');
  },
};
```

---

## Cross-Browser Testing

### Chromatic Browser Matrix

```javascript
// chromatic.config.js

module.exports = {
  // Test against these browsers
  browsers: [
    'chrome',  // Latest
    'firefox', // Latest
    'safari',  // Latest (macOS only)
    'edge',    // Latest
  ],

  // Viewport sizes for each browser
  viewports: {
    mobile: { width: 375, height: 667 },
    tablet: { width: 768, height: 1024 },
    desktop: { width: 1440, height: 900 },
  },
};
```

### Browser-Specific Stories

```typescript
// .storybook/preview.ts

const preview: Preview = {
  parameters: {
    // Skip specific browsers if needed
    chromatic: {
      viewports: [320, 1200, 1500],
      disable: false,
    },
  },
};
```

### Handling Browser Differences

```typescript
// src/components/Map/Map.stories.tsx

export const DesktopOnly: Story = {
  args: { location: 'Paris' },
  parameters: {
    // Skip in mobile viewports
    viewport: {
      defaultViewport: 'desktop',
    },
  },
};

export const MobileFallback: Story = {
  args: { location: 'Paris' },
  parameters: {
    viewport: {
      defaultViewport: 'mobile',
    },
  },
};
```

---

## Review Workflow

### PR Integration

```yaml
# .github/workflows/pr-check.yml

name: PR Check

on:
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  visual-regression:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - uses: actions/setup-node@v4

      - run: npm ci

      # Run Chromatic
      - uses: chromaui/action@v1
        with:
          token: ${{ secrets.GITHUB_TOKEN }}
          projectToken: ${{ secrets.CHROMATIC_PROJECT_TOKEN }}
          exitZeroOnChanges: true # Don't block, just comment

      # Comment on PR with results
      - uses: actions/github-script@v7
        if: steps.chromatic.outputs.hasChanges == 'true'
        with:
          script: |
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: '🎨 Visual changes detected! Review them here: ${{ steps.chromatic.outputs.url }}'
            })
```

### Review Guidelines

```markdown
# Visual Review Checklist

When reviewing visual changes in Chromatic:

## Review Focus Areas

1. **Layout & Spacing**
   - [ ] Consistent margins and padding
   - [ ] Proper alignment
   - [ ] No unintended overflow

2. **Typography**
   - [ ] Consistent font weights
   - [ ] Proper line heights
   - [ ] Readable at all sizes

3. **Colors**
   - [ ] WCAG contrast ratios met
   - [ ] Consistent color usage
   - [ ] Proper dark mode support

4. **States**
   - [ ] Hover states defined
   - [ ] Focus indicators visible
   - [ ] Disabled states clear

5. **Responsive**
   - [ ] Mobile layout correct
   - [ ] Tablet layout correct
   - [ ] Desktop layout correct

## Acceptance Criteria

- **Accept**: Changes are intentional improvements
- **Request Changes**: Unintended regressions
- **Skip**: Third-party library changes, test data only
```

### Handling False Positives

```typescript
// .storybook/preview.ts

// Ignore dynamic content
const preview: Preview = {
  parameters: {
    // Chromatic ignore patterns
    chromatic: {
      // Ignore specific selectors
      ignore: [
        '[data-testid="current-time"]', // Dynamic timestamps
        '[data-testid="random-id"]',    // Random IDs
      ],

      // CSS to ignore
      cssVariables: [
        '--random-value',
      ],

      // Delay before screenshot
      delay: 100,
    },
  },
};
```

### Snapshot Acceptance

```javascript
// chromatic.config.js

module.exports = {
  // Automatically accept changes for certain patterns
  onlyChanged: true,

  // Branches that auto-accept
  autoAcceptChanges: 'main',

  // Specific story patterns to skip
  skipStories: [
    '**/*.test.**',
    '**/stories/**',
  ],
};
```

---

## Summary

Visual regression testing strategy:

- **Storybook** for component documentation and visual testing
- **Chromatic** for automated visual regression in PRs
- **Test all variants**: states, sizes, themes, locales
- **Interaction testing** with @storybook/test
- **Cross-browser** validation through Chromatic
- **PR workflow** blocks on unexpected changes

**Coverage Goals:**
- All design system components: 100%
- Core booking components: 100%
- Form components: 100%
- Responsive breakpoints: 100%

---

**Next:** [Part 6: Performance Testing](./TESTING_STRATEGY_06_PERFORMANCE.md) — Lighthouse CI, bundle analysis, and load testing
