from concurrent.futures import ThreadPoolExecutor
from app.db import get_db_connection


def test_sqlite_request_connection_can_move_between_worker_threads(tmp_path, monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("AGROTWIN_DB", str(tmp_path / "request.db"))
    connection = get_db_connection()
    with ThreadPoolExecutor(max_workers=1) as pool:
        assert pool.submit(lambda: connection.execute("SELECT 1").fetchone()[0]).result() == 1
        pool.submit(connection.close).result()
