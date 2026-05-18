/**
 * SmartCombobox Component
 *
 * A dropdown that allows selecting from predefined options OR adding custom values.
 * Features:
 * - Predefined options with search/filter
 * - Custom value entry with title case normalization
 * - Fuzzy matching to suggest existing similar options
 * - Duplicate prevention via normalization
 * - Shows "suggested" match when input is similar to existing option
 *
 * @example
 * <SmartCombobox
 *   value={tripType}
 *   onChange={setTripType}
 *   options={TRIP_TYPE_OPTIONS}
 *   placeholder="Select or type trip type…"
 *   label="Trip Type"
 * />
 */

'use client';

import { useId, useState, useCallback, useMemo, useRef, useEffect } from 'react';
import { ChevronDown, X, Plus, AlertCircle } from 'lucide-react';
import {
  ComboboxOption,
  toTitleCase,
  findFuzzyMatches,
  findNearDuplicate,
  getGroupedOptions,
} from '@/lib/combobox';
import { getFocusableElements } from '@/lib/accessibility';

interface SmartComboboxProps {
  value: string;
  onChange: (value: string) => void;
  options: ComboboxOption[];
  placeholder?: string;
  label?: string;
  allowCustom?: boolean;
  fuzzyThreshold?: number;
  duplicateThreshold?: number;
  disabled?: boolean;
}

