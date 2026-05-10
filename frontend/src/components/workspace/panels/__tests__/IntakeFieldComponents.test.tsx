import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { EditableField, BudgetField, PlanningDetailSection } from '../IntakeFieldComponents';
import type { PlanningDetailId, PlanningDetailRow } from '../IntakePanel';

const currencyOptions = [
  { value: 'INR', label: 'Indian Rupee', symbol: '₹', flag: '🇮🇳' },
  { value: 'USD', label: 'US Dollar', symbol: '$', flag: '🇺🇸' },
  { value: 'EUR', label: 'Euro', symbol: '€', flag: '🇪🇺' },
];

describe('EditableField', () => {
  const baseProps = {
    label: 'Party',
    value: '2',
    field: 'party',
    isEditing: false,
    onStartEdit: vi.fn(),
    onSaveEdit: vi.fn(),
    onCancelEdit: vi.fn(),
    onEditValueChange: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders display value when not editing', () => {
    render(<EditableField {...baseProps} />);
    expect(screen.getByText('2')).toBeInTheDocument();
    expect(screen.getByText('Party')).toBeInTheDocument();
  });

  it('renders edit button with hover opacity', () => {
    render(<EditableField {...baseProps} />);
    const editBtn = screen.getByLabelText('Edit Party');
    expect(editBtn).toBeInTheDocument();
  });

  it('calls onStartEdit when edit button clicked', () => {
    render(<EditableField {...baseProps} />);
    fireEvent.click(screen.getByLabelText('Edit Party'));
    expect(baseProps.onStartEdit).toHaveBeenCalledWith('party', '2');
  });

  it('renders input when editing a generic field', () => {
    render(<EditableField {...baseProps} isEditing={true} value="4" />);
    const input = screen.getByDisplayValue('4');
    expect(input).toBeInTheDocument();
    expect(input.tagName).toBe('INPUT');
  });

  it('calls onEditValueChange when text input changes', async () => {
    render(<EditableField {...baseProps} isEditing={true} />);
    const input = screen.getByDisplayValue('2');
    await userEvent.clear(input);
    await userEvent.type(input, '5');
    expect(baseProps.onEditValueChange).toHaveBeenCalled();
  });

  it('calls onSaveEdit when save button clicked', () => {
    render(<EditableField {...baseProps} isEditing={true} />);
    fireEvent.click(screen.getByLabelText('Save Party'));
    expect(baseProps.onSaveEdit).toHaveBeenCalledWith('party');
  });

  it('calls onCancelEdit when cancel button clicked', () => {
    render(<EditableField {...baseProps} isEditing={true} />);
    fireEvent.click(screen.getByLabelText('Cancel editing'));
    expect(baseProps.onCancelEdit).toHaveBeenCalled();
  });

  it('renders select when type is select', () => {
    const selectProps = {
      ...baseProps,
      field: 'currency',
      isEditing: true,
      type: 'select' as const,
      options: currencyOptions,
      value: 'INR',
    };
    render(<EditableField {...selectProps} />);
    const select = screen.getByRole('combobox');
    expect(select).toBeInTheDocument();
    expect(select).toHaveValue('INR');
  });

  it('renders number input when type is number', () => {
    const numProps = {
      ...baseProps,
      field: 'budget',
      isEditing: true,
      type: 'number' as const,
      value: '5000',
    };
    render(<EditableField {...numProps} />);
    const input = screen.getByDisplayValue('5000');
    expect(input).toHaveAttribute('type', 'number');
  });

  it('renders SmartCombobox when field is type', () => {
    const typeProps = {
      ...baseProps,
      field: 'type',
      label: 'Trip Type',
      isEditing: true,
      value: 'Honeymoon',
    };
    render(<EditableField {...typeProps} />);
    expect(screen.getByLabelText('Save trip type')).toBeInTheDocument();
    expect(screen.getByLabelText('Cancel editing')).toBeInTheDocument();
  });

  it('shows displayValue when provided', () => {
    render(
      <EditableField
        {...baseProps}
        value="2026-06-14"
        displayValue="Jun 14-28, 2026"
      />
    );
    expect(screen.getByText('Jun 14-28, 2026')).toBeInTheDocument();
  });
});

