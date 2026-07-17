# semantic-layer-duckdb

Demo testing a semantic layer — a way to define business metrics, in a single file, instead of re-writing the same SQL/join logic every time someone wants to ask a question. Once defined, it is possible to query those metrics with plain python language — no need to know the underlying joins, table names, or aggregation formulas.

Here, it's demonstrated on NYC taxi trip data using DuckDB and [boring semantic layer](https://github.com/boringdata/boring-semantic-layer/) (a lightweight semantic layer library built on top of Ibis). The goal is to show what a semantic layer buys: consistent metric definitions, reusable across every query, without duplicating logic.

Two things are in this repo:
1. **`nyc_taxi.py` / `nyc_taxi.yml`** — a real semantic layer over the actual 20M-row NYC taxi dataset. This is the main example.
2. **`demo/`** — a small, self-contained script proving *why* this matters, using a tiny synthetic dataset instead of the real one. See [Why this matters](#why-this-matters-before-vs-after) below.

## Quick Start

Install [uv](https://docs.astral.sh/uv/) then run:
```bash
make install  # Install dependencies  | Or use `uv sync` directly
make run      # Run NYC taxi analysis | Or use `uv run python nyc_taxi.py` directly
```

> **NOTE: Download NYC data locally to not get 403 forbidden if you execute too many times**
>
> ```sh
> wget https://d37ci6vzurychx.cloudfront.net/trip-data/fhvhv_tripdata_2025-06.parquet
> wget https://d37ci6vzurychx.cloudfront.net/misc/taxi+_zone_lookup.csv
> ```

## What you get when you run it

`make run` executes `nyc_taxi.py`, which loads the semantic model from `nyc_taxi.yml` and runs five example queries against it — each answering a different kind of practical question (trip volume, popularity, pricing, revenue, accessibility). None of these queries write any SQL or joins by hand; they all just ask the pre-defined model for dimensions and measures by name.

**First, the model tells you what's queryable**, before you write a single query — this is the semantic layer introspecting itself:

```
Available dimensions (taxi_zones): ['location_id', 'borough', 'zone', 'service_zone']
Available measures (taxi_zones): ['zone_count']

Available dimensions (fhvhv_trips): ['hvfhs_license_num', ..., 'pickup_zone.borough', 'pickup_zone.zone', 'pickup_zone.service_zone']
Available measures (fhvhv_trips): ['trip_count', 'avg_trip_miles', 'avg_trip_time', 'avg_base_fare', 'total_revenue', 'avg_tips', 'avg_driver_pay', 'shared_trip_rate', 'wheelchair_request_rate', 'pickup_zone.zone_count']
```
The `pickup_zone.*` entries are dimensions from the *joined* zone lookup table — you get them for free once the join is defined in the YAML, without writing any join logic yourself.

**Then, five queries run against that model.** Each one below is: the question asked, the result, and one line on what it reveals about the data.

### 1. Trip volume by pickup borough
*"How many trips came from each borough, and how do fares compare?"*

| Borough | Trips | Avg miles | Avg fare |
|---|---|---|---|
| Manhattan | 7,122,571 | 5.30 | $33.58 |
| Brooklyn | 5,433,158 | 4.22 | $23.28 |
| Queens | 4,453,220 | 6.38 | $29.78 |
| Bronx | 2,541,614 | 4.40 | $20.31 |
| Staten Island | 316,533 | 5.26 | $22.20 |

**Takeaway:** Manhattan has the most trips but *not* the longest ones — its fares are highest despite shorter average distance, consistent with dense, short, expensive rides in the borough.

### 2. Most popular pickup zones
*"Which specific zones (not just boroughs) generate the most trips and revenue?"*

| Zone | Borough | Trips | Avg miles | Revenue |
|---|---|---|---|---|
| LaGuardia Airport | Queens | 436,708 | 11.95 | $27.4M |
| JFK Airport | Queens | 344,323 | 17.61 | $25.7M |
| Crown Heights North | Brooklyn | 262,172 | 3.77 | $5.8M |
| Times Sq/Theatre District | Manhattan | 234,675 | 6.55 | $10.6M |
| Bushwick South | Brooklyn | 228,584 | 4.14 | $5.4M |

**Takeaway:** the two airports dominate by revenue despite modest trip counts — long trips (12-18 miles) at premium fares.

### 3. Service zone analysis
*"Do fares and tipping behavior differ between Yellow Zone, Boro Zone, and Airports?"*

| Service zone | Trips | Avg fare | Avg tips | Shared-ride rate |
|---|---|---|---|---|
| Boro Zone | 13,066,427 | $22.23 | $0.72 | 2.27% |
| Yellow Zone | 6,019,638 | $35.42 | $1.92 | 1.16% |
| Airports | 781,031 | $68.07 | $4.61 | 0.0003% |

**Takeaway:** Airport trips cost ~2x Yellow Zone and ~3x Boro Zone fares — and are essentially never shared (0.0003% vs 1-2% elsewhere), which makes sense given airport pickups are usually solo travelers with luggage.

### 4. Revenue by service zone
*"Where does the money actually come from, and how well are drivers paid in each zone?"*

| Service zone | Trips | Total revenue | Avg driver pay | Avg miles |
|---|---|---|---|---|
| Boro Zone | 13,066,427 | $290.5M | $18.57 | 4.46 |
| Yellow Zone | 6,019,638 | $213.2M | $24.52 | 5.37 |
| Airports | 781,031 | $53.2M | $50.77 | 14.44 |

**Takeaway:** despite having 6% of the trip volume, Airports generate ~10% of total revenue and pay drivers over 2x more per trip on average.

### 5. Accessibility metrics
*"Is the service being used equitably across boroughs for wheelchair-accessible requests?"*

| Borough | Trips | Wheelchair request rate | Shared-ride rate |
|---|---|---|---|
| Bronx | 2,541,614 | 0.38% | 2.17% |
| Staten Island | 316,533 | 0.34% | 1.45% |
| Brooklyn | 5,433,158 | 0.33% | 2.39% |
| Manhattan | 7,122,571 | 0.30% | 1.30% |
| Queens | 4,453,220 | 0.27% | 1.90% |

**Takeaway:** wheelchair-accessible request rates are consistently under 0.4% across every borough — a small but non-zero fraction that a semantic layer makes trivial to track over time without re-deriving the calculation each time.

---

The point of all five tables above isn't the taxi insights themselves — it's that **every one of them came from the same reusable `.query(dimensions=..., measures=...)` call** against the `fhvhv_trips` model defined in `nyc_taxi.yml`. None of them needed a new join or a new aggregation formula written by hand; only the `dimensions=` and `measures=` arguments changed between queries.

<details>
<summary>Raw terminal output (click to expand)</summary>

```
❯ make run
uv run python nyc_taxi.py
Available dimensions (taxi_zones): ['location_id', 'borough', 'zone', 'service_zone']
Available measures (taxi_zones): ['zone_count']

Available dimensions (fhvhv_trips): ['hvfhs_license_num', 'dispatching_base_num', 'originating_base_num', 'request_datetime', 'pickup_datetime', 'dropoff_datetime', 'trip_miles', 'trip_time', 'base_passenger_fare', 'tolls', 'bcf', 'sales_tax', 'congestion_surcharge', 'airport_fee', 'tips', 'driver_pay', 'shared_request_flag', 'shared_match_flag', 'access_a_ride_flag', 'wav_request_flag', 'wav_match_flag', 'pickup_zone.location_id', 'pickup_zone.borough', 'pickup_zone.zone', 'pickup_zone.service_zone']
Available measures (fhvhv_trips): ['trip_count', 'avg_trip_miles', 'avg_trip_time', 'avg_base_fare', 'total_revenue', 'avg_tips', 'avg_driver_pay', 'shared_trip_rate', 'wheelchair_request_rate', 'pickup_zone.zone_count']

=== Trip Volume by Pickup Borough ===
Top 5 boroughs by trip volume:
  pickup_zone_borough  trip_count  avg_trip_miles  avg_base_fare
0           Manhattan     7122571        5.296985      33.575738
1            Brooklyn     5433158        4.215820      23.280429
2              Queens     4453220        6.379047      29.778835
3               Bronx     2541614        4.400500      20.313596
4       Staten Island      316533        5.262288      22.200712

=== Popular Pickup Zones ===
Top 10 pickup zones by trip count:
            pickup_zone_zone pickup_zone_borough  trip_count  avg_trip_miles  total_revenue
0          LaGuardia Airport              Queens      436708       11.948670    27430520.84
1                JFK Airport              Queens      344323       17.605666    25737628.22
2        Crown Heights North            Brooklyn      262172        3.770218     5804554.54
3  Times Sq/Theatre District           Manhattan      234675        6.549750    10573271.77
4             Bushwick South            Brooklyn      228584        4.138090     5419196.40
5             Midtown Center           Manhattan      225063        5.580742     9746426.13
6               East Village           Manhattan      222519        4.800763     6720649.62
7              East New York            Brooklyn      221220        3.829781     4122720.29
8       TriBeCa/Civic Center           Manhattan      212781        5.304404     7865380.79
9  Williamsburg (North Side)            Brooklyn      204630        4.609138     6006392.54

=== Service Zone Analysis ===
Trip metrics by service zone:
  pickup_zone_service_zone  trip_count  avg_base_fare  avg_tips  shared_trip_rate
0                Boro Zone    13066427      22.231723  0.717455          0.022743
1              Yellow Zone     6019638      35.424518  1.924227          0.011609
2                 Airports      781031      68.074313  4.613058          0.000003
3                      N/A         913      26.176429  0.539934          0.014239

=== Revenue Analysis by Trip Distance ===
Revenue by service zone:
  pickup_zone_service_zone  trip_count  total_revenue  avg_driver_pay  avg_trip_miles
0                Boro Zone    13066427   2.904892e+08       18.569082        4.458598
1              Yellow Zone     6019638   2.132428e+08       24.515914        5.374520
2                 Airports      781031   5.316815e+07       50.774571       14.442597
3                      N/A         913   2.389908e+04       22.145104        6.200545

=== Accessibility Metrics ===
Accessibility metrics by pickup borough:
  pickup_zone_borough  trip_count  wheelchair_request_rate  shared_trip_rate
0                 N/A         913                 0.005476          0.014239
1               Bronx     2541614                 0.003761          0.021734
2       Staten Island      316533                 0.003409          0.014520
3            Brooklyn     5433158                 0.003331          0.023856
4           Manhattan     7122571                 0.002980          0.013039
5              Queens     4453220                 0.002683          0.019028
```
</details>

## Why this matters: before vs. after

Everything above shows the semantic layer being *convenient* — fewer lines, no hand-written joins. But convenience isn't the strongest argument for using one. The stronger argument is **consistency**: without a shared definition, two people can both write reasonable-looking, error-free code and get *different* answers to the same question.

`demo/before_after_demo.py` proves this with a small, self-contained, runnable script — no need to download the 20M-row NYC file — that reproduces a realistic bug and shows how a shared definition prevents it.

### The setup

Two synthetic data sources, same shape as the real ones in this repo:
- a `trips` table (`PULocationID`, `base_passenger_fare`, ...)
- a `zones` lookup table (`LocationID`, `Borough`, ...) — with a **realistic data-quality flaw baked in**: `LocationID 4` ("Union Sq") appears **twice**, because a re-ingestion job appended instead of replaced. This is the same class of bug reported in [boring-semantic-layer issue #32](https://github.com/boringdata/boring-semantic-layer/issues/32).

### Before: two analysts, two answers, no error message

Two people independently answer "trip count and average fare by borough?" — one writes the obvious join, the other happens to add a `DISTINCT` because they'd seen dodgy lookup tables before. Both scripts run cleanly, with no error from either:

```
Analyst A's result (Dashboard #1):
     Borough  trip_count  avg_base_fare
2  Manhattan           6      27.416667      <-- inflated by the duplicate row

Analyst B's result (Dashboard #2), same question, same day:
     Borough  trip_count  avg_base_fare
2  Manhattan           3      27.416667      <-- correct

>>> Manhattan trip_count disagrees: Dashboard #1 says 6, Dashboard #2 says 3 <<<
>>> Neither query errored. Nobody would notice unless they compared them. <<<
```

**This is the real risk of not having a semantic layer**: not that queries fail, but that they *silently succeed with different answers*, because the join logic is duplicated and each copy drifts.

### After: one definition, every consumer agrees

With the join and the aggregation defined **once**, as a single shared function, instead of copy-pasted into every script:

```python
def query_trips_by_borough(con):
    return con.execute("""
        WITH zones_deduped AS (
            SELECT DISTINCT ON ("LocationID") "LocationID", "Borough"
            FROM read_csv('zones.csv')
        )
        SELECT z."Borough", COUNT(*) AS trip_count, AVG(t.base_passenger_fare) AS avg_base_fare
        FROM read_parquet('trips.parquet') t
        JOIN zones_deduped z ON t."PULocationID" = z."LocationID"
        GROUP BY z."Borough"
    """).df()
```

Now *any* consumer calling `query_trips_by_borough(con)` gets the same, correct number:

```
Dashboard #1 (calls the shared definition):
     Borough  trip_count  avg_base_fare
2  Manhattan           3      27.416667

Dashboard #2 (calls the shared definition), same question:
     Borough  trip_count  avg_base_fare
2  Manhattan           3      27.416667

>>> Identical every time, because there is only one place the
    join + the metric formula could have been written. <<<
```

This is a small stand-in for what `nyc_taxi.yml` does for real: the fix (deduping the zone lookup) lives in **one place**, and everything downstream inherits it automatically.

### The duplication, quantified

| | Before (raw, duplicated) | After (one shared definition) |
|---|---|---|
| Places the join is written | once per consumer script (2, 5, 10...) | once |
| Places the metric formula is defined | once per consumer script | once |
| Fixing a data bug (like the duplicate zone row) | edit every script that joins to `zones` | edit the one definition |
| Risk of two dashboards silently disagreeing | yes (demonstrated above) | no — same code path every time |

### Run it yourself

Only needs `duckdb` and `pandas` — nothing else, no version pinning to worry about:

```bash
cd demo

# Step 1: generate the synthetic trips/zones data (takes a few seconds, no download needed)
uv run --isolated --with duckdb --with pandas python make_data.py

# Step 2: run the before/after comparison
uv run --isolated --with duckdb --with pandas python before_after_demo.py
```

**What to look for in the output:**

1. Under `BEFORE`: two tables, both labeled "Manhattan" — **Dashboard #1 says `trip_count = 6`, Dashboard #2 says `trip_count = 3`**, for the exact same question, run the same day, with neither query throwing an error.
2. Under `AFTER`: two tables, both showing **`trip_count = 3`** for Manhattan — identical, because both dashboards call the same shared function instead of each writing their own copy of the join and aggregation.

If your output doesn't show that split (6 vs. 3) in the BEFORE section, re-run `make_data.py` first.

> **Why plain DuckDB instead of `boring-semantic-layer` for this specific demo:** the "after" half here demonstrates the underlying concept (one definition, called by every consumer) in plain Python rather than via `boring-semantic-layer` itself, because that library's YAML join syntax has changed across recent releases. The main project (`nyc_taxi.py` / `nyc_taxi.yml`) still uses `boring-semantic-layer` directly — if you hit a `ValueError` about a missing join field running that one, check which version got installed (`uv pip show boring-semantic-layer`) against what `nyc_taxi.yml`'s syntax expects.
