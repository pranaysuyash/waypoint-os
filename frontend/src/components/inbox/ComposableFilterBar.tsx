'use client';

import { memo, useState, useCallback, useRef, useEffect, type KeyboardEvent } from 'react';
import { X, ChevronDown } from 'lucide-react';
import type { InboxFilters, TripPriority } from '@/types/governance';
import { focusNextOutside } from '@/lib/accessibility';

// ============================================================================
// Types
// ============================================================================

interface FilterGroup {
  key: keyof InboxFilters;
  label: string;
  options: { value: string; label: string }[];
  multi: boolean;
}

const FILTER_GROUPS: FilterGroup[] = [
  {
    key: 'priority',
    label: 'Priority',
    options: [
      { value: 'critical', label: 'Critical' },
      { value: 'high', label: 'High' },
      { value: 'medium', label: 'Medium' },
      { value: 'low', label: 'Low' },
    ],
    multi: true,
  },
  {
    key: 'slaStatus',
    label: 'SLA Status',
    options: [
      { value: 'breached', label: 'Breached' },
      { value: 'at_risk', label: 'At Risk' },
      { value: 'on_track', label: 'On Track' },
    ],
    multi: true,
  },
  {
    key: 'stage',
    label: 'Stage',
    options: [
      { value: 'intake', label: 'Intake' },
      { value: 'details', label: 'Details' },
      { value: 'options', label: 'Options' },
      { value: 'review', label: 'Review' },
      { value: 'booking', label: 'Booking' },
      { value: 'completed', label: 'Completed' },
    ],
    multi: true,
  },
  {
    key: 'assignedTo',
    label: 'Assigned to',
    options: [
      { value: 'unassigned', label: 'Unassigned' },
    ],
    multi: true,
  },
  {
    key: 'minValue',
    label: 'Min value',
    options: [],
    multi: false,
  },
  {
    key: 'maxValue',
    label: 'Max value',
    options: [],
    multi: false,
  },
];

// ============================================================================
// FilterDropdown (single multi-select dropdown)
// ============================================================================

interface FilterDropdownProps {
  group: FilterGroup;
  selected: readonly string[] | undefined;
  onToggle: (key: keyof InboxFilters, value: string) => void;
  onClose: () => void;
  menuId: string;
}

