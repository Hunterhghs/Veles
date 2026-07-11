# Playbook: Datasets

Building, cleaning, and delivering datasets a client can trust and reuse.

## Deliverable standard

A dataset delivery is never just a file. It is:

1. **The data** — clean CSV (UTF-8, header row) by default; Parquet when
   large or typed precision matters; both when in doubt.
2. **A data dictionary** — `DATA_DICTIONARY.md` with one row per column:
   name, type, unit, allowed values/range, % missing, source, notes.
3. **The pipeline** — a re-runnable script (`build_dataset.py` or SQL file)
   that regenerates the output from raw sources. No untracked manual steps.
4. **A README** — provenance (where each source came from, retrieval date),
   transformations applied, known limitations, and row/column counts.

## Cleaning checklist (run in this order)

- Types: parse dates to ISO 8601, numerics to numbers (strip currency
  symbols, thousands separators), booleans normalized.
- Keys: define the grain (one row = one what?); check primary-key
  uniqueness; document any composite keys.
- Duplicates: detect exact and fuzzy duplicates; log how many were dropped
  and why.
- Missing values: quantify per column; decide explicitly — impute, flag, or
  leave null — and record the decision in the dictionary.
- Categorical hygiene: trim whitespace, unify case, collapse synonyms
  ("NY" / "New York"), map to a controlled vocabulary where sensible.
- Outliers: flag values outside plausible ranges; never silently delete —
  add an `is_outlier` flag or document removals.
- Consistency: cross-field checks (end_date ≥ start_date, parts ≤ totals).

## Validation before delivery

Write assertions into the pipeline, not a one-off notebook: row count within
expected range, key uniqueness, null thresholds, value ranges. The pipeline
fails loudly if any assertion breaks.

## Reporting the work

Always summarize: rows in → rows out, columns added/dropped/renamed, issues
found with counts, and any judgment calls a client should sign off on.
