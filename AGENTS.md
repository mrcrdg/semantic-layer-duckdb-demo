# AGENTS.md

Guidance for AI coding agents working in this repo.

## What this project is

A teaching/demo repo, not a product. It shows what a **semantic layer** buys you: business
metrics (dimensions, measures, joins) defined **once** in a declarative YAML file, then queried
by name instead of re-deriving SQL in every consumer script.

Stack: [DuckDB](https://duckdb.org) (engine) + [Ibis](https://ibis-project.org) (expressions) +
[boring-semantic-layer](https://github.com/boringdata/boring-semantic-layer) (BSL, the semantic
layer) + Altair/Vega-Lite (charting).

There are **two independent halves**, and they do not share code:

| Path | What it is | Dependencies |
|---|---|---|
| `nyc_taxi.py` + `nyc_taxi.yml` | The real semantic layer, over the ~20M-row public NYC FHVHV dataset | BSL, Ibis, DuckDB, Altair |
| `demo/` | A self-contained before/after script proving *why* a shared definition matters, on ~10 synthetic rows | `duckdb` + `pandas` only |

`demo/` deliberately does **not** use BSL — see `demo/AGENTS.md`.

## Layout

```
nyc_taxi.py       Entry point: connects DuckDB, loads the model, runs 5 queries, writes a PNG
nyc_taxi.yml      The semantic model — the heart of the repo. Two models + one join.
nyc_taxi.md       Hand-written notes on the YAML schema and BSL's join syntax
Makefile          install / run targets
README.md         Long-form narrative with expected output tables. Keep in sync with real output.
demo/             Standalone before/after demo (see demo/AGENTS.md)
data/             Gitignored scratch dir. Currently holds unrelated flights/carriers parquet — dead weight.
*.png             Committed chart output from nyc_taxi.py
```

## Commands

```bash
make install   # uv sync — installs from pyproject.toml + uv.lock
make run       # uv run python nyc_taxi.py
```

`make` with no target fails: `.DEFAULT_GOAL := query` but there is no `query` target.

`nyc_taxi.py` resolves `nyc_taxi.yml` relative to the **current working directory**, so it must
be run from the repo root.

## Critical constraints

**BSL is pinned for a reason.** `uv.lock` pins `boring-semantic-layer==0.1.4`. Its YAML join key
has changed across releases (`with:` → `left_on`/`right_on` → `with:`). `nyc_taxi.yml` uses
`with: _.PULocationID`, which is correct for 0.1.4. **Do not bump BSL without re-running
`make run`** — a version mismatch surfaces as a `ValueError` about a missing join field, not a
clean error. `requirements.txt` does *not* pin it and will drift; prefer `uv sync`.

**The remote dataset rate-limits.** `nyc_taxi.py` reads the parquet/CSV straight from
`d37ci6vzurychx.cloudfront.net`. Repeated runs return HTTP 403. For iteration, download once and
switch to the commented-out local branch of the `tables` dict — but note `BASE_PATH` currently
points at `/home/sspaeti/...`, a path from the upstream repo this was derived from. Fix it to a
local path rather than leaving it.

**Queries are expensive.** Each `.execute()` scans ~20M rows over the network. When verifying a
change to `nyc_taxi.yml`, test against a tiny in-memory table instead of running the full script.

**Known modeling limitation.** Only `pickup_zone` is joined. Joining `taxi_zones` twice
(pickup + dropoff) produces ambiguous column references in BSL's YAML. Documented in
`nyc_taxi.md`; don't "fix" it casually.

## Conventions

- YAML dimensions/measures use Ibis deferred expressions with the `_` placeholder:
  `avg_base_fare: _.base_passenger_fare.mean()`.
- Rate-style measures come from boolean means on `'Y'`/`'N'` string flags:
  `shared_trip_rate: (_.shared_match_flag == 'Y').mean()`.
- Joined dimensions are addressed as `pickup_zone.borough` and come back in results as
  `pickup_zone_borough` (dot → underscore). Chart specs must use the underscore form.
- Model YAML names snake_case; keep the alias/column mapping explicit even when they match.

## Editing rules

- **README.md contains real, pasted output.** If a change alters query results, columns, or
  measure names, re-run and update the tables *and* the collapsed raw-terminal block. Stale
  numbers in this repo are worse than a bug — the numbers are the whole point.
- There are no tests and no CI. Verification is manual: run it and read the output.
- This is a pedagogical repo. Prefer explicit, readable code over clever code; a reader who has
  never seen a semantic layer is the target audience.
