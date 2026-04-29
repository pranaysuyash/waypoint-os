# Rendered Design System Audit Report

**Date:** 2026-04-28
**Base URL:** http://localhost:3000
**Pages Audited:** /, /login, /inbox, /workspace, /settings, /itinerary-checker

## 1. CSS Custom Property Audit (vs DESIGN.md)

| Variable | Expected | Actual | Match |
|---|---|---|---|
| **backgrounds** | | | |
| `--bg-canvas` | `#080a0c` | `#080a0c` | ✅ exact |
| `--bg-surface` | `#0f1115` | `#0f1115` | ✅ exact |
| `--bg-elevated` | `#161b22` | `#161b22` | ✅ exact |
| `--bg-highlight` | `#1c2128` | `#1c2128` | ✅ exact |
| `--bg-input` | `#111318` | `#111318` | ✅ exact |
| **text** | | | |
| `--text-primary` | `#e6edf3` | `#e6edf3` | ✅ exact |
| `--text-secondary` | `#8b949e` | `#a8b3c1` | ⚠️ mismatch |
| `--text-tertiary` | `#6e7681` | `#9ba3b0` | ⚠️ mismatch |
| `--text-muted` | `#484f58` | `#8b949e` | ⚠️ mismatch |
| `--text-accent` | `#58a6ff` | `#58a6ff` | ✅ exact |
| **accents** | | | |
| `--accent-green` | `#3fb950` | `#3fb950` | ✅ exact |
| `--accent-amber` | `#d29922` | `#d29922` | ✅ exact |
| `--accent-red` | `#f85149` | `#f85149` | ✅ exact |
| `--accent-blue` | `#58a6ff` | `#58a6ff` | ✅ exact |
| `--accent-purple` | `#a371f7` | `#a371f7` | ✅ exact |
| `--accent-cyan` | `#39d0d8` | `#39d0d8` | ✅ exact |
| `--accent-orange` | `#ff9248` | `#ff9248` | ✅ exact |
| **geo** | | | |
| `--geo-land` | `#1c2128` | `#1c2128` | ✅ exact |
| `--geo-water` | `#0d2137` | `#0d2137` | ✅ exact |
| `--geo-route` | `#39d0d8` | `#39d0d8` | ✅ exact |
| `--geo-waypoint` | `#d29922` | `#d29922` | ✅ exact |
| `--geo-destination` | `#3fb950` | `#3fb950` | ✅ exact |
| **borders** | | | |
| `--border-default` | `#30363d` | `#30363d` | ✅ exact |
| `--border-hover` | `#8b949e` | `#8b949e` | ✅ exact |
| `--border-active` | `#58a6ff` | `#58a6ff` | ✅ exact |
| `--border-route` | `rgba(57, 208, 216, 0.3)` | `#39d0d84d` | ✅ exact |
| **spacing** | | | |
| `--space-1` | `4px` | `4px` | ✅ exact |
| `--space-2` | `8px` | `8px` | ✅ exact |
| `--space-3` | `12px` | `12px` | ✅ exact |
| `--space-4` | `16px` | `16px` | ✅ exact |
| `--space-5` | `20px` | `20px` | ✅ exact |
| `--space-6` | `24px` | `24px` | ✅ exact |
| `--space-8` | `32px` | `32px` | ✅ exact |
| `--space-10` | `40px` | `40px` | ✅ exact |
| `--space-12` | `48px` | `48px` | ✅ exact |

**CSS Token Compliance:** 32/35 (91%)

## 2. Page-Level Visual Audit

### Marketing Landing (`/`)

Screenshot: `screenshots/_.png`

#### Body Defaults
| Property | Value |
|---|---|
| Background | `rgb(8, 10, 12)` |
| Text Color | `rgb(230, 237, 243)` |
| Font Family | Rubik, "Rubik Fallback", system-ui, sans-serif |
| Font Size | 18px |
| Font Weight | 400 |
| Line Height | 28.8px |

#### Buttons
| Text | Bg | Color | Border | Radius | Font |
|---|---|---|---|---|---|
| Join | `rgba(0, 0, 0, 0)` | `rgb(7, 16, 24)` | `rgb(229, 231, 235)` | `9999px` | 12px 600 |

#### Inputs
| Type | Bg | Color | Border | Radius | Padding |
|---|---|---|---|---|---|
| INPUT (your@agency.com) | `rgba(0, 0, 0, 0)` | `rgb(230, 237, 243)` | `rgb(229, 231, 235)` | `0px` | 0px 0px 0px 0px |

