# Reporting Module — UX/UI Deep Dive

> Report builder interface, visualization components, and interactive dashboards

---

## Document Overview

**Series:** Reporting Module | **Document:** 2 of 4 | **Focus:** UX/UI Design

**Related Documents:**
- [01: Technical Deep Dive](./REPORTING_01_TECHNICAL_DEEP_DIVE.md) — Report engine architecture
- [03: Export Deep Dive](./REPORTING_03_EXPORT_DEEP_DIVE.md) — Export formats
- [04: Scheduling Deep Dive](./REPORTING_04_SCHEDULING_DEEP_DIVE.md) — Automated reports

---

## Table of Contents

1. [Report Builder Interface](#1-report-builder-interface)
2. [Field Selection & Configuration](#2-field-selection--configuration)
3. [Filter & Grouping UI](#3-filter--grouping-ui)
4. [Visualization Components](#4-visualization-components)
5. [Interactive Dashboards](#5-interactive-dashboards)
6. [Responsive Design](#6-responsive-design)
7. [Accessibility](#7-accessibility)

---

## 1. Report Builder Interface

### 1.1 Layout Overview

```
┌────────────────────────────────────────────────────────────────────────────┐
│                         REPORT BUILDER LAYOUT                              │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  ┌──────────────────────────────────────────────────────────────────────┐ │
│  │  HEADER: Save | Run | Schedule | Export | More ▼                     │ │
│  └──────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│  ┌────────────────┬─────────────────────────────────────────────────────┐ │
│  │                │                                                     │ │
│  │   SIDEBAR      │              CANVAS / PREVIEW                       │ │
│  │                │                                                     │ │
│  │ ┌────────────┐ │  ┌──────────────────────────────────────────────┐ │ │
│  │ │   FIELDS   │ │  │                                               │ │ │
│  │ │            │ │  │  [Data Table / Visualization Preview]         │ │ │
│  │ │ Dimensions │ │  │                                               │ │ │
│  │ │ Measures   │ │  │  ┌──────────┬──────────┬──────────┐           │ │ │
│  │ │            │ │ │  │  Name    │   Amount  │   Count  │           │ │ │
│  │ └────────────┘ │ │  │──────────│──────────│──────────│           │ │ │
│  │                │ │  │  Customer A│   $5,200  │    12    │           │ │ │
│  │ ┌────────────┐ │ │  │  Customer B│   $3,800  │     8    │           │ │ │
│  │ │  FILTERS   │ │ │  │  Customer C│   $2,100  │     5    │           │ │ │
│  │ │            │ │ │  └──────────┴──────────┴──────────┘           │ │ │
│  │ │ [Add       │ │  │                                               │ │ │
│  │ │  filter]   │ │ │  ┌────────────────────────────────────────────┐ │ │ │
│  │ └────────────┘ │ │  │ SQL Preview (collapsible)                  │ │ │ │
│  │                │ │  │ SELECT customer.name, sum(amount) ...      │ │ │ │
│  │ ┌────────────┐ │ │  └────────────────────────────────────────────┘ │ │ │
│  │ │   GROUP    │ │  │                                               │ │ │
│  │ │   BY       │ │ │  [Showing 25 of 1,234 rows]                     │ │ │
│  │ └────────────┘ │ │                                               │ │ │
│  │                │ └───────────────────────────────────────────────┘ │ │
│  │                │                                                     │ │
│  └────────────────┴─────────────────────────────────────────────────────┘ │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Builder Component Structure

```typescript
// Report builder component
interface ReportBuilderProps {
  reportId?: string; // undefined = new report
  onSave: (report: ReportDefinition) => Promise<void>;
  onCancel: () => void;
  initialConfig?: QueryConfiguration;
}

export const ReportBuilder: React.FC<ReportBuilderProps> = ({
  reportId,
  onSave,
  onCancel,
  initialConfig,
}) => {
  const [config, setConfig] = useState<QueryConfiguration>(
    initialConfig || defaultConfig
  );
  const [preview, setPreview] = useState<QueryResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [dirty, setDirty] = useState(false);

  const handleRun = async () => {
    setLoading(true);
    try {
      const result = await api.post('/reports/execute', { query: config });
      setPreview(result);
    } catch (error) {
      showToast('Failed to run report', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    const report: ReportDefinition = {
      id: reportId || uuid(),
      name: config.name || 'Untitled Report',
      query: config,
      createdBy: useAuthStore.getState().user.id,
      createdAt: Date.now(),
      updatedAt: Date.now(),
      version: 1,
      access: { visibility: 'private' },
      tags: [],
    };
    await onSave(report);
    setDirty(false);
  };

  return (
    <ReportBuilderLayout>
      <ReportBuilderHeader
        config={config}
        onConfigChange={setConfig}
        onSave={handleSave}
        onRun={handleRun}
        onCancel={onCancel}
        dirty={dirty}
        loading={loading}
      />

      <ReportBuilderContent>
        <FieldSelector
          config={config}
          onConfigChange={(newConfig) => {
            setConfig(newConfig);
            setDirty(true);
          }}
        />

        <FilterBuilder
          config={config}
          onConfigChange={(newConfig) => {
            setConfig(newConfig);
            setDirty(true);
          }}
        />

        <GroupBySelector
          config={config}
          onConfigChange={(newConfig) => {
            setConfig(newConfig);
            setDirty(true);
          }}
        />
      </ReportBuilderContent>

      <ReportPreview
        data={preview}
        loading={loading}
        config={config}
      />
    </ReportBuilderLayout>
  );
};
```

### 1.3 Builder Layout Component

```typescript
// Split-pane layout for builder
const ReportBuilderLayout: React.FC<{ children: React.ReactNode }> = ({
  children
}) => {
  return (
    <div className={styles.reportBuilder}>
      {children}
    </div>
  );
};

const ReportBuilderContent: React.FC<{ children: React.ReactNode }> = ({
  children
}) => {
  const [sidebarWidth, setSidebarWidth] = useState(320);

  return (
    <div className={styles.content}>
      <Resizable
        width={sidebarWidth}
        onResize={(e) => setSidebarWidth(e.width)}
        minSize={280}
        maxSize={480}
      >
        <div className={styles.sidebar} style={{ width: sidebarWidth }}>
          {children}
        </div>
      </Resizable>

      <div className={styles.preview}>
        {/* Preview rendered by parent */}
      </div>
    </div>
  );
};

// Styles
const styles = css`
  .reportBuilder {
    display: flex;
    flex-direction: column;
    height: 100vh;
    background: var(--bg-primary);
  }

  .content {
    display: flex;
    flex: 1;
    overflow: hidden;
  }

  .sidebar {
    background: var(--bg-secondary);
    border-right: 1px solid var(--border);
    overflow-y: auto;
    padding: var(--space-4);
  }

  .preview {
    flex: 1;
    overflow: hidden;
  }
`;
```

---

## 2. Field Selection & Configuration

### 2.1 Field Picker

```typescript
// Field picker component
interface FieldPickerProps {
  availableFields: AvailableField[];
  selectedFields: FieldConfig[];
  onChange: (fields: FieldConfig[]) => void;
}

interface AvailableField {
  id: string;
  name: string;
  displayName: string;
  type: 'dimension' | 'measure';
  dataType: 'string' | 'number' | 'date' | 'boolean';
  table: string;
  description?: string;
}

export const FieldPicker: React.FC<FieldPickerProps> = ({
  availableFields,
  selectedFields,
  onChange,
}) => {
  const [search, setSearch] = useState('');
  const [draggedField, setDraggedField] = useState<string | null>(null);

  const groupedFields = useMemo(() => {
    const groups: Record<string, AvailableField[]> = {
      Dimensions: [],
      Measures: [],
    };

    availableFields
      .filter(f =>
        f.displayName.toLowerCase().includes(search.toLowerCase()) ||
        f.name.toLowerCase().includes(search.toLowerCase())
      )
      .forEach(field => {
        if (field.type === 'dimension') {
          groups.Dimensions.push(field);
        } else {
          groups.Measures.push(field);
        }
      });

    return groups;
  }, [availableFields, search]);

  const handleAddField = (field: AvailableField) => {
    const fieldConfig: FieldConfig = {
      id: uuid(),
      name: field.name,
      type: field.type,
      dataType: field.dataType,
    };

    if (field.type === 'measure') {
      fieldConfig.aggregation = 'sum';
    }

    onChange([...selectedFields, fieldConfig]);
  };

  const handleRemoveField = (fieldId: string) => {
    onChange(selectedFields.filter(f => f.id !== fieldId));
  };

  const handleReorder = (fromIndex: number, toIndex: number) => {
    const newFields = [...selectedFields];
    const [moved] = newFields.splice(fromIndex, 1);
    newFields.splice(toIndex, 0, moved);
    onChange(newFields);
  };

  return (
    <div className={styles.fieldPicker}>
      <Input
        placeholder="Search fields..."
        value={search}
        onChange={setSearch}
        icon={<SearchIcon />}
      />

      <div className={styles.fieldLists}>
        {/* Available fields */}
        <div className={styles.availableFields}>
          {Object.entries(groupedFields).map(([group, fields]) => (
            <div key={group} className={styles.fieldGroup}>
              <h4 className={styles.groupTitle}>{group}</h4>
              {fields.map(field => (
                <FieldItem
                  key={field.id}
                  field={field}
                  onAdd={() => handleAddField(field)}
                  disabled={selectedFields.some(f => f.name === field.name)}
                />
              ))}
            </div>
          ))}
        </div>

        {/* Selected fields */}
        <div className={styles.selectedFields}>
          <h4 className={styles.sectionTitle}>Selected Fields</h4>
          {selectedFields.length === 0 ? (
            <EmptyState
              icon="fields"
              message="Drag fields here or click to add"
            />
          ) : (
            <DraggableList
              items={selectedFields}
              renderItem={(field, index) => (
                <SelectedFieldItem
                  key={field.id}
                  field={field}
                  onRemove={() => handleRemoveField(field.id)}
                  onDragStart={() => setDraggedField(field.id)}
                  onDragEnd={() => setDraggedField(null)}
                  isDragging={draggedField === field.id}
                />
              )}
              onReorder={handleReorder}
            />
          )}
        </div>
      </div>
    </div>
  );
};

// Individual field item
const FieldItem: React.FC<{
  field: AvailableField;
  onAdd: () => void;
  disabled?: boolean;
}> = ({ field, onAdd, disabled }) => {
  return (
    <button
      className={styles.fieldItem}
      onClick={onAdd}
      disabled={disabled}
    >
      <FieldIcon type={field.type} dataType={field.dataType} />
      <span className={styles.fieldName}>{field.displayName}</span>
      {!disabled && <PlusIcon className={styles.addIcon} />}
      {disabled && <CheckIcon className={styles.addedIcon} />}
    </button>
  );
};

// Selected field with configuration
const SelectedFieldItem: React.FC<{
  field: FieldConfig;
  onRemove: () => void;
  onDragStart: () => void;
  onDragEnd: () => void;
  isDragging: boolean;
}> = ({ field, onRemove, onDragStart, onDragEnd, isDragging }) => {
  const [configuring, setConfiguring] = useState(false);

  return (
    <div
      className={cn(styles.selectedField, { [styles.dragging]: isDragging })}
      draggable
      onDragStart={onDragStart}
      onDragEnd={onDragEnd}
    >
      <DragHandleIcon className={styles.dragHandle} />

      <FieldIcon type={field.type} dataType={field.dataType} />
      <span className={styles.fieldName}>
        {field.alias || field.name}
      </span>

      {field.type === 'measure' && (
        <AggregationSelector
          value={field.aggregation}
          onChange={(agg) => {/* update */}}
        />
      )}

      <button
        className={styles.configButton}
        onClick={() => setConfiguring(true)}
      >
        <SettingsIcon />
      </button>

      <button
        className={styles.removeButton}
        onClick={onRemove}
      >
        <CloseIcon />
      </button>

      {configuring && (
        <FieldConfigDialog
          field={field}
          onClose={() => setConfiguring(false)}
          onSave={(config) => {/* update */}}
        />
      )}
    </div>
  );
};
```

### 2.2 Field Configuration Dialog

```typescript
// Field configuration options
interface FieldConfigDialogProps {
  field: FieldConfig;
  onClose: () => void;
  onSave: (config: FieldConfig) => void;
}

export const FieldConfigDialog: React.FC<FieldConfigDialogProps> = ({
  field,
  onClose,
  onSave,
}) => {
  const [alias, setAlias] = useState(field.alias || '');
  const [aggregation, setAggregation] = useState(field.aggregation || 'sum');
  const [expression, setExpression] = useState(field.expression || '');

  const handleSave = () => {
    onSave({
      ...field,
      alias,
      aggregation,
      expression,
    });
    onClose();
  };

  return (
    <Dialog open onClose={onClose}>
      <DialogTitle>Configure Field</DialogTitle>
      <DialogContent>
        <FormField label="Display Name (Alias)">
          <Input
            value={alias}
            onChange={setAlias}
            placeholder={field.name}
          />
        </FormField>

        {field.type === 'measure' && (
          <FormField label="Aggregation">
            <Select value={aggregation} onChange={setAggregation}>
              <option value="sum">Sum</option>
              <option value="count">Count</option>
              <option value="count_distinct">Count Distinct</option>
              <option value="avg">Average</option>
              <option value="min">Minimum</option>
              <option value="max">Maximum</option>
              <option value="median">Median</option>
            </Select>
          </FormField>
        )}

        <FormField label="Custom Expression (Optional)">
          <Textarea
            value={expression}
            onChange={setExpression}
            placeholder="e.g., amount * 0.1 for commission"
            rows={3}
          />
          <FormHint>
            Use SQL expressions for calculated fields. Reference other fields
            by their table.column name.
          </FormHint>
        </FormField>

        <FormField label="Format">
          <FormatSelector
            dataType={field.dataType}
            value={field.format}
            onChange={(format) => {/* update */}}
          />
        </FormField>
      </DialogContent>
      <DialogActions>
        <Button variant="secondary" onClick={onClose}>Cancel</Button>
        <Button onClick={handleSave}>Apply</Button>
      </DialogActions>
    </Dialog>
  );
};

// Number formatting options
const FormatSelector: React.FC<{
  dataType: string;
  value?: string;
  onChange: (format: string) => void;
}> = ({ dataType, value, onChange }) => {
  if (dataType === 'number') {
    return (
      <Select value={value} onChange={onChange}>
        <option value="">Default</option>
        <option value="number">1,234.56</option>
        <option value="currency">$1,234.56</option>
        <option value="percent">45.67%</option>
        <option value="integer">1,235</option>
      </Select>
    );
  }

  if (dataType === 'date') {
    return (
      <Select value={value} onChange={onChange}>
        <option value="">Default</option>
        <option value="date">2026-04-25</option>
        <option value="datetime">2026-04-25 14:30</option>
        <option value="time">14:30</option>
        <option value="relative">2 hours ago</option>
      </Select>
    );
  }

  return null;
};
```

---

## 3. Filter & Grouping UI

### 3.1 Filter Builder

```typescript
// Filter builder component
interface FilterBuilderProps {
  filters: FilterGroup;
  onChange: (filters: FilterGroup) => void;
  availableFields: AvailableField[];
}

export const FilterBuilder: React.FC<FilterBuilderProps> = ({
  filters,
  onChange,
  availableFields,
}) => {
  const [adding, setAdding] = useState(false);

  const handleAddFilter = (filter: Filter) => {
    onChange({
      ...filters,
      and: [...(filters.and || []), filter],
    });
  };

  const handleUpdateFilter = (index: number, filter: Filter) => {
    const newAnd = [...(filters.and || [])];
    newAnd[index] = filter;
    onChange({ ...filters, and: newAnd });
  };

  const handleRemoveFilter = (index: number) => {
    const newAnd = filters.and?.filter((_, i) => i !== index);
    onChange({ ...filters, and: newAnd });
  };

  return (
    <div className={styles.filterBuilder}>
      <div className={styles.header}>
        <h4>Filters</h4>
        <Button
          size="sm"
          variant="ghost"
          onClick={() => setAdding(true)}
        >
          <PlusIcon /> Add Filter
        </Button>
      </div>

      <div className={styles.filters}>
        {filters.and?.length === 0 ? (
          <EmptyState
            icon="filter"
            message="No filters applied"
            size="sm"
          />
        ) : (
          filters.and?.map((filter, index) => (
            <FilterRow
              key={index}
              filter={filter}
              availableFields={availableFields}
              onChange={(f) => handleUpdateFilter(index, f)}
              onRemove={() => handleRemoveFilter(index)}
            />
          ))
        )}
      </div>

      {adding && (
        <FilterAddDialog
          availableFields={availableFields}
          onClose={() => setAdding(false)}
          onAdd={(filter) => {
            handleAddFilter(filter);
            setAdding(false);
          }}
        />
      )}
    </div>
  );
};

// Individual filter row
const FilterRow: React.FC<{
  filter: Filter;
  availableFields: AvailableField[];
  onChange: (filter: Filter) => void;
  onRemove: () => void;
}> = ({ filter, availableFields, onChange, onRemove }) => {
  const field = availableFields.find(f => f.name === filter.field);
  const operators = getOperatorsForType(field?.dataType || 'string');

  return (
    <div className={styles.filterRow}>
      <Select
        value={filter.field}
        onChange={(value) => onChange({ ...filter, field: value })}
        className={styles.fieldSelect}
      >
        {availableFields.map(f => (
          <option key={f.id} value={f.name}>{f.displayName}</option>
        ))}
      </Select>

      <Select
        value={filter.operator}
        onChange={(value) => onChange({ ...filter, operator: value as any })}
        className={styles.operatorSelect}
      >
        {operators.map(op => (
          <option key={op.value} value={op.value}>{op.label}</option>
        ))}
      </Select>

      <FilterValueInput
        field={field!}
        operator={filter.operator}
        value={filter.value}
        onChange={(value) => onChange({ ...filter, value })}
      />

      <Button
        variant="ghost"
        size="sm"
        onClick={onRemove}
        className={styles.removeButton}
      >
        <CloseIcon />
      </Button>
    </div>
  );
};

// Value input based on field type and operator
const FilterValueInput: React.FC<{
  field: AvailableField;
  operator: string;
  value: any;
  onChange: (value: any) => void;
}> = ({ field, operator, value, onChange }) => {
  // IN operator gets multi-select
  if (operator === 'in') {
    return (
      <MultiSelect
        values={value || []}
        onChange={onChange}
        placeholder="Select values..."
      />
    );
  }

  // Date fields get date picker
  if (field.dataType === 'date') {
    return (
      <DatePicker
        value={value}
        onChange={onChange}
        includeTime
      />
    );
  }

  // Boolean fields get toggle
  if (field.dataType === 'boolean') {
    return (
      <Toggle
        checked={value}
        onChange={onChange}
      />
    );
  }

  // Number fields get number input
  if (field.dataType === 'number') {
    return (
      <Input
        type="number"
        value={value}
        onChange={onChange}
      />
    );
  }

  // Default: text input
  return (
    <Input
      value={value}
      onChange={onChange}
      placeholder="Value..."
    />
  );
};

// Get available operators for data type
function getOperatorsForType(dataType: string): Array<{ value: string; label: string }> {
  const common = [
    { value: 'eq', label: 'equals' },
    { value: 'ne', label: 'not equals' },
    { value: 'is_null', label: 'is null' },
    { value: 'is_not_null', label: 'is not null' },
  ];

  if (dataType === 'string') {
    return [
      ...common,
      { value: 'like', label: 'contains' },
      { value: 'in', label: 'in list' },
    ];
  }

  if (dataType === 'number') {
    return [
      ...common,
      { value: 'gt', label: 'greater than' },
      { value: 'gte', label: 'greater or equal' },
      { value: 'lt', label: 'less than' },
      { value: 'lte', label: 'less or equal' },
      { value: 'in', label: 'in list' },
    ];
  }

  if (dataType === 'date') {
    return [
      ...common,
      { value: 'gt', label: 'after' },
      { value: 'gte', label: 'on or after' },
      { value: 'lt', label: 'before' },
      { value: 'lte', label: 'on or before' },
    ];
  }

  return common;
}
```

### 3.2 Group By Selector

```typescript
// Group by component
interface GroupBySelectorProps {
  groupBy?: string[];
  availableFields: AvailableField[];
  onChange: (groupBy: string[]) => void;
}

export const GroupBySelector: React.FC<GroupBySelectorProps> = ({
  groupBy = [],
  availableFields,
  onChange,
}) => {
  const dimensionFields = availableFields.filter(f => f.type === 'dimension');

  return (
    <div className={styles.groupBySelector}>
      <h4>Group By</h4>

      {groupBy.length === 0 ? (
        <EmptyState
          icon="group"
          message="Add fields to group by"
          size="sm"
        />
      ) : (
        <div className={styles.selectedGroups}>
          {groupBy.map(field => (
            <Chip
              key={field}
              label={field}
              onRemove={() => onChange(groupBy.filter(f => f !== field))}
            />
          ))}
        </div>
      )}

      <Dropdown
        trigger={
          <Button variant="secondary" size="sm">
            <PlusIcon /> Add Grouping
          </Button>
        }
      >
        {dimensionFields
          .filter(f => !groupBy.includes(f.name))
          .map(field => (
            <DropdownItem
              key={field.id}
              label={field.displayName}
              onClick={() => onChange([...groupBy, field.name])}
            />
          ))}
      </Dropdown>
    </div>
  );
};

// Time-based grouping for date fields
interface TimeGroupSelectorProps {
  dateField: string;
  granularity: TimeGranularity;
  onChange: (granularity: TimeGranularity) => void;
}

type TimeGranularity = 'minute' | 'hour' | 'day' | 'week' | 'month' | 'quarter' | 'year';

export const TimeGroupSelector: React.FC<TimeGroupSelectorProps> = ({
  dateField,
  granularity,
  onChange,
}) => {
  return (
    <div className={styles.timeGroupSelector}>
      <label>Time Granularity</label>
      <SegmentedControl
        value={granularity}
        onChange={onChange}
        options={[
          { value: 'hour', label: 'Hour' },
          { value: 'day', label: 'Day' },
          { value: 'week', label: 'Week' },
          { value: 'month', label: 'Month' },
          { value: 'quarter', label: 'Quarter' },
          { value: 'year', label: 'Year' },
        ]}
      />
    </div>
  );
};
```

---

## 4. Visualization Components

### 4.1 Visualization Types

```
┌────────────────────────────────────────────────────────────────────────────┐
│                        VISUALIZATION TYPE GUIDE                           │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  TABLE              ┌─────────────────────────────────────────────────┐   │
│                     │  Best for: Detailed data, exact values          │   │
│                     │  Dimensions: 1-2 columns, 1+ measures            │   │
│                     └─────────────────────────────────────────────────┘   │
│                                                                            │
│  BAR CHART          ╭────╮                                                │
│                     │ ██ │     Best for: Comparisons across categories    │
│               ╭─────│ ██ │─────╮  Dimensions: 1 dimension, 1-2 measures    │
│               │ ████│ ██ │████ │  Recommended: ≤ 20 categories            │
│               ╰─────│ ██ │─────╯                                          │
│                     └────┘                                                │
│                                                                            │
│  LINE CHART         ╭────╮                                                │
│                  ╭──┤ ██ │     Best for: Trends over time                 │
│              ╭────┤──┤ ██ │     Dimensions: 1 date, 1-2 measures            │
│          ╭────┤───┤  └────┘                                             │
│          │ ███│───┤→                                                       │
│          └────┴───╯                                                        │
│                                                                            │
│  PIE CHART             ╱‾‾‾╲                                              │
│                    ╱  ██  ╲     Best for: Part-to-whole relationships     │
│                   │   ███   │    Dimensions: 1 dimension, 1 measure        │
│                    ╲       ╱     Recommended: ≤ 8 segments                 │
│                     ╲______╱                                              │
│                                                                            │
│  NUMBER                ╭────╮                                              │
│  (KPI)                │ 125│     Best for: Single metric display           │
│                       │    │     Dimensions: 1 measure only                │
│                       │ +5%│                                               │
│                       └────┘                                               │
│                                                                            │
│  AREA CHART       ╭────────────────╮                                       │
│                  │████████████████ │  Best for: Volume over time            │
│                  │██████████████████│  Dimensions: 1 date, 1-2 measures     │
│                  └─────────────────╯                                       │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Visualization Component

```typescript
// Universal visualization component
interface VisualizationProps {
  type: VisualizationType;
  data: QueryResult;
  config: VisualizationConfig;
  width?: number;
  height?: number;
  onDrillDown?: (dimension: string, value: any) => void;
}

export const Visualization: React.FC<VisualizationProps> = ({
  type,
  data,
  config,
  width,
  height,
  onDrillDown,
}) => {
  const processedData = useMemo(() => {
    return processDataForVisualization(data, type, config);
  }, [data, type, config]);

  switch (type) {
    case 'table':
      return <TableVisualization data={processedData} config={config} />;

    case 'bar':
    case 'column':
      return <BarVisualization data={processedData} config={config} />;

    case 'line':
    case 'area':
      return <LineVisualization data={processedData} config={config} />;

    case 'pie':
    case 'donut':
      return <PieVisualization data={processedData} config={config} />;

    case 'number':
    case 'kpi':
      return <KPIVisualization data={processedData} config={config} />;

    case 'heatmap':
      return <HeatmapVisualization data={processedData} config={config} />;

    default:
      return <div>Unknown visualization type: {type}</div>;
  }
};

// Bar chart component
const BarVisualization: React.FC<{
  data: ChartData;
  config: ChartConfig;
}> = ({ data, config }) => {
  const chartRef = useRef<ChartJS>(null);

  const chartData = {
    labels: data.labels,
    datasets: data.datasets.map(ds => ({
      label: ds.label,
      data: ds.data,
      backgroundColor: ds.color,
      borderRadius: 4,
    })),
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: data.datasets.length > 1,
        position: 'top' as const,
      },
      tooltip: {
        callbacks: {
          label: (context: any) => {
            return `${context.dataset.label}: ${formatValue(
              context.raw,
              config.format
            )}`;
          },
        },
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        ticks: {
          callback: (value: any) => formatValue(value, config.format),
        },
      },
    },
    onClick: (event: any, elements: any[]) => {
      if (elements.length > 0 && config.onDrillDown) {
        const index = elements[0].index;
        config.onDrillDown(data.labels[index]);
      }
    },
  };

  return (
    <div className={styles.chartContainer} style={{ height: config.height || 400 }}>
      <Chart ref={chartRef} type="bar" data={chartData} options={options} />
    </div>
  );
};

// Line chart component
const LineVisualization: React.FC<{
  data: ChartData;
  config: ChartConfig;
}> = ({ data, config }) => {
  const chartData = {
    labels: data.labels,
    datasets: data.datasets.map(ds => ({
      label: ds.label,
      data: ds.data,
      borderColor: ds.color,
      backgroundColor: alpha(ds.color, 0.1),
      fill: config.type === 'area',
      tension: 0.3,
    })),
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
      intersect: false,
      mode: 'index' as const,
    },
    plugins: {
      legend: {
        display: true,
        position: 'top' as const,
      },
      tooltip: {
        callbacks: {
          label: (context: any) => {
            return `${context.dataset.label}: ${formatValue(
              context.raw,
              config.format
            )}`;
          },
        },
      },
    },
    scales: {
      y: {
        beginAtZero: config.type === 'area',
        ticks: {
          callback: (value: any) => formatValue(value, config.format),
        },
      },
    },
  };

  return (
    <div className={styles.chartContainer} style={{ height: config.height || 400 }}>
      <Chart type="line" data={chartData} options={options} />
    </div>
  );
};

// KPI/Number component
const KPIVisualization: React.FC<{
  data: ChartData;
  config: ChartConfig;
}> = ({ data, config }) => {
  const value = data.datasets[0]?.data[0] || 0;
  const previousValue = data.datasets[0]?.data[1] || value;
  const change = previousValue !== 0
    ? ((value - previousValue) / previousValue) * 100
    : 0;

  return (
    <div className={styles.kpiContainer}>
      <div className={styles.kpiValue}>
        {formatValue(value, config.format)}
      </div>
      {config.showChange && (
        <div className={cn(styles.kpiChange, {
          [styles.positive]: change > 0,
          [styles.negative]: change < 0,
        })}>
          {change > 0 ? <ArrowUpIcon /> : <ArrowDownIcon />}
          {Math.abs(change).toFixed(1)}%
        </div>
      )}
      {config.label && (
        <div className={styles.kpiLabel}>{config.label}</div>
      )}
    </div>
  );
};
```

### 4.3 Visualization Configurator

```typescript
// Visualization configuration panel
interface VisualizationConfiguratorProps {
  config: VisualizationConfig;
  data: QueryResult;
  onChange: (config: VisualizationConfig) => void;
}

export const VisualizationConfigurator: React.FC<VisualizationConfiguratorProps> = ({
  config,
  data,
  onChange,
}) => {
  return (
    <div className={styles.vizConfigurator}>
      <FormField label="Chart Type">
        <ChartTypeSelector
          value={config.type}
          onChange={(type) => onChange({ ...config, type })}
          data={data}
        />
      </FormField>

      {config.type !== 'table' && config.type !== 'kpi' && (
        <>
          <FormField label="X Axis">
            <AxisSelector
              columns={data.columns}
              value={config.xAxis}
              onChange={(xAxis) => onChange({ ...config, xAxis })}
            />
          </FormField>

          <FormField label="Y Axis">
            <MeasureSelector
              columns={data.columns}
              value={config.yAxis}
              onChange={(yAxis) => onChange({ ...config, yAxis })}
            />
          </FormField>

          {data.columns.length > 2 && (
            <FormField label="Group By (Optional)">
              <Select
                value={config.groupBy || ''}
                onChange={(groupBy) => onChange({ ...config, groupBy })}
              >
                <option value="">None</option>
                {data.columns.map(col => (
                  <option key={col.name} value={col.name}>{col.displayName}</option>
                ))}
              </Select>
            </FormField>
          )}
        </>
      )}

      <FormField label="Color Theme">
        <ColorThemeSelector
          value={config.colorTheme}
          onChange={(colorTheme) => onChange({ ...config, colorTheme })}
        />
      </FormField>

      <FormField label="Height">
        <Slider
          value={config.height || 400}
          onChange={(height) => onChange({ ...config, height })}
          min={200}
          max={800}
          step={50}
        />
      </FormField>

      {config.type === 'kpi' && (
        <FormField label="Show Change">
          <Toggle
            checked={config.showChange}
            onChange={(showChange) => onChange({ ...config, showChange })}
          />
        </FormField>
      )}
    </div>
  );
};

// Chart type selector with recommendations
const ChartTypeSelector: React.FC<{
  value: VisualizationType;
  onChange: (type: VisualizationType) => void;
  data: QueryResult;
}> = ({ value, onChange, data }) => {
  const recommended = recommendChartType(data);

  const types: Array<{
    value: VisualizationType;
    label: string;
    icon: string;
    description: string;
  }> = [
    { value: 'table', label: 'Table', icon: 'table', description: 'Detailed view' },
    { value: 'bar', label: 'Bar', icon: 'bar', description: 'Compare categories' },
    { value: 'line', label: 'Line', icon: 'line', description: 'Show trends' },
    { value: 'area', label: 'Area', icon: 'area', description: 'Volume over time' },
    { value: 'pie', label: 'Pie', icon: 'pie', description: 'Part to whole' },
    { value: 'kpi', label: 'KPI', icon: 'number', description: 'Single metric' },
  ];

  return (
    <div className={styles.chartTypeSelector}>
      {types.map(type => (
        <button
          key={type.value}
          className={cn(styles.chartType, {
            [styles.selected]: value === type.value,
            [styles.recommended]: recommended === type.value,
          })}
          onClick={() => onChange(type.value)}
        >
          <ChartIcon type={type.icon} />
          <span>{type.label}</span>
          {recommended === type.value && (
            <Badge variant="info" size="sm">Recommended</Badge>
          )}
        </button>
      ))}
    </div>
  );
};

// Recommend chart type based on data
function recommendChartType(data: QueryResult): VisualizationType {
  const hasDate = data.columns.some(c => c.dataType === 'date');
  const dimensions = data.columns.filter(c => c.type === 'dimension').length;
  const measures = data.columns.filter(c => c.type === 'measure').length;

  // Single measure → KPI
  if (measures === 1 && dimensions === 0) {
    return 'kpi';
  }

  // Date dimension → Line/Area
  if (hasDate) {
    return 'line';
  }

  // Single dimension, 1-2 measures → Bar
  if (dimensions === 1 && measures <= 2) {
    return 'bar';
  }

  // Default to table
  return 'table';
}
```

---

## 5. Interactive Dashboards

### 5.1 Dashboard Layout

```typescript
// Dashboard component
interface DashboardProps {
  dashboardId: string;
  editable?: boolean;
}

export const Dashboard: React.FC<DashboardProps> = ({
  dashboardId,
  editable = false,
}) => {
  const [dashboard, setDashboard] = useState<DashboardConfig | null>(null);
  const [filters, setFilters] = useState<GlobalFilters>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboard();
  }, [dashboardId]);

  const loadDashboard = async () => {
    setLoading(true);
    try {
      const data = await api.get(`/dashboards/${dashboardId}`);
      setDashboard(data);
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateLayout = (layout: WidgetLayout[]) => {
    setDashboard(prev => prev ? { ...prev, widgets: layout } : null);
    // Save to backend
    api.put(`/dashboards/${dashboardId}`, { widgets: layout });
  };

  if (loading) {
    return <DashboardSkeleton />;
  }

  if (!dashboard) {
    return <EmptyState message="Dashboard not found" />;
  }

  return (
    <div className={styles.dashboard}>
      <DashboardHeader
        dashboard={dashboard}
        editable={editable}
        onEdit={() => {/* open edit dialog */}}
      />

      <DashboardFilters
        filters={dashboard.filters}
        values={filters}
        onChange={setFilters}
      />

      <DashboardGrid
        widgets={dashboard.widgets}
        filters={filters}
        editable={editable}
        onLayoutChange={handleUpdateLayout}
      />
    </div>
  );
};

// Dashboard grid with drag-and-drop
const DashboardGrid: React.FC<{
  widgets: WidgetConfig[];
  filters: GlobalFilters;
  editable?: boolean;
  onLayoutChange?: (layout: WidgetLayout[]) => void;
}> = ({ widgets, filters, editable, onLayoutChange }) => {
  const layouts = widgets.map(w => ({
    i: w.id,
    x: w.x || 0,
    y: w.y || 0,
    w: w.w || 4,
    h: w.h || 3,
    minW: 2,
    minH: 2,
  }));

  return (
    <ResponsiveGridLayout
      layouts={{ lg: layouts }}
      breakpoints={{ lg: 1200, md: 996, sm: 768, xs: 480, xxs: 0 }}
      cols={{ lg: 12, md: 10, sm: 6, xs: 4, xxs: 2 }}
      isDraggable={editable}
      isResizable={editable}
      onLayoutChange={onLayoutChange}
    >
      {widgets.map(widget => (
        <div key={widget.id}>
          <DashboardWidget
            widget={widget}
            filters={filters}
            editable={editable}
            onRemove={() => {/* remove */}}
          />
        </div>
      ))}
    </ResponsiveGridLayout>
  );
};

// Individual widget
const DashboardWidget: React.FC<{
  widget: WidgetConfig;
  filters: GlobalFilters;
  editable?: boolean;
  onRemove?: () => void;
}> = ({ widget, filters, editable, onRemove }) => {
  const [data, setData] = useState<QueryResult | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadWidgetData();
  }, [widget, filters]);

  const loadWidgetData = async () => {
    setLoading(true);
    try {
      const result = await api.post('/reports/execute', {
        query: widget.query,
        filters: applyGlobalFilters(widget.query, filters),
      });
      setData(result);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.widget}>
      <div className={styles.widgetHeader}>
        <h3>{widget.title}</h3>
        {editable && (
          <div className={styles.widgetActions}>
            <Button size="sm" variant="ghost">
              <SettingsIcon />
            </Button>
            <Button size="sm" variant="ghost" onClick={onRemove}>
              <CloseIcon />
            </Button>
          </div>
        )}
      </div>

      <div className={styles.widgetContent}>
        {loading ? (
          <WidgetSkeleton type={widget.visualization.type} />
        ) : data ? (
          <Visualization
            type={widget.visualization.type}
            data={data}
            config={widget.visualization}
          />
        ) : (
          <EmptyState message="No data" size="sm" />
        )}
      </div>
    </div>
  );
};
```

### 5.2 Global Filters

```typescript
// Dashboard global filters
interface DashboardFiltersProps {
  filters: FilterDefinition[];
  values: GlobalFilters;
  onChange: (values: GlobalFilters) => void;
}

export const DashboardFilters: React.FC<DashboardFiltersProps> = ({
  filters,
  values,
  onChange,
}) => {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className={styles.dashboardFilters}>
      <div className={styles.filterBar}>
        {filters.map(filter => (
          <DashboardFilter
            key={filter.id}
            filter={filter}
            value={values[filter.id]}
            onChange={(value) => onChange({ ...values, [filter.id]: value })}
          />
        ))}

        <Button
          variant="ghost"
          size="sm"
          onClick={() => setExpanded(!expanded)}
        >
          <FilterIcon /> {expanded ? 'Hide' : 'More'} Filters
        </Button>

        {Object.keys(values).length > 0 && (
          <Button
            variant="ghost"
            size="sm"
            onClick={() => onChange({})}
          >
            Clear All
          </Button>
        )}
      </div>

      {expanded && (
        <div className={styles.expandedFilters}>
          {filters.map(filter => (
            <ExpandedFilter
              key={filter.id}
              filter={filter}
              value={values[filter.id]}
              onChange={(value) => onChange({ ...values, [filter.id]: value })}
            />
          ))}
        </div>
      )}
    </div>
  );
};

// Individual dashboard filter
const DashboardFilter: React.FC<{
  filter: FilterDefinition;
  value: any;
  onChange: (value: any) => void;
}> = ({ filter, value, onChange }) => {
  if (filter.type === 'date_range') {
    return (
      <DateRangeFilter
        label={filter.label}
        value={value}
        onChange={onChange}
      />
    );
  }

  if (filter.type === 'select') {
    return (
      <SelectFilter
        label={filter.label}
        options={filter.options}
        value={value}
        onChange={onChange}
      />
    );
  }

  return null;
};
```

---

## 6. Responsive Design

### 6.1 Breakpoint Strategy

```
┌────────────────────────────────────────────────────────────────────────────┐
│                         RESPONSIVE BREAKPOINTS                             │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  Mobile (320px - 767px)                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │ • Stacked layout                                                     │ │
│  │ • Single column reports                                              │ │
│  │ • Full-width tables with horizontal scroll                           │ │
│  │ • Simplified filters (collapsible)                                   │ │
│  │ • Tab-based navigation                                               │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│  Tablet (768px - 1023px)                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │ • Side-by-side preview on larger tablets                             │ │
│  │ • Collapsible sidebar                                               │ │
│  │ • Multi-column tables                                                │ │
│  │ • Dashboard grid: 2 columns                                          │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│  Desktop (1024px+)                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │ • Fixed sidebar + preview                                           │ │
│  │ • Full feature set                                                   │ │
│  │ • Dashboard grid: 3-4 columns                                        │ │
│  │ • Inline SQL preview                                                 │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

### 6.2 Responsive Components

```typescript
// Responsive report preview
const ResponsiveReportPreview: React.FC<{
  data: QueryResult;
  config: QueryConfiguration;
}> = ({ data, config }) => {
  const isMobile = useMediaQuery('(max-width: 767px)');
  const isTablet = useMediaQuery('(max-width: 1023px)');

  if (isMobile) {
    return <MobileReportView data={data} config={config} />;
  }

  if (isTablet) {
    return <TabletReportView data={data} config={config} />;
  }

  return <DesktopReportView data={data} config={config} />;
};

// Mobile-optimized table view
const MobileReportView: React.FC<{
  data: QueryResult;
  config: QueryConfiguration;
}> = ({ data, config }) => {
  return (
    <div className={styles.mobileView}>
      {/* Summary cards for key metrics */}
      <div className={styles.summaryCards}>
        {data.columns
          .filter(c => c.type === 'measure')
          .slice(0, 3)
          .map(col => (
            <SummaryCard
              key={col.name}
              label={col.displayName}
              value={sumColumn(data, col.name)}
              format={col.format}
            />
          ))}
      </div>

      {/* Card-based row display */}
      <div className={styles.rowCards}>
        {data.rows.map((row, i) => (
          <RowCard
            key={i}
            data={row}
            columns={data.columns}
            onTap={() => {/* show detail modal */}}
          />
        ))}
      </div>

      {/* Load more */}
      {data.hasMore && (
        <Button
          variant="secondary"
          block
          onPress={() => {/* load more */}}
        >
          Load More
        </Button>
      )}
    </div>
  );
};

// Card-based row display for mobile
const RowCard: React.FC<{
  data: any;
  columns: Column[];
  onTap: () => void;
}> = ({ data, columns, onTap }) => {
  const titleColumn = columns.find(c => c.type === 'dimension') || columns[0];
  const valueColumns = columns.filter(c => c.type === 'measure');

  return (
    <Touchable onPress={onTap}>
      <View style={styles.rowCard}>
        <Text style={styles.rowTitle}>{data[titleColumn.name]}</Text>

        {valueColumns.map(col => (
          <View key={col.name} style={styles.rowValue}>
            <Text style={styles.rowValueLabel}>{col.displayName}</Text>
            <Text style={styles.rowValueText}>
              {formatValue(data[col.name], col.format)}
            </Text>
          </View>
        ))}
      </View>
    </Touchable>
  );
};
```

---

## 7. Accessibility

### 7.1 Keyboard Navigation

```typescript
// Keyboard navigation for report builder
export const useReportKeyboardNav = () => {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ctrl/Cmd + S: Save
      if ((e.ctrlKey || e.metaKey) && e.key === 's') {
        e.preventDefault();
        // Trigger save
      }

      // Ctrl/Cmd + Enter: Run report
      if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        e.preventDefault();
        // Trigger run
      }

      // Escape: Cancel/close dialog
      if (e.key === 'Escape') {
        // Close any open dialogs
      }

      // Tab: Navigate between fields
      // Arrow keys: Navigate within lists
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, []);
};

// Keyboard-accessible filter builder
const AccessibleFilterBuilder: React.FC<FilterBuilderProps> = (props) => {
  const [focusedIndex, setFocusedIndex] = useState(0);
  const filters = props.filters.and || [];

  const handleKeyDown = (e: React.KeyboardEvent, index: number) => {
    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setFocusedIndex(Math.min(index + 1, filters.length - 1));
        break;
      case 'ArrowUp':
        e.preventDefault();
        setFocusedIndex(Math.max(index - 1, 0));
        break;
      case 'Delete':
        if (e.altKey) {
          props.onRemove(index);
        }
        break;
    }
  };

  return (
    <div role="list" aria-label="Report filters">
      {filters.map((filter, index) => (
        <div
          key={index}
          role="listitem"
          tabIndex={focusedIndex === index ? 0 : -1}
          onKeyDown={(e) => handleKeyDown(e, index)}
          aria-label={`Filter ${index + 1}: ${filter.field} ${filter.operator}`}
        >
          {/* Filter content */}
        </div>
      ))}
    </div>
  );
};
```

### 7.2 Screen Reader Support

```typescript
// Screen reader announcements
const useAnnouncer = () => {
  const announce = (message: string, priority: 'polite' | 'assertive' = 'polite') => {
    const announcement = document.createElement('div');
    announcement.setAttribute('role', 'status');
    announcement.setAttribute('aria-live', priority);
    announcement.setAttribute('aria-atomic', 'true');
    announcement.className = 'sr-only';
    announcement.textContent = message;

    document.body.appendChild(announcement);
    setTimeout(() => document.body.removeChild(announcement), 1000);
  };

  return { announce };
};

// Accessible visualization
const AccessibleChart: React.FC<VisualizationProps> = (props) => {
  const { announce } = useAnnouncer();

  const handleDrillDown = (dimension: string, value: any) => {
    announce(`Drilling down into ${dimension}: ${value}`);
    props.onDrillDown?.(dimension, value);
  };

  // Generate data table for screen readers
  const dataTable = useMemo(() => {
    return generateDataTable(props.data, props.config);
  }, [props.data, props.config]);

  return (
    <div>
      <div role="img" aria-label={generateChartDescription(props.data, props.config)}>
        {/* Chart rendered here */}
      </div>

      {/* Hidden data table for screen readers */}
      <div className="sr-only">
        <table>
          <caption>{props.config.title || 'Report data'}</caption>
          <thead>
            <tr>
              {dataTable.columns.map(col => (
                <th key={col}>{col}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {dataTable.rows.map((row, i) => (
              <tr key={i}>
                {row.map((cell, j) => (
                  <td key={j}>{cell}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

// Generate text description of chart
function generateChartDescription(data: QueryResult, config: ChartConfig): string {
  const type = config.type;
  const labels = data.labels?.slice(0, 5) || [];
  const values = data.datasets?.[0]?.data?.slice(0, 5) || [];

  if (type === 'bar' || type === 'column') {
    return `Bar chart showing ${labels.join(', ')}. ` +
           `Highest value is ${Math.max(...values)} for ${labels[values.indexOf(Math.max(...values))]}.`;
  }

  if (type === 'line') {
    return `Line chart showing trend over ${labels.length} periods. ` +
           `Starting at ${values[0]} and ending at ${values[values.length - 1]}.`;
  }

  if (type === 'pie') {
    return `Pie chart with ${labels.length} segments. ` +
           `Largest segment is ${labels[0]} at ${values[0]}.`;
  }

  return 'Chart visualization';
}
```

---

## Summary

The report builder provides an intuitive, powerful interface for creating custom reports:

| Component | Purpose |
|-----------|---------|
| **Builder Layout** | Split-pane: sidebar for config, preview for results |
| **Field Picker** | Drag-drop field selection with search |
| **Filter Builder** | Visual filter construction with type-aware inputs |
| **Group By** | Dimension-based grouping with time granularity |
| **Visualizations** | Table, bar, line, pie, KPI, area, heatmap |
| **Dashboards** | Multi-widget, grid-based layout |
| **Global Filters** | Cross-widget filter propagation |
| **Responsive Design** | Mobile-optimized, tablet-adaptive, desktop-full |
| **Accessibility** | Keyboard nav, screen reader support |

**Key Takeaways:**
- Use drag-and-drop for intuitive field selection
- Provide smart defaults based on data types
- Show chart type recommendations
- Support drill-down from visualizations
- Enable global filters on dashboards
- Optimize for mobile with card-based layouts
- Ensure full keyboard navigation
- Provide screen reader descriptions

---

**Related:** [03: Export Deep Dive](./REPORTING_03_EXPORT_DEEP_DIVE.md) → Excel, CSV, PDF export formats