export function SmartCombobox({
  value,
  onChange,
  options,
  placeholder = 'Select or type…',
  label,
  allowCustom = true,
  fuzzyThreshold = 0.6,
  duplicateThreshold = 0.85,
  disabled = false,
}: SmartComboboxProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [inputValue, setInputValue] = useState('');
  const [highlightedIndex, setHighlightedIndex] = useState(-1);
  const containerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const ids = {
    input: useId(),
    listbox: `${useId()}-listbox`,
    status: `${useId()}-status`,
  } as const;

  const displayValue = isOpen ? inputValue : value;
  const normalizedDisplayValue = displayValue.trim().toLowerCase();
  const { predefined, custom } = useMemo(() => getGroupedOptions(options), [options]);

  const filteredOptions = useMemo(() => {
    if (!displayValue || displayValue.trim().length === 0) {
      return [...predefined, ...custom];
    }

    const nearDuplicate = findNearDuplicate(displayValue, options, duplicateThreshold);
    if (nearDuplicate) {
      return [nearDuplicate];
    }

    const matches = findFuzzyMatches(displayValue, options, fuzzyThreshold);
    return matches.map((m) => m.option);
  }, [displayValue, options, predefined, custom, duplicateThreshold, fuzzyThreshold]);

  const duplicateOption = useMemo(() => {
    if (!displayValue || normalizedDisplayValue.length === 0) return null;
    return findNearDuplicate(displayValue, options, duplicateThreshold);
  }, [displayValue, options, duplicateThreshold, normalizedDisplayValue]);

  const isCustomValue = useMemo(() => {
    if (!displayValue || displayValue.trim().length === 0) return false;
    const normalized = toTitleCase(displayValue);
    return !options.some((opt) => opt.value.toLowerCase() === normalized.toLowerCase());
  }, [displayValue, options]);

  const splitFiltered = useMemo(() => {
    const groupedPredefined: ComboboxOption[] = [];
    const groupedCustom: ComboboxOption[] = [];
    for (const option of filteredOptions) {
      if (option.isCustom) {
        groupedCustom.push(option);
      } else {
        groupedPredefined.push(option);
      }
    }
    return { predefined: groupedPredefined, custom: groupedCustom };
  }, [filteredOptions]);

  const visibleOptions = useMemo(() => {
    if (splitFiltered.predefined.length === 0 && splitFiltered.custom.length === 0) {
      return [];
    }
    return [
      ...splitFiltered.predefined.map((option) => ({ ...option, section: 'predefined' as const })),
      ...splitFiltered.custom.map((option) => ({ ...option, section: 'custom' as const })),
    ];
  }, [splitFiltered]);

  const normalizedHighlightedIndex = useMemo(() => {
    if (!isOpen || visibleOptions.length === 0) {
      return -1;
    }

    if (highlightedIndex < 0) {
      return 0;
    }

    if (highlightedIndex >= visibleOptions.length) {
      return visibleOptions.length - 1;
    }

    return highlightedIndex;
  }, [isOpen, visibleOptions, highlightedIndex]);

  const optionAtIndex = useMemo(
    () => (index: number) => visibleOptions[index] ?? null,
    [visibleOptions]
  );

  const optionId = useCallback((index: number) => `${ids.listbox}-option-${index}`, [ids.listbox]);

  const openDropdown = useCallback(() => {
    if (disabled) return;
    setInputValue(value);
    setHighlightedIndex(filteredOptions.length > 0 ? 0 : -1);
    setIsOpen(true);

    if (inputRef.current) {
      inputRef.current.focus();
    }
  }, [disabled, value, filteredOptions.length]);

  const closeDropdown = useCallback(() => {
    setIsOpen(false);
    setHighlightedIndex(-1);
  }, []);

  const focusNextOutsideCombobox = useCallback(() => {
    const focusables = getFocusableElements(document);
    const currentIndex = inputRef.current ? focusables.indexOf(inputRef.current) : -1;

    if (currentIndex === -1) {
      return;
    }

    for (let i = currentIndex + 1; i < focusables.length; i += 1) {
      const candidate = focusables[i];
      if (!containerRef.current?.contains(candidate)) {
        candidate.focus();
        return;
      }
    }

    inputRef.current?.blur();
  }, [inputRef, containerRef]);

  const selectOption = useCallback((option: ComboboxOption) => {
    setInputValue(option.value);
    onChange(option.value);
    closeDropdown();
  }, [onChange, closeDropdown]);

  const handleCustomEntry = useCallback(() => {
    if (!displayValue || displayValue.trim().length === 0) return;
    if (duplicateOption) {
      selectOption(duplicateOption);
      return;
    }

    const normalized = toTitleCase(displayValue);
    setInputValue(normalized);
    onChange(normalized);
    closeDropdown();
  }, [displayValue, duplicateOption, onChange, selectOption, closeDropdown]);

  const moveHighlight = useCallback((nextIndex: number) => {
    if (visibleOptions.length === 0) {
      setHighlightedIndex(-1);
      return;
    }

    if (nextIndex < 0) {
      setHighlightedIndex(visibleOptions.length - 1);
      return;
    }

    if (nextIndex >= visibleOptions.length) {
      setHighlightedIndex(0);
      return;
    }

    setHighlightedIndex(nextIndex);
  }, [visibleOptions]);

  const handleKeyDown = useCallback((event: React.KeyboardEvent<HTMLInputElement>) => {
    if (!isOpen && event.key === 'ArrowDown') {
      event.preventDefault();
      openDropdown();
      return;
    }

    if (!isOpen) {
      if (event.key === 'ArrowUp' || event.key === 'Enter') {
        event.preventDefault();
        openDropdown();
      }
      return;
    }

    switch (event.key) {
      case 'ArrowDown':
        event.preventDefault();
        moveHighlight(highlightedIndex + 1);
        break;
      case 'ArrowUp':
        event.preventDefault();
        moveHighlight(highlightedIndex - 1);
        break;
      case 'Home':
        event.preventDefault();
        moveHighlight(0);
        break;
      case 'End':
        event.preventDefault();
        moveHighlight(visibleOptions.length - 1);
        break;
      case 'Enter':
        event.preventDefault();
        if (normalizedHighlightedIndex >= 0) {
          const option = optionAtIndex(normalizedHighlightedIndex);
          if (option) {
            selectOption(option);
            break;
          }
        }

        if (allowCustom && isCustomValue) {
          handleCustomEntry();
          break;
        }

        closeDropdown();
        break;
      case 'Escape':
        event.preventDefault();
        closeDropdown();
        inputRef.current?.focus();
        break;
      case 'Tab':
        event.preventDefault();
        closeDropdown();
        focusNextOutsideCombobox();
        break;
      default:
        break;
    }
  }, [
    isOpen,
    openDropdown,
    closeDropdown,
    highlightedIndex,
    moveHighlight,
    optionAtIndex,
    selectOption,
    allowCustom,
    isCustomValue,
    handleCustomEntry,
    focusNextOutsideCombobox,
    visibleOptions,
    normalizedHighlightedIndex,
  ]);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        closeDropdown();
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }

    return undefined;
  }, [isOpen, closeDropdown]);

  return (
    <div ref={containerRef} className='relative'>
      {label && (
        <label htmlFor={ids.input} className='block text-[var(--ui-text-sm)] font-medium text-[var(--text-secondary)] mb-2'>
          {label}
        </label>
      )}

      <div className='relative'>
        <input
          id={ids.input}
          ref={inputRef}
          type='text'
          value={displayValue}
          onChange={(e) => setInputValue(e.target.value)}
          onFocus={openDropdown}
          onKeyDown={handleKeyDown}
          disabled={disabled}
          placeholder={placeholder}
          role='combobox'
          aria-expanded={isOpen}
          aria-haspopup='listbox'
          aria-controls={ids.listbox}
          aria-autocomplete='list'
          aria-activedescendant={normalizedHighlightedIndex >= 0 ? optionId(normalizedHighlightedIndex) : undefined}
          className='w-full px-3 py-2 bg-[var(--bg-surface)] border border-[var(--border-default)] rounded-lg text-[var(--ui-text-sm)] text-[var(--text-primary)] placeholder:text-[var(--text-secondary)] focus:outline-none focus:border-[#58a6ff] disabled:opacity-50 disabled:cursor-not-allowed pr-20'
        />

        <div className='absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1'>
          {value && (
            <button
              type='button'
              onClick={() => {
                setInputValue('');
                onChange('');
                closeDropdown();
              }}
              className='p-1 text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors'
              title='Clear'
              aria-label='Clear selection'
            >
              <X className='size-4' />
            </button>
          )}
          <button
            type='button'
            onClick={() => {
              if (isOpen) {
                closeDropdown();
              } else {
                openDropdown();
              }
            }}
            className='p-1 text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors'
            aria-label='Toggle options'
          >
            <ChevronDown className={`size-4 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
          </button>
        </div>
      </div>

      <div id={ids.status} className='sr-only' role='status' aria-live='polite'>
        {isOpen
          ? filteredOptions.length === 0
            ? 'No matching options'
            : `${filteredOptions.length} option${filteredOptions.length === 1 ? '' : 's'} available`
          : null}
      </div>

      {duplicateOption && displayValue !== duplicateOption.value && (
        <div className='mt-1 flex items-center gap-2 text-[var(--ui-text-xs)] text-[var(--accent-amber)]'>
          <AlertCircle className='size-3 flex-shrink-0' />
          <span>
            Similar to existing option “{duplicateOption.value}”. Use that instead?
          </span>
          <button
            type='button'
            onClick={() => selectOption(duplicateOption)}
            className='text-[var(--accent-blue)] hover:underline'
          >
            Yes, use existing
          </button>
        </div>
      )}

      {isOpen && !disabled && (
        <ul
          role='listbox'
          id={ids.listbox}
          className='absolute z-10 w-full mt-1 bg-[#161b22] border border-[var(--border-default)] rounded-lg shadow-xl max-h-60 overflow-y-auto'
          aria-label={label ?? 'Options'}
          aria-describedby={ids.status}
        >
          {filteredOptions.length === 0 ? (
            <li className='p-3 text-[var(--ui-text-sm)] text-[var(--text-secondary)] text-center'>
              No matching options
              {allowCustom && displayValue && (
                <div className='mt-2'>
                  <button
                    type='button'
                    onClick={handleCustomEntry}
                    className='flex items-center justify-center gap-2 w-full px-3 py-2 bg-[var(--accent-blue)] text-[var(--text-on-accent)] rounded-lg text-[var(--ui-text-sm)] font-medium hover:bg-[var(--accent-blue-hover)] transition-colors'
                  >
                    <Plus className='size-4' />
                    Add “{toTitleCase(displayValue)}”
                  </button>
                </div>
              )}
            </li>
          ) : (
            <>
              {splitFiltered.predefined.length > 0 && (
                <li role='presentation'>
                  <div className='p-1'>
                    {splitFiltered.predefined.map((option, idx) => {
                      const optionIndex = idx;
                      const optionIsActive = normalizedHighlightedIndex === optionIndex;
                      return (
                        <button
                          key={`predefined-${option.value}`}
                          id={optionId(optionIndex)}
                          role='option'
                          type='button'
                          aria-selected={value === option.value}
                          onMouseDown={(event) => {
                            event.preventDefault();
                            selectOption(option);
                          }}
                          className={`w-full text-left px-3 py-2 text-[var(--ui-text-sm)] rounded-md transition-colors ${
                            optionIsActive
                              ? 'bg-[var(--accent-blue)] text-[var(--text-on-accent)]'
                              : option.value === value
                              ? 'bg-[var(--accent-blue)]/20 text-[var(--accent-blue)]'
                              : 'text-[var(--text-primary)] hover:bg-[#161b22]'
                          }`}
                        >
                          {option.label}
                        </button>
                      );
                    })}
                  </div>
                </li>
              )}

              {splitFiltered.custom.length > 0 && (
                <li role='presentation'>
                  <div className='border-t border-[var(--border-default)]'>
                    <div className='px-3 py-1 text-[var(--ui-text-xs)] text-[var(--text-secondary)] uppercase tracking-wide'>
                      Custom
                    </div>
                    <div className='p-1'>
                      {splitFiltered.custom.map((option, idx) => {
                        const optionIndex = splitFiltered.predefined.length + idx;
                        const optionIsActive = normalizedHighlightedIndex === optionIndex;
                        return (
                          <button
                            key={`custom-${option.value}`}
                            id={optionId(optionIndex)}
                            role='option'
                            type='button'
                            aria-selected={value === option.value}
                            onMouseDown={(event) => {
                              event.preventDefault();
                              selectOption(option);
                            }}
                            className={`w-full text-left px-3 py-2 text-[var(--ui-text-sm)] rounded-md transition-colors ${
                              optionIsActive
                                ? 'bg-[var(--accent-blue)] text-[var(--text-on-accent)]'
                                : option.value === value
                                ? 'bg-[var(--accent-blue)]/20 text-[var(--accent-blue)]'
                                : 'text-[var(--text-primary)] hover:bg-[#161b22]'
                            }`}
                          >
                            {option.label}
                          </button>
                        );
                      })}
                    </div>
                  </div>
                </li>
              )}

              {allowCustom && isCustomValue && displayValue && !duplicateOption && (
                <li role='presentation'>
                  <div className='border-t border-[var(--border-default)] p-2'>
                    <button
                      type='button'
                      onMouseDown={(event) => {
                        event.preventDefault();
                        handleCustomEntry();
                      }}
                      className='flex items-center justify-center gap-2 w-full px-3 py-2 bg-[var(--bg-count-badge)] text-[var(--accent-blue)] border border-[var(--border-default)] border-dashed rounded-lg text-[var(--ui-text-sm)] hover:bg-[var(--accent-blue)/0.1] transition-colors'
                    >
                      <Plus className='size-4' />
                      Add new option: “{toTitleCase(displayValue)}”
                    </button>
                  </div>
                </li>
              )}
            </>
          )}
        </ul>
      )}
    </div>
  );
}
