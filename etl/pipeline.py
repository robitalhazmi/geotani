"""TaniScope End-to-End Suitability Scoring Pipeline.

Orchestrates:
  1. Environmental factor extraction (or loads cached factors)
  2. Multi-crop suitability scoring (Coffee, Cocoa, Sugarcane)
  3. Output generation (CSV, GPKG) and PostGIS ingestion
  4. Calibration summaries and benchmark validation
"""

import argparse
import os
from pathlib import Path

import geopandas as gpd
import pandas as pd
from sqlalchemy import create_engine, text

from etl.scoring.crop_params import CROP_REQUIREMENTS
from etl.scoring.fuzzy import score_village_factors
from etl.zonal_stats import extract_all_factors

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
DEFAULT_DB_URL = "postgresql://taniscope:taniscope_dev@localhost:5432/taniscope"


def run_scoring_pipeline(force_extract: bool = False, load_to_db: bool = True):
    """Run full scoring pipeline across all crops and villages."""
    factors_gpkg = DATA_PROCESSED / "village_environmental_factors.gpkg"

    # Step 1: Feature Extraction
    if force_extract or not factors_gpkg.exists():
        print("\n[Step 1/3] Running Environmental Factor Extraction...")
        gdf_factors = extract_all_factors()
    else:
        print(f"\n[Step 1/3] Loading cached environmental factors from {factors_gpkg.name}...")
        gdf_factors = gpd.read_file(factors_gpkg)

    print(f"Loaded {len(gdf_factors)} villages/regions.")

    # Step 2: Crop Suitability Scoring
    print("\n[Step 2/3] Computing Multi-Crop Suitability Scores...")
    all_scores_records = []

    for crop_id, crop_req in CROP_REQUIREMENTS.items():
        print(f"  - Scoring: {crop_req.display_name} ({crop_id})...")
        crop_scores = []
        crop_climate_scores = []
        crop_soil_scores = []
        crop_terrain_scores = []
        crop_access_scores = []

        for _, row in gdf_factors.iterrows():
            factor_dict = {
                "temp_c": row.get("temp_c"),
                "rainfall_mm": row.get("rainfall_mm"),
                "elevation_m": row.get("elevation_m"),
                "slope_deg": row.get("slope_deg"),
                "soil_ph": row.get("soil_ph"),
                "clay_pct": row.get("clay_pct"),
                "sand_pct": row.get("sand_pct"),
                "soc_g_kg": row.get("soc_g_kg"),
                "dist_road_m": row.get("dist_road_m"),
            }

            res = score_village_factors(factor_dict, crop_req)

            crop_scores.append(res["final_score"])
            crop_climate_scores.append(res["climate_score"])
            crop_soil_scores.append(res["soil_score"])
            crop_terrain_scores.append(res["terrain_score"])
            crop_access_scores.append(res["access_score"])

            all_scores_records.append(
                {
                    "adm_pcode": row["adm_pcode"],
                    "crop": crop_id,
                    "score": res["final_score"],
                    "climate_score": res["climate_score"],
                    "soil_score": res["soil_score"],
                    "terrain_score": res["terrain_score"],
                    "access_score": res["access_score"],
                }
            )

        gdf_factors[f"score_{crop_id}"] = crop_scores
        gdf_factors[f"climate_{crop_id}"] = crop_climate_scores
        gdf_factors[f"soil_{crop_id}"] = crop_soil_scores
        gdf_factors[f"terrain_{crop_id}"] = crop_terrain_scores

    # Step 3: Export Results
    print("\n[Step 3/3] Exporting Results...")
    scores_df = pd.DataFrame(all_scores_records)

    scores_csv = DATA_PROCESSED / "suitability_scores.csv"
    scores_df.to_csv(scores_csv, index=False)
    print(f"  - Saved flat scores to {scores_csv} ({len(scores_df)} rows)")

    enriched_gpkg = DATA_PROCESSED / "taniscope_scored_villages.gpkg"
    gdf_factors.to_file(enriched_gpkg, driver="GPKG")
    print(f"  - Saved enriched spatial boundaries to {enriched_gpkg}")

    if load_to_db:
        ingest_scores_to_postgis(scores_df)

    print_calibration_summary(gdf_factors)


