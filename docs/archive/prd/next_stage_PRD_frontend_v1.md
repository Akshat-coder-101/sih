# Product Requirements Document
## IBVAP Frontend v1: Watermelon Command Center Experience

| Field | Value |
|---|---|
| Document version | 1.0 |
| Status | Proposed frontend-only implementation PRD |
| Scope | React/Vite frontend, UI/UX, responsive behavior, accessibility, frontend performance |
| Backend impact | None in this document; existing API contracts remain unchanged |
| Baseline | Current IBVAP React dashboard with Tailwind, DaisyUI, Tabler Icons, Lucide, and TensorFlow.js |
| Primary users | Security operators, supervisors, administrators, evaluators |

## 1. Product Intent

Create a calm, high-confidence command-center interface for monitoring camera feeds, triaging alerts, reviewing evidence, and understanding system health. The interface should feel operational rather than promotional: fast to scan, clear under pressure, and honest about real, simulated, offline, and unavailable data.

The visual direction is **Watermelon Command**: a dark graphite workspace with watermelon-red threat states, fresh green operational states, pale rind neutrals, and restrained cyan instrumentation accents. The palette must communicate urgency without turning every screen into an alarm panel.

The redesign shall use existing React and Tailwind patterns where possible. shadcn/ui and Radix-style interaction patterns may be adopted for accessible dialogs, menus, tabs, tooltips, command menus, and popovers, but the project must avoid adding a large component framework without need.

## 2. Design Principles

- **Operational clarity:** status, ownership, source, confidence, and next action are always visible.
- **Signal hierarchy:** critical events dominate attention; routine telemetry stays quiet.
- **Honest provenance:** real detector, simulation, fixture, replay, offline, and unavailable states are distinct.
- **Progressive disclosure:** show the most important information first, with details available on demand.
- **Touch-ready:** primary controls work comfortably on small screens and touch devices.
- **Accessible by default:** semantic HTML, keyboard operation, focus visibility, contrast, labels, and reduced motion.
- **Consistent feedback:** every action has loading, success, failure, and permission behavior.
- **No decorative noise:** motion, gradients, badges, and visual effects must support comprehension.

## 3. Users and Core Jobs

| User | Core job | Primary views |
|---|---|---|
| Operator | Monitor sectors and act on urgent alerts | Live Monitor, Alert Queue, Evidence |
| Supervisor | Review incidents and assess system quality | Alerts, Analytics, Audit, Reports |
| Administrator | Configure cameras, rules, roles, and system state | Camera Config, Model Status, Settings |
| Evaluator | Demonstrate the end-to-end platform honestly | Live Monitor, AI Pipeline, About, Readiness |

## 4. Information Architecture

The application shall use a persistent shell with responsive navigation:

```text
Command Center
  - Live Monitor
  - Camera Grid
  - Alerts
  - Analytics
  - AI Pipeline
  - Camera Configuration
  - About
  - Contact
  - Privacy
  - Terms
```

### Desktop

- Fixed left navigation rail, 240px maximum width.
- Compact top status bar.
- Main content fills the remaining viewport.
- No page-level horizontal scrolling.

### Mobile

- Top bar with menu button, current view title, connection status, and one primary action.
- Navigation opens as a full-height drawer with backdrop and focus handling.
- Drawer closes after navigation, backdrop click, Escape, or close button.
- Content uses one-column layouts with fixed media aspect ratios.
- Secondary controls move into a filter/action sheet or horizontal scroll region contained within its parent.

## 5. Visual System: Watermelon Command

### Color tokens

| Token | Purpose | Suggested value |
|---|---|---|
| `ink-950` | App background | `#101313` |
| `ink-900` | Sidebar and top bar | `#171b1a` |
| `ink-800` | Panels | `#202624` |
| `rind-100` | Primary text | `#f2f5ee` |
| `rind-300` | Secondary text | `#b6c1b7` |
| `rind-500` | Muted text and dividers | `#718077` |
| `melon-500` | Primary action | `#ff6b5f` |
| `melon-600` | Critical action | `#e84d52` |
| `seed-900` | Threat background | `#351d24` |
| `leaf-500` | Healthy/online state | `#65d68b` |
| `leaf-900` | Healthy background | `#193126` |
| `instrument-400` | Telemetry accent | `#56c7d9` |
| `warning-400` | Warning state | `#f4bd5b` |

The palette must remain multi-hue. Red is reserved for threat and destructive states; green is reserved for healthy and successful states; cyan is for instrumentation and links.

### Typography

- Display and section headings: `Space Grotesk` or equivalent expressive sans-serif.
- Body text: `DM Sans` or equivalent readable sans-serif.
- Telemetry, IDs, timestamps, and coordinates: `JetBrains Mono`.
- Do not use oversized hero typography inside operational views.
- Do not use negative letter spacing.

### Shape and depth

- Maximum standard radius: 10px.
- Use framed panels only for tools, dialogs, repeated alert items, and camera tiles.
- Avoid nested cards and excessive floating containers.
- Use thin borders and restrained shadows instead of heavy gradients.
- Use a subtle grid/noise texture only as a background layer, never behind dense text.

