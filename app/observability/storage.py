"""SQLite-backed observability persistence."""

from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path
from typing import Any, Dict, List


ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "data" / "observability.sqlite3"
LLM_USAGE_FALLBACK_PATH = ROOT / "data" / "observability_llm_usage.jsonl"


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    try:
        return _initialized_connection()
    except sqlite3.OperationalError:
        _quarantine_db()
        return _initialized_connection()


def _initialized_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, timeout=10, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS pipeline_runs (
            request_id TEXT PRIMARY KEY,
            started_at TEXT,
            finished_at TEXT,
            status TEXT,
            duration_ms REAL,
            failed_stage TEXT,
            user_query TEXT,
            payload_json TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS llm_usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            stage TEXT,
            model TEXT,
            input_tokens INTEGER,
            output_tokens INTEGER,
            total_tokens INTEGER,
            estimated_cost_usd REAL,
            metadata_json TEXT
        )
        """
    )
    return conn


def _quarantine_db() -> None:
    """Move an unreadable SQLite file aside so telemetry can recover."""
    stamp = int(time.time())
    for path in [DB_PATH, DB_PATH.with_name(f"{DB_PATH.name}-journal")]:
        if not path.exists():
            continue
        backup = path.with_name(f"{path.name}.bad-{stamp}")
        try:
            path.replace(backup)
        except OSError:
            pass


def save_pipeline_run(run: Dict[str, Any]) -> None:
    try:
        with _connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO pipeline_runs (
                    request_id, started_at, finished_at, status, duration_ms,
                    failed_stage, user_query, payload_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run.get("request_id"),
                    run.get("started_at"),
                    run.get("finished_at"),
                    run.get("status"),
                    run.get("duration_ms"),
                    run.get("failed_stage"),
                    run.get("user_query"),
                    json.dumps(run, default=str),
                ),
            )
    except sqlite3.Error:
        return


def load_recent_pipeline_runs(limit: int = 20) -> List[Dict[str, Any]]:
    try:
        with _connect() as conn:
            rows = conn.execute(
                """
                SELECT payload_json
                FROM pipeline_runs
                ORDER BY started_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
    except sqlite3.Error:
        return []
    return [json.loads(row["payload_json"]) for row in rows]


def save_llm_usage(usage: Dict[str, Any]) -> None:
    try:
        with _connect() as conn:
            conn.execute(
                """
                INSERT INTO llm_usage (
                    timestamp, stage, model, input_tokens, output_tokens,
                    total_tokens, estimated_cost_usd, metadata_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    usage.get("timestamp"),
                    usage.get("stage"),
                    usage.get("model"),
                    usage.get("input_tokens"),
                    usage.get("output_tokens"),
                    usage.get("total_tokens"),
                    usage.get("estimated_cost_usd"),
                    json.dumps(usage.get("metadata", {}), default=str),
                ),
            )
    except sqlite3.Error:
        _append_jsonl(LLM_USAGE_FALLBACK_PATH, usage)
        return


def load_llm_usage(limit: int = 50) -> List[Dict[str, Any]]:
    try:
        with _connect() as conn:
            rows = conn.execute(
                """
                SELECT *
                FROM llm_usage
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
    except sqlite3.Error:
        return _load_jsonl(LLM_USAGE_FALLBACK_PATH, limit)
    result: List[Dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        item["metadata"] = json.loads(item.pop("metadata_json") or "{}")
        result.append(item)
    return result


def _append_jsonl(path: Path, item: Dict[str, Any]) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(item, default=str) + "\n")
    except OSError:
        return


def _load_jsonl(path: Path, limit: int) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []

    items: List[Dict[str, Any]] = []
    for line in reversed(lines):
        if not line.strip():
            continue
        try:
            items.append(json.loads(line))
        except json.JSONDecodeError:
            continue
        if len(items) >= limit:
            break
    return items
