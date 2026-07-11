# Playbook: Business Reports

Client-ready analyses and executive reports. Builds on the Reporter agent's
formatting rules; this playbook adds the business-analyst framing.

## The BA framing (what separates a report from a data dump)

- Lead with the **"so what"**: every section moves from finding → implication
  → recommended action. A number without a consequence is filler.
- Quantify recommendations: expected impact, cost, effort, and time horizon
  wherever the data allows. Mark estimates as estimates.
- Keep an **assumptions log**: every assumption made (exchange rates, growth
  rates, exclusions) listed in one appendix table so the client can challenge
  them.
- Segment before averaging: totals hide the story; break down by the 1–2
  dimensions the client manages against (region, product, channel, cohort).

## Structure for client deliverables

1. Executive summary (≤ 1 page: question, answer, top 3 numbers, top 3 actions)
2. Background & scope (what was asked, data used, period covered)
3. Findings (one section per theme, chart or table per finding)
4. Recommendations (ordered by impact/effort, each with owner + timeline)
5. Appendix (methodology, assumptions log, data dictionary, full tables)

## Evidence rules

- Every chart/table answers a stated question; caption it with the takeaway
  ("Churn concentrates in month 2"), not a description ("Churn by month").
- Cite the source and date of every external figure. Internal figures name
  the dataset and pipeline that produced them.
- Show comparisons, not absolutes: vs prior period, vs target, vs benchmark.
- Round for the audience (executives: 2 significant figures in prose, exact
  values in appendix tables).

## Delivery formats

- Markdown master → HTML (styled, print-ready) → PDF via the Reporter's
  converter chain. Deliver the PDF for clients, keep the markdown in the
  repo as the source of truth.
- For recurring engagements, parameterize the report generation so next
  month's version is a re-run, not a rewrite.