const FilterDropdown = memo(function FilterDropdown({
  group,
  selected,
  onToggle,
  onClose,
  menuId,
}: FilterDropdownProps) {
  if (!group.multi) return null;

  const isSelected = (val: string) => selected?.includes(val) ?? false;
  const listboxRef = useRef<HTMLDivElement>(null);
  const optionRefs = useRef<Array<HTMLButtonElement | null>>([]);
  const [activeIndex, setActiveIndex] = useState(0);

  useEffect(() => {
    setActiveIndex(0);
    const firstOption = optionRefs.current[0];
    firstOption?.focus();
  }, [group.options]);

  const close = useCallback((moveFocusOut = false) => {
    onClose();
    if (moveFocusOut) {
      const active = document.activeElement;
      if (active instanceof HTMLElement && listboxRef.current) {
        focusNextOutside(listboxRef.current, {
          from: active,
          fallbackFrom: listboxRef.current,
        });
      }
    }
  }, [onClose]);

  const moveActive = useCallback((nextIndex: number) => {
    if (group.options.length === 0) return;
    if (nextIndex < 0) {
      setActiveIndex(group.options.length - 1);
      return;
    }
    if (nextIndex >= group.options.length) {
      setActiveIndex(0);
      return;
    }
    setActiveIndex(nextIndex);
  }, [group.options.length]);

  useEffect(() => {
    const target = optionRefs.current[activeIndex];
    if (target) {
      target.focus();
    }
  }, [activeIndex]);

  const handleKeyDown = useCallback((event: KeyboardEvent<HTMLDivElement>) => {
    if (group.options.length === 0) {
      if (event.key === 'Escape' || event.key === 'Tab') {
        event.preventDefault();
        close(event.key === 'Tab');
      }
      return;
    }

    switch (event.key) {
      case 'ArrowDown':
        event.preventDefault();
        moveActive(activeIndex + 1);
        break;
      case 'ArrowUp':
        event.preventDefault();
        moveActive(activeIndex - 1);
        break;
      case 'Home':
        event.preventDefault();
        moveActive(0);
        break;
      case 'End':
        event.preventDefault();
        moveActive(group.options.length - 1);
        break;
      case 'Enter':
      case ' ':
        event.preventDefault();
        if (group.options[activeIndex]) {
          onToggle(group.key, group.options[activeIndex].value);
        }
        break;
      case 'Escape':
        event.preventDefault();
        close();
        break;
      case 'Tab':
        event.preventDefault();
        close(true);
        break;
      default:
        break;
    }
  }, [activeIndex, close, group.options, group.key, moveActive, onToggle]);

  return (
    <div
      ref={listboxRef}
      id={menuId}
      role='listbox'
      aria-label={`${group.label} options`}
      aria-activedescendant={group.options[activeIndex] ? `${menuId}-option-${activeIndex}` : undefined}
      onKeyDown={handleKeyDown}
      onMouseDown={(e) => e.preventDefault()}
      className='absolute top-full left-0 mt-1 w-48 bg-[#161b22] border border-[#30363d] rounded-lg shadow-xl z-20 py-1'
    >
      {group.options.map((option, optionIndex) => {
        const active = isSelected(option.value);
        return (
          <button
            key={option.value}
            ref={(element) => {
              optionRefs.current[optionIndex] = element;
            }}
            id={`${menuId}-option-${optionIndex}`}
            role='option'
            aria-selected={active}
            tabIndex={optionIndex === activeIndex ? 0 : -1}
            onClick={(event) => {
              event.preventDefault();
              event.stopPropagation();
              onToggle(group.key, option.value);
            }}
            onMouseEnter={() => setActiveIndex(optionIndex)}
            className='w-full flex items-center gap-2 px-3 py-2 text-left text-ui-sm text-[#e6edf3] hover:bg-[#1c2128] transition-colors'
          >
            <span
              className={`inline-flex items-center justify-center size-4 rounded border ${
                active
                  ? 'bg-[#58a6ff] border-[#58a6ff]'
                  : 'border-[#30363d]'
              }`}
            >
              {active && (
                <svg width='10' height='10' viewBox='0 0 24 24' fill='none' stroke='#0d1117' strokeWidth='3'>
                  <path d='M20 6L9 17l-5-5' />
                </svg>
              )}
            </span>
            <span>{option.label}</span>
          </button>
        );
      })}
    </div>
  );
});

// ============================================================================
// ActiveFilterChips
// ============================================================================

interface ActiveFilterChipsProps {
  filters: InboxFilters;
  onRemove: (key: keyof InboxFilters, value?: string) => void;
}

const CHIP_LABELS: Record<string, (val: string) => string> = {
  priority: (v) => `Priority: ${v.charAt(0).toUpperCase() + v.slice(1)}`,
  slaStatus: (v) => `SLA: ${v.replace('_', ' ').replace(/\\b\\w/g, (c) => c.toUpperCase())}`,
  stage: (v) => `Stage: ${v.charAt(0).toUpperCase() + v.slice(1)}`,
  assignedTo: () => 'Unassigned',
  minValue: (v) => `Min value: $${v}`,
  maxValue: (v) => `Max value: $${v}`,
};

