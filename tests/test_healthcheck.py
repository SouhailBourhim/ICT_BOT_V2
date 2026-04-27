from types import SimpleNamespace

from scripts import healthcheck


def test_healthcheck_filesystem_only(monkeypatch, tmp_path):
    fake_settings = SimpleNamespace(
        DATA_DIR=tmp_path / "data",
        DOCUMENTS_DIR=tmp_path / "data" / "documents",
        PROCESSED_DIR=tmp_path / "data" / "processed",
        DATABASE_DIR=tmp_path / "database",
        CHROMA_PERSIST_DIR=tmp_path / "database" / "chroma_db",
        LOGS_DIR=tmp_path / "logs",
    )
    monkeypatch.setattr(healthcheck, "settings", fake_settings)

    report = healthcheck.run_checks(
        include_streamlit=False,
        include_ollama=False,
        timeout=0.1,
    )

    assert report["ok"] is True
    assert set(report["checks"]) == {
        "data_dir",
        "documents_dir",
        "conversations_dir",
        "processed_dir",
        "database_dir",
        "chroma_dir",
        "logs_dir",
    }
