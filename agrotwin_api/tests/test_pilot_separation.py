from app.api.routes import list_fields


def test_pilot_records_are_separate_even_when_not_synthetic(conn, ids):
    conn.execute("UPDATE fields SET field_code='REAL-007', is_synthetic=0 WHERE field_id=?", (ids["field_id"],))
    assert list_fields(conn) == []
    pilot = list_fields(conn, demo=True)
    assert len(pilot) == 1
    assert pilot[0]["is_demo"] is True
    assert pilot[0]["field_code"] == "REAL-007"


def test_farmer_field_without_soil_has_no_score(conn, ids):
    conn.execute("UPDATE fields SET field_code='FARM-OWN', is_synthetic=0 WHERE field_id=?", (ids["field_id"],))
    conn.execute("DELETE FROM soil_tests WHERE field_id=?", (ids["field_id"],))
    fields = list_fields(conn)
    assert fields[0]["field_code"] == "FARM-OWN"
    assert fields[0]["soil_health_score"] is None
    assert list_fields(conn, demo=True) == []
