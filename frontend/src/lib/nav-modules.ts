export interface NavItem {
  href: string;
  label: string;
  icon: string;
  description: string;
  enabled: boolean;
}

export interface NavSection {
  label: string;
  items: NavItem[];
}

export interface RolloutGate {
  id: string;
  description: string;
  complete: boolean;
}

/**
 * Explicit rollout gates for enabling /documents as a top-level module.
 * Keep this as the single source of truth for nav enablement readiness.
 */
export const DOCUMENTS_MODULE_ROLLOUT_GATES: RolloutGate[] = [
  {
    id: 'ops-path-stable',
    description: 'Ops panel canonical document workflow is stable and verified.',
    complete: true,
  },
  {
    id: 'privacy-redaction-enforced',
    description: 'Redaction and secure-mode controls are enforced for debug/export surfaces.',
    complete: true,
  },
  {
    id: 'route-level-shell-ready',
    description: '/documents route has product-ready shell UX backed by canonical contracts.',
    complete: true,
  },
  {
    id: 'contract-regression-suite',
    description: 'Integration tests cover document upload/review/extract/apply across role paths.',
    complete: true,
  },
];

export function isDocumentsModuleEnabled(): boolean {
  return DOCUMENTS_MODULE_ROLLOUT_GATES.every((gate) => gate.complete);
}

/**
 * Explicit rollout gates for the mature-module surfaces (R-13). These routes
 * exist and are wired to real trip-data hooks, but their product completeness
 * varies. Making enablement gate-controlled (rather than a hardcoded flag)
 * keeps the intended rollout state visible and truthful.
 */
export const MODULE_ROLLOUT_GATES: Record<string, RolloutGate[]> = {
  quotes: [
    { id: 'route-wired', description: 'Quotes route exists and reads live trip data.', complete: true },
    { id: 'value-surface-complete', description: 'Quote value cards backed by real fields and versioned proposals.', complete: true },
  ],
  bookings: [
    { id: 'route-wired', description: 'Bookings route exists and reads live trip data.', complete: true },
    { id: 'value-surface-complete', description: 'Booking value cards backed by real fields and operational records.', complete: true },
  ],
  suppliers: [
    { id: 'route-wired', description: 'Suppliers route exists and reads live trip data.', complete: true },
    { id: 'value-surface-complete', description: 'Supplier intelligence backed by real directory, contracts, and SLAs.', complete: true },
  ],
  knowledge: [
    { id: 'route-wired', description: 'Knowledge route exists.', complete: true },
    { id: 'value-surface-complete', description: 'Knowledge base is a real agency-memory surface with semantic search and playbooks.', complete: true },
  ],
};

export function isModuleEnabled(moduleKey: string): boolean {
  const gates = MODULE_ROLLOUT_GATES[moduleKey];
  if (!gates) return true;
  return gates.every((gate) => gate.complete);
}

/**
 * Durable navigation model for the Agency OS.
 *
 * Sections encode the full agency lifecycle - not just what exists today.
 * Modules that are not yet ready are marked `enabled: false` and rendered
 * as grayed-out placeholders with a "Soon" badge, so the shell communicates
 * the product's operating model rather than only the current implementation surface.
 *
 * To enable a module, flip `enabled: true`. The route and page must exist
 * before enabling.
 *
 * Architectural note:
 * - Routes represent product modules, not personas. No /owner/* or /agent/* prefixes.
 * - Actions like "New Inquiry" do not belong in `NAV_SECTIONS`; they should live as shell CTAs.
 * - /workbench is not a durable user-facing module name. If the New Inquiry CTA routes there
 *   temporarily, keep the user-facing label as "New Inquiry" until `/inquiries/new` exists.
 */
export const NAV_SECTIONS: NavSection[] = [
  {
    label: 'COMMAND',
    items: [
      { href: '/overview', label: 'Overview', icon: 'LayoutDashboard', description: 'Command center and trip health', enabled: true },
      { href: '/inbox', label: 'Lead Inbox', icon: 'Inbox', description: 'Sort and prioritize new inquiries', enabled: true },
      { href: '/reviews', label: 'Quote Review', icon: 'ClipboardCheck', description: 'Review high-risk quotes, changes, and exceptions', enabled: true },
    ],
  },
  {
    label: 'PLANNING',
    items: [
      { href: '/trips', label: 'Trips in Planning', icon: 'Layers', description: 'Active trip planning and execution', enabled: true },
      { href: '/quotes', label: 'Quotes', icon: 'FileText', description: 'Commercial proposals and quote versions', enabled: isModuleEnabled('quotes') },
      { href: '/bookings', label: 'Bookings', icon: 'CalendarCheck', description: 'Confirmed operational records', enabled: isModuleEnabled('bookings') },
    ],
  },
  {
    label: 'OPERATIONS',
    items: [
      { href: '/documents', label: 'Documents', icon: 'FileText', description: 'Passports, visas, vouchers, insurance', enabled: isDocumentsModuleEnabled() },
      { href: '/payments', label: 'Payments', icon: 'DollarSign', description: 'Collections, milestones, and payment risk', enabled: true },
      { href: '/suppliers', label: 'Suppliers', icon: 'Briefcase', description: 'Preferred suppliers, rates, and reliability notes', enabled: isModuleEnabled('suppliers') },
    ],
  },
  {
    label: 'INTELLIGENCE',
    items: [
      { href: '/insights', label: 'Insights', icon: 'BarChart2', description: 'Quality, throughput, conversion, and margin intelligence', enabled: true },
      { href: '/audit', label: 'Audit', icon: 'Search', description: 'Trip fit, waste, and compliance audit', enabled: true },
      { href: '/knowledge', label: 'Knowledge Base', icon: 'BookOpen', description: 'Agency memory, playbooks, and learned preferences', enabled: isModuleEnabled('knowledge') },
    ],
  },
  {
    label: 'ADMIN',
    items: [
      { href: '/settings', label: 'Settings', icon: 'Settings', description: 'Agency profile, rules, users, and preferences', enabled: true },
      { href: '/seasons', label: 'Seasonal Campaigns', icon: 'CalendarDays', description: 'Campaign-level seasonal planning and launch control', enabled: true },
    ],
  },
];