### Login (`/login`)

Screenshot: `screenshots/_login.png`

#### Body Defaults
| Property | Value |
|---|---|
| Background | `rgb(8, 10, 12)` |
| Text Color | `rgb(230, 237, 243)` |
| Font Family | Rubik, "Rubik Fallback", system-ui, sans-serif |
| Font Size | 18px |
| Font Weight | 400 |
| Line Height | 28.8px |

#### Cards
| # | Background | Border | Radius | Shadow |
|---|---|---|---|---|
| 0 | `rgb(13, 17, 23)` | `rgb(28, 33, 40)` | `12px` | none |

#### Buttons
| Text | Bg | Color | Border | Radius | Font |
|---|---|---|---|---|---|
| Sign in | `rgba(0, 0, 0, 0)` | `rgb(255, 255, 255)` | `rgb(255, 255, 255)` | `8px` | 13px 600 |

#### Inputs
| Type | Bg | Color | Border | Radius | Padding |
|---|---|---|---|---|---|
| INPUT (you@agency.com) | `rgb(8, 10, 12)` | `rgb(230, 237, 243)` | `rgb(28, 33, 40)` | `8px` | 8px 12px 8px 12px |
| INPUT (Enter your password) | `rgb(8, 10, 12)` | `rgb(230, 237, 243)` | `rgb(28, 33, 40)` | `8px` | 8px 12px 8px 12px |

### Inbox (`/inbox`)

Screenshot: `screenshots/_inbox.png`

#### Body Defaults
| Property | Value |
|---|---|
| Background | `rgb(8, 10, 12)` |
| Text Color | `rgb(230, 237, 243)` |
| Font Family | Rubik, "Rubik Fallback", system-ui, sans-serif |
| Font Size | 18px |
| Font Weight | 400 |
| Line Height | 28.8px |

#### Cards
| # | Background | Border | Radius | Shadow |
|---|---|---|---|---|
| 0 | `rgb(13, 17, 23)` | `rgb(28, 33, 40)` | `12px` | none |

#### Buttons
| Text | Bg | Color | Border | Radius | Font |
|---|---|---|---|---|---|
| Sign in | `rgba(0, 0, 0, 0)` | `rgb(255, 255, 255)` | `rgb(255, 255, 255)` | `8px` | 13px 600 |

#### Inputs
| Type | Bg | Color | Border | Radius | Padding |
|---|---|---|---|---|---|
| INPUT (you@agency.com) | `rgb(8, 10, 12)` | `rgb(230, 237, 243)` | `rgb(28, 33, 40)` | `8px` | 8px 12px 8px 12px |
| INPUT (Enter your password) | `rgb(8, 10, 12)` | `rgb(230, 237, 243)` | `rgb(28, 33, 40)` | `8px` | 8px 12px 8px 12px |

### Workspace (`/workspace`)

Screenshot: `screenshots/_workspace.png`

#### Body Defaults
| Property | Value |
|---|---|
| Background | `rgb(8, 10, 12)` |
| Text Color | `rgb(230, 237, 243)` |
| Font Family | Rubik, "Rubik Fallback", system-ui, sans-serif |
| Font Size | 18px |
| Font Weight | 400 |
| Line Height | 28.8px |

#### Cards
| # | Background | Border | Radius | Shadow |
|---|---|---|---|---|
| 0 | `rgb(13, 17, 23)` | `rgb(28, 33, 40)` | `12px` | none |

#### Buttons
| Text | Bg | Color | Border | Radius | Font |
|---|---|---|---|---|---|
| Sign in | `rgba(0, 0, 0, 0)` | `rgb(255, 255, 255)` | `rgb(255, 255, 255)` | `8px` | 13px 600 |

#### Inputs
| Type | Bg | Color | Border | Radius | Padding |
|---|---|---|---|---|---|
| INPUT (you@agency.com) | `rgb(8, 10, 12)` | `rgb(230, 237, 243)` | `rgb(28, 33, 40)` | `8px` | 8px 12px 8px 12px |
| INPUT (Enter your password) | `rgb(8, 10, 12)` | `rgb(230, 237, 243)` | `rgb(28, 33, 40)` | `8px` | 8px 12px 8px 12px |

### Settings (`/settings`)

Screenshot: `screenshots/_settings.png`

