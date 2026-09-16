# AGENTS.md — `demo/`

Standalone before/after demo. Independent from the parent project: **no BSL, no Ibis, no
`uv sync`** — only `duckdb` and `pandas`.

## What it proves

Not that a semantic layer is convenient — that it prevents **silent disagreement**. Two analysts
write reasonable, error-free queries for the same question and get different answers, because the
`zones` lookup contains a duplicate `LocationID 4` (a re-ingestion job that appended instead of
replaced) and only one of them deduped. Same class of bug as
[boring-semantic-layer#32](https://github.com/boringdata/boring-semantic-layer/issues/32).

## Files

- `make_data.py` — writes `trips.parquet` (10 rows) and `zones.csv` (5 rows, one duplicate) into
  the **current directory**. Both outputs are gitignored.
- `before_after_demo.py` — reads those two files by bare relative name, prints BEFORE (two
  disagreeing dashboards) then AFTER (one shared function, identical output).
- `nyc_taxi_demo.yml` — **orphan.** A BSL model for the synthetic tables, left over from an
  earlier version of the demo. Nothing loads it. Note its join uses `left_on`/`right_on`, which
  is *not* the syntax the pinned BSL 0.1.4 accepts — so it is also stale, not just unused.

## Running

Must be run from inside `demo/` — both scripts use bare relative paths.

```bash
cd demo
uv run --isolated --with duckdb --with pandas python make_data.py
uv run --isolated --with duckdb --with pandas python before_after_demo.py
```

`--isolated` is deliberate: it keeps this demo working regardless of what the parent project's
lockfile resolves to.

## Load-bearing detail

The expected output is **Manhattan `trip_count = 6` vs `3`** in the BEFORE section, and `3 == 3`
in the AFTER section. That 6-vs-3 split is the entire point of the demo and is asserted on in
prose in the root `README.md`. It depends on:

- `LocationID 4` appearing exactly twice in `taxi_zones_tbl` (fan-out doubles 3 trips → 6), and
- exactly 3 trips having `PULocationID = 4`.

Do not "clean up" the duplicate row in `make_data.py`. Changing either number breaks the demo and
silently invalidates the README.

The `NULL` fare on `trip_id 7` is also intentional (voided trip), though the current demo does not
yet exercise the AVG-ignores-NULL divergence it was seeded for.

## Why plain SQL instead of BSL here

Deliberate. BSL's YAML join syntax churned across releases while this was being written, so the
"after" half demonstrates the *concept* (one definition, called by every consumer) as a plain
Python function. This keeps the demo runnable years from now with zero version pinning. If you
rewrite it to use BSL, you re-introduce exactly the fragility it was written to avoid.
