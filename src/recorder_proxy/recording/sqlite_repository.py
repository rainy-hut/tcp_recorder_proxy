from __future__ import annotations

from pathlib import Path
import json
import sqlite3

from recorder_proxy.recording.models import ParsedMessage, RawCaptureEvent


class SQLiteRepository:
    def __init__(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(path)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self._init_schema()

    def _init_schema(self) -> None:
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS raw_events (
              event_id TEXT PRIMARY KEY,
              session_id TEXT NOT NULL,
              device_id TEXT NOT NULL,
              route_id TEXT NOT NULL,
              connection_id TEXT NOT NULL,
              direction TEXT NOT NULL,
              timestamp_ns INTEGER NOT NULL,
              chunk_sequence INTEGER NOT NULL,
              byte_length INTEGER NOT NULL,
              sha256 TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS parsed_messages (
              message_id TEXT PRIMARY KEY,
              session_id TEXT NOT NULL,
              device_id TEXT NOT NULL,
              route_id TEXT NOT NULL,
              connection_id TEXT NOT NULL,
              direction TEXT NOT NULL,
              classification TEXT NOT NULL,
              parse_status TEXT NOT NULL,
              source_event_ids TEXT NOT NULL,
              message_start_offset INTEGER NOT NULL,
              message_length INTEGER NOT NULL,
              message_sha256 TEXT NOT NULL,
              decoded_summary TEXT NOT NULL,
              raw_message_hex TEXT NOT NULL,
              parse_error TEXT
            );
            """
        )
        self.conn.commit()

    def insert_raw_event(self, event: RawCaptureEvent, sha256: str) -> None:
        c = event.connection
        self.conn.execute(
            """
            INSERT OR REPLACE INTO raw_events VALUES (?,?,?,?,?,?,?,?,?,?)
            """,
            (
                event.event_id,
                c.session_id,
                c.device_id,
                c.route_id,
                c.connection_id,
                event.direction,
                event.timestamp_ns,
                event.chunk_sequence,
                len(event.data),
                sha256,
            ),
        )

    def insert_parsed_message(self, message: ParsedMessage) -> None:
        self.conn.execute(
            """
            INSERT OR REPLACE INTO parsed_messages VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                message.message_id,
                message.session_id,
                message.device_id,
                message.route_id,
                message.connection_id,
                message.direction,
                message.classification,
                message.parse_status,
                json.dumps(message.source_event_ids, ensure_ascii=False),
                message.message_start_offset,
                message.message_length,
                message.message_sha256,
                json.dumps(message.decoded_summary, ensure_ascii=False),
                message.raw_message_hex,
                message.parse_error,
            ),
        )

    def commit(self) -> None:
        self.conn.commit()

    def close(self) -> None:
        self.conn.commit()
        self.conn.close()
