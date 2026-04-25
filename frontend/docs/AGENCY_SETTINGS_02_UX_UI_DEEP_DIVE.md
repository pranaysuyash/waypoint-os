# Agency Settings — UX/UI Deep Dive

> Part 2 of 4 in Agency Settings Exploration Series

---

## Document Overview

**Series:** Agency Settings / Configuration
**Part:** 2 — UX/UI Design
**Status:** Complete
**Last Updated:** 2026-04-25

---

## Table of Contents

1. [Design Philosophy](#design-philosophy)
2. [Information Architecture](#information-architecture)
3. [Settings Layout](#settings-layout)
4. [Component Library](#component-library)
5. [Key Screens](#key-screens)
6. [Interaction Patterns](#interaction-patterns)
7. [Mobile Experience](#mobile-experience)
8. [Accessibility](#accessibility)

---

## Design Philosophy

### Core Principles

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      AGENCY SETTINGS DESIGN PHILOSOPHY                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. PROGRESSIVE DISCLOSURE                                                  │
│     ┌─────────────────────────────────────────────────────────────────┐    │
│     │ Show simple options first, advanced settings behind "More"      │    │
│     │ Group related settings together, hide complexity                │    │
│     └─────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│  2. IMMEDIATE FEEDBACK                                                     │
│     ┌─────────────────────────────────────────────────────────────────┐    │
│     │ Save happens automatically with clear indication                 │    │
│     │ Visual confirmation for all actions                             │    │
│     └─────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│  3. CLEAR VISUAL HIERARCHY                                                 │
│     ┌─────────────────────────────────────────────────────────────────┐    │
│     │ Important settings prominent, rarely-used tucked away            │    │
│     │ Use spacing, typography, and color to guide attention           │    │
│     └─────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│  4. ERROR PREVENTION                                                       │
│     ┌─────────────────────────────────────────────────────────────────┐    │
│     │ Validate before saving, show warnings for destructive actions   │    │
│     │ Clear labels, inline help, and examples for complex settings    │    │
│     └─────────────────────────────────────────────────────────────────┘    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Visual Language

| Element | Specification | Rationale |
|---------|---------------|-----------|
| **Primary Action** | `#6366F1` (Indigo) | Consistent with product branding |
| **Destructive Action** | `#EF4444` (Red) | Clear danger indication |
| **Success State** | `#10B981` (Green) | Positive confirmation |
| **Warning State** | `#F59E0B` (Amber) | Caution without alarm |
| **Section Divider** | `#E5E7EB` (Gray 200) | Subtle separation |
| **Card Background** | `#FFFFFF` (White) | Clean content areas |
| **Page Background** | `#F9FAFB` (Light Gray) | Reduced eye strain |
| **Text Primary** | `#111827` (Gray 900) | High readability |
| **Text Secondary** | `#6B7280` (Gray 500) | Supporting information |

---

## Information Architecture

### Site Map

```
Agency Settings
├── /settings (default: General)
│   ├── Overview (quick stats & quick actions)
│   └── General
│       ├── Profile (name, contact, address)
│       ├── Business identifiers (GST, PAN)
│       └── Business hours
│
├── Branding
│   ├── Logo & visual identity
│   ├── Colors & typography
│   ├── Email templates
│   └── Custom domain
│
├── Team
│   ├── Members list
│   ├── Roles & permissions
│   └── Groups
│
├── Preferences
│   ├── Regional (currency, timezone, language)
│   ├── Date & time formats
│   └── Number formats
│
├── Notifications
│   ├── Email preferences
│   ├── Push notifications
│   └── SMS alerts
│
├── Integrations
│   ├── WhatsApp Business
│   ├── Email service
│   ├── SMS gateway
│   ├── Payment gateway
│   └── Accounting (Tally)
│
├── Billing
│   ├── Plan & usage
│   ├── Payment method
│   ├── Invoices
│   └── Billing history
│
└── Security
    ├── Two-factor authentication
    ├── Active sessions
    ├── Audit log
    └── API keys
```

### Navigation Structure

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Settings                                                       [Save] [×] │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ╔═══════════════════════════════════════════════════════════════════════════╗ │
│  ║ Sidebar Navigation                                                     ║ │
│  ╠═══════════════════════════════════════════════════════════════════════════╣ │
│  ║                                                                         ║ │
│  ║  ┌──────────────────────┐                                              ║ │
│  ║  │ Overview             │                                              ║ │
│  ║  └──────────────────────┘                                              ║ │
│  ║                                                                         ║ │
│  ║  GENERAL                                                                 ║ │
│  ║  ┌──────────────────────┐  ┌──────────────────────┐                     ║ │
│  ║  │ Profile              │  │ Business             │                     ║ │
│  ║  └──────────────────────┘  └──────────────────────┘                     ║ │
│  ║  ┌──────────────────────┐                                               ║ │
│  ║  │ Hours                │                                               ║ │
│  ║  └──────────────────────┘                                               ║ │
│  ║                                                                         ║ │
│  ║  BRANDING                                                                ║ │
│  ║  ┌──────────────────────┐  ┌──────────────────────┐                     ║ │
│  ║  │ Logo & Colors        │  │ Email Templates      │                     ║ │
│  ║  └──────────────────────┘  └──────────────────────┘                     ║ │
│  ║                                                                         ║ │
│  ║  TEAM                                              ⟳ 3                  ║ │
│  ║  ┌──────────────────────┐  ┌──────────────────────┐                     ║ │
│  ║  │ Members              │  │ Roles                │                     ║ │
│  ║  └──────────────────────┘  └──────────────────────┘                     ║ │
│  ║                                                                         ║ │
│  ║  PREFERENCES                                                              ║ │
│  ║  ┌──────────────────────┐                                               ║ │
│  ║  │ Regional             │                                               ║ │
│  ║  └──────────────────────┘                                               ║ │
│  ║                                                                         ║ │
│  ║  NOTIFICATIONS                                                           ║ │
│  ║  ┌──────────────────────┐                                               ║ │
│  ║  │ Email & Push         │                                               ║ │
│  ║  └──────────────────────┘                                               ║ │
│  ║                                                                         ║ │
│  ║  INTEGRATIONS                                       ⟳ 5                  ║ │
│  ║  ┌──────────────────────┐                                               ║ │
│  ║  │ Connected            │                                               ║ │
│  ║  └──────────────────────┘                                               ║ │
│  ║                                                                         ║ │
│  ║  BILLING                                                                 ║ │
│  ║  ┌──────────────────────┐                                               ║ │
│  ║  │ Plan & Usage         │                                               ║ │
│  ║  └──────────────────────┘                                               ║ │
│  ║                                                                         ║ │
│  ║  SECURITY                                                                ║ │
│  ║  ┌──────────────────────┐                                               ║ │
│  ║  │ 2FA & Sessions        │                                               ║ │
│  ║  └──────────────────────┘                                               ║ │
│  ║                                                                         ║ │
│  ╚═══════════════════════════════════════════════════════════════════════════╝ │
│                                                                              │
│  ╔═══════════════════════════════════════════════════════════════════════════╗ │
│  ║ Main Content Area                                                       ║ │
│  ╠═══════════════════════════════════════════════════════════════════════════╣ │
│  ║                                                                         ║ │
│  ║  ┌─────────────────────────────────────────────────────────────────────┐ ║ │
│  ║  │ Profile Settings                                                   │ ║ │
│  ║  │                                                                   │ ║ │
│  ║  │  ┌─────────────────────────────────────────────────────────────────┤│ ║ │
│  ║  │  │ Agency Name                                                    ││ ║ │
│  ║  │  │ ┌─────────────────────────────────────────────────────────────┐ ││ ║ │
│  ║  │  │ │ ABC Travels Pvt Ltd                                        │ ││ ║ │
│  ║  │  │ └─────────────────────────────────────────────────────────────┘ ││ ║ │
│  ║  │  │                                                               ││ ║ │
│  ║  │  │  This name appears on quotes, invoices, and customer emails.   ││ ║ │
│  ║  │  │                                                               ││ ║ │
│  ║  │  ├─────────────────────────────────────────────────────────────────┤│ ║ │
│  ║  │  │ Agency Email                                                 ││ ║ │
│  ║  │  │ ┌─────────────────────────────────────────────────────────────┐ ││ ║ │
│  ║  │  │ │ contact@abctravels.com                                    │ ││ ║ │
│  ║  │  │ └─────────────────────────────────────────────────────────────┘ ││ ║ │
│  ║  │  │                                                               ││ ║ │
│  ║  │  │  Used for sending notifications and as reply-to address.       ││ ║ │
│  ║  │  │                                                               ││ ║ │
│  ║  │  ├─────────────────────────────────────────────────────────────────┤│ ║ │
│  ║  │  │ Agency Phone                                                 ││ ║ │
│  ║  │  │ ┌─────────────────────────────────────────────────────────────┐ ││ ║ │
│  ║  │  │ │ +91 98765 43210                                           │ ││ ║ │
│  ║  │  │ └─────────────────────────────────────────────────────────────┘ ││ ║ │
│  ║  │  │                                                               ││ ║ │
│  ║  │  │  Displayed on customer portal and documents.                   ││ ║ │
│  ║  │  │                                                               ││ ║ │
│  ║  │  ├─────────────────────────────────────────────────────────────────┤│ ║ │
│  ║  │  │ Agency Website                                               ││ ║ │
│  ║  │  │ ┌─────────────────────────────────────────────────────────────┐ ││ ║ │
│  ║  │  │ │ https://abctravels.com                                    │ ││ ║ │
│  ║  │  │ └─────────────────────────────────────────────────────────────┘ ││ ║ │
│  ║  │  │                                                               ││ ║ │
│  ║  │  │  Linked on customer-facing documents.                          ││ ║ │
│  ║  │  │                                                               ││ ║ │
│  ║  │  └─────────────────────────────────────────────────────────────────┘│ ║ │
│  ║  │                                                                   │ ║ │
│  ║  │                                          [All changes saved]      │ ║ │
│  ║  └─────────────────────────────────────────────────────────────────────┘ ║ │
│  ║                                                                         ║ │
│  ╚═══════════════════════════════════════════════════════════════════════════╝ │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Settings Layout

### Layout Component

```typescript
// components/settings/SettingsLayout.tsx

interface SettingsLayoutProps {
  children: React.ReactNode;
  currentSection?: string;
}

export const SettingsLayout: React.FC<SettingsLayoutProps> = ({
  children,
  currentSection = 'general'
}) => {
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle');

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar Navigation */}
      <SettingsSidebar currentSection={currentSection} />

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <SettingsHeader
          currentSection={currentSection}
          saveStatus={saveStatus}
        />

        {/* Content Area */}
        <main className="flex-1 overflow-y-auto p-6">
          {children}
        </main>
      </div>
    </div>
  );
};

const SettingsSidebar: React.FC<{ currentSection: string }> = ({ currentSection }) => {
  const navigation = useSettingsNavigation();

  return (
    <aside className="w-64 bg-white border-r border-gray-200 overflow-y-auto">
      <div className="p-4">
        <h2 className="text-lg font-semibold text-gray-900">Settings</h2>
      </div>

      <nav className="px-2">
        {navigation.map((section) => (
          <div key={section.id} className="mb-4">
            {section.label && (
              <h3 className="px-3 mb-1 text-xs font-semibold text-gray-500 uppercase tracking-wider">
                {section.label}
              </h3>
            )}

            {section.items.map((item) => (
              <Link
                key={item.id}
                href={item.href}
                className={cn(
                  "flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors",
                  item.id === currentSection
                    ? "bg-indigo-50 text-indigo-700"
                    : "text-gray-700 hover:bg-gray-100"
                )}
              >
                <item.icon size={16} />
                <span>{item.label}</span>
                {item.badge && (
                  <Badge size="sm" variant="neutral">
                    {item.badge}
                  </Badge>
                )}
              </Link>
            ))}
          </div>
        ))}
      </nav>
    </aside>
  );
};

const SettingsHeader: React.FC<{
  currentSection: string;
  saveStatus: 'idle' | 'saving' | 'saved' | 'error';
}> = ({ currentSection, saveStatus }) => {
  const sectionInfo = useSectionInfo(currentSection);

  return (
    <header className="bg-white border-b border-gray-200 px-6 py-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-gray-900">
            {sectionInfo.title}
          </h1>
          {sectionInfo.description && (
            <p className="text-sm text-gray-500 mt-1">
              {sectionInfo.description}
            </p>
          )}
        </div>

        <SaveStatusIndicator status={saveStatus} />
      </div>
    </header>
  );
};

const SaveStatusIndicator: React.FC<{ status: 'idle' | 'saving' | 'saved' | 'error' }> = ({ status }) => {
  if (status === 'idle') return null;

  const config = {
    saving: { icon: <Spinner size="sm" />, text: 'Saving...', color: 'text-gray-500' },
    saved: { icon: <CheckIcon size="sm" />, text: 'All changes saved', color: 'text-green-600' },
    error: { icon: <AlertIcon size="sm" />, text: 'Failed to save', color: 'text-red-600' }
  }[status];

  return (
    <div className={cn("flex items-center gap-2 text-sm", config.color)}>
      {config.icon}
      <span>{config.text}</span>
    </div>
  );
};
```

### Settings Card Component

```typescript
// components/settings/SettingsCard.tsx

interface SettingsCardProps {
  title: string;
  description?: string;
  icon?: React.ReactNode;
  action?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
}

/**
 * Card component for grouping related settings
 */
export const SettingsCard: React.FC<SettingsCardProps> = ({
  title,
  description,
  icon,
  action,
  children,
  className
}) => {
  return (
    <div className={cn("bg-white rounded-xl border border-gray-200", className)}>
      {/* Card Header */}
      <div className="px-6 py-4 border-b border-gray-100">
        <div className="flex items-start justify-between">
          <div className="flex items-start gap-3">
            {icon && (
              <div className="p-2 bg-indigo-50 rounded-lg text-indigo-600">
                {icon}
              </div>
            )}
            <div>
              <h3 className="text-base font-semibold text-gray-900">{title}</h3>
              {description && (
                <p className="text-sm text-gray-500 mt-1">{description}</p>
              )}
            </div>
          </div>
          {action}
        </div>
      </div>

      {/* Card Content */}
      <div className="p-6">
        {children}
      </div>
    </div>
  );
};
```

---

## Component Library

### SettingsField Component

```typescript
// components/settings/SettingsField.tsx

interface SettingsFieldProps {
  label: string;
  description?: string;
  htmlFor?: string;
  required?: boolean;
  error?: string;
  warning?: string;
  children: React.ReactNode;
  actions?: React.ReactNode;
}

/**
 * Form field wrapper for consistent settings form layout
 */
export const SettingsField: React.FC<SettingsFieldProps> = ({
  label,
  description,
  htmlFor,
  required,
  error,
  warning,
  children,
  actions
}) => {
  return (
    <div className="space-y-1">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <label
            htmlFor={htmlFor}
            className="block text-sm font-medium text-gray-700"
          >
            {label}
            {required && <span className="text-red-500 ml-1">*</span>}
          </label>
          {description && (
            <p className="text-sm text-gray-500 mt-1">{description}</p>
          )}
        </div>
        {actions}
      </div>

      {children}

      {error && (
        <p className="text-sm text-red-600 flex items-center gap-1">
          <AlertCircleIcon size="xs" />
          {error}
        </p>
      )}

      {warning && (
        <p className="text-sm text-amber-600 flex items-center gap-1">
          <WarningIcon size="xs" />
          {warning}
        </p>
      )}
    </div>
  );
};

// Usage example
<SettingsField
  label="Agency Name"
  description="This name appears on quotes, invoices, and customer emails."
  htmlFor="agencyName"
  required
  error={errors.agencyName}
>
  <Input
    id="agencyName"
    value={values.agencyName}
    onChange={(v) => setFieldValue('agencyName', v)}
    placeholder="Enter agency name"
  />
</SettingsField>
```

### Branding Components

```typescript
// components/branding/LogoUploader.tsx

interface LogoUploaderProps {
  currentLogo?: string;
  variant?: 'light' | 'dark' | 'icon';
  onUpload: (file: File) => Promise<{ url: string; width: number; height: number }>;
  onDelete?: () => Promise<void>;
}

/**
 * Logo upload component with preview
 */
export const LogoUploader: React.FC<LogoUploaderProps> = ({
  currentLogo,
  variant = 'light',
  onUpload,
  onDelete
}) => {
  const [isUploading, setIsUploading] = useState(false);
  const [isDragging, setIsDragging] = useState(false);

  const handleFile = async (file: File) => {
    if (!file.type.startsWith('image/')) {
      toast.error('Please upload an image file');
      return;
    }

    if (file.size > 5 * 1024 * 1024) {
      toast.error('File size must be less than 5MB');
      return;
    }

    setIsUploading(true);

    try {
      const result = await onUpload(file);
      toast.success('Logo uploaded successfully');
    } catch (error) {
      toast.error('Failed to upload logo');
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="space-y-4">
      {/* Preview */}
      {currentLogo ? (
        <div className="relative group">
          <div className="flex items-center justify-center p-8 bg-gray-50 rounded-lg border-2 border-dashed border-gray-200">
            <img
              src={currentLogo}
              alt="Agency logo"
              className="max-h-32 max-w-full object-contain"
            />
          </div>

          {/* Actions */}
          <div className="absolute inset-0 flex items-center justify-center bg-black/50 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity">
            <label className="flex items-center gap-2 px-4 py-2 bg-white rounded-lg shadow cursor-pointer hover:bg-gray-50">
              <UploadIcon size="sm" />
              <span>Replace</span>
              <input
                type="file"
                className="hidden"
                accept="image/*"
                onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])}
              />
            </label>

            {onDelete && (
              <Button
                variant="destructive"
                size="sm"
                icon={<TrashIcon />}
                onClick={onDelete}
                className="ml-2"
              >
                Remove
              </Button>
            )}
          </div>
        </div>
      ) : (
        /* Upload Area */
        <div
          className={cn(
            "relative p-8 border-2 border-dashed rounded-lg text-center transition-colors",
            isDragging ? "border-indigo-500 bg-indigo-50" : "border-gray-300 hover:border-gray-400"
          )}
          onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
          onDragLeave={() => setIsDragging(false)}
          onDrop={(e) => {
            e.preventDefault();
            setIsDragging(false);
            const file = e.dataTransfer.files[0];
            if (file) handleFile(file);
          }}
        >
          <input
            type="file"
            className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
            accept="image/*"
            onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])}
            disabled={isUploading}
          />

          <div className="space-y-2">
            <div className="w-12 h-12 bg-gray-100 rounded-full flex items-center justify-center mx-auto">
              {isUploading ? (
                <Spinner />
              ) : (
                <ImageIcon className="text-gray-400" size={24} />
              )}
            </div>
            <div>
              <p className="text-sm font-medium text-gray-700">
                {isDragging ? 'Drop image here' : 'Click to upload or drag and drop'}
              </p>
              <p className="text-xs text-gray-500 mt-1">
                SVG, PNG, JPG up to 5MB
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Size info */}
      <div className="flex items-center justify-between text-xs text-gray-500">
        <span>Recommended: 400px width, transparent background</span>
        {currentLogo && (
          <Button variant="ghost" size="xs" onClick={() => window.open(currentLogo, '_blank')}>
            View full size
          </Button>
        )}
      </div>
    </div>
  );
};
```

### ColorPicker Component

```typescript
// components/branding/ColorPicker.tsx

interface ColorPickerProps {
  label: string;
  value: string;
  onChange: (color: string) => void;
  presets?: string[];
  allowAlpha?: boolean;
}

/**
 * Color picker with preset swatches
 */
export const ColorPicker: React.FC<ColorPickerProps> = ({
  label,
  value,
  onChange,
  presets = [
    '#6366F1', '#8B5CF6', '#EC4899', '#F59E0B',
    '#10B981', '#3B82F6', '#EF4444', '#111827'
  ],
  allowAlpha = false
}) => {
  const [showPicker, setShowPicker] = useState(false);
  const pickerRef = useRef<HTMLDivElement>(null);

  useClickOutside(pickerRef, () => setShowPicker(false));

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <label className="text-sm font-medium text-gray-700">{label}</label>
        <Button
          variant="ghost"
          size="xs"
          onClick={() => onChange('#6366F1')}
        >
          Reset
        </Button>
      </div>

      <div className="flex items-center gap-3">
        {/* Color Preview */}
        <button
          onClick={() => setShowPicker(!showPicker)}
          className="relative w-10 h-10 rounded-lg border-2 border-gray-200 hover:border-gray-300 transition-colors"
          style={{ backgroundColor: value }}
        >
          {showPicker && (
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="w-4 h-4 bg-white rounded-full shadow" />
            </div>
          )}
        </button>

        {/* Hex Input */}
        <div className="flex-1">
          <Input
            value={value}
            onChange={(v) => {
              if (/^#[0-9A-Fa-f]{6}$/.test(v)) {
                onChange(v);
              }
            }}
            placeholder="#000000"
            className="uppercase"
          />
        </div>
      </div>

      {/* Presets */}
      {presets.length > 0 && (
        <div className="flex items-center gap-2 flex-wrap">
          {presets.map((preset) => (
            <button
              key={preset}
              onClick={() => onChange(preset)}
              className={cn(
                "w-6 h-6 rounded border-2 transition-transform hover:scale-110",
                value === preset ? "border-gray-900" : "border-gray-200"
              )}
              style={{ backgroundColor: preset }}
              title={preset}
            />
          ))}
        </div>
      )}

      {/* Color Picker Popover */}
      {showPicker && (
        <div
          ref={pickerRef}
          className="absolute z-50 p-3 bg-white rounded-lg shadow-xl border border-gray-200"
        >
          <input
            type="color"
            value={value}
            onChange={(e) => onChange(e.target.value)}
            className="w-32 h-32 cursor-pointer"
          />
        </div>
      )}
    </div>
  );
};
```

### TeamMemberList Component

```typescript
// components/team/TeamMemberList.tsx

interface TeamMemberListProps {
  members: TeamMember[];
  currentUserRole: string;
  onRemove?: (memberId: string) => void;
  onUpdateRole?: (memberId: string, role: string) => void;
}

/**
 * Team members list with inline actions
 */
export const TeamMemberList: React.FC<TeamMemberListProps> = ({
  members,
  currentUserRole,
  onRemove,
  onUpdateRole
}) => {
  const [expandedMember, setExpandedMember] = useState<string | null>(null);

  return (
    <div className="space-y-2">
      {members.map((member) => (
        <div
          key={member.id}
          className={cn(
            "flex items-center gap-4 p-4 rounded-lg border transition-colors",
            expandedMember === member.id ? "bg-indigo-50 border-indigo-200" : "bg-white border-gray-200 hover:border-gray-300"
          )}
        >
          {/* Avatar */}
          <Avatar src={member.avatar_url} name={member.name} size="md" />

          {/* Info */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <h4 className="text-sm font-medium text-gray-900 truncate">
                {member.name}
              </h4>
              {member.status === 'pending' && (
                <Badge variant="warning" size="sm">Pending</Badge>
              )}
            </div>
            <p className="text-sm text-gray-500 truncate">{member.email}</p>
          </div>

          {/* Role */}
          {member.status === 'active' && (
            <div className="flex items-center gap-2">
              <Badge variant="neutral">{member.role_name}</Badge>
              {member.job_title && (
                <span className="text-sm text-gray-500">{member.job_title}</span>
              )}
            </div>
          )}

          {/* Actions */}
          <div className="flex items-center gap-2">
            {canManageMember(currentUserRole, member) && (
              <>
                {onUpdateRole && member.status === 'active' && (
                  <RoleSelector
                    currentRole={member.role_name}
                    onSelect={(role) => onUpdateRole(member.id, role)}
                  />
                )}
                {onRemove && (
                  <Button
                    variant="ghost"
                    size="sm"
                    icon={<MoreVerticalIcon />}
                    onClick={() => setExpandedMember(member.id)}
                  />
                )}
              </>
            )}
          </div>

          {/* Expanded Actions */}
          {expandedMember === member.id && (
            <div className="absolute right-4 top-full mt-2 z-10 bg-white rounded-lg shadow-xl border border-gray-200 py-1 min-w-[150px]">
              <button
                onClick={() => {
                  onRemove?.(member.id);
                  setExpandedMember(null);
                }}
                className="w-full px-4 py-2 text-left text-sm text-red-600 hover:bg-red-50 flex items-center gap-2"
              >
                <TrashIcon size="sm" />
                Remove member
              </button>
            </div>
          )}
        </div>
      ))}
    </div>
  );
};

function canManageMember(currentRole: string, member: TeamMember): boolean {
  // Owners can't be removed
  if (member.role_name === 'Owner') return false;

  // Only admins and owners can manage members
  return ['Owner', 'Admin'].includes(currentRole);
}
```

---

## Key Screens

### General Settings Screen

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Profile Settings                                    [All changes saved]     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │ Agency Information                                                        ││
│  │                                                                          ││
│  │  Agency Name                                                              ││
│  │  ┌────────────────────────────────────────────────────────────────────┐ ││
│  │  │ ABC Travels Pvt Ltd                                                │ ││
│  │  └────────────────────────────────────────────────────────────────────┘ ││
│  │  This name appears on quotes, invoices, and customer emails.             ││
│  │                                                                          ││
│  │  Agency Email                                                             ││
│  │  ┌────────────────────────────────────────────────────────────────────┐ ││
│  │  │ contact@abctravels.com                                              │ ││
│  │  └────────────────────────────────────────────────────────────────────┘ ││
│  │  Used for sending notifications and as reply-to address.                 ││
│  │                                                                          ││
│  │  Agency Phone                                                             ││
│  │  ┌────────────────────────────────────────────────────────────────────┐ ││
│  │  │ +91 98765 43210                                                     │ ││
│  │  └────────────────────────────────────────────────────────────────────┘ ││
│  │  Displayed on customer portal and documents.                             ││
│  │                                                                          ││
│  │  Agency Website                                                           ││
│  │  ┌────────────────────────────────────────────────────────────────────┐ ││
│  │  │ https://abctravels.com                                              │ ││
│  │  └────────────────────────────────────────────────────────────────────┘ ││
│  │  Linked on customer-facing documents.                                    ││
│  │                                                                          ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │ Business Address                                                          ││
│  │                                                                          ││
│  │  Address Line 1                                                           ││
│  │  ┌────────────────────────────────────────────────────────────────────┐ ││
│  │  │ 123, MG Road                                                         │ ││
│  │  └────────────────────────────────────────────────────────────────────┘ ││
│  │                                                                          ││
│  │  Address Line 2 (Optional)                                               ││
│  │  ┌────────────────────────────────────────────────────────────────────┐ ││
│  │  │                                                                     │ ││
│  │  └────────────────────────────────────────────────────────────────────┘ ││
│  │                                                                          ││
│  │  City                      State                    Postal Code            ││
│  │  ┌────────────────────┐ ┌────────────────────┐ ┌────────────────────┐ ││
│  │  │ Mumbai             │ │ Maharashtra        │ │ 400001             │ ││
│  │  └────────────────────┘ └────────────────────┘ └────────────────────┘ ││
│  │                                                                          ││
│  │  Country                                                                   ││
│  │  ┌────────────────────────────────────────────────────────────────────┐ ││
│  │  │ India                                    ▼                         │ ││
│  │  └────────────────────────────────────────────────────────────────────┘ ││
│  │                                                                          ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │ Tax Information                                               (Optional) ││
│  │                                                                          ││
│  │  GST Number                                                                ││
│  │  ┌────────────────────────────────────────────────────────────────────┐ ││
│  │  │ 27ABCDE1234F1Z5                                                     │ ││
│  │  └────────────────────────────────────────────────────────────────────┘ ││
│  │  Used for GST-compliant invoicing.                                        ││
│  │                                                                          ││
│  │  PAN Number                                                                ││
│  │  ┌────────────────────────────────────────────────────────────────────┐ ││
│  │  │ ABCDE1234F                                                          │ ││
│  │  └────────────────────────────────────────────────────────────────────┘ ││
│  │  Required for TDS compliance and tax reporting.                           ││
│  │                                                                          ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Branding Settings Screen

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Logo & Visual Identity                                   [All changes saved]  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │ Logo                                                                     ││
│  │                                                                          ││
│  │  ┌────────────────────┐    ┌────────────────────┐                      ││
│  │  │   Light Mode        │    │   Dark Mode         │                      ││
│  │  │                    │    │                    │                      ││
│  │  │   [Your Logo Here]  │    │   [Your Logo Here]  │                      ││
│  │  │       400x200       │    │       400x200       │                      ││
│  │  │                    │    │                    │                      ││
│  │  │   [Replace] [Remove]│    │   [Replace] [Remove]│                      ││
│  │  └────────────────────┘    └────────────────────┘                      ││
│  │                                                                          ││
│  │  ┌────────────────────┐                                                    ││
│  │  │   App Icon (Favicon)│                                                   ││
│  │  │                    │                                                    ││
│  │  │      [Logo]        │   Recommended: 512x512, transparent background     ││
│  │  │      64x64         │                                                    ││
│  │  │   [Replace] [Remove]│                                                   ││
│  │  └────────────────────┘                                                    ││
│  │                                                                          ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │ Colors                                                                   ││
│  │                                                                          ││
│  │  Primary Color                Secondary Color              Accent Color    ││
│  │  ┌──────────────────────────┐ ┌──────────────────────────┐ ┌──────────┐│
│  │  │ ●     #6366F1           │ │ ●     #8B5CF6           │ │ ● #EC4899 ││
│  │  │                          │ │                          │ │          ││
│  │  │ [Reset]                  │ │ [Reset]                  │ │ [Reset]   ││
│  │  └──────────────────────────┘ └──────────────────────────┘ └──────────┘│
│  │                                                                          ││
│  │  Suggested palettes based on your logo:                                  ││
│  │  ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐                                        ││
│  │  │ ░░░│ │ ░░░│ │ ░░░│ │ ░░░│ │ ░░░│  [Generate from logo]      ││
│  │  │ ░░░│ │ ░░░│ │ ░░░│ │ ░░░│ │ ░░░│                                        ││
│  │  └────┘ └────┘ └────┘ └────┘ └────┘                                        ││
│  │                                                                          ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │ Typography                                                               ││
│  │                                                                          ││
│  │  Font Family                    Base Font Size                           ││
│  │  ┌──────────────────────────┐ ┌──────────────────────────┐            ││
│  │  │ Inter              ▼     │ │ 16                    │ │            ││
│  │  │ ┌──────────────────────┐ │ │ ┌────┐ ┌────┐          │ │            ││
│  │  │ │ Inter               │ │ │ │ -  │ │ +  │          │ │            ││
│  │  │ │ Poppins             │ │ │ └────┘ └────┘          │ │            ││
│  │  │ │ Roboto              │ │ │                          │ │            ││
│  │  │ │ Open Sans           │ │ │                          │ │            ││
│  │  │ │ Lato                │ │ │                          │ │            ││
│  │  └──────────────────────┘ │ │                          │ │            ││
│  │  └──────────────────────────┘ │                          │ │            ││
│  │                              └──────────────────────────┘            ││
│  │                                                                          ││
│  │  Preview:                                                                  ││
│  │  ┌────────────────────────────────────────────────────────────────────┐ ││
│  │  │ Agency Name in Inter font                                           │ ││
│  │  │ This is how your headings will look to customers                     │ ││
│  │  └────────────────────────────────────────────────────────────────────┘ ││
│  │                                                                          ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Team Settings Screen

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Team & Permissions                                                    [+]  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │ Team Members (12)                                            Search...  ││
│  │                                                                          ││
│  │  ┌─────────────────────────────────────────────────────────────────────┤│
│  │  │ ┌─────┐ Rajesh Kumar                  Owner               [⋮]        │││
│  │  │ │ 👤  │ rajesh@abctravels.com                                        │││
│  │  │ └─────┘ Last active 2 hours ago                                      │││
│  │  ├─────────────────────────────────────────────────────────────────────┤││
│  │  │ ┌─────┐ Priya Sharma                   Admin               [⋮]        │││
│  │  │ │ 👤  │ priya@abctravels.com                                         │││
│  │  │ └─────┘ Last active 5 minutes ago                                     │││
│  │  ├─────────────────────────────────────────────────────────────────────┤││
│  │  │ ┌─────┐ Amit Verma                    Agent               [⋮]        │││
│  │  │ │ 👤  │ amit@abctravels.com                                           │││
│  │  │ └─────┘ Last active 1 day ago                                        │││
│  │  ├─────────────────────────────────────────────────────────────────────┤││
│  │  │ ┌─────┐ Neha Singh                     Agent               [⋮]        │││
│  │  │ │ 📧  │ neha.singh@email.com         [Pending invitation]          │││
│  │  │ └─────┘ Invited 2 days ago                                           │││
│  │  ├─────────────────────────────────────────────────────────────────────┤││
│  │  │ ┌─────┐ Suresh Iyer                    Agent               [⋮]        │││
│  │  │ │ 👤  │ suresh@abctravels.com                                          │││
│  │  │ └─────┘ Last active 3 days ago                                        │││
│  │  └─────────────────────────────────────────────────────────────────────┘││
│  │                                                                          ││
│  │                                            [Load more...]                   ││
│  │                                                                          ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │ Roles                                                                    ││
│  │                                                                          ││
│  │  ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐          ││
│  │  │ Owner            │ │ Admin            │ │ Agent            │          ││
│  │  │ Full access      │ │ Manage team      │ │ View trips        │          ││
│  │  │ to all settings  │ │ & settings       │ │ & send messages  │          ││
│  │  └──────────────────┘ └──────────────────┘ └──────────────────┘          ││
│  │                                                                          ││
│  │  ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐          ││
│  │  │ Senior Agent     │ │ Junior Agent     │ │ [Custom Role]    │          ││
│  │  │ Advanced access  │ │ Limited access   │ │                   │          ││
│  │  │                  │ │                  │ │                   │          ││
│  │  └──────────────────┘ └──────────────────┘ └──────────────────┘          ││
│  │                                                                          ││
│  │                                    [+ Create custom role]               ││
│  │                                                                          ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Interaction Patterns

### Auto-Save Pattern

```typescript
// hooks/useAutoSaveSettings.ts

interface UseAutoSaveSettingsOptions<T> {
  category: string;
  debounceMs?: number;
  onSuccess?: () => void;
  onError?: (error: Error) => void;
}

export function useAutoSaveSettings<T extends Record<string, unknown>>(
  initialData: T,
  options: UseAutoSaveSettingsOptions<T>
) {
  const [data, setData] = useState<T>(initialData);
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle');
  const [unsavedChanges, setUnsavedChanges] = useState(false);

  const debouncedSave = useMemo(
    () => debounce(async (values: T) => {
      setSaveStatus('saving');

      try {
        await updateSettings(values);
        setSaveStatus('saved');
        setUnsavedChanges(false);
        options.onSuccess?.();
      } catch (error) {
        setSaveStatus('error');
        options.onError?.(error as Error);
      }
    }, options.debounceMs || 1000),
    [options.category, options.debounceMs, options.onSuccess, options.onError]
  );

  const updateValue = useCallback((key: keyof T, value: T[keyof T]) => {
    const newData = { ...data, [key]: value };
    setData(newData);
    setUnsavedChanges(true);
    debouncedSave(newData);
  }, [data, debouncedSave]);

  const updateValues = useCallback((updates: Partial<T>) => {
    const newData = { ...data, ...updates };
    setData(newData);
    setUnsavedChanges(true);
    debouncedSave(newData);
  }, [data, debouncedSave]);

  const reset = useCallback(() => {
    setData(initialData);
    setUnsavedChanges(false);
    debouncedSave.cancel();
  }, [initialData, debouncedSave]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      debouncedSave.cancel();
    };
  }, [debouncedSave]);

  return {
    data,
    updateValue,
    updateValues,
    reset,
    saveStatus,
    unsavedChanges
  };
}
```

### Confirmation Dialog Pattern

```typescript
// components/settings/ConfirmDangerousAction.tsx

interface ConfirmDangerousActionProps {
  trigger: React.ReactNode;
  title: string;
  description: string;
  confirmText?: string;
  onConfirm: () => Promise<void> | void;
}

/**
 * Wrapper for dangerous actions with confirmation
 */
export const ConfirmDangerousAction: React.FC<ConfirmDangerousActionProps> = ({
  trigger,
  title,
  description,
  confirmText = 'Confirm',
  onConfirm
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [isConfirming, setIsConfirming] = useState(false);

  const handleConfirm = async () => {
    setIsConfirming(true);

    try {
      await onConfirm();
      setIsOpen(false);
    } catch (error) {
      console.error('Action failed:', error);
    } finally {
      setIsConfirming(false);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogTrigger asChild>
        {trigger}
      </DialogTrigger>

      <DialogContent>
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <AlertTriangleIcon className="text-red-500" />
            {title}
          </DialogTitle>
          <DialogDescription>{description}</DialogDescription>
        </DialogHeader>

        <div className="flex items-center gap-4 p-4 bg-red-50 rounded-lg border border-red-200">
          <AlertCircleIcon className="text-red-500 shrink-0" />
          <p className="text-sm text-red-700">
            This action cannot be undone. Please be certain.
          </p>
        </div>

        <DialogFooter>
          <Button
            variant="ghost"
            onClick={() => setIsOpen(false)}
            disabled={isConfirming}
          >
            Cancel
          </Button>
          <Button
            variant="destructive"
            onClick={handleConfirm}
            disabled={isConfirming}
          >
            {isConfirming ? <Spinner size="sm" /> : confirmText}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

// Usage
<ConfirmDangerousAction
  trigger={
    <Button variant="ghost" size="sm" icon={<TrashIcon />}>
      Remove
    </Button>
  }
  title="Remove team member"
  description="Are you sure you want to remove this team member? They will lose access to all agency data."
  confirmText="Remove member"
  onConfirm={async () => await removeMember(member.id)}
/>
```

---

## Mobile Experience

### Responsive Layout

```css
/* Settings responsive breakpoints */

.sidebar {
  position: fixed;
  inset-y: 0;
  left: 0;
  width: 256px;
  transform: translateX(0);
  transition: transform 0.3s ease;
  z-index: 40;
}

@media (max-width: 768px) {
  .sidebar {
    transform: translateX(-100%);
  }

  .sidebar.open {
    transform: translateX(0);
  }

  .main-content {
    padding-left: 0;
  }

  .settings-card {
    border-radius: 0;
    border-left: none;
    border-right: none;
  }
}
```

### Mobile Navigation

```
┌─────────────────────────────────┐
│  ← Settings        [Save]      │
├─────────────────────────────────┤
│                                 │
│  ┌─────────────────────────────┐│
│  │ Profile Settings            ││
│  └─────────────────────────────┘│
│                                 │
│  ┌─────────────────────────────┐│
│  │ Agency Name                  ││
│  │ ┌───────────────────────────┐││
│  │ │ ABC Travels Pvt Ltd       │││
│  │ └───────────────────────────┘││
│  │                              ││
│  │ Agency Email                 ││
│  │ ┌───────────────────────────┐││
│  │ │ contact@abctravels.com    │││
│  │ └───────────────────────────┘││
│  │                              ││
│  │ Agency Phone                 ││
│  │ ┌───────────────────────────┐││
│  │ │ +91 98765 43210          │││
│  │ └───────────────────────────┘││
│  │                              ││
│  └─────────────────────────────┘│
│                                 │
└─────────────────────────────────┘

```

---

## Accessibility

### Keyboard Navigation

```
Settings shortcuts:

Tab           - Navigate between fields
Shift + Tab   - Navigate backwards
Enter         - Open dropdowns/menus
Escape        - Close modals/dropdowns
Cmd/Ctrl + S  - Save changes
Cmd/Ctrl + Z  - Undo (where applicable)
```

### ARIA Labels

```tsx
{/* Accessible form field */}
<SettingsField
  label="Agency Name"
  description="This name appears on quotes, invoices, and customer emails."
  htmlFor="agencyName"
>
  <Input
    id="agencyName"
    value={value}
    onChange={onChange}
    aria-describedby="agency-name-description"
    aria-invalid={!!error}
    aria-required="true"
  />
  <p id="agency-name-description" className="text-sm text-gray-500">
    This name appears on quotes, invoices, and customer emails.
  </p>
  {error && (
    <p id="agency-name-error" role="alert" className="text-sm text-red-600">
      {error}
    </p>
  )}
</SettingsField>

{/* Accessible color picker */}
<div role="group" aria-label="Color selection">
  <label id="primary-color-label" class="sr-only">Primary color</label>
  <input
    type="color"
    id="primary-color"
    value={primaryColor}
    onChange={(e) => setPrimaryColor(e.target.value)}
    aria-labelledby="primary-color-label"
    aria-describedby="primary-color-value"
  />
  <span id="primary-color-value" aria-live="polite">
    {primaryColor}
  </span>
</div>
```

---

## Summary

The Agency Settings UX/UI design provides:

1. **Clear Navigation**: Organized sidebar with logical groupings
2. **Progressive Disclosure**: Simple options first, advanced behind "More"
3. **Immediate Feedback**: Auto-save with clear status indicators
4. **Visual Consistency**: Unified design language across all settings
5. **Error Prevention**: Clear labels, inline help, confirmation dialogs
6. **Mobile Responsive**: Full functionality on all devices
7. **Accessibility First**: WCAG 2.1 AA compliant with keyboard navigation

---

**Next:** Agency Settings Branding Deep Dive (AGENCY_SETTINGS_03) — logo management, color theming, and template customization
