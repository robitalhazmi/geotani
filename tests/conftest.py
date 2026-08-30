"""Pytest configuration and test database fixtures for GeoTani."""

import pytest
from sqlalchemy import func, text

from api.database import SessionLocal, engine
from api.models import Village


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Ensure database tables and minimal sample records exist for integration tests."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1;"))

        from etl.load_postgis import create_tables

        create_tables(engine, drop=False)

        with SessionLocal() as db:
            count = db.query(func.count(Village.id)).scalar() or 0
            if count == 0:
                poly1 = (
                    "POLYGON((112.55 -8.15, 112.58 -8.15, 112.58 -8.12, "
                    "112.55 -8.12, 112.55 -8.15))"
                )
                poly2 = (
                    "POLYGON((112.72 -7.26, 112.75 -7.26, 112.75 -7.23, "
                    "112.72 -7.23, 112.72 -7.26))"
                )

                village_insert = f"""
                    INSERT INTO villages
                        (id, adm_pcode, name, kecamatan, kabupaten, province, resolution, geom)
                    VALUES
                        (1, 'ID3507180001', 'Ardirejo', 'Kepanjen', 'Malang', 'Jawa Timur',
                         'village', ST_Multi(ST_GeomFromText('{poly1}', 4326))),
                        (2, 'ID3578250003', 'Alon-Alon Contong', 'Bubutan', 'Kota Surabaya',
                         'Jawa Timur', 'village', ST_Multi(ST_GeomFromText('{poly2}', 4326)))
                    ON CONFLICT (id) DO NOTHING;
                """
                db.execute(text(village_insert))

                scores_insert = """
                    INSERT INTO suitability_scores
                        (village_id, crop, score, climate_score,
                         soil_score, terrain_score, access_score)
                    VALUES
                        (1, 'coffee', 85.5, 90.0, 80.0, 85.0, 95.0),
                        (1, 'cocoa', 72.0, 75.0, 70.0, 70.0, 95.0),
                        (1, 'sugarcane', 65.0, 60.0, 70.0, 70.0, 95.0),
                        (2, 'coffee', 45.0, 50.0, 60.0, 40.0, 100.0),
                        (2, 'cocoa', 60.0, 65.0, 60.0, 55.0, 100.0),
                        (2, 'sugarcane', 92.0, 95.0, 90.0, 90.0, 100.0)
                    ON CONFLICT (village_id, crop) DO NOTHING;
                """
                db.execute(text(scores_insert))
                db.commit()

    except Exception as e:
        print(f"\n[Warning] Database not available during test session setup: {e}")

    yield
