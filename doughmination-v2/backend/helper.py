"""
Copyright (c) 2026 Clove Twilight
Licensed under the ESAL-1.3 Licence.
See LICENCE.md in the project root for full licence information.
"""

"""
Visitor logging helper.

Logs page visits to SQLite + JSONL. The frontend pings POST /helper on every
route change (valid or 404), and this module records the visit along with
client IP, headers, fingerprint, etc.

LogQuery is preserved for ad-hoc analysis (find by IP, path, time range,
suspicious patterns, CSV export).
"""

import csv
import hashlib
import json
import logging
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Request
from pydantic import BaseModel

from app.core.config import DATA_DIR


# ---------------------------------------------------------------------------
# Visitor logger
# ---------------------------------------------------------------------------

class VisitorLogger:
    def __init__(self, db_path: Path, log_file: Path):
        self.db_path = str(db_path)
        self.log_file = str(log_file)
        self.init_database()
        self.setup_file_logging()

    def init_database(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS visitor_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                unix_timestamp REAL NOT NULL,
                ip_address TEXT NOT NULL,
                user_agent TEXT,
                referer TEXT,
                method TEXT,
                path TEXT,
                query_string TEXT,
                remote_addr TEXT,
                x_forwarded_for TEXT,
                x_real_ip TEXT,
                accept_language TEXT,
                accept_encoding TEXT,
                host TEXT,
                all_headers TEXT,
                cookies TEXT,
                body_size INTEGER,
                response_code INTEGER,
                request_time_ms REAL,
                browser_fingerprint TEXT,
                country TEXT,
                asn TEXT
            )
        """)

        cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON visitor_logs(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ip ON visitor_logs(ip_address)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_path ON visitor_logs(path)")

        conn.commit()
        conn.close()

    def setup_file_logging(self):
        self.file_logger = logging.getLogger("visitor_logger")
        self.file_logger.setLevel(logging.INFO)
        self.file_logger.propagate = False

        # Don't double-attach if module is re-imported (e.g. uvicorn reload)
        target = str(Path(self.log_file).resolve())
        for h in self.file_logger.handlers:
            if isinstance(h, logging.FileHandler) and h.baseFilename == target:
                return

        handler = logging.FileHandler(self.log_file)
        handler.setFormatter(logging.Formatter("%(message)s"))
        self.file_logger.addHandler(handler)

    @staticmethod
    def get_client_ip(request: Request) -> str:
        xff = request.headers.get("X-Forwarded-For")
        if xff:
            return xff.split(",")[0].strip()
        for header in ("X-Real-IP", "CF-Connecting-IP", "True-Client-IP"):
            value = request.headers.get(header)
            if value:
                return value
        return request.client.host if request.client else ""

    @staticmethod
    def get_browser_fingerprint(request: Request) -> str:
        ua = request.headers.get("User-Agent", "")
        lang = request.headers.get("Accept-Language", "")
        encoding = request.headers.get("Accept-Encoding", "")
        return hashlib.md5(f"{ua}|{lang}|{encoding}".encode()).hexdigest()

    def log_visitor(
        self,
        request: Request,
        path: Optional[str] = None,
        body_size: int = 0,
        response_code: int = 200,
        request_time_ms: float = 0.0,
    ):
        now = datetime.now(timezone.utc)
        timestamp = now.isoformat().replace("+00:00", "Z")
        unix_timestamp = now.timestamp()

        all_headers = dict(request.headers)
        cookies = dict(request.cookies) if request.cookies else {}

        log_data = {
            "timestamp": timestamp,
            "unix_timestamp": unix_timestamp,
            "ip_address": self.get_client_ip(request),
            "user_agent": request.headers.get("User-Agent", ""),
            "referer": request.headers.get("Referer", ""),
            "method": request.method,
            # The frontend tells us which page it was on; fall back to the
            # actual request path if that wasn't supplied.
            "path": path or request.url.path,
            "query_string": request.url.query or "",
            "remote_addr": request.client.host if request.client else "",
            "x_forwarded_for": request.headers.get("X-Forwarded-For", ""),
            "x_real_ip": request.headers.get("X-Real-IP", ""),
            "accept_language": request.headers.get("Accept-Language", ""),
            "accept_encoding": request.headers.get("Accept-Encoding", ""),
            "host": request.headers.get("Host", ""),
            "all_headers": all_headers,
            "cookies": cookies,
            "body_size": body_size,
            "response_code": response_code,
            "request_time_ms": request_time_ms,
            "browser_fingerprint": self.get_browser_fingerprint(request),
            "country": "Unknown",  # Optional: integrate GeoIP
            "asn": "Unknown",      # Optional: integrate ASN lookup
        }

        # JSONL on disk (easy to grep/tail)
        self.file_logger.info(json.dumps(log_data))

        # SQLite for structured querying
        self._log_to_db(log_data)

    def _log_to_db(self, log_data):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO visitor_logs (
                    timestamp, unix_timestamp, ip_address, user_agent, referer,
                    method, path, query_string, remote_addr, x_forwarded_for,
                    x_real_ip, accept_language, accept_encoding, host,
                    all_headers, cookies, body_size, response_code,
                    request_time_ms, browser_fingerprint, country, asn
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                log_data["timestamp"], log_data["unix_timestamp"], log_data["ip_address"],
                log_data["user_agent"], log_data["referer"], log_data["method"],
                log_data["path"], log_data["query_string"], log_data["remote_addr"],
                log_data["x_forwarded_for"], log_data["x_real_ip"],
                log_data["accept_language"], log_data["accept_encoding"],
                log_data["host"], json.dumps(log_data["all_headers"]),
                json.dumps(log_data["cookies"]), log_data["body_size"],
                log_data["response_code"], log_data["request_time_ms"],
                log_data["browser_fingerprint"], log_data["country"], log_data["asn"],
            ))

            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Database logging error: {e}")


# ---------------------------------------------------------------------------
# Query helpers
# ---------------------------------------------------------------------------

class LogQuery:
    def __init__(self, db_path: Path):
        self.db_path = str(db_path)

    def find_by_ip(self, ip_address):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM visitor_logs
            WHERE ip_address = ?
            ORDER BY timestamp DESC
        """, (ip_address,))
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results

    def find_by_path(self, path):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM visitor_logs
            WHERE path LIKE ?
            ORDER BY timestamp DESC
        """, (f"%{path}%",))
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results

    def find_by_time_range(self, start_timestamp, end_timestamp):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM visitor_logs
            WHERE unix_timestamp BETWEEN ? AND ?
            ORDER BY timestamp DESC
        """, (start_timestamp, end_timestamp))
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results

    def find_suspicious_patterns(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT ip_address, COUNT(*) as visit_count,
                   MIN(timestamp) as first_visit, MAX(timestamp) as last_visit
            FROM visitor_logs
            WHERE unix_timestamp > (strftime('%s', 'now') - 3600)
            GROUP BY ip_address
            HAVING COUNT(*) > 20
            ORDER BY visit_count DESC
        """)
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results

    def export_to_csv(self, output_file: str = "visitor_logs.csv"):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM visitor_logs ORDER BY timestamp DESC")
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            print("No logs to export")
            return

        with open(output_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows([dict(row) for row in rows])

        print(f"Exported {len(rows)} entries to {output_file}")


# ---------------------------------------------------------------------------
# FastAPI router
# ---------------------------------------------------------------------------

DB_PATH = DATA_DIR / "visitor_logs.db"
LOG_FILE = DATA_DIR / "visitor_logs.jsonl"

# Single shared logger instance for the lifetime of the process
_visitor_logger = VisitorLogger(db_path=DB_PATH, log_file=LOG_FILE)

router = APIRouter()


class HelperPing(BaseModel):
    path: Optional[str] = None
    referer: Optional[str] = None


@router.post("/helper")
async def helper_ping(payload: HelperPing, request: Request):
    """Log a page visit. Called by the frontend on every navigation."""
    _visitor_logger.log_visitor(request=request, path=payload.path)
    return {"ok": True}


@router.get("/helper")
async def helper_ping_get(request: Request):
    """GET fallback (e.g. sendBeacon image, no-CORS)."""
    _visitor_logger.log_visitor(
        request=request,
        path=request.query_params.get("path"),
    )
    return {"ok": True}