const ActiveFilterChips = memo(function ActiveFilterChips({
  filters,
  onRemove,
}: ActiveFilterChipsProps) {
  const chips: { key: keyof InboxFilters; label: string; value?: string }[] = [];

  if (filters.priority?.length) {
    for (const v of filters.priority) {
      chips.push({ key: 'priority', label: CHIP_LABELS.priority(v), value: v });
    }
  }
  if (filters.slaStatus?.length) {
    for (const v of filters.slaStatus) {
      chips.push({ key: 'slaStatus', label: CHIP_LABELS.slaStatus(v), value: v });
    }
  }
  if (filters.stage?.length) {
    for (const v of filters.stage) {
      chips.push({ key: 'stage', label: CHIP_LABELS.stage(v), value: v });
    }
  }
  if (filters.assignedTo?.length) {
    for (const v of filters.assignedTo) {
      chips.push({ key: 'assignedTo', label: CHIP_LABELS.assignedTo(v), value: v });
    }
  }
  if (filters.minValue !== undefined) {
    chips.push({ key: 'minValue', label: CHIP_LABELS.minValue(String(filters.minValue)) });
  }
  if (filters.maxValue !== undefined) {
    chips.push({ key: 'maxValue', label: CHIP_LABELS.maxValue(String(filters.maxValue)) });
  }

  if (chips.length === 0) return null;

  return (
    <div className='flex flex-wrap items-center gap-1.5 mt-2'>
      <span className='text-ui-xs text-[#8b949e] font-medium mr-1'>Active:</span>
      {chips.map((chip, i) => (
        <span
          key={`${chip.key}-${chip.value ?? i}`}
          className='inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-[12px] font-medium transition-colors'
          style={{
            background: 'rgba(88,166,255,0.10)',
            color: '#58a6ff',
            border: '1px solid rgba(88,166,255,0.20)',
          }}
        >
          <span>{chip.label}</span>
          <button
            type='button'
            onClick={() => onRemove(chip.key, chip.value)}
            className='inline-flex items-center justify-center size-3.5 rounded-full hover:bg-[rgba(88,166,255,0.20)] transition-colors'
            aria-label={`Remove ${chip.label}`}
          >
            <X className='size-2.5' />
          </button>
        </span>
      ))}
    </div>
  );
});

// ============================================================================
// QuickPresets
// ============================================================================

interface QuickPresetsProps {
  onApply: (filters: Partial<InboxFilters>) => void;
}

const PRESETS: { label: string; filters: Partial<InboxFilters> }[] = [
  {
    label: 'My Urgent',
    filters: {
      priority: ['critical', 'high'] as readonly TripPriority[],
      slaStatus: ['breached', 'at_risk'] as readonly ('on_track' | 'at_risk' | 'breached')[],
    },
  },
  {
    label: 'Needs Owner',
    filters: {
      assignedTo: ['unassigned'] as readonly string[],
      slaStatus: ['breached'] as readonly ('on_track' | 'at_risk' | 'breached')[],
    },
  },
];

