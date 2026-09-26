"""Shared in-memory Digital Twin fixture for agent / pipeline tests."""

from __future__ import annotations

import os
import sqlite3
import sys
from datetime import date

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

SCHEMA_PATH = os.path.join(ROOT, "schema_sqlite.sql")


def make_test_db():
    c = sqlite3.connect(":memory:", check_same_thread=False)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys = ON")
    with open(SCHEMA_PATH, encoding="utf-8") as f:
        c.executescript(f.read())

    c.execute("INSERT INTO regions (region_code, region_name) VALUES ('MH','Maharashtra')")
    region_id = c.execute("SELECT last_insert_rowid()").fetchone()[0]
    c.execute(
        "INSERT INTO districts (region_id, district_code, district_name) VALUES (?,?,?)",
        (region_id, "KOLHAPUR", "Kolhapur"),
    )
    district_id = c.execute("SELECT last_insert_rowid()").fetchone()[0]
    c.execute(
        """INSERT INTO fields
           (region_id, district_id, field_code, area_ha, irrigation_type, lat, lon)
           VALUES (?,?,?,?,?,?,?)""",
        (region_id, district_id, "TEST-001", 2.0, "Irrigated", 16.7, 74.2),
    )
    field_id = c.execute("SELECT last_insert_rowid()").fetchone()[0]
    c.execute("INSERT INTO crops (crop_code, crop_name) VALUES ('SUGARCANE','Sugarcane')")
    crop_id = c.execute("SELECT last_insert_rowid()").fetchone()[0]
    for code, name, n, p, k in [
        ("UREA", "Urea", 46.0, 0.0, 0.0),
        ("DAP", "DAP", 18.0, 46.0, 0.0),
        ("MOP", "MOP", 0.0, 0.0, 60.0),
        ("SSP", "SSP", 0.0, 16.0, 0.0),
    ]:
        c.execute(
            "INSERT INTO fertilizer_products "
            "(product_code, product_name, n_percent, p2o5_percent, k2o_percent) "
            "VALUES (?,?,?,?,?)",
            (code, name, n, p, k),
        )
    c.execute(
        """INSERT INTO fertilizer_recommendations
           (crop_id, recommendation_type, n_kg_ha, p2o5_kg_ha, k2o_kg_ha, source_citation)
           VALUES (?,?,?,?,?,?)""",
        (crop_id, "PRE_SEASONAL", 340, 170, 170, "mpkv_icar_rdf.md, Sugarcane pre-seasonal"),
    )
    c.execute(
        """INSERT INTO soil_tests
           (field_id, test_date, n_kg_ha, p_kg_ha, k_kg_ha, ph, oc_percent, source)
           VALUES (?,?,?,?,?,?,?,?)""",
        (field_id, date.today().isoformat(), 120.0, 40.0, 80.0, 7.2, 0.65, "lab"),
    )
    soil_test_id = c.execute("SELECT last_insert_rowid()").fetchone()[0]
    c.execute(
        """INSERT INTO field_crops
           (field_id, crop_id, sowing_date, current_stage, recommendation_type, is_active)
           VALUES (?,?,?,?,?,?)""",
        (field_id, crop_id, "2026-06-01", "GRAND_GROWTH", "PRE_SEASONAL", 1),
    )
    c.commit()
    ids = {
        "field_id": field_id,
        "crop_id": crop_id,
        "soil_test_id": soil_test_id,
        "region_id": region_id,
        "district_id": district_id,
    }
    return c, ids


@pytest.fixture
def db():
    return make_test_db()


@pytest.fixture
def conn(db):
    return db[0]


@pytest.fixture
def ids(db):
    return db[1]


@pytest.fixture
def field_row(db):
    c, i = db
    return c.execute(
        "SELECT * FROM field_active_crop WHERE field_id = ?",
        (i["field_id"],),
    ).fetchone()
