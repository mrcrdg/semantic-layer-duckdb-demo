"""
BEFORE vs AFTER demo for sspaeti/semantic-layer-duckdb
=======================================================

Question everyone asks: "trip count and average fare by borough?"

BEFORE (no semantic layer): two analysts each write their own SQL/Ibis.
Both look reasonable. Both compile. Both run without error.
They give DIFFERENT numbers -- because the join and the null-handling
logic live in two places and were each implemented slightly differently.

AFTER (with boring-semantic-layer): the join + the measure are defined
ONCE in nyc_taxi.yml. Every consumer gets the identical, correct number.
"""
import duckdb
import ibis
from boring_semantic_layer import from_yaml

print("=" * 70)
print("BEFORE: two analysts independently write 'raw' queries")
print("=" * 70)

con = duckdb.connect(":memory:")

# --- Analyst A: straightforward join, forgets the lookup table has a
#     duplicate row for LocationID 4 -> trips fan out (double-counted)
analyst_a = con.execute("""
    SELECT z."Borough",
           COUNT(*)                       AS trip_count,
           AVG(t.base_passenger_fare)      AS avg_base_fare
    FROM read_parquet('trips.parquet') t
    JOIN read_csv('zones.csv') z ON t."PULocationID" = z."LocationID"
    GROUP BY z."Borough"
    ORDER BY z."Borough"
""").df()

# --- Analyst B: dedupes the zone lookup before joining (the "correct"
#     approach), but does it independently, in their own script
analyst_b = con.execute("""
    WITH zones_deduped AS (
        SELECT DISTINCT "LocationID", "Borough" FROM read_csv('zones.csv')
    )
    SELECT z."Borough",
           COUNT(*)                       AS trip_count,
           AVG(t.base_passenger_fare)      AS avg_base_fare
    FROM read_parquet('trips.parquet') t
    JOIN zones_deduped z ON t."PULocationID" = z."LocationID"
    GROUP BY z."Borough"
    ORDER BY z."Borough"
""").df()

print("\nAnalyst A's result (Dashboard #1):")
print(analyst_a)
print("\nAnalyst B's result (Dashboard #2), same question, same day:")
print(analyst_b)

manhattan_a = analyst_a.loc[analyst_a.Borough == "Manhattan", "trip_count"].iloc[0]
manhattan_b = analyst_b.loc[analyst_b.Borough == "Manhattan", "trip_count"].iloc[0]
print(f"\n>>> Manhattan trip_count disagrees: Dashboard #1 says {manhattan_a}, "
      f"Dashboard #2 says {manhattan_b} <<<")
print(">>> Neither query errored. Nobody would notice unless they compared them. <<<")

print()
print("=" * 70)
print("AFTER: one semantic-layer definition (nyc_taxi.yml-style), used twice")
print("=" * 70)

bcon = ibis.duckdb.connect(":memory:")
tables = {
    # The dedup fix is applied ONCE, right here, at the data-prep step --
    # not copy-pasted into every consumer query like Analyst B had to.
    "taxi_zones_tbl": bcon.read_csv("zones.csv").distinct(on=["LocationID"]),
    "trips_tbl": bcon.read_parquet("trips.parquet"),
}
models = from_yaml("nyc_taxi_demo.yml", tables=tables)
trips_sm = models["fhvhv_trips_demo"]

# "Dashboard #1" and "Dashboard #2" now both just call the model --
# neither of them writes a single line of join or aggregation logic.
q1 = trips_sm.query(
    dimensions=["pickup_zone.borough"],
    measures=["trip_count", "avg_base_fare"],
).execute()
q2 = trips_sm.query(
    dimensions=["pickup_zone.borough"],
    measures=["trip_count", "avg_base_fare"],
).execute()
sort_col = [c for c in q1.columns if "borough" in c][0]
dashboard_1 = q1.sort_values(sort_col)
dashboard_2 = q2.sort_values(sort_col)

print("\nDashboard #1 (via semantic layer):")
print(dashboard_1)
print("\nDashboard #2 (via semantic layer), same question:")
print(dashboard_2)
print("\n>>> Identical every time, because there is only one place the",
      "\n    join + the metric formula could have been written. <<<")

print()
print("=" * 70)
print("LINES OF LOGIC THAT DEFINE THE JOIN + METRIC")
print("=" * 70)
print("Before (raw): join logic duplicated in every script that needs it")
print("  - Analyst A's script:  3 lines of join/groupby logic")
print("  - Analyst B's script:  5 lines of join/groupby logic (dedup added)")
print("  - a 3rd, 4th, 5th consumer: 3-5 MORE lines each, copy-pasted")
print()
print("After (semantic layer): join + metric logic defined ONCE, in YAML")
print("  - joins.pickup_zone:        3 lines, in nyc_taxi_demo.yml")
print("  - measures.avg_base_fare:   1 line,  in nyc_taxi_demo.yml")
print("  - every consumer query:     2 lines of Python, zero SQL")
