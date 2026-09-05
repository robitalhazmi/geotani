"""Load processed boundaries into PostGIS."""

import argparse
import os
from pathlib import Path

import geopandas as gpd
from shapely.geometry import MultiPolygon, Polygon
from sqlalchemy import create_engine, text

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed" / "boundaries"
DEFAULT_DB_URL = "postgresql://geotani:geotani_dev@localhost:5432/geotani"


def get_engine():
    db_url = os.environ.get("DATABASE_URL", DEFAULT_DB_URL)
    return create_engine(db_url)


def create_tables(engine, drop=False):
    with engine.begin() as conn:
        if drop:
            print("Dropping existing tables...")
            conn.execute(text("DROP TABLE IF EXISTS suitability_scores CASCADE;"))
            conn.execute(text("DROP TABLE IF EXISTS villages CASCADE;"))

        exists_q = text(
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'villages');"
        )
        res = conn.execute(exists_q)
        exists = res.scalar()
        if exists and not drop:
            count = conn.execute(text("SELECT COUNT(*) FROM villages;")).scalar()
            if count > 0:
                print(f"Table 'villages' has {count} rows. Skipping creation (use --drop).")
                return False

        print("Creating tables...")
        conn.execute(
            text(
                """
            CREATE TABLE IF NOT EXISTS villages (
                id SERIAL PRIMARY KEY,
                adm_pcode TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                kecamatan TEXT,
                kabupaten TEXT,
                province TEXT,
                resolution TEXT NOT NULL,
                geom GEOMETRY(MultiPolygon, 4326) NOT NULL
            );
        """
            )
        )

        conn.execute(
            text(
                """
            CREATE TABLE IF NOT EXISTS suitability_scores (
                id SERIAL PRIMARY KEY,
                village_id INTEGER REFERENCES villages(id),
                crop TEXT NOT NULL,
                score NUMERIC(5,2) NOT NULL,
                climate_score NUMERIC(5,2),
                soil_score NUMERIC(5,2),
                terrain_score NUMERIC(5,2),
                access_score NUMERIC(5,2),
                computed_at TIMESTAMPTZ DEFAULT now(),
                UNIQUE(village_id, crop)
            );
        """
            )
        )
        return True


def force_multipolygon(geom):
    if geom is None:
        return None
    if isinstance(geom, Polygon):
        return MultiPolygon([geom])
    return geom


def load_data(engine):
    in_file = DATA_PROCESSED / "geotani_boundaries.gpkg"
    if not in_file.exists():
        in_file = DATA_PROCESSED / "taniscope_boundaries.gpkg"
    if not in_file.exists():
        raise FileNotFoundError(f"Input file not found: {in_file}")

    print(f"Reading from {in_file}...")
    gdf = gpd.read_file(in_file)

    print("Ensuring MultiPolygon geometries...")
    gdf["geometry"] = gdf["geometry"].apply(force_multipolygon)

    print("Loading into PostGIS...")
    gdf = gdf.rename(columns={"geometry": "geom"}).set_geometry("geom")

    gdf.to_postgis(
        "villages",
        engine,
        if_exists="append",
        index=False,
        dtype={"geom": "Geometry('MULTIPOLYGON', 4326)"},
    )

    with engine.begin() as conn:
        print("Running ST_MakeValid on loaded geometries...")
        res = conn.execute(
            text("UPDATE villages SET geom = ST_MakeValid(geom) WHERE ST_IsValid(geom) = false;")
        )
        invalid_fixed = res.rowcount
        print(f"Fixed {invalid_fixed} invalid geometries via PostGIS.")

        print("Creating indexes...")
        conn.execute(
            text("CREATE INDEX IF NOT EXISTS idx_villages_geom ON villages USING GIST (geom);")
        )
        conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS idx_villages_resolution "
                "ON villages (resolution);"
            )
        )

        print("Creating spatial view 'village_suitability' for Martin tile server...")
        conn.execute(text("DROP VIEW IF EXISTS village_suitability CASCADE;"))
        conn.execute(
            text(
                """
            CREATE VIEW village_suitability AS
            SELECT
                v.id,
                v.adm_pcode,
                v.name,
                v.kecamatan,
                v.kabupaten,
                v.province,
                v.resolution,
                v.geom,
                MAX(CASE WHEN s.crop = 'coffee' THEN s.score END)::float AS score_coffee,
                MAX(CASE WHEN s.crop = 'cocoa' THEN s.score END)::float AS score_cocoa,
                MAX(CASE WHEN s.crop = 'sugarcane' THEN s.score END)::float AS score_sugarcane
            FROM villages v
            LEFT JOIN suitability_scores s ON v.id = s.village_id
            GROUP BY
                v.id, v.adm_pcode, v.name, v.kecamatan,
                v.kabupaten, v.province, v.resolution, v.geom;
        """
            )
        )

    # Print summary
    with engine.connect() as conn:
        total_rows = conn.execute(text("SELECT COUNT(*) FROM villages;")).scalar()
        res_counts = conn.execute(
            text("SELECT resolution, COUNT(*) FROM villages GROUP BY resolution;")
        ).fetchall()
        prov_counts = conn.execute(
            text(
                "SELECT province, COUNT(*) FROM villages "
                "WHERE resolution='village' GROUP BY province;"
            )
        ).fetchall()
        size_res = conn.execute(
            text("SELECT pg_size_pretty(pg_total_relation_size('villages'));")
        ).scalar()

    print("\n--- Summary ---")
    print(f"Total rows loaded: {total_rows}")
    print("Rows per resolution type:")
    for r, count in res_counts:
        print(f"  {r}: {count}")
    print("Rows per province (village resolution):")
    for p, count in prov_counts:
        print(f"  {p}: {count}")
    print(f"Invalid geometries fixed by ST_MakeValid: {invalid_fixed}")
    print(f"Table size on disk: {size_res}")


def main():
    parser = argparse.ArgumentParser(description="Load boundaries into PostGIS.")
    parser.add_argument("--drop", action="store_true", help="Drop and recreate tables if existing.")
    args = parser.parse_args()

    engine = get_engine()
    if create_tables(engine, args.drop):
        load_data(engine)
    else:
        print("✓ Villages table already loaded. Ensuring spatial views and indexes exist...")
        with engine.begin() as conn:
            conn.execute(
                text("CREATE INDEX IF NOT EXISTS idx_villages_geom ON villages USING GIST (geom);")
            )
            conn.execute(
                text("CREATE INDEX IF NOT EXISTS idx_villages_pcode ON villages (adm_pcode);")
            )
            conn.execute(text("DROP VIEW IF EXISTS village_suitability CASCADE;"))
            conn.execute(
                text(
                    """
                CREATE VIEW village_suitability AS
                SELECT
                    v.id,
                    v.adm_pcode,
                    v.name,
                    v.kecamatan,
                    v.kabupaten,
                    v.province,
                    v.resolution,
                    v.geom,
                    MAX(CASE WHEN s.crop = 'coffee' THEN s.score END)::float AS score_coffee,
                    MAX(CASE WHEN s.crop = 'cocoa' THEN s.score END)::float AS score_cocoa,
                    MAX(CASE WHEN s.crop = 'sugarcane' THEN s.score END)::float AS score_sugarcane
                FROM villages v
                LEFT JOIN suitability_scores s ON v.id = s.village_id
                GROUP BY
                    v.id, v.adm_pcode, v.name, v.kecamatan,
                    v.kabupaten, v.province, v.resolution, v.geom;
            """
                )
            )
        print("✓ View 'village_suitability' refreshed.")


if __name__ == "__main__":
    main()
