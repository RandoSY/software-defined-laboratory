#!/usr/bin/env python3
"""UNO Q Spirit local experiment dashboard and recorder."""
from __future__ import annotations

import csv
from contextlib import closing
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import re
import sqlite3
import threading
import time
from typing import Any
from urllib.parse import unquote, urlparse
import uuid

from spirit_cli import LocalBridge, sample

ROOT = Path(__file__).resolve().parents[1]
WEB_ROOT = ROOT / "dashboard"
DATA_ROOT = Path(os.environ.get("SPIRIT_DATA_DIR", Path.home() / ".local/share/uno-q-spirit"))
DB_PATH = DATA_ROOT / "experiments.sqlite3"
POLL_SECONDS = 1.0
CSV_COLUMNS = (
    "sample_number", "timestamp_utc", "mode", "profile",
    "temperature_state", "temperature_c", "hx711_state", "hx711_counts", "hx711_grams", "hx711_calibrated",
    "distance_state", "distance_cm", "spectral_state", "spectral_gain_code",
    "spectral_channels", "loop_ticks",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


class DashboardService:
    def __init__(self) -> None:
        DATA_ROOT.mkdir(parents=True, exist_ok=True)
        self._init_db()
        self.lock = threading.RLock()
        self.stop_event = threading.Event()
        self.latest: dict[str, Any] | None = None
        self.last_error: str | None = None
        self.run_id: str | None = None
        self.next_record_at = 0.0
        self.record_interval = 3.0
        self.worker = threading.Thread(target=self._sampling_loop, name="spirit-sampler", daemon=True)
        self.worker.start()

    def _connect_db(self) -> sqlite3.Connection:
        db = sqlite3.connect(DB_PATH, timeout=5)
        db.row_factory = sqlite3.Row
        return db

    def _init_db(self) -> None:
        with closing(self._connect_db()) as db:
            db.executescript("""
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS runs (
                    run_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    started_at_utc TEXT NOT NULL,
                    ended_at_utc TEXT,
                    sample_interval_s REAL NOT NULL,
                    notes TEXT NOT NULL,
                    mode_at_start TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS samples (
                    sample_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT NOT NULL REFERENCES runs(run_id),
                    timestamp_utc TEXT NOT NULL,
                    payload_json TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS samples_run_time ON samples(run_id, sample_id);
            """)
            db.commit()

    def _sampling_loop(self) -> None:
        while not self.stop_event.is_set():
            try:
                with LocalBridge() as client:
                    while not self.stop_event.is_set():
                        data = sample(client)
                        observed = utc_now()
                        snapshot = {"timestamp_utc": observed, "data": data}
                        with self.lock:
                            self.latest = snapshot
                            self.last_error = None
                            active_run = self.run_id
                            should_record = active_run is not None and time.monotonic() >= self.next_record_at
                            if should_record:
                                self.next_record_at += self.record_interval
                                if self.next_record_at < time.monotonic():
                                    self.next_record_at = time.monotonic() + self.record_interval
                        if should_record and active_run:
                            self._insert_sample(active_run, snapshot)
                        self.stop_event.wait(POLL_SECONDS)
            except Exception as exc:  # Keep the dashboard available through router outages.
                with self.lock:
                    self.last_error = str(exc)
                self.stop_event.wait(2.0)

    def _insert_sample(self, run_id: str, snapshot: dict[str, Any]) -> None:
        with closing(self._connect_db()) as db:
            db.execute(
                "INSERT INTO samples(run_id, timestamp_utc, payload_json) VALUES (?, ?, ?)",
                (run_id, snapshot["timestamp_utc"], json.dumps(snapshot["data"], separators=(",", ":"))),
            )
            db.commit()

    def state(self) -> dict[str, Any]:
        with self.lock:
            latest = self.latest
            last_error = self.last_error
            run_id = self.run_id
        run = self._get_run(run_id) if run_id else None
        return {
            "connected": latest is not None and last_error is None,
            "last_error": last_error,
            "latest": latest,
            "recording": run is not None,
            "active_run": run,
        }

    def _get_run(self, run_id: str) -> dict[str, Any] | None:
        with closing(self._connect_db()) as db:
            row = db.execute("""
                SELECT r.*, (SELECT COUNT(*) FROM samples s WHERE s.run_id = r.run_id) AS sample_count
                FROM runs r WHERE r.run_id = ?
            """, (run_id,)).fetchone()
        return dict(row) if row else None

    def start_run(self, body: dict[str, Any]) -> dict[str, Any]:
        name = str(body.get("name", "")).strip()
        notes = str(body.get("notes", "")).strip()
        try:
            interval = float(body.get("interval_s", 3))
        except (TypeError, ValueError):
            raise ValueError("Sample interval must be a number.")
        if not name or len(name) > 100:
            raise ValueError("Enter an experiment name up to 100 characters.")
        if len(notes) > 2000:
            raise ValueError("Notes must be 2,000 characters or fewer.")
        if not 1 <= interval <= 3600:
            raise ValueError("Sample interval must be between 1 and 3,600 seconds.")
        with self.lock:
            if self.last_error or self.latest is None:
                raise RuntimeError("The board telemetry is not connected yet.")
            if self.run_id is not None:
                raise RuntimeError("An experiment is already recording.")
            run_id = uuid.uuid4().hex
            started = utc_now()
            mode = self.latest["data"].get("mode", "unknown")
            with closing(self._connect_db()) as db:
                db.execute(
                    "INSERT INTO runs(run_id, name, started_at_utc, sample_interval_s, notes, mode_at_start) VALUES (?, ?, ?, ?, ?, ?)",
                    (run_id, name, started, interval, notes, mode),
                )
                db.commit()
            self.run_id = run_id
            self.record_interval = interval
            self.next_record_at = time.monotonic()
        return self._get_run(run_id) or {}

    def stop_run(self) -> dict[str, Any]:
        with self.lock:
            run_id = self.run_id
            if run_id is None:
                raise RuntimeError("There is no active experiment.")
            self.run_id = None
            with closing(self._connect_db()) as db:
                db.execute("UPDATE runs SET ended_at_utc = ? WHERE run_id = ?", (utc_now(), run_id))
                db.commit()
        return self._get_run(run_id) or {}

    def list_runs(self, limit: int = 50) -> list[dict[str, Any]]:
        with closing(self._connect_db()) as db:
            rows = db.execute("""
                SELECT r.*, (SELECT COUNT(*) FROM samples s WHERE s.run_id = r.run_id) AS sample_count
                FROM runs r ORDER BY r.started_at_utc DESC LIMIT ?
            """, (limit,)).fetchall()
        return [dict(row) for row in rows]

    def run_csv(self, run_id: str) -> tuple[str, str] | None:
        with closing(self._connect_db()) as db:
            run = db.execute("SELECT * FROM runs WHERE run_id = ?", (run_id,)).fetchone()
            rows = db.execute("SELECT timestamp_utc, payload_json FROM samples WHERE run_id = ? ORDER BY sample_id", (run_id,)).fetchall()
        if not run:
            return None
        from io import StringIO
        out = StringIO(newline="")
        writer = csv.DictWriter(out, fieldnames=CSV_COLUMNS, lineterminator="\r\n")
        writer.writeheader()
        for index, row in enumerate(rows, 1):
            data = json.loads(row["payload_json"])
            spectral = data.get("spectral", {})
            writer.writerow({
                "sample_number": index,
                "timestamp_utc": row["timestamp_utc"],
                "mode": data.get("mode"),
                "profile": data.get("profile"),
                "temperature_state": data.get("temp_c", {}).get("state"),
                "temperature_c": data.get("temp_c", {}).get("value"),
                "hx711_state": data.get("hx711_counts", {}).get("state"),
                "hx711_counts": data.get("hx711_counts", {}).get("value"),
                "hx711_grams": data.get("hx711_grams"),
                "hx711_calibrated": data.get("hx711_calibrated"),
                "distance_state": data.get("distance_cm", {}).get("state"),
                "distance_cm": data.get("distance_cm", {}).get("value"),
                "spectral_state": spectral.get("state"),
                "spectral_gain_code": spectral.get("gain_code"),
                "spectral_channels": json.dumps(spectral.get("channels", []), separators=(",", ":")),
                "loop_ticks": data.get("loop_ticks"),
            })
        filename = re.sub(r"[^A-Za-z0-9_-]+", "_", run["name"]).strip("_") or "experiment"
        return f"{filename}_{run_id[:8]}.csv", out.getvalue()


SERVICE = DashboardService()


class Handler(BaseHTTPRequestHandler):
    server_version = "UNO-Q-Spirit-Dashboard/1.0"

    def _send(self, status: int, content: bytes, content_type: str, extra: dict[str, str] | None = None) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        if extra:
            for key, value in extra.items():
                self.send_header(key, value)
        self.end_headers()
        self.wfile.write(content)

    def _json(self, status: int, value: Any) -> None:
        self._send(status, json.dumps(value, separators=(",", ":")).encode(), "application/json; charset=utf-8")

    def _body_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        if length > 65536:
            raise ValueError("Request body too large.")
        value = json.loads(self.rfile.read(length) or b"{}")
        if not isinstance(value, dict):
            raise ValueError("Expected a JSON object.")
        return value

    def do_GET(self) -> None:
        path = unquote(urlparse(self.path).path)
        if path == "/api/state":
            self._json(200, SERVICE.state())
            return
        if path == "/api/runs":
            self._json(200, {"runs": SERVICE.list_runs()})
            return
        match = re.fullmatch(r"/api/runs/([a-f0-9]{32})/csv", path)
        if match:
            result = SERVICE.run_csv(match.group(1))
            if result is None:
                self._json(404, {"error": "Experiment not found."})
                return
            filename, content = result
            self._send(200, content.encode("utf-8"), "text/csv; charset=utf-8", {
                "Content-Disposition": f'attachment; filename="{filename}"'
            })
            return
        if path == "/healthz":
            state = SERVICE.state()
            self._json(200 if state["connected"] else 503, {"ok": state["connected"], "bridge_ok": (state.get("latest") or {}).get("data", {}).get("bridge_ok", False), "error": state["last_error"]})
            return
        if path == "/brand/uno-q-spirit-logo.svg":
            target = ROOT / "assets/uno-q-spirit-logo.svg"
        else:
            relative = "index.html" if path == "/" else path.lstrip("/")
            target = (WEB_ROOT / relative).resolve()
        allowed_root = ROOT / "assets" if path.startswith("/brand/") else WEB_ROOT.resolve()
        if allowed_root.resolve() not in target.resolve().parents or not target.is_file():
            self._json(404, {"error": "Not found."})
            return
        content_type = "text/html; charset=utf-8" if target.suffix == ".html" else "text/css; charset=utf-8" if target.suffix == ".css" else "application/javascript; charset=utf-8" if target.suffix == ".js" else "image/svg+xml" if target.suffix == ".svg" else "application/octet-stream"
        self._send(200, target.read_bytes(), content_type)

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        try:
            body = self._body_json()
            if path == "/api/runs":
                self._json(201, {"run": SERVICE.start_run(body)})
                return
            if path == "/api/runs/stop":
                self._json(200, {"run": SERVICE.stop_run()})
                return
            self._json(404, {"error": "Not found."})
        except (ValueError, json.JSONDecodeError) as exc:
            self._json(400, {"error": str(exc)})
        except RuntimeError as exc:
            self._json(409, {"error": str(exc)})

    def log_message(self, fmt: str, *args: Any) -> None:
        print(f"{utc_now()} {self.address_string()} {fmt % args}", flush=True)


def main() -> None:
    host = os.environ.get("SPIRIT_DASHBOARD_HOST", "0.0.0.0")
    port = int(os.environ.get("SPIRIT_DASHBOARD_PORT", "7000"))
    server = ThreadingHTTPServer((host, port), Handler)
    server.daemon_threads = True
    print(f"UNO Q Spirit dashboard listening on http://{host}:{port}", flush=True)
    try:
        server.serve_forever(poll_interval=0.5)
    except KeyboardInterrupt:
        pass
    finally:
        SERVICE.stop_event.set()
        server.server_close()


if __name__ == "__main__":
    main()
