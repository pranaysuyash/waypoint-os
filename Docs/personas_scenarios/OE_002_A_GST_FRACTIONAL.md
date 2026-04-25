# OE-002-A: The 'GST-Fractional' Group

**Persona**: Family Coordinator (S2) + Junior Agent (P3)
**Scenario**: A multi-family group booking requires the agency to split costs and generate three distinct invoices, one of which must be a corporate GST-compliant invoice for an Indian business.

---

## 1. Situation

- **Travelers**: 
  - Group A: The Mehtas (India-based, 4 pax).
  - Group B: The Smiths (UK-based, 2 pax).
  - Group C: The Johnsons (US-based, 2 pax).
- **Booking**: A 10-day luxury stay in a shared villa ($20,000) + separate flights for each group.
- **Problem**: 
  - The Mehtas need a **GST Invoice** with their company's tax ID to claim a business expense.
  - The Smiths need a **VAT-inclusive** invoice.
  - The agency must ensure the "Shared Villa" cost is split exactly 50/25/25.

---

## 2. What the System Should Do

### Step 1: Sub-Group Definition
- **System Action**: Allow the agent to create three `sub_groups` within the `CanonicalPacket`.
- **Assignment**: Drag-and-drop travelers into their respective groups.

### Step 2: Cost Attribution (The Split)
- **Direct Costs**: Flight for Group A assigned 100% to Group A.
- **Shared Costs**: 
  - Villa ($20,000) split:
    - Group A: $10,000 (50%).
    - Group B: $5,000 (25%).
    - Group C: $5,000 (25%).
- **Logic**: Use the `weight` field to handle the 50/25/25 split.

### Step 3: Tax-Aware Invoice Generation
- **Group A (India)**:
  - Base: $10,000.
  - GST (18% on service fee component).
  - TCS (20% on international remittance component).
  - **Output**: Formal GST Invoice with `GSTIN` and `Address`.
- **Group B (UK)**:
  - Base: $5,000.
  - VAT (20% if applicable).
- **Group C (US)**:
  - Base: $5,000.
  - No tax ID required.

---

## 3. Operational Logic & Rules

- **Rule 1**: The sum of all fractional invoices MUST equal the total supplier cost + agency service fee.
- **Rule 2**: If a `sub_group` is marked as `Corporate_India`, the system must block "Ready-for-Send" if the GST ID is missing or invalid.
- **Rule 3**: Any change to the villa price must auto-recalculate all three fractional invoices proportionally.

---

## 4. Success Criteria

- **Audit**: Zero variance between `Total_Invoiced` and `Total_Cost`.
- **Compliance**: Group A's invoice passes an Indian GST validator.
- **UX**: The "Split Cost Canvas" reduces agent time for multi-party reconciliation by 80%.

---

## 5. Case Study Execution Plan (Future)

- **Input**: A `CanonicalPacket` with 3 `sub_groups`.
- **System Trace**: Verify the generation of 3 separate PDF invoices.
- **Verification**: Check the `AuditStore` for the split-payment ledger entries.