const QuickPresets = memo(function QuickPresets({ onApply }: QuickPresetsProps) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const listRef = useRef<HTMLDivElement>(null);
  const presetRefs = useRef<Array<HTMLButtonElement | null>>([]);
  const [activePreset, setActivePreset] = useState(0);

  useEffect(() => {
    if (open) {
      presetRefs.current[0]?.focus();
    }
  }, [open]);

  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  const movePreset = useCallback((nextIndex: number) => {
    if (PRESETS.length === 0) return;
    if (nextIndex < 0) {
      setActivePreset(PRESETS.length - 1);
      return;
    }
    if (nextIndex >= PRESETS.length) {
      setActivePreset(0);
      return;
    }
    setActivePreset(nextIndex);
  }, []);

  useEffect(() => {
    const target = presetRefs.current[activePreset];
    if (open && target) {
      target.focus();
    }
  }, [activePreset, open]);

  const close = useCallback((moveFocusOut = false) => {
    setOpen(false);
    if (moveFocusOut && ref.current) {
      const active = document.activeElement;
      focusNextOutside(ref.current, {
        from: active instanceof HTMLElement ? active : null,
        fallbackFrom: ref.current,
      });
    }
  }, []);

  const handleKeyDown = useCallback((event: KeyboardEvent<HTMLDivElement>) => {
    if (!open) return;
    switch (event.key) {
      case 'ArrowDown':
        event.preventDefault();
        movePreset(activePreset + 1);
        break;
      case 'ArrowUp':
        event.preventDefault();
        movePreset(activePreset - 1);
        break;
      case 'Home':
        event.preventDefault();
        movePreset(0);
        break;
      case 'End':
        event.preventDefault();
        movePreset(PRESETS.length - 1);
        break;
      case 'Tab':
        event.preventDefault();
        close(true);
        break;
      case 'Escape':
        event.preventDefault();
        close();
        break;
      case 'Enter':
      case ' ':
        event.preventDefault();
        if (PRESETS[activePreset]) {
          onApply(PRESETS[activePreset].filters);
          close();
        }
        break;
      default:
        break;
    }
  }, [activePreset, close, movePreset, open]);

  return (
    <div className='relative' ref={ref}>
      <button
        type='button'
        aria-expanded={open}
        aria-controls='inbox-quick-presets'
        onClick={() => setOpen(!open)}
        onKeyDown={(event) => {
          if (event.key === 'ArrowDown' || event.key === 'Enter' || event.key === ' ') {
            event.preventDefault();
            setOpen(true);
          }
          if (event.key === 'Escape') {
            event.preventDefault();
            setOpen(false);
          }
        }}
        className='flex items-center gap-1.5 px-3 py-2 bg-[#161b22] border border-[#30363d] rounded-lg text-ui-sm text-[#e6edf3] hover:border-[#484f58] transition-colors'
      >
        Quick presets
        <ChevronDown className='size-3.5 text-[#8b949e]' />
      </button>
      {open && (
        <div
          id='inbox-quick-presets'
          ref={listRef}
          role='menu'
          onKeyDown={handleKeyDown}
          className='absolute top-full right-0 mt-1 w-48 bg-[#0f1115] border border-[#30363d] rounded-lg shadow-xl z-20 py-1'
        >
          {PRESETS.map((preset, presetIndex) => (
            <button
              key={preset.label}
              ref={(element) => {
                presetRefs.current[presetIndex] = element;
              }}
              type='button'
              role='menuitem'
              tabIndex={presetIndex === activePreset ? 0 : -1}
              onMouseEnter={() => setActivePreset(presetIndex)}
              onClick={() => {
                onApply(preset.filters);
                close();
              }}
              className='w-full flex items-center gap-2 px-3 py-2 text-left text-ui-sm text-[#e6edf3] hover:bg-[#1c2128] transition-colors'
            >
              {preset.label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
});

// ============================================================================
// ComposableFilterBar (main)
// ============================================================================

export interface ComposableFilterBarProps {
  filters: InboxFilters;
  onFiltersChange: (filters: InboxFilters) => void;
  total?: number;
  className?: string;
}

export const ComposableFilterBar = memo(function ComposableFilterBar({
  filters,
  onFiltersChange,
  total,
  className,
}: ComposableFilterBarProps) {
  const [openDropdown, setOpenDropdown] = useState<string | null>(null);
  const barRef = useRef<HTMLDivElement>(null);

  const hasFilters = (
    (filters.priority?.length ?? 0) > 0 ||
    (filters.slaStatus?.length ?? 0) > 0 ||
    (filters.stage?.length ?? 0) > 0 ||
    (filters.assignedTo?.length ?? 0) > 0 ||
    filters.minValue !== undefined ||
    filters.maxValue !== undefined
  );

  const handleToggle = useCallback(
    (key: keyof InboxFilters, value: string) => {
      const current = filters[key];
      let next: readonly string[] | undefined;

      if (Array.isArray(current)) {
        next = current.includes(value)
          ? current.filter((v) => v !== value)
          : [...current, value];
      } else {
        next = [value];
      }

      onFiltersChange({ ...filters, [key]: next.length > 0 ? next : undefined });
      setOpenDropdown(null);
    },
    [filters, onFiltersChange],
  );

  const handleRemoveChip = useCallback(
    (key: keyof InboxFilters, value?: string) => {
      const current = filters[key];
      if (Array.isArray(current) && value) {
        const next = current.filter((v) => v !== value);
        onFiltersChange({ ...filters, [key]: next.length > 0 ? next : undefined });
      } else {
        onFiltersChange({ ...filters, [key]: undefined });
      }
    },
    [filters, onFiltersChange],
  );

  const handleClearAll = useCallback(() => {
    onFiltersChange({});
  }, [onFiltersChange]);

  const handlePreset = useCallback(
    (preset: Partial<InboxFilters>) => {
      onFiltersChange(preset as InboxFilters);
      setOpenDropdown(null);
    },
    [onFiltersChange],
  );

  const handleDropdownClose = useCallback(() => setOpenDropdown(null), []);

  useEffect(() => {
    if (!openDropdown) {
      return undefined;
    }

    const handleClick = (event: MouseEvent) => {
      if (barRef.current && !barRef.current.contains(event.target as Node)) {
        setOpenDropdown(null);
      }
    };

    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, [openDropdown]);

  const handleFilterButtonDown = useCallback((groupKey: keyof InboxFilters) => (event: KeyboardEvent<HTMLButtonElement>) => {
    if (event.key === 'ArrowDown' || event.key === ' ' || event.key === 'Enter') {
      event.preventDefault();
      setOpenDropdown(groupKey);
      return;
    }
    if (event.key === 'Escape') {
      event.preventDefault();
      setOpenDropdown(null);
    }
  }, []);

  return (
    <div className={className} ref={barRef}>
      <div className='flex flex-wrap items-center gap-2'>
        {/* Reset pill */}
        <button
          type='button'
          onClick={!hasFilters ? undefined : handleClearAll}
          className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-ui-xs font-semibold transition-colors border border-transparent ${
            !hasFilters
              ? 'bg-[#1c2128] text-[#e6edf3] border-[#30363d]'
              : 'text-[#8b949e] hover:text-[#e6edf3] hover:bg-[#1c2128]'
          }`}
        >
          {total !== undefined ? `All (${total})` : 'All'}
        </button>

        {/* Filter dropdowns - skip minValue/maxValue for now (input-based) */}
        {FILTER_GROUPS.flatMap((g) => {
          if (!g.multi) return [];
          const selected = filters[g.key] as readonly string[] | undefined;
          const count = selected?.length ?? 0;
          const menuId = `inbox-filter-${g.key}-listbox`;
          return [(
            <div key={g.key} className='relative'>
              <button
                type='button'
                aria-expanded={openDropdown === g.key}
                aria-controls={menuId}
                onClick={() => setOpenDropdown(openDropdown === g.key ? null : g.key)}
                onKeyDown={handleFilterButtonDown(g.key)}
                className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-ui-xs font-semibold transition-colors border ${
                  count > 0
                    ? 'bg-[rgba(88,166,255,0.10)] text-[#58a6ff] border-[rgba(88,166,255,0.28)]'
                    : 'text-[#8b949e] hover:text-[#e6edf3] hover:bg-[#1c2128] border-[#30363d]'
                }`}
              >
                <span>{g.label}</span>
                {count > 0 && (
                  <span className='tabular-nums px-1 py-0.5 rounded bg-[rgba(88,166,255,0.15)] text-[10px]'>
                    {count}
                  </span>
                )}
                <ChevronDown className='size-3' />
              </button>
              {openDropdown === g.key && (
                <FilterDropdown
                  group={g}
                  selected={selected}
                  onToggle={handleToggle}
                  onClose={handleDropdownClose}
                  menuId={menuId}
                />
              )}
            </div>
          )];
        })}

        {/* Quick presets */}
        <QuickPresets onApply={handlePreset} />

        {/* Clear all */}
        {hasFilters && (
          <button
            type='button'
            onClick={handleClearAll}
            className='text-ui-xs text-[#8b949e] hover:text-[#e6edf3] underline underline-offset-2'
          >
            Clear all
          </button>
        )}
      </div>

      {/* Active filter chips */}
      <ActiveFilterChips filters={filters} onRemove={handleRemoveChip} />
    </div>
  );
});