## 6. Component Rules

### Buttons

- Use familiar icons for icon-only actions and provide tooltips.
- Use icon plus text for commands such as acknowledge, resolve, export, and start camera.
- Destructive actions require confirmation.
- All buttons have visible hover, focus, pressed, disabled, and loading states.
- Minimum touch target: 44px on mobile, 36px on desktop where appropriate.

### Status indicators

Every status badge must include text, not color alone. Required states:

- Online / Offline
- Live / Reconnecting / Unavailable
- Detector Ready / Detector Missing / Simulation
- Open / Acknowledged / Resolved / False Positive / Escalated
- Saved / Saving / Save Failed

### Data density

- Prefer compact tables and alert rows for repeated operational data.
- Use truncation only when the full value is available through tooltip, detail view, or expansion.
- Preserve stable columns and widths so live updates do not shift controls.

## 7. Screen Requirements

### 7.1 Live Monitor

- Show active camera name, location, source type, connection state, inference state, provenance, and timestamp.
- Keep the video viewport at a stable 16:9 or 16:10 ratio.
- Show detections with readable labels, confidence, track ID, and threat styling.
- Provide camera switching through an accessible tab/list control.
- Provide start/stop webcam controls only when CAM-01 is selected.
- Display a clear DEMO or SIMULATION banner for generated sources/events.
- Show the live alert queue beside the video on desktop and below it on mobile.
- Include an offline/error overlay with retry or fallback action.

### 7.2 Camera Grid

- Responsive grid: 1 column mobile, 2 columns tablet, 2 or 4 columns desktop depending on width.
- Every tile includes camera identity, state, source, FPS, alert count, and last frame time.
- Offline tiles remain visible and explain why the feed is unavailable.
- Clicking a tile opens an accessible fullscreen evidence view.
- Failed image streams may show a labelled generated fallback only when fallback mode is enabled.

### 7.3 Alerts

- Provide filter controls for type, severity, lifecycle state, provenance, camera, site, and time range.
- Show pending count and a clear active filter summary.
- Support quick acknowledge and resolve actions from each row.
- Require a reason code for false positive and resolution actions.
- Use an empty state when no alerts match filters.
- Use a first-load state when the backend has not responded.
- Use an error state with retry when loading fails.
- Export must show server-authoritative success or a blocking error; no silent local compliance export.

### 7.4 Evidence Detail

- Open from an alert row, live queue item, or analytics item.
- Show image/video, alert ID, camera, site, timestamp, confidence, model version, rule version, provenance, hash, and lifecycle state.
- Explain unavailable, expired, processing, and missing evidence.
- Prevent content overflow for long IDs, GPS values, notes, and alert details.
- Use a focus-trapped dialog with Escape and close controls.

### 7.5 Analytics

- Present measured values with time window, site, and data source.
- Label estimated, simulated, and unavailable metrics explicitly.
- Prefer trend charts and compact comparisons over decorative KPI tiles.
- Provide empty states for insufficient data.
- Support keyboard-readable chart summaries and table alternatives.

### 7.6 AI Pipeline

- Display model name, version, load state, device, thresholds, and provenance.
- Separate active production models from planned or unavailable models.
- Never show a fabricated latency or throughput value without a measured/simulated label.
- Provide a concise explanation of the pipeline stages and current health.

### 7.7 Camera Configuration

- Restrict controls based on server-provided role and permission state.
- Use form validation before submission.
- Show unsaved, saving, saved, and failed states.
- Protect stream URLs and credentials from display where applicable.
- Provide confirmation for disabling a camera or deleting a rule.

### 7.8 About, Contact, Privacy, Terms

- Keep these pages compact and navigable from the shell footer or menu.
- Use truthful project and team information only.
- Contact page shall provide clickable email and phone links.
- Privacy and Terms pages shall clearly identify prototype limitations and data handling.

## 8. Interaction and Feedback Requirements

- Toasts are for short confirmations and recoverable errors; do not use browser `alert()` for product feedback.
- Inline errors appear next to the field or action that failed.
- Network errors provide retry and explain whether local state changed.
- Optimistic updates must roll back when persistence fails or show an explicit unsaved state.
- Long operations show progress or an indeterminate loading state.
- Destructive actions require a confirmation dialog with a specific consequence.
- Empty states contain a useful next action where one exists.
- All dialogs and menus close correctly on Escape and restore focus to their trigger.

## 9. Responsive Requirements

Target widths:

- 320px narrow mobile
- 390px standard mobile
- 430px large mobile
- 768px tablet
- 1024px small desktop
- 1440px desktop

Requirements:

- `document.documentElement.scrollWidth` shall not exceed viewport width.
- No fixed-width panel may force page overflow.
- Camera and evidence media shall use stable aspect ratios.
- Tables may scroll inside a bounded table region, never the whole page.
- Topbar controls collapse by priority at narrow widths.
- Text must wrap or truncate safely within its parent.
- Mobile drawer and modal layers must not create inaccessible off-screen controls.

## 10. Accessibility Requirements

