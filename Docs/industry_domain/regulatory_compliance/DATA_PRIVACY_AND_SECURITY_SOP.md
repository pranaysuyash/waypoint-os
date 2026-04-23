# Domain Knowledge: Data Privacy & Security SOP

**Category**: Global Regulatory & Compliance  
**Focus**: GDPR, CCPA, PII protection, and secure document handling.

---

## 1. Defining PII in Travel

Travel agents handle some of the most sensitive Personally Identifiable Information (PII) available.

### Critical Data Points
- **Identity**: Passport Numbers, Aadhaar/SSN, Date of Birth.
- **Financial**: Credit Card Numbers, CVV, Billing Addresses.
- **Health/Bio**: Vaccination records, dietary requirements (religious/health), and medical assistance needs.
- **Location**: Real-time flight tracking and hotel room numbers (high-risk for high-profile clients).

---

## 2. Regulatory Frameworks (The "Shield")

### GDPR (EU) / CCPA (California) / DPB (India)
- **Principle**: "Data Minimization." Only collect what is absolutely necessary for the booking.
- **SOP**: PII must be encrypted at rest and in transit. Access must be restricted to the "Booking Agent" only.

### PCI-DSS (Payment Card Industry Data Security Standard)
- **Rule**: Never store CVV codes after authorization.
- **Rule**: Mask credit card numbers in the GDS (e.g., `************1234`).
- **SOP**: Use a "Secure Payment Link" (e.g., Stripe, Razorpay) instead of asking the client to text/email their card details.

---

## 3. Secure Document Handling

### Passport Management
- **The "Vault"**: Passports should be stored in a secure, encrypted CRM module, not as email attachments or in local folders.
- **Deletion Policy**: Delete passport copies once the trip is complete and the "Visa Audit" period has passed.

### The "Assistant" Risk
- **Issue**: EAs often send PII via unencrypted WhatsApp or email.
- **SOP**: Redirect all PII submission to a "Secure Portal."

---

## 4. Emergency Data Access

### Duty of Care Sharing
- **Logic**: In a crisis (e.g., a coup or earthquake), the agency may need to share the traveler's location with government authorities or "Duty of Care" providers (e.g., International SOS).
- **SOP**: Ensure the "Traveler Agreement" includes a clause for emergency data sharing.

---

## 5. Proposed Scenarios
- **Data Breach**: An agent's email is compromised, and 50 passport scans are leaked. The agency must execute the "Notification SOP."
- **Right to be Forgotten**: A former client requests that all their historical travel data be deleted. The agent must purge the CRM while maintaining tax records.
- **PCI Failure**: An agent saves a full credit card number (including CVV) in the GDS remarks field. This must be detected and redacted.
