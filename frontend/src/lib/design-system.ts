export const STATE_COLORS = {
  PROCEED_TRAVELER_SAFE: "state-green",
  PROCEED_INTERNAL_DRAFT: "state-amber",
  BRANCH_OPTIONS: "state-amber",
  STOP_NEEDS_REVIEW: "state-red",
  ASK_FOLLOWUP: "state-blue",
} as const;

export type StateColorKey = keyof typeof STATE_COLORS;

export interface NavItem {
  label: string;
  href: string;
  description: string;
}

export interface NavSection {
  label: string;
  items: NavItem[];
}

export const PRODUCT_COPY = {
  name: "Waypoint OS",
  shortName: "Waypoint",
  tagline: "Decision intelligence for travel operations",
  mission: "Convert messy travel requests into precise, safe, and actionable decisions.",
} as const;

export const NAV_SECTIONS: NavSection[] = [
  {
    label: "Operate",
    items: [
      {
        label: "Inbox",
        href: "/inbox",
        description: "Triage and prioritize incoming demand",
      },
      {
        label: "Trip Workspace",
        href: "/workbench",
        description: "Inspect trip details, quote status, options, and review",
      },
    ],
  },
  {
    label: "Govern",
    items: [
      {
        label: "Owner Reviews",
        href: "/owner/reviews",
        description: "Approve high-risk and exception decisions",
      },
      {
        label: "Owner Insights",
        href: "/owner/insights",
        description: "Monitor quality, throughput, and conversion",
      },
    ],
  },
];

export function isRouteActive(pathname: string, href: string): boolean {
  if (href === "/") {
    return pathname === "/";
  }

  return pathname === href || pathname.startsWith(`${href}/`);
}

export function getPageTitle(pathname: string): string {
  for (const section of NAV_SECTIONS) {
    for (const item of section.items) {
      if (isRouteActive(pathname, item.href)) {
        return item.label;
      }
    }
  }

  if (pathname === "/") {
    return "Command Overview";
  }

  return "Workspace";
}