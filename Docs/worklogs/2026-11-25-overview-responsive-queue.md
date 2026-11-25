# Responsive Overview enquiry queue

25 November 2026 · Authenticated local demo · Uncommitted

The screenshot was reproduced at 854 CSS pixels. The Action Required item used a viewport breakpoint to reserve a column for the action links. Its examples sat inside the other column and split again at the same breakpoint. When the 220px sidebar appeared at 768px, each enquiry tile had only 53px. At 854px the tiles had 96px each. The baseline geometry regression failed at 10 of 14 widths, even though the document did not overflow horizontally.

The summary and action links now wrap according to the space inside the card. The example grid spans the card and uses a 16rem minimum for side-by-side tiles. At tighter widths each tile occupies its own row. The diagnostic text, pending chips, next action, example titles, metadata and links are preserved. The canonical component is also synced into the isolated 3017 demo copy. No data, channel, auth or service configuration changes were made.

## Verification

- An authenticated Chrome test resized one page through 360, 390, 430, 639, 640, 767, 768, 820, 854, 1024, 1280, 1366, 1440 and 1920 CSS pixels. It checked internal card and tile widths, page overflow, both action links, individual tile destinations and displayed travel, party size, assignment and reference details. It also clicked Open oldest enquiry and Open all enquiries and verified their destinations.
- The exact geometry assertion failed on baseline source and passed with the fix (S2). Chrome on the seeded local demo provides local browser and integration evidence. Physical-device and hosted behavior remain unverified.
- Matched card captures, before on the left and after on the right, were inspected at [390](../evidence/overview-responsive-2026-11-25/comparison-390.png), [768](../evidence/overview-responsive-2026-11-25/comparison-768.png), [854](../evidence/overview-responsive-2026-11-25/comparison-854.png), [1024](../evidence/overview-responsive-2026-11-25/comparison-1024.png), and [1440](../evidence/overview-responsive-2026-11-25/comparison-1440.png). The fixed mobile navigation is visible in the phone crop.
- All 62 focused Overview tests and targeted ESLint passed. Full frontend TypeScript reported an out-of-scope overload error at ChannelMessagesPanel.test.tsx:203. The Overview component and responsive spec produced no TypeScript diagnostics.

## Responsive review rule

Check common phone, tablet and desktop widths when changing a rendered layout, plus both sides of breakpoints that alter the shell or component layout. Resize the same page and verify content, interaction, and component-level fit. Preserve features and data through the comparison.
