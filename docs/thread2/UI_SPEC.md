# Thread 2 — Rich UI Elevation Spec (T2.5)

Reference: the cardiology health-record shot (Ron Design) + segmented-invoice + workspace
ribbon shots Misha shared. We adapt its STRUCTURE, not its medical styling: keep
paper/ink/forest tokens, lime reserved for live/now. Investor-grade restraint, tactile
richness. This spec is the bar; Claude screenshot-reviews every round against it and
bounces work back until it passes.

## Critique of current UI (why it reads simplistic)

1. Evidence timeline is a flat vertical list — the reference's entire character comes
   from a horizontal spine with node markers, branch lines, and attached cards.
2. Zero inline micro-charts — reference embeds a mini area chart INSIDE each Blood
   Pressure card; our commit-burst/star events are text-only.
3. Vitals are four separate plain boxes — reference uses one compact inline strip
   (label · big value · unit) that reads at a glance.
4. No section-jump chips (reference: Visits/Medications/Labs pills with icons).
5. Time scrubber is a bare range input — reference's bottom ribbon has month ticks,
   per-month event badges, icon chips, a distinct draggable knob.
6. No circular icon buttons; few chips; flat single-layer cards (radius 12, one
   shadow) vs reference's layered soft depth (outer radius ~24-28, nested 14-16).
7. Radar rows have no trajectory sparkline and no per-axis micro-bars.

## Global design system upgrades (round 1)

- Surface layers: page = paper; primary panels radius 26, soft double shadow
  (ambient 0 24px 60px rgba(29,40,33,.08) + key 0 2px 6px rgba(29,40,33,.05));
  nested cards radius 16 on #fbfcfa with hairline border. Section headers INSIDE
  panels (reference puts "Blood Pressure" inside the card).
- Chip system (one component, variants): filter chip (icon + label + count badge),
  nav chip (icon + label; active = ink bg / paper text, like reference's dark pill),
  event chip (tiny icon + terse value, e.g. "38 commits · 7d" — the "Aspirin ×2"
  pattern), status chip (verification badges, existing colors).
- Circular icon buttons 36/44px (paper bg, hairline border, ink icon; hover lifts):
  external-link, scroll arrows, expand, back.
- Micro-chart primitives (hand-rolled SVG, no lib): `<MiniArea>` (28-40px tall,
  forest fill 12% opacity, 1.5px line), `<MiniBars>`, `<ConfidenceArc>` (claim
  confidence as small arc dial). Respect prefers-reduced-motion.
- Numerals: tabular-nums everywhere data renders; ui-monospace for ids/scores-in-tables.
- Lime usage expands slightly: timeline node markers + "now"/detection cursor +
  live states. Never for static decoration.

## Founder record page rebuild (round 1 — the centerpiece)

Header zone (reference's patient card + vitals row):
- Avatar circle 64px (initials), name, @login · company as chips, source badge.
- Section-nav chips row: Overview · Timeline · Memo · Claims · Runs (icons; smooth
  scroll; active tracks scroll position).
- Vitals strip replaces the four boxes: one panel, inline groups —
  "Signal 91" (big, top-2% sub-label) · "Momentum ↑14%" · "3-axis 9.1/7.4/7.8"
  (three micro-bars, never averaged) · "First detection Mar 2025". Compact, one line
  on desktop.

THE TIMELINE (this is the make-or-break component):
- Horizontal spine across a full-width panel; month markers along it; year labels.
- The score trajectory IS the spine: a 2px line whose stroke interpolates
  muted→forest with score, drawn along the spine axis (reference's red→green vitals
  line). Detection month = lime node with halo ring.
- Evidence clustered per month: node dot on the spine sized by event count; branch
  line (1px hairline with rounded elbow, like the reference's connector curves) down
  (or up, alternating) to an attached card.
- Attached cards by dominant type: commit_burst → MiniArea of commit volume + event
  chip "38 commits · 7d"; star_milestone → MiniBars + "629 ★"; release → version
  chips ("v0.18"); readme/org/repo events → icon + one-liner. Card footer: repo link
  as circular icon button. Multiple event-type chips when a month is mixed.
- Type filter chips ABOVE the timeline (existing types + counts); filtering
  collapses/fades non-matching nodes (FLIP).
- Horizontal scroll with circular arrow buttons at panel edges + drag; current
  viewport month range echoed in the panel header.
- Keyboard: ←/→ steps months, Enter opens the month's card stack.

## Radar page (round 2)

- Scrubber → ribbon (workspace-shot style): dark ink rounded bar, month ticks,
  tiny per-month evidence-count badges, lime draggable knob, year labels; "future
  evidence hidden" chip attaches to the knob when not at max.
- Each row gains: 90px trajectory sparkline (MiniArea), three axis micro-bars,
  momentum chip (arrow + value in a pill), evidence-count chip. Row hover lifts
  (2px) with shadow; keyboard selection = forest left rail (existing) + lifted state.
- Thesis controls: sliders get value pills; toggles become chips (consistent system).

## Run view (round 2)

- Step feed becomes a vertical trace with the same node/branch language: spine,
  node per step colored by kind (plan=ink, sql=blue, fetch=amber, evidence=forest,
  claim=forest-bright, gap=red, done=lime), branch to a card for payload-bearing
  steps. Sandbox code in reason steps: collapsed to 3 lines with expand (circular
  chevron button), mono, syntax-tinted comments.
- Claims materialize as cards with ConfidenceArc + status chip; the Trust-contract
  panel stays.
- Live run: lime pulse on the newest node (reduced-motion: static ring).

## Explicitly out (kitsch guard)

No dark device frame, no photos/avatars of people, no gradient backgrounds, no
glassmorphism, no decorative icons without data. Whitespace stays generous; density
comes from information, not ornament.

## Acceptance per round (Claude, in-browser)

R1: founder record — timeline reads as spine+nodes+branch cards at a glance;
micro-charts render real per-month aggregates from the evidence API (no fake data);
vitals strip one-line; section chips track scroll; 4 e2e tests still pass + new
timeline smoke test (nodes count matches months with evidence; filter chips hide
nodes). R2: radar ribbon + enriched rows; run-view trace. Each round: screenshots
compared against the reference; anything reading "flat list" bounces.
