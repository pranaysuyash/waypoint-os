# Privacy Redaction Gate Update

Date: 2026-05-12  
Gate: `privacy-redaction-enforced`

## Outcome

Gate moved to complete in [`src/lib/nav-modules.ts`](../../src/lib/nav-modules.ts).

## Implemented Controls

1. Central privacy control module:
   - [`src/lib/privacy-controls.ts`](../../src/lib/privacy-controls.ts)
   - Debug JSON visibility is policy-gated (`NEXT_PUBLIC_ALLOW_DEBUG_JSON=true` required).
   - Audit export redaction is default-on (`NEXT_PUBLIC_ALLOW_RAW_AUDIT_EXPORT` opt-out only).

2. Audit export redaction:
   - [`src/hooks/useFieldAuditLog.ts`](../../src/hooks/useFieldAuditLog.ts)
   - `exportChanges()` now emits redacted payload by default.

3. Debug bundle protection:
   - [`src/components/workspace/panels/OutputPanel.tsx`](../../src/components/workspace/panels/OutputPanel.tsx)
   - Technical JSON block stays hidden unless explicit secure-env toggle is set.

## Verification

1. `npm test -- "src/components/workspace/panels/__tests__/OutputPanel.test.tsx" --reporter=dot`
2. `npm test -- "src/hooks/__tests__/useFieldAuditLog.contract-surface.test.tsx" --reporter=dot`
3. `npm test -- "src/lib/__tests__/nav-modules.test.ts" --reporter=dot`

## Notes

- This closes the privacy gate for current frontend surfaces without introducing a parallel path.
- At the time this gate was completed, additional `/documents` gates remained. See latest enablement state in [DOCUMENTS_MODULE_ENABLEMENT_CONTRACT_2026-05-11.md](./DOCUMENTS_MODULE_ENABLEMENT_CONTRACT_2026-05-11.md).
