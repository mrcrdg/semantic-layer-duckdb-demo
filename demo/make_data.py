"""
Builds a tiny synthetic stand-in for the real NYC taxi tables used in
sspaeti/semantic-layer-duckdb, with the SAME column names as nyc_taxi.yml
(PULocationID, base_passenger_fare, Borough, Zone, service_zone, ...).

On purpose, it bakes in a data-quality flaw that is extremely common in
real lookup tables: LocationID 4 ("Manhattan / Union Sq") appears TWICE
in the zone lookup (e.g. from a re-run ingestion job that appended
instead of replaced). This is the same *class* of bug reported against
this exact join in boring-semantic-layer issue #32.
"""
import duckdb

con = duckdb.connect(":memory:")

con.execute("""
CREATE TABLE trips_tbl AS
SELECT * FROM (VALUES
    (1, 4,  28.50),
    (2, 4,  31.00),
    (3, 4,  22.75),
    (4, 7,  19.90),
    (5, 7,  24.10),
    (6, 12, 45.00),
    (7, 12, NULL),   -- voided / refunded trip: fare never captured
    (8, 12, 38.20),
    (9, 1,  15.60),
    (10, 1, 17.40)
) AS t(trip_id, "PULocationID", base_passenger_fare)
""")

con.execute("""
CREATE TABLE taxi_zones_tbl AS
SELECT * FROM (VALUES
    (1,  'Bronx',      'Mott Haven',        'Boro Zone'),
    (4,  'Manhattan',  'Union Sq',          'Yellow Zone'),
    (4,  'Manhattan',  'Union Sq (resend)', 'Yellow Zone'),  -- duplicate row, same LocationID
    (7,  'Queens',     'Astoria',           'Boro Zone'),
    (12, 'Brooklyn',   'Williamsburg',      'Boro Zone')
) AS t("LocationID", "Borough", "Zone", service_zone)
""")

con.execute("COPY trips_tbl TO 'trips.parquet' (FORMAT PARQUET)")
con.execute("COPY taxi_zones_tbl TO 'zones.csv' (FORMAT CSV, HEADER)")
print("Wrote trips.parquet and zones.csv")
print()
print("trips_tbl:")
print(con.execute("SELECT * FROM trips_tbl ORDER BY trip_id").df())
print()
print("taxi_zones_tbl (note: LocationID 4 appears twice):")
print(con.execute("SELECT * FROM taxi_zones_tbl ORDER BY \"LocationID\"").df())
