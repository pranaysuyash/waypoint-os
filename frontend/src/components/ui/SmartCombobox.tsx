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

import { useState, useCallback, useMemo, useRef, useEffect } from 'react';
import { ChevronDown, X, Plus, AlertCircle } from 'lucide-react';
import {
  ComboboxOption,
  toTitleCase,
  findFuzzyMatches,
  findNearDuplicate,
  addCustomOption,
  getGroupedOptions,
} from '@/lib/combobox';

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
  const [inputValue, setInputValue] = useState(value);
  const [highlightedIndex, setHighlightedIndex] = useState(-1);
  const containerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Update input when value changes externally
  useEffect(() => {
    setInputValue(value);
  }, [value]);

  // Group options into predefined and custom
  const { predefined, custom } = useMemo(
    () => getGroupedOptions(options),
    [options]
  );

  // Filter options based on input
  const filteredOptions = useMemo(() => {
    if (!inputValue || inputValue.trim().length === 0) {
      return [...predefined, ...custom];
    }

    // First check for near duplicate (exact match after normalization)
    const nearDuplicate = findNearDuplicate(inputValue, options, duplicateThreshold);
    if (nearDuplicate) {
      return [nearDuplicate];
    }

    // Otherwise, fuzzy match
    const matches = findFuzzyMatches(inputValue, options, fuzzyThreshold);
    return matches.map(m => m.option);
  }, [inputValue, options, predefined, custom, duplicateThreshold, fuzzyThreshold]);

  // Check if current input would be a duplicate
  const duplicateOption = useMemo(() => {
    if (!inputValue || inputValue.trim().length === 0) return null;
    return findNearDuplicate(inputValue, options, duplicateThreshold);
  }, [inputValue, options, duplicateThreshold]);

  // Check if input is a new custom value
  const isCustomValue = useMemo(() => {
    if (!inputValue || inputValue.trim().length === 0) return false;
    const normalized = toTitleCase(inputValue);
    return !options.some(opt => opt.value.toLowerCase() === normalized.toLowerCase());
  }, [inputValue, options]);

  // Handle selection
  const handleSelect = useCallback((option: ComboboxOption) => {
    setInputValue(option.value);
    onChange(option.value);
    setIsOpen(false);
    setHighlightedIndex(-1);
  }, [onChange]);

  // Handle custom value entry
  const handleCustomEntry = useCallback(() => {
    if (!inputValue || inputValue.trim().length === 0) return;
    if (duplicateOption) {
      // Use the existing option instead
      handleSelect(duplicateOption);
      return;
    }

    const normalized = toTitleCase(inputValue);
    setInputValue(normalized);
    onChange(normalized);
    setIsOpen(false);
  }, [inputValue, duplicateOption, onChange, handleSelect]);

  // Handle keyboard navigation
  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (!isOpen) {
      if (e.key === 'ArrowDown' || e.key === 'ArrowUp' || e.key === 'Enter') {
        setIsOpen(true);
      }
      return;
    }

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setHighlightedIndex(prev =>
          prev < filteredOptions.length - 1 ? prev + 1 : prev
        );
        break;
      case 'ArrowUp':
        e.preventDefault();
        setHighlightedIndex(prev => (prev > 0 ? prev - 1 : 0));
        break;
      case 'Enter':
        e.preventDefault();
        if (highlightedIndex >= 0 && filteredOptions[highlightedIndex]) {
          handleSelect(filteredOptions[highlightedIndex]);
        } else if (allowCustom && isCustomValue) {
          handleCustomEntry();
        } else {
          setIsOpen(false);
        }
        break;
      case 'Escape':
        setIsOpen(false);
        setHighlightedIndex(-1);
        break;
      case 'Tab':
        if (isOpen) {
          setIsOpen(false);
        }
        break;
    }
  }, [isOpen, filteredOptions, highlightedIndex, handleSelect, allowCustom, isCustomValue, handleCustomEntry]);

  // Click outside to close
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [isOpen]);

  return (
    <div ref={containerRef} className='relative'>
      {label && (
        <label className='block text-[var(--ui-text-sm)] font-medium text-[var(--text-secondary)] mb-2'>
          {label}
        </label>
      )}

      <div className='relative'>
        <input
          ref={inputRef}
          type='text'
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onFocus={() => !disabled && setIsOpen(true)}
          onKeyDown={handleKeyDown}
          disabled={disabled}
          placeholder={placeholder}
          className='w-full px-3 py-2 bg-[var(--bg-surface)] border border-[var(--border-default)] rounded-lg text-[var(--ui-text-sm)] text-[var(--text-primary)] placeholder:text-[var(--text-secondary)] focus:outline-none focus:border-[#58a6ff] disabled:opacity-50 disabled:cursor-not-allowed pr-20'
        />

        {/* Right side controls */}
        <div className='absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1'>
          {value && (
            <button
              type='button'
              onClick={() => {
                setInputValue('');
                onChange('');
              }}
              className='p-1 text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors'
              title='Clear'
            >
              <X className='size-4' />
            </button>
          )}
          <button
            type='button'
            onClick={() => !disabled && setIsOpen(!isOpen)}
            className='p-1 text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors'
          >
            <ChevronDown className={`size-4 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
          </button>
        </div>
      </div>

      {/* Duplicate warning */}
      {duplicateOption && inputValue !== duplicateOption.value && (
        <div className='mt-1 flex items-center gap-2 text-[var(--ui-text-xs)] text-[var(--accent-amber)]'>
          <AlertCircle className='size-3 flex-shrink-0' />
          <span>
            Similar to existing option "{duplicateOption.value}". Use that instead?
          </span>
          <button
            type='button'
            onClick={() => handleSelect(duplicateOption)}
            className='text-[var(--accent-blue)] hover:underline'
          >
            Yes, use existing
          </button>
        </div>
      )}

      {/* Dropdown */}
      {isOpen && !disabled && (
        <div className='absolute z-10 w-full mt-1 bg-[#161b22] border border-[var(--border-default)] rounded-lg shadow-xl max-h-60 overflow-y-auto'>
          {filteredOptions.length === 0 ? (
            <div className='p-3 text-[var(--ui-text-sm)] text-[var(--text-secondary)] text-center'>
              No matching options
              {allowCustom && inputValue && (
                <div className='mt-2'>
                  <button
                    type='button'
                    onClick={handleCustomEntry}
                    className='flex items-center justify-center gap-2 w-full px-3 py-2 bg-[var(--accent-blue)] text-[var(--text-on-accent)] rounded-lg text-[var(--ui-text-sm)] font-medium hover:bg-[var(--accent-blue-hover)] transition-colors'
                  >
                    <Plus className='size-4' />
                    Add "{toTitleCase(inputValue)}"
                  </button>
                </div>
              )}
            </div>
          ) : (
            <>
              {(() => {
                const predefined: typeof filteredOptions = [];
                const custom: typeof filteredOptions = [];
                for (const opt of filteredOptions) {
                  if (opt.isCustom) custom.push(opt);
                  else predefined.push(opt);
                }
                return (
                  <>
                    {predefined.length > 0 && (
                      <div className='p-1'>
                        {predefined.map((option, idx) => (
                          <button
                            key={option.value}
                            type='button'
                            onClick={() => handleSelect(option)}
                            className={`w-full text-left px-3 py-2 text-[var(--ui-text-sm)] rounded-md transition-colors ${
                              highlightedIndex === idx
                                ? 'bg-[var(--accent-blue)] text-[var(--text-on-accent)]'
                                : option.value === value
                                ? 'bg-[var(--accent-blue)]/20 text-[var(--accent-blue)]'
                                : 'text-[var(--text-primary)] hover:bg-[#161b22]'
                            }`}
                          >
                            {option.label}
                          </button>
                        ))}
                      </div>
                    )}
                    {custom.length > 0 && (
                      <div className='border-t border-[var(--border-default)]'>
                        <div className='px-3 py-1 text-[var(--ui-text-xs)] text-[var(--text-secondary)] uppercase tracking-wide'>
                          Custom
                        </div>
                        <div className='p-1'>
                          {custom.map((option) => (
                            <button
                              key={option.value}
                              type='button'
                              onClick={() => handleSelect(option)}
                              className={`w-full text-left px-3 py-2 text-[var(--ui-text-sm)] rounded-md transition-colors ${
                                option.value === value
                                  ? 'bg-[var(--accent-blue)]/20 text-[var(--accent-blue)]'
                                  : 'text-[var(--text-primary)] hover:bg-[#161b22]'
                              }`}
                            >
                              {option.label}
                            </button>
                          ))}
                        </div>
                      </div>
                    )}
                  </>
                );
              })()}

              {/* Add new custom option */}
              {allowCustom && isCustomValue && inputValue && !duplicateOption && (
                <div className='border-t border-[var(--border-default)] p-2'>
                  <button
                    type='button'
                    onClick={handleCustomEntry}
                    className='flex items-center justify-center gap-2 w-full px-3 py-2 bg-[var(--bg-count-badge)] text-[var(--accent-blue)] border border-[var(--border-default)] border-dashed rounded-lg text-[var(--ui-text-sm)] hover:bg-[var(--accent-blue)/0.1] transition-colors'
                  >
                    <Plus className='size-4' />
                    Add new option: "{toTitleCase(inputValue)}"
                  </button>
                </div>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
}
