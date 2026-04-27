import pytest
from pydantic import ValidationError

from src.config.settings import Settings


def test_settings_builds_default_sqlite_url():
    settings = Settings(_env_file=None)

    assert settings.SQLITE_DB_URL == f"sqlite:///{settings.SQLITE_DB_PATH}"
    assert settings.OLLAMA_MODEL == "qwen2.5:3b"


def test_settings_rejects_invalid_retrieval_weights():
    with pytest.raises(ValidationError, match="must sum to 1.0"):
        Settings(SEMANTIC_WEIGHT=0.9, BM25_WEIGHT=0.3, _env_file=None)


def test_settings_rejects_invalid_chunk_overlap():
    with pytest.raises(ValidationError, match="CHUNK_OVERLAP"):
        Settings(CHUNK_SIZE=100, CHUNK_OVERLAP=100, _env_file=None)


def test_settings_rejects_invalid_ollama_url():
    with pytest.raises(ValidationError, match="absolute http"):
        Settings(OLLAMA_BASE_URL="ollama:11434", _env_file=None)
