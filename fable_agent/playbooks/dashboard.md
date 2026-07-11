# Playbook: Dashboards

Client-facing analytics dashboards. The bar: a stakeholder opens it, finds
the number they care about in under 10 seconds, and trusts it.

## Before building

- Identify the audience and the 3–7 KPIs that drive their decisions. Every
  widget must answer a question someone actually asks; cut vanity metrics.
- Establish the data source and refresh story: static snapshot, file upload,
  or live API. State the "data as of" timestamp on the dashboard itself.

## Default technical approach

- **Single-file HTML dashboard** (default for freelance deliverables):
  self-contained `index.html` with Chart.js or ECharts from a CDN, data
  inlined as JSON or loaded from a sibling `data.json`. Zero build step,
  opens anywhere, easy to email or host.
- **React + Tailwind + Recharts** when the client already has a React stack
  or needs interactivity beyond filters (drill-downs, auth, live data).
- **Python (Streamlit/Plotly Dash)** when the audience is internal and the
  data work is heavy.

## Layout standard

```
┌────────────────────────────────────────────────┐
│ Title · date range picker · filters      as-of │
├──────────┬──────────┬──────────┬───────────────┤
│ KPI card │ KPI card │ KPI card │ KPI card      │  ← headline numbers +
├──────────┴──────────┴──────────┴───────────────┤    delta vs prior period
│ Primary trend chart (the main story)           │
├────────────────────────┬───────────────────────┤
│ Breakdown (bar/table)  │ Composition (donut/   │
│ by segment/category    │ stacked bar)          │
├────────────────────────┴───────────────────────┤
│ Detail table (sortable, top-N with totals row) │
└────────────────────────────────────────────────┘
```

- KPI cards: big number, unit, delta arrow with color (green up / red down —
  inverted for cost metrics), sparkline if space allows.
- One accent color for the primary metric; muted palette for the rest;
  colorblind-safe (avoid red/green as the only signal).

## Chart selection rules

- Trend over time → line. Comparison across categories → horizontal bar.
- Composition → stacked bar (donut only for ≤ 4 slices). Never 3D, never
  dual y-axes without explicit labeling.
- Label axes with units; format ticks (1.2M not 1200000); tooltips show
  exact values.

## Quality gate before delivery

- Renders correctly at 375px, 768px, and 1440px widths.
- All numbers reconcile with the source dataset (spot-check 3 values).
- Empty/loading states exist if data loads asynchronously.
- Filters change every dependent widget, not just some.
