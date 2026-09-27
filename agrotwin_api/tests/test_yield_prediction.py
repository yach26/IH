import json
import subprocess

import pytest
from fastapi.testclient import TestClient

from app import ledger, yield_prediction as yp
from app.api.routes import get_conn
from app.main import app


@pytest.fixture
def client(conn):
    app.dependency_overrides[get_conn] = lambda: conn
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


def test_real_prediction_preserves_ledger_and_database(client, conn, field_row):
    before = json.dumps(ledger.run_field_ledger(conn, field_row), sort_keys=True)
    changes = conn.total_changes
    response = client.get('/fields/TEST-001/yield-estimate?rainfall_mm_season=1100')
    assert response.status_code == 200, response.text
    data = response.json()
    prediction = data['yield_prediction']
    assert prediction['status'] == 'OK', prediction
    assert prediction['predicted_yield_kg_ha'] > 0
    assert prediction['caveats'] and 'synthetic' in prediction['caveats'][0].lower()
    assert isinstance(prediction['confidence'], float)
    assert isinstance(data['ledger']['confidence'], str)
    assert before == json.dumps(data['ledger'], sort_keys=True)
    assert before == json.dumps(ledger.run_field_ledger(conn, field_row), sort_keys=True)
    assert conn.total_changes == changes
    plan = data['ledger']['plan_kg_ha']
    inputs = prediction['inputs']['fertilizer_plan']
    assert inputs['applied_n_kg_ha'] == pytest.approx(plan['DAP_kg_ha'] * .18 + plan['UREA_kg_ha'] * .46)
    assert inputs['applied_p2o5_kg_ha'] == pytest.approx(plan['DAP_kg_ha'] * .46)
    assert inputs['applied_k2o_kg_ha'] == pytest.approx(plan['MOP_kg_ha'] * .60)
    assert inputs['required_n_kg_ha'] == 340


@pytest.mark.parametrize('change', [
    "UPDATE crops SET crop_code='RICE'",
    "UPDATE districts SET district_name='Pune'",
    "UPDATE fields SET irrigation_type='Unknown'",
])
def test_unsupported_scope(client, conn, change):
    conn.execute(change)
    response = client.get('/fields/TEST-001/yield-estimate?rainfall_mm_season=1100')
    assert response.status_code == 200
    assert response.json()['yield_prediction']['status'] == 'ABSTAIN'


def test_missing_model(client, monkeypatch, tmp_path):
    # Real worker and inference code, but a deployment with no model artifact.
    import shutil
    shutil.copytree(yp.ML_ROOT / 'src', tmp_path / 'src')
    shutil.copy(yp.ML_ROOT / 'worker.py', tmp_path / 'worker.py')
    monkeypatch.setenv('AGROTWIN_ML_ROOT', str(tmp_path))
    response = client.get('/fields/TEST-001/yield-estimate?rainfall_mm_season=1100')
    assert response.status_code == 200
    assert response.json()['yield_prediction']['status'] == 'UNAVAILABLE'
    assert response.json()['ledger']['status'] == 'PLAN_GENERATED'
    assert client.get('/health').json()['status'] == 'ok'


@pytest.mark.parametrize('failure', [subprocess.TimeoutExpired('worker', 15), RuntimeError('broken')])
def test_failure_isolated(client, monkeypatch, failure):
    def fail(*args, **kwargs):
        raise failure
    monkeypatch.setattr(yp.subprocess, 'run', fail)
    response = client.get('/fields/TEST-001/yield-estimate?rainfall_mm_season=1100')
    assert response.status_code == 200
    assert response.json()['yield_prediction']['status'] == 'UNAVAILABLE'
    assert response.json()['ledger']['plan_kg_ha']['DAP_kg_ha'] > 0


def test_missing_inputs(client, conn):
    assert client.get('/fields/TEST-001/yield-estimate').json()['yield_prediction']['status'] == 'ABSTAIN'
    conn.execute('UPDATE soil_tests SET oc_percent=NULL')
    assert client.get('/fields/TEST-001/yield-estimate?rainfall_mm_season=1100').json()['yield_prediction']['status'] == 'ABSTAIN'
    conn.execute('DELETE FROM field_crops')
    assert client.get('/fields/TEST-001/yield-estimate?rainfall_mm_season=1100').json()['yield_prediction']['status'] == 'ABSTAIN'


@pytest.mark.parametrize('rain', ['-1', 'nan', 'inf'])
def test_invalid_rainfall(client, rain):
    assert client.get('/fields/TEST-001/yield-estimate?rainfall_mm_season=' + rain).status_code == 422


def test_unknown_field(client):
    assert client.get('/fields/unknown/yield-estimate?rainfall_mm_season=1100').status_code == 404


def test_extrapolation_flag_present(client, conn, field_row):
    """The response must include an explicit extrapolation boolean."""
    response = client.get('/fields/TEST-001/yield-estimate?rainfall_mm_season=1100')
    assert response.status_code == 200
    prediction = response.json()['yield_prediction']
    assert 'extrapolation' in prediction
    assert isinstance(prediction['extrapolation'], bool)


def test_extrapolation_triggered_by_rainfall(client, conn, field_row):
    """Rainfall outside the training range must set extrapolation=True."""
    # Kolhapur training range is 900-1300mm; 500mm is well below
    response = client.get('/fields/TEST-001/yield-estimate?rainfall_mm_season=500')
    assert response.status_code == 200
    prediction = response.json()['yield_prediction']
    assert prediction['extrapolation'] is True
    assert any('outside' in c.lower() for c in prediction['caveats'])


def test_no_extrapolation_within_range(client, conn, field_row):
    """Rainfall within the training range must set extrapolation=False."""
    response = client.get('/fields/TEST-001/yield-estimate?rainfall_mm_season=1100')
    assert response.status_code == 200
    prediction = response.json()['yield_prediction']
    assert prediction['extrapolation'] is False


def test_ledger_quantities_unchanged_after_prediction(client, conn, field_row):
    """Ledger plan_kg_ha must be identical before and after yield prediction."""
    before = ledger.run_field_ledger(conn, field_row)
    before_plan = json.dumps(before['plan_kg_ha'], sort_keys=True)
    before_required = json.dumps(before['required'], sort_keys=True)

    client.get('/fields/TEST-001/yield-estimate?rainfall_mm_season=1100')

    after = ledger.run_field_ledger(conn, field_row)
    after_plan = json.dumps(after['plan_kg_ha'], sort_keys=True)
    after_required = json.dumps(after['required'], sort_keys=True)

    assert before_plan == after_plan
    assert before_required == after_required


def test_abstain_includes_extrapolation_false(client, conn, field_row):
    """Abstained predictions must include extrapolation=False."""
    conn.execute("UPDATE crops SET crop_code='RICE'")
    response = client.get('/fields/TEST-001/yield-estimate?rainfall_mm_season=1100')
    assert response.status_code == 200
    prediction = response.json()['yield_prediction']
    assert prediction['status'] == 'ABSTAIN'
    assert prediction['extrapolation'] is False
