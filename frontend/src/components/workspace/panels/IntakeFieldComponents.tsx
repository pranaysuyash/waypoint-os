'use client';

import { CheckCircle, Edit2, MapPin, Users, Wallet, X } from 'lucide-react';
import { SmartCombobox } from '@/components/ui/SmartCombobox';
import { Button } from '@/components/ui/button';
import { TRIP_TYPE_OPTIONS, DESTINATION_OPTIONS } from '@/lib/combobox';
import { formatBudgetDisplay } from '@/lib/lead-display';
import type { SupportedCurrency } from '@/lib/currency';
import type { PlanningDetailId, PlanningDetailRow } from './IntakePanel';

interface EditableFieldProps {
  label: string;
  value: string;
  displayValue?: string;
  field: string;
  isEditing: boolean;
  icon?: React.ComponentType<{ className?: string }>;
  type?: 'text' | 'select' | 'number' | 'combobox';
  options?: Array<{ value: string; label: string; symbol?: string; flag?: string }>;
  onStartEdit: (field: string, currentValue: string) => void;
  onSaveEdit: (field: string) => void;
  onCancelEdit: () => void;
  onEditValueChange: (field: string, value: string) => void;
}

export function EditableField({
  label,
  value,
  displayValue,
  field,
  isEditing,
  icon: Icon,
  type = 'text',
  options,
  onStartEdit,
  onSaveEdit,
  onCancelEdit,
  onEditValueChange,
}: EditableFieldProps) {
  if (field === 'type' && isEditing) {
    return (
      <div className='bg-[var(--bg-surface)] border border-[var(--accent-blue)] rounded-lg p-2 -m-1'>
        <div className='flex items-center justify-between gap-1'>
          <span className='text-[var(--ui-text-xs)] text-[var(--accent-blue)] uppercase tracking-wide'>{label}</span>
          <div className='flex items-center gap-1'>
            <button
              onClick={() => onSaveEdit(field)}
              className='p-1 bg-[var(--accent-green)] text-[var(--text-on-accent)] rounded hover:opacity-80'
              title='Save'
              aria-label='Save trip type'
            >
              <CheckCircle className='size-3' />
            </button>
            <button
              onClick={onCancelEdit}
              className='p-1 bg-[var(--accent-red)] text-[var(--text-on-accent)] rounded hover:opacity-80'
              title='Cancel'
              aria-label='Cancel editing'
            >
              <X className='size-3' />
            </button>
          </div>
        </div>
        <SmartCombobox
          value={value}
          onChange={(val) => onEditValueChange(field, val)}
          options={TRIP_TYPE_OPTIONS}
          placeholder='Select or type trip type…'
          allowCustom={true}
        />
      </div>
    );
  }

  if (field === 'destination' && isEditing) {
    return (
      <div className='bg-[var(--bg-surface)] border border-[var(--accent-blue)] rounded-lg p-2 -m-1'>
        <div className='flex items-center justify-between gap-1'>
          <span className='text-[var(--ui-text-xs)] text-[var(--accent-blue)] uppercase tracking-wide'>{label}</span>
          <div className='flex items-center gap-1'>
            <button
              onClick={() => onSaveEdit(field)}
              className='p-1 bg-[var(--accent-green)] text-[var(--text-on-accent)] rounded hover:opacity-80'
              title='Save'
              aria-label='Save destination'
            >
              <CheckCircle className='size-3' />
            </button>
            <button
              onClick={onCancelEdit}
              className='p-1 bg-[var(--accent-red)] text-[var(--text-on-accent)] rounded hover:opacity-80'
              title='Cancel'
              aria-label='Cancel editing'
            >
              <X className='size-3' />
            </button>
          </div>
        </div>
        <SmartCombobox
          value={value}
          onChange={(val) => onEditValueChange(field, val)}
          options={DESTINATION_OPTIONS}
          placeholder='Select or type destination…'
          allowCustom={true}
        />
      </div>
    );
  }

  if (isEditing) {
    return (
      <div className='bg-[var(--bg-surface)] border border-[var(--accent-blue)] rounded-lg p-2 -m-1'>
        <div className='flex items-center gap-1 mb-1'>
          <span className='text-[var(--ui-text-xs)] text-[var(--accent-blue)] uppercase tracking-wide'>{label}</span>
        </div>
        <div className='flex items-center gap-1'>
          {type === 'select' && options ? (
            <select
              value={value}
              onChange={(e) => onEditValueChange(field, e.target.value)}
              className='flex-1 px-2 py-1 bg-[var(--bg-elevated)] border border-[var(--border-default)] rounded text-[var(--ui-text-xs)] text-[var(--text-primary)] focus:outline-none focus:border-[var(--accent-blue)]'
            >
              {options.map(opt => (
                <option key={opt.value} value={opt.value}>
                  {opt.flag} {opt.label}
                </option>
              ))}
            </select>
          ) : (
            <input
              type={type === 'number' ? 'number' : 'text'}
              value={value}
              onChange={(e) => onEditValueChange(field, e.target.value)}
              className='flex-1 px-2 py-1 bg-[var(--bg-elevated)] border border-[var(--border-default)] rounded text-[var(--ui-text-xs)] text-[var(--text-primary)] focus:outline-none focus:border-[var(--accent-blue)]'
              autoFocus
            />
          )}
          <button
            onClick={() => onSaveEdit(field)}
            className='p-1 bg-[var(--accent-green)] text-[var(--text-on-accent)] rounded hover:opacity-80'
            title='Save'
            aria-label={`Save ${label}`}
          >
            <CheckCircle className='size-3' />
          </button>
          <button
            onClick={onCancelEdit}
            className='p-1 bg-[var(--accent-red)] text-[var(--text-on-accent)] rounded hover:opacity-80'
            title='Cancel'
            aria-label='Cancel editing'
          >
            <X className='size-3' />
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className='group relative'>
      <span className='text-[var(--ui-text-xs)] text-[var(--text-secondary)] uppercase tracking-wide'>{label}</span>
      <p className='text-[var(--ui-text-sm)] text-[var(--text-primary)] font-medium mt-0.5 flex items-center gap-1'>
        {Icon && <Icon className='size-3 text-[var(--text-secondary)]' />}
        {displayValue || value}
        <button
          onClick={() => onStartEdit(field, value)}
          className='ml-1 opacity-[0.3] group-hover:opacity-100 transition-opacity'
          title={`Edit ${label}`}
          aria-label={`Edit ${label}`}
        >
          <Edit2 className='size-3 text-[var(--accent-blue)]' />
        </button>
      </p>
    </div>
  );
}

interface BudgetFieldProps {
  budget: string | undefined;
  budgetAmount: string;
  budgetCurrency: SupportedCurrency;
  isEditing: boolean;
  currencyOptions: Array<{ value: string; label: string; symbol?: string; flag?: string }>;
  onStartEdit: () => void;
  onSaveEdit: () => void;
  onCancelEdit: () => void;
  onAmountChange: (value: string) => void;
  onCurrencyChange: (value: SupportedCurrency) => void;
}

export function BudgetField({
  budget,
  budgetAmount,
  budgetCurrency,
  isEditing,
  currencyOptions,
  onStartEdit,
  onSaveEdit,
  onCancelEdit,
  onAmountChange,
  onCurrencyChange,
}: BudgetFieldProps) {
  const displayBudget = formatBudgetDisplay(budget);

  if (isEditing) {
    return (
      <div className='bg-[var(--bg-surface)] border border-[var(--accent-blue)] rounded-lg p-2 -m-1'>
        <div className='flex items-center gap-1 mb-1'>
          <span className='text-[var(--ui-text-xs)] text-[var(--accent-blue)] uppercase tracking-wide'>Budget</span>
        </div>
        <div className='flex items-center gap-1'>
          <input
            type='number'
            value={budgetAmount}
            onChange={(e) => onAmountChange(e.target.value)}
            placeholder='Amount'
            className='flex-1 px-2 py-1 bg-[var(--bg-elevated)] border border-[var(--border-default)] rounded text-[var(--ui-text-xs)] text-[var(--text-primary)] focus:outline-none focus:border-[var(--accent-blue)]'
            autoFocus
          />
          <select
            value={budgetCurrency}
            onChange={(e) => onCurrencyChange(e.target.value as SupportedCurrency)}
            className='px-2 py-1 bg-[var(--bg-elevated)] border border-[var(--border-default)] rounded text-[var(--ui-text-xs)] text-[var(--text-primary)] focus:outline-none focus:border-[var(--accent-blue)]'
          >
            {currencyOptions.map(opt => (
              <option key={opt.value} value={opt.value}>
                {opt.flag} {opt.value}
              </option>
            ))}
          </select>
          <button
            onClick={onSaveEdit}
            className='p-1 bg-[var(--accent-green)] text-[var(--text-on-accent)] rounded hover:opacity-80'
            title='Save'
            aria-label='Save budget'
          >
            <CheckCircle className='size-3' />
          </button>
          <button
            onClick={onCancelEdit}
            className='p-1 bg-[var(--accent-red)] text-[var(--text-on-accent)] rounded hover:opacity-80'
            title='Cancel'
            aria-label='Cancel editing'
          >
            <X className='size-3' />
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className='group relative'>
      <span className='text-[var(--ui-text-xs)] text-[var(--text-secondary)] uppercase tracking-wide'>Budget</span>
      <p className='text-[var(--ui-text-sm)] text-[var(--text-primary)] font-medium mt-0.5 flex items-center gap-1'>
        <Wallet className='size-3 text-[var(--accent-green)]' />
        {displayBudget}
        <button
          onClick={onStartEdit}
          className='ml-1 opacity-[0.3] group-hover:opacity-100 transition-opacity'
          title='Edit Budget'
          aria-label='Edit budget'
        >
          <Edit2 className='size-3 text-[var(--accent-blue)]' />
        </button>
      </p>
    </div>
  );
}

interface PlanningDetailSectionProps {
  title: string;
  tone: 'required' | 'recommended';
  rows: PlanningDetailRow[];
  onOpenEditor: (id: PlanningDetailId) => void;
  onAskTraveler: () => void;
  renderEditor: (id: PlanningDetailId | null) => React.ReactNode;
}

export function PlanningDetailSection({
  title,
  tone,
  rows,
  onOpenEditor,
  onAskTraveler,
  renderEditor,
}: PlanningDetailSectionProps) {
  if (rows.length === 0) return null;

  const toneClasses = tone === 'required'
    ? 'border-[rgba(248,81,73,0.18)] bg-[rgba(248,81,73,0.04)]'
    : 'border-[rgba(88,166,255,0.16)] bg-[rgba(88,166,255,0.04)]';

  return (
    <div className={`rounded-xl border p-3 ${toneClasses}`}>
      <div className='mb-3 flex items-center justify-between gap-3'>
        <h4 className='text-[12px] font-semibold text-[var(--text-secondary)]'>
          {title}
        </h4>
        <span className='text-[var(--ui-text-xs)] text-[var(--text-secondary)]'>
          {rows.length} {rows.length === 1 ? 'field' : 'fields'}
        </span>
      </div>
      <div className='space-y-3'>
        {rows.map((detail) => (
          <div key={detail.id} className='rounded-xl border border-[var(--border-default)] bg-[var(--bg-surface)] p-3'>
            <div className='flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between'>
              <div>
                <div className='flex flex-wrap items-center gap-2'>
                  <span className='text-[var(--ui-text-sm)] font-medium text-[var(--text-primary)]'>{detail.label}</span>
                  <span className={`rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${detail.requirement === 'Required' ? 'bg-[rgba(248,81,73,0.12)] text-[var(--accent-red)]' : 'bg-[rgba(88,166,255,0.12)] text-[var(--accent-blue)]'}`}>
                    {detail.requirement}
                  </span>
                </div>
                <p className='mt-1 text-[var(--ui-text-xs)] text-[var(--text-secondary)]'>
                  {detail.requirement === 'Required'
                    ? 'Needed before the planner can build confident options.'
                    : 'Useful for improving option quality without blocking the next step.'}
                </p>
              </div>
              <div className='flex flex-wrap gap-2'>
                <Button type='button' variant='secondary' size='sm' onClick={() => onOpenEditor(detail.id)}>
                  {detail.addLabel}
                </Button>
                <Button type='button' variant='outline' size='sm' onClick={onAskTraveler}>
                  {detail.askLabel}
                </Button>
              </div>
            </div>
            {renderEditor(detail.id)}
          </div>
        ))}
      </div>
    </div>
  );
}
