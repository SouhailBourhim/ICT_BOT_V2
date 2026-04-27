"""
Production health checks for the RAG application stack.

This script is intentionally lightweight: it checks local filesystem readiness,
Streamlit health, and Ollama/model availability without importing the Streamlit app.
"""
from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path
from typing import Any

import requests

sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.config.settings import settings


def _result(ok: bool, detail: str) -> dict[str, Any]:
    return {"ok": ok, "detail": detail}


def check_writable(path: Path) -> dict[str, Any]:
    try:
        path.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=path, prefix=".healthcheck-", delete=True):
            pass
        return _result(True, f"{path} is writable")
    except Exception as exc:
        return _result(False, f"{path} is not writable: {exc}")


def check_streamlit(url: str, timeout: float) -> dict[str, Any]:
    try:
        response = requests.get(url, timeout=timeout)
        if response.status_code == 200:
            return _result(True, f"Streamlit health endpoint returned {response.status_code}")
        return _result(False, f"Streamlit health endpoint returned {response.status_code}")
    except Exception as exc:
        return _result(False, f"Streamlit health endpoint failed: {exc}")


def check_ollama(timeout: float) -> dict[str, Any]:
    try:
        response = requests.get(f"{settings.OLLAMA_BASE_URL}/api/tags", timeout=timeout)
        if response.status_code != 200:
            return _result(False, f"Ollama returned {response.status_code}")

        models = response.json().get("models", [])
        model_names = {model.get("name") for model in models}
        if settings.OLLAMA_MODEL not in model_names:
            return _result(False, f"Ollama model '{settings.OLLAMA_MODEL}' is not installed")

        return _result(True, f"Ollama is reachable and model '{settings.OLLAMA_MODEL}' is installed")
    except Exception as exc:
        return _result(False, f"Ollama check failed: {exc}")


def run_checks(include_streamlit: bool, include_ollama: bool, timeout: float) -> dict[str, Any]:
    checks = {
        "data_dir": check_writable(settings.DATA_DIR),
        "documents_dir": check_writable(settings.DOCUMENTS_DIR),
        "conversations_dir": check_writable(settings.DATA_DIR / "conversations"),
        "processed_dir": check_writable(settings.PROCESSED_DIR),
        "database_dir": check_writable(settings.DATABASE_DIR),
        "chroma_dir": check_writable(settings.CHROMA_PERSIST_DIR),
        "logs_dir": check_writable(settings.LOGS_DIR),
    }

    if include_streamlit:
        checks["streamlit"] = check_streamlit(
            "http://localhost:8501/_stcore/health",
            timeout=timeout,
        )

    if include_ollama:
        checks["ollama"] = check_ollama(timeout=timeout)

    return {"ok": all(check["ok"] for check in checks.values()), "checks": checks}


def main() -> int:
    parser = argparse.ArgumentParser(description="Run production health checks.")
    parser.add_argument("--skip-streamlit", action="store_true", help="Do not check Streamlit HTTP health.")
    parser.add_argument("--skip-ollama", action="store_true", help="Do not check Ollama/model availability.")
    parser.add_argument("--timeout", type=float, default=5.0, help="HTTP timeout in seconds.")
    args = parser.parse_args()

    report = run_checks(
        include_streamlit=not args.skip_streamlit,
        include_ollama=not args.skip_ollama,
        timeout=args.timeout,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
