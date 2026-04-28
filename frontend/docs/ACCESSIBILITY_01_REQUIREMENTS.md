# Accessibility — Standards, Compliance & Requirements

> Research document for accessibility standards, legal requirements, and inclusive travel platform needs.

---

## Key Questions

1. **What accessibility standards apply to a travel platform (WCAG, ADA, RPWD Act)?**
2. **What are the legal obligations for digital accessibility in India and target markets?**
3. **How do accessibility requirements differ between the agent workbench and customer-facing surfaces?**
4. **What's the cost of accessibility compliance vs. the cost of exclusion?**
5. **How do we test accessibility across our stack (React components, PDFs, emails)?**

---

## Research Areas

### Regulatory Landscape

| Regulation | Region | Scope | Requirements |
|-----------|--------|-------|--------------|
| RPWD Act 2016 | India | Digital + physical | Reasonable accommodation, equal access |
| WCAG 2.1 AA | Global (standard) | Web content | Perceivable, operable, understandable, robust |
| ADA Title III | US | Public accommodations | Accessible digital services |
| European Accessibility Act | EU | Products & services | Accessibility requirements from June 2025 |
| Section 508 | US (federal) | Government-adjacent | WCAG 2.0 AA minimum |
| AODA | Ontario, Canada | Organizations | WCAG 2.0 AA, moving to 2.1 AA |

**India-specific (RPWD Act):**
- Applies to both government and private entities
- "Reasonable accommodation" for persons with disabilities
- Benchmarks to WCAG standards for digital platforms
- Travel is specifically mentioned as a service that must be accessible
- Penalties for non-compliance

### WCAG 2.1 AA Checklist (Priority Items for Travel Platform)

```typescript
interface AccessibilityAuditItem {
  guideline: string;           // WCAG criterion (e.g., "1.1.1")
  level: 'A' | 'AA' | 'AAA';
  category: AccessibilityCategory;
  description: string;
  applicableComponents: string[];
  currentStatus: 'pass' | 'fail' | 'partial' | 'not_tested';
  remediationEffort: 'low' | 'medium' | 'high';
}

type AccessibilityCategory =
  | 'perceivable'       // Text alternatives, captions, adaptable content
  | 'operable'          // Keyboard, timing, navigation, input
  | 'understandable'    // Readable, predictable, input assistance
  | 'robust';           // Compatible with assistive technologies
```

### Agent Workbench Accessibility

**The workbench is an internal tool used by agents — many of whom may have disabilities:**

- Keyboard navigation for all workbench actions (no mouse required)
- Screen reader compatible panel layout
- Sufficient color contrast in dark and light themes
- Focus management when panels open/close
- Form field labels and error messages accessible to screen readers
- Spine run progress announcements for screen readers
- Reduced motion option for animations/transitions

### Customer-Facing Accessibility

**Customer surfaces include web, mobile web, email, and PDF documents:**

- Responsive design that works with zoom levels up to 400%
- Alt text for all hotel/destination images
- Form inputs with visible labels and ARIA attributes
- Skip navigation links
- Accessible date pickers and dropdown menus
- PDF itineraries tagged for screen readers (PDF/UA)
- Email templates with accessible HTML (tables for layout avoided)
- Video content with captions
- High-contrast mode for customers with low vision

---

## Open Problems

1. **Complex interactive components** — The itinerary builder, map views, and timeline are highly visual/interactive. Making these fully accessible requires significant effort beyond basic compliance.

2. **Third-party content accessibility** — Hotel images, supplier descriptions, and review content from external sources may not be accessible. We can't control their alt text or quality.

3. **PDF accessibility** — Generated itineraries and quotes as PDFs need proper tagging, reading order, and alt text. Most PDF generators don't produce accessible output by default.

4. **Accessibility testing automation** — Automated tools (axe, Lighthouse) catch ~30% of issues. Manual testing with screen readers (NVDA, VoiceOver) is essential but time-consuming.

5. **Assistive technology compatibility** — Screen readers, voice control, switch access, and magnifiers all interact differently with web applications. Testing across all is impractical but important.

---

## Next Steps

- [ ] Run automated accessibility audit on current workbench (axe-core, Lighthouse)
- [ ] Map WCAG 2.1 AA criteria to specific components and pages
- [ ] Research accessible component libraries (Radix, Headless UI, Reach UI)
- [ ] Study PDF/UA generation for accessible document output
- [ ] Create accessibility testing checklist for PR reviews
- [ ] Research assistive technology testing workflows (screen reader, keyboard-only)
