"""Regression tests for Groq/OCR/database integration with the yield model."""
from decimal import Decimal
import json
from types import SimpleNamespace

import pytest

from app.core import llm, ocr
from app import yield_prediction as yp


@pytest.fixture(autouse=True)
def no_live_llm(monkeypatch):
    monkeypatch.delenv('GROQ_API_KEY', raising=False)
    monkeypatch.delenv('XAI_API_KEY', raising=False)
    monkeypatch.setattr(llm, '_client', None)
    monkeypatch.setattr(llm, '_client_config', None)


def test_missing_key_never_creates_client(monkeypatch):
    monkeypatch.setattr(llm, 'get_client', lambda: pytest.fail('No request without credentials'))
    assert llm.generate_chat_completion([]) == ''


@pytest.mark.parametrize('variable,key,url,model', [
    ('GROQ_API_KEY', 'gsk_test', 'https://api.groq.com/openai/v1', 'llama-3.3-70b-versatile'),
    ('XAI_API_KEY', 'gsk_legacy', 'https://api.groq.com/openai/v1', 'llama-3.3-70b-versatile'),
    ('XAI_API_KEY', 'xai_test', 'https://api.x.ai/v1', 'grok-4.3'),
])
def test_provider_configuration(monkeypatch, variable, key, url, model):
    import openai
    monkeypatch.setenv(variable, key)
    monkeypatch.delenv('GROQ_MODEL', raising=False)
    monkeypatch.delenv('XAI_MODEL', raising=False)
    calls = {}
    def create(**kwargs):
        calls['request'] = kwargs
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content='Explanation'))])
    def client(**kwargs):
        calls['client'] = kwargs
        return SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    monkeypatch.setattr(openai, 'OpenAI', client)
    assert llm.generate_chat_completion([]) == 'Explanation'
    assert calls['client']['base_url'] == url
    assert calls['client']['timeout'] == 10
    assert calls['client']['max_retries'] == 0
    assert calls['request']['model'] == model


def test_provider_failure_returns_no_advice(monkeypatch):
    monkeypatch.setenv('GROQ_API_KEY', 'gsk_test')
    def fail():
        raise RuntimeError('provider failure')
    monkeypatch.setattr(llm, 'get_client', fail)
    assert llm.generate_chat_completion([]) == ''


def test_narrative_does_not_change_plan(conn, field_row, monkeypatch):
    from app.pipeline import RecommendationPipeline
    weather = dict(rainfall_mm_next_7d=0, rainfall_probability=0, heavy_rain_alert=False)
    baseline = RecommendationPipeline().run(conn, field_row, mock_weather=weather, persist=False, emit_events=False)
    monkeypatch.setattr(llm, 'generate_chat_completion', lambda *a, **k: 'Explanation only')
    enriched = RecommendationPipeline().run(conn, field_row, mock_weather=weather, persist=False, emit_events=False)
    assert enriched['narrative'] == 'Explanation only'
    assert enriched['plan_kg_ha'] == baseline['plan_kg_ha']
    assert enriched['confidence'] == baseline['confidence']


def test_ocr_failure_does_not_parse_binary_as_text(monkeypatch):
    monkeypatch.setattr(ocr, '_ocr_image_bytes', lambda data: ([], 'no_ocr_engine'))
    data = b'\x89PNG\x00\xffNitrogen: 7\npH: 8'
    result = ocr.run_ocr_pipeline(data, 'report.png')
    assert result['status'] == 'no_text_detected'
    assert all(v['value'] is None for v in result['extracted_data'].values())


def test_llm_ocr_suggestions_still_require_confirmation(monkeypatch):
    monkeypatch.setattr(llm, 'generate_chat_completion', lambda *a, **k: '{"ph":7.2,"oc_percent":-5,"n_kg_ha":"nan"}')
    result = ocr.run_ocr_pipeline(b'Soil report: pH unclear', 'report.txt')
    assert result['extracted_data']['ph']['value'] == 7.2
    assert 'ph' in result['fields_needing_review']
    assert result['extracted_data']['oc_percent']['value'] is None
    assert result['extracted_data']['n_kg_ha']['value'] is None


def test_yield_accepts_postgres_dicts_and_decimals(conn, field_row, monkeypatch):
    class Cursor:
        def __init__(self, cursor):
            self.cursor = cursor
        def convert(self, row):
            if row is None:
                return None
            return {k: Decimal(str(v)) if isinstance(v, float) else v for k, v in dict(row).items()}
        def execute(self, *args):
            self.cursor.execute(*args)
            return self
        def fetchone(self):
            return self.convert(self.cursor.fetchone())
        def fetchall(self):
            return [self.convert(row) for row in self.cursor.fetchall()]
    class DictConnection:
        def cursor(self):
            return Cursor(conn.cursor())
        def execute(self, *args):
            return self.cursor().execute(*args)
    def predict(payload):
        json.dumps(payload, allow_nan=False)
        assert payload['soil']['district'] == 'Kolhapur'
        assert isinstance(payload['soil']['oc_percent'], float)
        return dict(status='OK', predicted_yield_kg_ha=1000, caveats=[])
    monkeypatch.setattr(yp, '_predict', predict)
    result = yp.estimate(DictConnection(), dict(field_row), 1100)
    assert result['yield_prediction']['status'] == 'OK'


def test_demo_seed_has_one_active_crop_per_field():
    import sqlite3
    from scripts.demo_yield import build_demo
    conn = sqlite3.connect(':memory:')
    try:
        build_demo(conn)
        counts = conn.execute('SELECT COUNT(*) FROM field_crops WHERE is_active=1 GROUP BY field_id').fetchall()
        assert len(counts) == 8
        assert all(count == 1 for (count,) in counts)
    finally:
        conn.close()


def test_multiline_ocr_preserves_weakest_actual_confidence():
    result = ocr.parse_extracted_blocks([('Available Nitrogen:', 0.97), ('198', 0.78)])
    assert result['fields']['n_kg_ha']['value'] == 198
    assert result['fields']['n_kg_ha']['confidence'] == 0.78


def test_what_if_does_not_save_a_recommendation(conn):
    from fastapi.testclient import TestClient
    from app.main import app
    from app.api.routes import get_conn
    before = conn.execute('SELECT COUNT(*) FROM recommendations').fetchone()[0]
    app.dependency_overrides[get_conn] = lambda: conn
    try:
        with TestClient(app) as client:
            result = client.post('/fields/TEST-001/what-if', json={'fertilizer_delta_pct': -10, 'rainfall_mm': 2})
            assert result.status_code == 200, result.text
        assert conn.execute('SELECT COUNT(*) FROM recommendations').fetchone()[0] == before
    finally:
        app.dependency_overrides.pop(get_conn, None)