def ingest_scores_to_postgis(scores_df: pd.DataFrame):
    """Ingest calculated scores directly into PostGIS suitability_scores table."""
    db_url = os.environ.get("DATABASE_URL", DEFAULT_DB_URL)
    print(f"\nAttempting PostGIS ingestion at {db_url}...")
    try:
        engine = create_engine(db_url)
        with engine.connect() as conn:
            table_check = conn.execute(text("SELECT to_regclass('villages');")).scalar()
            if not table_check:
                print("  - 'villages' table not found in PostGIS. Run etl/load_postgis.py first.")
                return

            print("  - Mapping village IDs from database...")
            villages_map = pd.read_sql("SELECT id, adm_pcode FROM villages;", conn)

        merged = scores_df.merge(villages_map, on="adm_pcode", how="inner")
        if len(merged) == 0:
            print("  - No matching village P-codes found in database.")
            return

        db_scores = pd.DataFrame(
            {
                "village_id": merged["id"],
                "crop": merged["crop"],
                "score": merged["score"],
                "climate_score": merged["climate_score"],
                "soil_score": merged["soil_score"],
                "terrain_score": merged["terrain_score"],
                "access_score": merged["access_score"],
            }
        )

        with engine.begin() as conn:
            print("  - Clearing previous suitability scores...")
            conn.execute(text("TRUNCATE TABLE suitability_scores RESTART IDENTITY;"))

            print(f"  - Ingesting {len(db_scores)} score records...")
            db_scores.to_sql(
                "suitability_scores", conn, if_exists="append", index=False, chunksize=5000
            )

            conn.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS idx_scores_crop_score "
                    "ON suitability_scores (crop, score);"
                )
            )
            conn.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS idx_scores_village_crop "
                    "ON suitability_scores (village_id, crop);"
                )
            )

        print("  - Successfully loaded suitability scores into PostGIS!")

    except Exception as e:
        print(f"  - Database ingestion skipped (could not connect to PostGIS): {e}")


def print_calibration_summary(gdf: gpd.GeoDataFrame):
    """Print mean score comparison per province to validate against benchmarks."""
    print("\n" + "=" * 65)
    print("           TANISCOPE CALIBRATION & BENCHMARK SUMMARY           ")
    print("=" * 65)

    pilot_villages = gdf[gdf["resolution"] == "village"]

    score_cols = [f"score_{c}" for c in CROP_REQUIREMENTS.keys()]
    prov_summary = pilot_villages.groupby("province")[score_cols].mean().round(1)

    print("\nMean Suitability Score (0-100%) by Pilot Province:")
    print("-" * 65)
    header = f"{'Province':<22} | {'Coffee (Robusta)':<16} | {'Cocoa':<12} | {'Sugarcane':<12}"
    print(header)
    print("-" * 65)

    for prov, row in prov_summary.iterrows():
        c_score = row.get("score_coffee", 0)
        co_score = row.get("score_cocoa", 0)
        s_score = row.get("score_sugarcane", 0)
        print(f"{prov:<22} | {c_score:>14.1f}% | {co_score:>10.1f}% | {s_score:>10.1f}%")

    print("-" * 65)

    for crop_id, crop_req in CROP_REQUIREMENTS.items():
        col = f"score_{crop_id}"
        cols_to_show = ["name", "kecamatan", "kabupaten", "province", col]
        top_villages = pilot_villages.nlargest(3, col)[cols_to_show]
        print(f"\nTop 3 Villages for {crop_req.display_name}:")
        for _, r in top_villages.iterrows():
            loc_str = f"{r['name']} ({r['kecamatan']}, {r['kabupaten']} - {r['province']})"
            print(f"  * {loc_str}: {r[col]}%")

    print("=" * 65 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Run TaniScope suitability scoring pipeline.")
    parser.add_argument(
        "--extract",
        action="store_true",
        help="Force re-extraction of environmental factors from rasters.",
    )
    parser.add_argument("--no-db", action="store_true", help="Skip PostGIS ingestion.")
    args = parser.parse_args()

    run_scoring_pipeline(force_extract=args.extract, load_to_db=not args.no_db)


if __name__ == "__main__":
    main()