#### Body Defaults
| Property | Value |
|---|---|
| Background | `rgb(8, 10, 12)` |
| Text Color | `rgb(230, 237, 243)` |
| Font Family | Rubik, "Rubik Fallback", system-ui, sans-serif |
| Font Size | 18px |
| Font Weight | 400 |
| Line Height | 28.8px |

#### Cards
| # | Background | Border | Radius | Shadow |
|---|---|---|---|---|
| 0 | `rgb(13, 17, 23)` | `rgb(28, 33, 40)` | `12px` | none |

#### Buttons
| Text | Bg | Color | Border | Radius | Font |
|---|---|---|---|---|---|
| Sign in | `rgba(0, 0, 0, 0)` | `rgb(255, 255, 255)` | `rgb(255, 255, 255)` | `8px` | 13px 600 |

#### Inputs
| Type | Bg | Color | Border | Radius | Padding |
|---|---|---|---|---|---|
| INPUT (you@agency.com) | `rgb(8, 10, 12)` | `rgb(230, 237, 243)` | `rgb(28, 33, 40)` | `8px` | 8px 12px 8px 12px |
| INPUT (Enter your password) | `rgb(8, 10, 12)` | `rgb(230, 237, 243)` | `rgb(28, 33, 40)` | `8px` | 8px 12px 8px 12px |

### Itinerary Checker (`/itinerary-checker`)

Screenshot: `screenshots/_itinerary-checker.png`

#### Body Defaults
| Property | Value |
|---|---|
| Background | `rgb(8, 10, 12)` |
| Text Color | `rgb(230, 237, 243)` |
| Font Family | Rubik, "Rubik Fallback", system-ui, sans-serif |
| Font Size | 18px |
| Font Weight | 400 |
| Line Height | 28.8px |

#### Cards
| # | Background | Border | Radius | Shadow |
|---|---|---|---|---|
| 0 | `rgb(13, 17, 23)` | `rgb(28, 33, 40)` | `12px` | none |

#### Buttons
| Text | Bg | Color | Border | Radius | Font |
|---|---|---|---|---|---|
| Sign in | `rgba(0, 0, 0, 0)` | `rgb(255, 255, 255)` | `rgb(255, 255, 255)` | `8px` | 13px 600 |

#### Inputs
| Type | Bg | Color | Border | Radius | Padding |
|---|---|---|---|---|---|
| INPUT (you@agency.com) | `rgb(8, 10, 12)` | `rgb(230, 237, 243)` | `rgb(28, 33, 40)` | `8px` | 8px 12px 8px 12px |
| INPUT (Enter your password) | `rgb(8, 10, 12)` | `rgb(230, 237, 243)` | `rgb(28, 33, 40)` | `8px` | 8px 12px 8px 12px |

## 3. Discrepancies & Issues

| Severity | Category | Detail |
|---|---|---|
| ⚠️ warn | CSS Variable: text | `--text-secondary` expected `#8b949e` but found `#a8b3c1` |
| ⚠️ warn | CSS Variable: text | `--text-tertiary` expected `#6e7681` but found `#9ba3b0` |
| ⚠️ warn | CSS Variable: text | `--text-muted` expected `#484f58` but found `#8b949e` |
| 💡 info | DESIGN.md vs globals.css | Docs/DESIGN.md specifies --text-secondary as #8b949e, but globals.css uses #a8b3c1. The globals.css has a note: "Lightened from #8b949e for AA compliance". Docs/DESIGN.md may need updating to match. |
| 💡 info | DESIGN.md vs globals.css | Docs/DESIGN.md specifies --text-tertiary as #6e7681, but globals.css uses #9ba3b0. globals.css comment: "Lighter tertiary for better readability (~4.5:1)". Docs/DESIGN.md should be updated. |
| 💡 info | DESIGN.md Duplication | Two DESIGN.md files exist: frontend/DESIGN.md (1112 lines, "Waypoint OS") and Docs/DESIGN.md (1185 lines, "Travel Agency Agent"). These have diverged significantly. Recommend consolidating to a single source of truth. |

## 4. Recommendations

| Priority | Action |
|---|---|
| 🟡 Medium | `--text-secondary` expected `#8b949e` but found `#a8b3c1` |
| 🟡 Medium | `--text-tertiary` expected `#6e7681` but found `#9ba3b0` |
| 🟡 Medium | `--text-muted` expected `#484f58` but found `#8b949e` |