- Use semantic landmarks: `header`, `nav`, `main`, `aside`, `section`, and headings.
- All interactive elements must be keyboard reachable.
- Focus indicators must be visible against the dark palette.
- Icon-only controls require accessible names and tooltips.
- Color must not be the only status signal.
- Dialogs require focus management and screen-reader labels.
- Respect `prefers-reduced-motion` and disable scanline/pulse effects when requested.
- Provide text/table summaries for charts and detection overlays where possible.
- Target WCAG 2.2 AA contrast for text and essential controls.

## 11. Performance Requirements

- Initial shell should render before TensorFlow.js model loading completes.
- Lazy-load TensorFlow.js and heavy analytics views where feasible.
- Use route/component-level code splitting when URL routing is introduced.
- Avoid rendering more than the visible alert rows on large histories.
- Throttle live clock, telemetry, and animation updates.
- Revoke object URLs after downloads and clean up media streams on unmount.
- Target Lighthouse mobile performance score of 75+ for non-webcam views.
- Keep the primary non-model JavaScript payload below 500KB compressed where practical.

## 12. Frontend State Contract

The UI state layer shall expose:

- `loading`, `ready`, `empty`, `error`, `offline`, and `forbidden` states for network-backed views.
- `sourceProvenance`: `real`, `simulation`, `fixture`, `replay`, or `unknown`.
- `persistenceState`: `idle`, `saving`, `saved`, `failed`.
- `permissionState`: `allowed`, `restricted`, `forbidden`, or `unknown`.
- `lastUpdatedAt` and `staleAfter` for live data.

API errors should normalize into a common shape:

```ts
interface UiError {
  code: string;
  message: string;
  retryable: boolean;
  requestId?: string;
}
```

## 13. Implementation Phases

### Phase 1: Foundation

- Add design tokens and Watermelon Command theme.
- Replace browser alerts with reusable dialogs and toasts.
- Normalize page shell, headings, buttons, status badges, and focus states.
- Add shared empty, loading, error, offline, and forbidden components.

### Phase 2: Navigation and mobile

- Complete responsive sidebar drawer.
- Add accessible menu, breadcrumbs where useful, and page-level navigation state.
- Eliminate horizontal overflow at all target widths.
- Stabilize camera, table, modal, and chart dimensions.

### Phase 3: Operational workflows

- Redesign Live Monitor, Camera Grid, Alerts, Evidence, and Camera Config.
- Add lifecycle action feedback and explicit persistence states.
- Add provenance and system-health presentation.
- Improve table filtering, row actions, keyboard navigation, and mobile triage.

### Phase 4: Performance and QA

- Lazy-load heavy model and analytics code.
- Add visual regression and responsive browser tests.
- Run accessibility checks and keyboard workflow tests.
- Validate real, simulated, offline, empty, error, and permission states.

## 14. Test Plan

### Unit tests

- State reducers and normalized API errors.
- Filter combinations and empty-state logic.
- Permission-based action visibility.
- Alert lifecycle transitions.
- Provenance labels and status mapping.

### Component tests

- Drawer open/close/focus behavior.
- Accessible dialogs and evidence modal.
- Toast success/error/loading behavior.
- Alert row actions and rollback behavior.
- Responsive camera tile and table rendering.

### Browser tests

- Desktop navigation across every page.
- Mobile navigation at 320px, 390px, and 430px.
- No horizontal overflow on every primary page.
- Live monitor fallback and offline states.
- Alert filtering, acknowledge, resolve, and export failure/success.
- Evidence open/close and keyboard focus.
- Contact email and phone links.
- Invalid view renders the custom 404 screen.

### Performance tests

- Cold load without TensorFlow model.
- Cold load with TensorFlow model.
- Alert list with 1,000 rows.
- Camera grid with 4 and 16 tiles.
- Repeated WebSocket updates for 10 minutes.

## 15. Acceptance Criteria

The frontend release is accepted when:

1. The Watermelon Command visual system is consistently applied across all primary screens.
2. The dashboard has no horizontal document overflow from 320px through 1440px.
3. Mobile navigation works with keyboard, touch, backdrop, and Escape.
4. Every network-backed view has loading, empty, error, offline, and forbidden states where applicable.
5. Every mutation communicates saving, success, failure, and local-only status accurately.
6. Alert provenance and measured/simulated status are visible wherever relevant.
7. Evidence dialogs are accessible, responsive, and safe for long content.
8. No product workflow uses native browser alerts for normal feedback.
9. All icon-only controls have accessible names and tooltips.
10. Heavy TensorFlow code does not block the initial shell render.
11. Browser tests pass at all required viewport sizes.
12. Frontend production build passes with zero TypeScript errors.
13. Existing API contracts remain compatible unless separately approved.

## 16. Non-Goals

- No backend route, database, authentication, model, or C2 changes.
- No fabricated reviews, metrics, team photos, or operational claims.
- No marketing landing page or oversized hero section.
- No replacement of real camera/evidence content with AI-generated imagery.
- No new UI library adoption without bundle, accessibility, and maintenance review.