describe('BudgetField', () => {
  const baseProps = {
    budget: '$5,000',
    budgetAmount: '5000',
    budgetCurrency: 'USD' as const,
    isEditing: false,
    currencyOptions,
    onStartEdit: vi.fn(),
    onSaveEdit: vi.fn(),
    onCancelEdit: vi.fn(),
    onAmountChange: vi.fn(),
    onCurrencyChange: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders formatted budget when not editing', () => {
    render(<BudgetField {...baseProps} />);
    expect(screen.getByText('Budget')).toBeInTheDocument();
    expect(screen.getByLabelText('Edit budget')).toBeInTheDocument();
  });

  it('calls onStartEdit when edit button clicked', () => {
    render(<BudgetField {...baseProps} />);
    fireEvent.click(screen.getByLabelText('Edit budget'));
    expect(baseProps.onStartEdit).toHaveBeenCalled();
  });

  it('renders amount input and currency select when editing', () => {
    render(<BudgetField {...baseProps} isEditing={true} />);
    expect(screen.getByDisplayValue('5000')).toBeInTheDocument();
    expect(screen.getByText('🇺🇸 USD')).toBeInTheDocument();
  });

  it('calls onAmountChange when amount input changes', async () => {
    render(<BudgetField {...baseProps} isEditing={true} />);
    const input = screen.getByDisplayValue('5000');
    await userEvent.clear(input);
    await userEvent.type(input, '10000');
    expect(baseProps.onAmountChange).toHaveBeenCalled();
  });

  it('calls onSaveEdit when save button clicked', () => {
    render(<BudgetField {...baseProps} isEditing={true} />);
    fireEvent.click(screen.getByLabelText('Save budget'));
    expect(baseProps.onSaveEdit).toHaveBeenCalled();
  });

  it('calls onCancelEdit when cancel button clicked', () => {
    render(<BudgetField {...baseProps} isEditing={true} />);
    fireEvent.click(screen.getByLabelText('Cancel editing'));
    expect(baseProps.onCancelEdit).toHaveBeenCalled();
  });
});

describe('PlanningDetailSection', () => {
  const mockRows: PlanningDetailRow[] = [
    {
      id: 'budget' as PlanningDetailId,
      label: 'Budget range',
      requirement: 'Required' as const,
      addLabel: 'Add budget',
      askLabel: 'Ask traveler',
      value: null,
    },
    {
      id: 'origin' as PlanningDetailId,
      label: 'Origin city',
      requirement: 'Recommended' as const,
      addLabel: 'Add origin',
      askLabel: 'Ask traveler',
      value: null,
    },
  ];

  const baseProps = {
    title: 'Required missing fields',
    tone: 'required' as const,
    rows: mockRows,
    onOpenEditor: vi.fn(),
    onAskTraveler: vi.fn(),
    renderEditor: vi.fn(() => null),
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders nothing when rows is empty', () => {
    const { container } = render(
      <PlanningDetailSection {...baseProps} rows={[]} />
    );
    expect(container.firstChild).toBeNull();
  });

  it('renders section title and row count', () => {
    render(<PlanningDetailSection {...baseProps} />);
    expect(screen.getByText('Required missing fields')).toBeInTheDocument();
    expect(screen.getByText('2 fields')).toBeInTheDocument();
  });

  it('renders row labels with requirement badges', () => {
    render(<PlanningDetailSection {...baseProps} />);
    expect(screen.getByText('Budget range')).toBeInTheDocument();
    expect(screen.getByText('Origin city')).toBeInTheDocument();
    expect(screen.getByText('Required')).toBeInTheDocument();
    expect(screen.getByText('Recommended')).toBeInTheDocument();
  });

  it('calls onOpenEditor when add button clicked', () => {
    render(<PlanningDetailSection {...baseProps} />);
    fireEvent.click(screen.getByRole('button', { name: 'Add budget' }));
    expect(baseProps.onOpenEditor).toHaveBeenCalledWith('budget');
  });

  it('calls onAskTraveler when ask button clicked', () => {
    render(<PlanningDetailSection {...baseProps} />);
    const askButtons = screen.getAllByRole('button', { name: 'Ask traveler' });
    fireEvent.click(askButtons[0]);
    expect(baseProps.onAskTraveler).toHaveBeenCalled();
  });

  it('renders singular "1 field" for single row', () => {
    render(
      <PlanningDetailSection
        {...baseProps}
        rows={mockRows.slice(0, 1)}
      />
    );
    expect(screen.getByText('1 field')).toBeInTheDocument();
  });

  it('renders editor via renderEditor callback', () => {
    const renderEditor = vi.fn((id) => {
      if (id === 'budget') return <div data-testid="budget-editor">Budget Editor</div>;
      return null;
    });
    render(
      <PlanningDetailSection {...baseProps} renderEditor={renderEditor} />
    );
    expect(screen.getByTestId('budget-editor')).toBeInTheDocument();
    expect(screen.getByText('Budget Editor')).toBeInTheDocument();
  });
});
