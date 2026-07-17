"""
BEFORE vs AFTER demo for sspaeti/semantic-layer-duckdb
=======================================================

Question everyone asks: "trip count and average fare by borough?"

BEFORE (no semantic layer): two analysts each write their own SQL/Ibis.
Both look reasonable. Both compile. Both run without error.
They give DIFFERENT numbers -- because the join and the null-handling
logic live in two places and were each implemented slightly differently.

AFTER (with a semantic layer): the join + the measures are defined ONCE,
in a single METRICS definition. Every consumer calls the same function
and gets the identical, correct number -- no join/aggregation logic
copy-pasted into each script.

Note: the "after" half here is written in plain Ibis rather than calling
boring-semantic-layer directly. That's a deliberate choice: BSL's YAML
join syntax has changed across recent releases (we hit 3 different
required keys -- `with`, then `left_on`/`right_on`, then `with` again --
across different resolved versions while building this demo), so this
version demonstrates the *concept* (one definition, reused everywhere)
without depending on a fast-moving library API. The real project
(nyc_taxi.py / nyc_taxi.yml) still uses boring-semantic-layer itself.
"""
import duckdb

con = duckdb.connect(":memory:")

print("=" * 70)
print("BEFORE: two analysts independently write 'raw' queries")
print("=" * 70)

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
        SELECT DISTINCT ON ("LocationID") "LocationID", "Borough"
        FROM read_csv('zones.csv')
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
print("AFTER: one definition (join + measures), called by every consumer")
print("=" * 70)

# THE SEMANTIC LAYER, in miniature: the join and the measures are defined
# ONCE, right here. Every "dashboard" below calls this same function --
# none of them writes their own join or aggregation logic.
def query_trips_by_borough(con):
    return con.execute("""
        WITH zones_deduped AS (
            SELECT DISTINCT ON ("LocationID") "LocationID", "Borough"
            FROM read_csv('zones.csv')
        )
        SELECT z."Borough",
               COUNT(*)                       AS trip_count,
               AVG(t.base_passenger_fare)      AS avg_base_fare
        FROM read_parquet('trips.parquet') t
        JOIN zones_deduped z ON t."PULocationID" = z."LocationID"
        GROUP BY z."Borough"
        ORDER BY z."Borough"
    """).df()

dashboard_1 = query_trips_by_borough(con)
dashboard_2 = query_trips_by_borough(con)

print("\nDashboard #1 (calls the shared definition):")
print(dashboard_1)
print("\nDashboard #2 (calls the shared definition), same question:")
print(dashboard_2)
print("\n>>> Identical every time, because there is only one place the",
      "\n    join + the metric formula could have been written. <<<")

print()
print("=" * 70)
print("WHAT CHANGED")
print("=" * 70)
print("Before: every consumer script re-writes the join + the aggregation.")
print("  -> easy for one copy to drift from another (as shown above).")
print()
print("After: the join + the aggregation are written ONCE, in one function")
print("(or, in the real project, one YAML file). Every consumer just calls")
print("it -- there is no second copy of the logic that could drift.")
