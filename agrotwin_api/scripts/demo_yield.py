"""Run a real yield prediction on synthetic fixtures, or serve a separate demo DB.

python scripts/demo_yield.py
python scripts/demo_yield.py --serve
"""
import argparse
import json
import os
from pathlib import Path
import sqlite3
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import seed_data


def build_demo(conn):
    conn.executescript((ROOT / 'schema_sqlite.sql').read_text(encoding='utf-8'))
    region, districts = seed_data.seed_regions_districts_talukas(conn)
    crops = seed_data.seed_crops(conn)
    seed_data.seed_fertilizer_products(conn)
    seed_data.seed_fertilizer_recommendations(conn, crops)
    fields = seed_data.seed_fields_and_soil_tests(conn, region, districts, crops)
    for code, meta in fields.items():
        conn.execute('INSERT INTO field_crops (field_id,crop_id,current_stage,recommendation_type,is_active) VALUES (?,?,?,?,1)',
                     (meta['field_id'], crops[meta['crop_code']], meta['current_stage'],
                      seed_data.RECOMMENDATION_TYPE_BY_RECORD[code]))
    conn.commit()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--serve', action='store_true')
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix='agrotwin-yield-') as folder:
        path = str(Path(folder) / 'demo.db')
        conn = sqlite3.connect(path)
        build_demo(conn)
        conn.close()
        os.environ['AGROTWIN_DB'] = path
        if args.serve:
            import uvicorn
            print('Synthetic demo: http://127.0.0.1:8000/fields/SYN-003/yield-estimate?rainfall_mm_season=1100')
            uvicorn.run('app.main:app', host='127.0.0.1', port=8000)
        else:
            from fastapi.testclient import TestClient
            from app.main import app
            with TestClient(app) as client:
                response = client.get('/fields/SYN-003/yield-estimate?rainfall_mm_season=1100')
                response.raise_for_status()
                print(json.dumps(response.json(), indent=2))
                assert response.json()['yield_prediction']['status'] == 'OK'
