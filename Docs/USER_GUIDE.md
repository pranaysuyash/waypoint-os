# User Guide

## Capturing Calls

### Overview

The Call Capture feature allows you to quickly record phone calls or inquiries from customers and create a Trip record that you can work with immediately. This is useful for capturing initial customer intent when on the phone, then following up with structured details after the call.

### How to Capture a Call

1. **Open the IntakePanel**
   - Navigate to a customer's workspace (or create a new workspace)
   - Look for the "Capture Call" button in the top-right area of the IntakePanel

2. **Fill in the Capture Form**
   - **Raw Note** (required): Write down the customer's stated travel intent in your own words
     - Example: "Customer wants a 2-week trip to Europe next summer, flexible dates, interested in Rome and Paris"
     - This is typically captured while you're on the phone with the customer
   
   - **Owner Notes** (optional): Add your own notes about the call
     - Example: "Customer seemed interested in art museums, mentioned budget around $5k per person"
     - Use this to capture impressions, follow-up items, or context that won't go in the raw note
   
   - **Follow-up Due Date** (optional): When you promised to follow up with the customer
     - Default: 48 hours from now
     - You can change this if you promised a different timeline
     - Example: If the call is on Monday and you promised to follow up Wednesday, set it to Wednesday's date

3. **Save the Capture**
   - Click "Save" to create the Trip and open the workspace
   - The workspace will open with your new Trip ready for editing
   - Click "Cancel" to close the form without saving (form data is cleared)

### What Happens After You Save

1. A new Trip record is created with:
   - The `raw_note` from your input
   - The `agentNotes` from your owner notes (if provided)
   - The `follow_up_due_date` you specified (defaults to 48 hours)
   - A new, unique ID
   - A creation timestamp

2. The workspace opens automatically with the Trip ready for:
   - Adding structured details (destination, dates, budget, etc.)
   - Attaching documents
   - Viewing your notes
   - Following up with the customer

3. You can continue working on the Trip immediately or come back to it later

### What Information Is Captured

When you submit a call capture, the following information is stored in the Trip:

| Field | Captured From | Required? | Details |
|-------|---------------|-----------|---------|
| `raw_note` | Raw Note input | Yes | Customer's stated travel intent |
| `agentNotes` | Owner Notes input | No | Your notes from the call |
| `follow_up_due_date` | Follow-up Due Date picker | No | Default is 48 hours from now |
| `id` | Auto-generated | System | Unique trip identifier |
| `createdAt` | Current time | System | When the trip was created |

### Keyboard Shortcuts

- **Tab**: Navigate between form fields
- **Shift+Tab**: Navigate to previous field
- **Enter**: Submit the form (when focus is on Save button)
- **Escape**: Cancel and close the form

### Tips and Best Practices

1. **Capture Details While Fresh**
   - Fill in the form while the customer is still on the phone or immediately after
   - Don't wait—details get fuzzy fast
   - If you forget something, you can add it in Owner Notes later

2. **Be Clear in Raw Note**
   - Don't use shorthand you won't remember later
   - Include key details: destination(s), rough dates, party size if mentioned
   - Example good: "3 adults, 2 kids. Europe summer 2025. Rome, Florence, Venice preferred."
   - Example bad: "wants Europe trip"

3. **Use Owner Notes for Context**
   - Capture your impressions: Which customer type? Interest level? Special requests?
   - Note any constraints: "Budget-conscious", "Last-minute decision needed by Friday"
   - Document decisions: "Told them flights out of SFO are cheapest"

4. **Set Follow-up Dates Realistically**
   - Default 48 hours works for most calls
   - Adjust if you made a specific promise ("I'll have quotes by Friday")
   - System will remind you when follow-up is due

5. **After Capture**
   - Workspace opens immediately—don't close it yet
   - Add structured details while conversation context is fresh
   - Save progress frequently

### Troubleshooting

**Problem**: Raw Note field is empty but I thought I filled it in
- **Solution**: The field is required. If you didn't fill it, the form won't submit. Try again.

**Problem**: I set a follow-up date but it's not showing in the workspace
- **Solution**: The date is stored internally. You can view it in the Trip details or edit it later via PATCH if needed.

**Problem**: Submitted the form but nothing happened
- **Solution**: Check that the Raw Note field has text. If it's empty, the form won't submit. Also check browser console for any errors.

### Related Topics

- **Trip Workspace**: Once a call is captured, you work with it in the Trip Workspace (see Trip Workspace Guide)
- **Following Up**: Use the follow-up due date to remind yourself when to reach out (future feature)
- **Developer Integration**: See `Docs/DEVELOPMENT.md` for technical details on the PATCHABLE_FIELDS pattern

---

**Last Updated**: 2026-04-29  
**Feature**: Call Capture (Unit-1)  
**Status**: Launch Ready
