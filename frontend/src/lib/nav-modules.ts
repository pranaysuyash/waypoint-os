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

/**
 * Durable navigation model for the Agency OS.
 *
 * Sections encode the full agency lifecycle — not just what exists today.
 * Modules that are not yet ready are marked `enabled: false` and rendered
 * as grayed-out placeholders with a "Soon" badge, so the shell communicates
 * the product's operating model rather than only the current implementation surface.
 *
 * To enable a module, flip `enabled: true`. The route and page must exist
 * before enabling.
 *
 * Architectural note:
 * - Routes represent product modules, not personas. No /owner/* or /agent/* prefixes.
 * - New Inquiry is an action, not a place. It will eventually move to a shell header CTA.
 * - /workbench is a dev surface, not a durable user-facing module. Not exposed in nav.
 */
export const NAV_SECTIONS: NavSection[] = [
  {
    label: 'COMMAND',
    items: [
      { href: '/overview', label: 'Overview', icon: 'LayoutDashboard', description: 'Command center and trip health', enabled: true },
      { href: '/inbox', label: 'Inbox', icon: 'Inbox', description: 'Sort and prioritize new inquiries', enabled: true },
      { href: '/reviews', label: 'Approval Queue', icon: 'ClipboardCheck', description: 'Approve high-risk quotes, changes, and exceptions', enabled: true },
    ],
  },
  {
    label: 'PIPELINE',
    items: [
      { href: '/trips', label: 'Trips', icon: 'Layers', description: 'Active trips in progress', enabled: true },
      { href: '/quotes', label: 'Quotes', icon: 'FileText', description: 'Commercial proposal objects', enabled: false },
      { href: '/bookings', label: 'Bookings', icon: 'CalendarCheck', description: 'Confirmed operational records', enabled: false },
    ],
  },
  {
    label: 'OPERATIONS',
    items: [
      { href: '/documents', label: 'Documents', icon: 'FileText', description: 'Passports, visas, vouchers, insurance', enabled: false },
      { href: '/payments', label: 'Payments', icon: 'DollarSign', description: 'Collection and milestones', enabled: false },
      { href: '/suppliers', label: 'Suppliers', icon: 'Briefcase', description: 'Preferred supplier relationships', enabled: false },
    ],
  },
  {
    label: 'INTELLIGENCE',
    items: [
      { href: '/insights', label: 'Insights', icon: 'BarChart2', description: 'Monitor quality, throughput, and conversion', enabled: true },
      { href: '/audit', label: 'Audit', icon: 'Search', description: 'Trip quality and compliance audit', enabled: false },
      { href: '/knowledge', label: 'Knowledge Base', icon: 'BookOpen', description: 'Agency memory and playbooks', enabled: false },
    ],
  },
  {
    label: 'ADMIN',
    items: [
      { href: '/settings', label: 'Settings', icon: 'Settings', description: 'Agency profile, autonomy, and operations', enabled: true },
    ],
  },
];
