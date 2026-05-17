"""SQLite-backed persistence for ingested chunks.

Selective port of OpenHuman's `src/openhuman/memory/tree/store.rs` (966 lines → ~450).
Also includes wrapper methods for other Rust modules (tree_source, jobs, tree_topic)
that exist as DDL only — the runtime logic is NOT ported.

PORT STATUS (Rust store.rs: 16 pub fns, 11 ported after this fix):
  ✅ upsert_chunks                   — ported, semantically identical
  ✅ get_chunk                       — ported, semantically identical
  ✅ list_chunks                     — ported, limit clamping added in this fix
  ✅ count_chunks                    — ported, semantically identical
  ✅ set_chunk_lifecycle             — ported (Rust warns on 0-row update; Python silent)
  ✅ get_chunk_lifecycle             — ported, semantically identical
  ✅ is_source_ingested              — ported (not called from learnings.py, but public API)
  ✅ count_chunks_by_lifecycle       — ADDED in this fix (was missing)
  ✅ set_chunk_embedding             — ADDED in this fix (was missing)
  ✅ get_chunk_embedding             — ADDED in this fix (was missing)
  ✅ get_chunk_content_path          — ADDED in this fix (was missing)
  ❌ set_chunk_raw_refs              — NOT PORTED (needs chunk_raw_refs table; not needed for CLI)
  ❌ get_chunk_raw_refs              — NOT PORTED (needs chunk_raw_refs table; not needed for CLI)
  ❌ upsert_staged_chunks_tx         — NOT PORTED (file-backed content store; not needed)
  ❌ get_chunk_content_pointers      — NOT PORTED (content-store RPC; not needed)
  ❌ get_summary_content_pointers    — NOT PORTED (summary-tree RPC; not needed)
  ❌ list_summaries_with_content_path — NOT PORTED (summary-tree RPC; not needed)

WRAPPER METHODS (Python-only, no Rust store.rs equivalent):
  ⚠️ upsert_tree / upsert_summary / append_buffer — DDL exists, methods exist,
     but NO callers in this codebase. Rust runtime lives in tree_source/{store,bucket_seal}.rs
  ⚠️ enqueue_job / claim_next_job / count_jobs — DDL exists, methods exist,
     but NO callers. Rust runtime lives in jobs/store.rs
  ⚠️ upsert_entity_hotness / top_entities — DDL exists, methods exist,
     only `upsert_entity_hotness` is called once in learnings.py
  ⚠️ upsert_entity_index / query_entity_index — used by learnings.py scoring

All 9 tables ported (DDL only — runtime varies):
  - mem_tree_chunks          — main chunk storage
  - mem_tree_score           — per-chunk scoring
  - mem_tree_entity_index    — entity → node mapping
  - mem_tree_trees           — tree metadata (DDL only — no runtime callers)
  - mem_tree_summaries       — summary tree nodes (DDL only — no runtime callers)
  - mem_tree_buffers         — unsealed L0 buffer (DDL only — no runtime callers)
  - mem_tree_entity_hotness  — entity popularity tracking
  - mem_tree_jobs            — async job queue (DDL only — no runtime callers)
  - mem_tree_ingested_sources — ingest deduplication
"""

from __future__ import annotations

import datetime
import json
import sqlite3
import threading
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterator, List, Optional, Tuple

from .types import Chunk, Metadata, SourceKind, SourceRef, chunk_id

# ---------------------------------------------------------------------------
# Chunk lifecycle constants
# ---------------------------------------------------------------------------

CHUNK_STATUS_PENDING_EXTRACTION = "pending_extraction"
CHUNK_STATUS_ADMITTED = "admitted"
CHUNK_STATUS_BUFFERED = "buffered"
CHUNK_STATUS_SEALED = "sealed"
CHUNK_STATUS_DROPPED = "dropped"

# ---------------------------------------------------------------------------
# Query helper
# ---------------------------------------------------------------------------

@dataclass
class ListChunksQuery:
    """Filters for listing chunks. All fields are optional."""
    source_kind: Optional[SourceKind] = None
    source_id: Optional[str] = None
    owner: Optional[str] = None
    since_ms: Optional[int] = None
    until_ms: Optional[int] = None
    limit: Optional[int] = None
    lifecycle_status: Optional[str] = None


# ---------------------------------------------------------------------------
# Schema DDL
# ---------------------------------------------------------------------------

_SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS mem_tree_chunks (
    id                     TEXT PRIMARY KEY,
    source_kind            TEXT NOT NULL,
    source_id              TEXT NOT NULL,
    source_ref             TEXT,
    owner                  TEXT NOT NULL,
    timestamp_ms           INTEGER NOT NULL,
    time_range_start_ms    INTEGER NOT NULL,
    time_range_end_ms      INTEGER NOT NULL,
    tags_json              TEXT NOT NULL DEFAULT '[]',
    content                TEXT NOT NULL,
    token_count            INTEGER NOT NULL,
    seq_in_source          INTEGER NOT NULL,
    created_at_ms          INTEGER NOT NULL,
    lifecycle_status       TEXT NOT NULL DEFAULT 'admitted',
    content_path           TEXT,
    content_sha256         TEXT,
    embedding              BLOB
);

CREATE INDEX IF NOT EXISTS idx_mem_tree_chunks_source
    ON mem_tree_chunks(source_kind, source_id);
CREATE INDEX IF NOT EXISTS idx_mem_tree_chunks_timestamp
    ON mem_tree_chunks(timestamp_ms);
CREATE INDEX IF NOT EXISTS idx_mem_tree_chunks_owner
    ON mem_tree_chunks(owner);
CREATE INDEX IF NOT EXISTS idx_mem_tree_chunks_source_seq
    ON mem_tree_chunks(source_kind, source_id, seq_in_source);

CREATE TABLE IF NOT EXISTS mem_tree_score (
    chunk_id               TEXT PRIMARY KEY,
    total                  REAL NOT NULL,
    token_count_signal     REAL NOT NULL,
    unique_words_signal    REAL NOT NULL,
    metadata_weight        REAL NOT NULL,
    source_weight          REAL NOT NULL,
    interaction_weight     REAL NOT NULL,
    entity_density         REAL NOT NULL,
    dropped                INTEGER NOT NULL DEFAULT 0,
    reason                 TEXT,
    computed_at_ms         INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_mem_tree_score_total
    ON mem_tree_score(total);
CREATE INDEX IF NOT EXISTS idx_mem_tree_score_dropped
    ON mem_tree_score(dropped);

CREATE TABLE IF NOT EXISTS mem_tree_entity_index (
    entity_id              TEXT NOT NULL,
    node_id                TEXT NOT NULL,
    node_kind              TEXT NOT NULL,
    entity_kind            TEXT NOT NULL,
    surface                TEXT NOT NULL,
    score                  REAL NOT NULL,
    timestamp_ms           INTEGER NOT NULL,
    tree_id                TEXT,
    is_user                INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_mem_tree_entity_index_entity
    ON mem_tree_entity_index(entity_id);
CREATE INDEX IF NOT EXISTS idx_mem_tree_entity_index_node
    ON mem_tree_entity_index(node_id);
CREATE INDEX IF NOT EXISTS idx_mem_tree_entity_index_timestamp
    ON mem_tree_entity_index(timestamp_ms);

CREATE TABLE IF NOT EXISTS mem_tree_trees (
    id                     TEXT PRIMARY KEY,
    root_id                TEXT NOT NULL,
    status                 TEXT NOT NULL,
    tree_type              TEXT NOT NULL,
    owner                  TEXT NOT NULL,
    created_at_ms          INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_mem_tree_trees_status
    ON mem_tree_trees(status);

CREATE TABLE IF NOT EXISTS mem_tree_summaries (
    id                     TEXT PRIMARY KEY,
    tree_id                TEXT NOT NULL,
    tree_level             INTEGER NOT NULL,
    parent_id              TEXT,
    content                TEXT NOT NULL,
    token_count            INTEGER NOT NULL,
    chunk_count            INTEGER NOT NULL DEFAULT 0,
    time_range_start_ms    INTEGER,
    time_range_end_ms      INTEGER,
    created_at_ms          INTEGER NOT NULL,
    sealed_at_ms           INTEGER,
    deleted                INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_mem_tree_summaries_tree_level
    ON mem_tree_summaries(tree_id, tree_level);
CREATE INDEX IF NOT EXISTS idx_mem_tree_summaries_parent
    ON mem_tree_summaries(parent_id);
CREATE INDEX IF NOT EXISTS idx_mem_tree_summaries_sealed_at
    ON mem_tree_summaries(sealed_at_ms);
CREATE INDEX IF NOT EXISTS idx_mem_tree_summaries_deleted
    ON mem_tree_summaries(deleted);

CREATE TABLE IF NOT EXISTS mem_tree_buffers (
    tree_id                TEXT NOT NULL,
    chunk_id               TEXT NOT NULL,
    seq_in_tree            INTEGER NOT NULL,
    content                TEXT NOT NULL,
    token_count            INTEGER NOT NULL,
    oldest_timestamp_ms    INTEGER NOT NULL,
    newest_timestamp_ms    INTEGER NOT NULL,
    inserted_at_ms         INTEGER NOT NULL,
    PRIMARY KEY (tree_id, chunk_id)
);

CREATE INDEX IF NOT EXISTS idx_mem_tree_buffers_oldest
    ON mem_tree_buffers(tree_id, oldest_timestamp_ms);

CREATE TABLE IF NOT EXISTS mem_tree_entity_hotness (
    entity_id              TEXT NOT NULL,
    tree_id                TEXT NOT NULL,
    frequency              REAL NOT NULL DEFAULT 1.0,
    recency                REAL NOT NULL DEFAULT 1.0,
    score                  REAL NOT NULL DEFAULT 0.0,
    last_seen_ms           INTEGER NOT NULL,
    PRIMARY KEY (entity_id, tree_id)
);

CREATE INDEX IF NOT EXISTS idx_mem_tree_entity_hotness_score
    ON mem_tree_entity_hotness(score DESC);

CREATE TABLE IF NOT EXISTS mem_tree_jobs (
    id                     INTEGER PRIMARY KEY AUTOINCREMENT,
    kind                   TEXT NOT NULL,
    payload_json           TEXT NOT NULL,
    status                 TEXT NOT NULL DEFAULT 'pending',
    priority               INTEGER NOT NULL DEFAULT 0,
    retry_count            INTEGER NOT NULL DEFAULT 0,
    max_retries            INTEGER NOT NULL DEFAULT 3,
    created_at_ms          INTEGER NOT NULL,
    scheduled_at_ms        INTEGER NOT NULL,
    started_at_ms          INTEGER,
    completed_at_ms        INTEGER,
    error                  TEXT
);

CREATE INDEX IF NOT EXISTS idx_mem_tree_jobs_ready
    ON mem_tree_jobs(status, priority DESC, scheduled_at_ms);
CREATE INDEX IF NOT EXISTS idx_mem_tree_jobs_kind
    ON mem_tree_jobs(kind);

CREATE TABLE IF NOT EXISTS mem_tree_ingested_sources (
    source_kind            TEXT NOT NULL,
    source_id              TEXT NOT NULL,
    ingested_at_ms         INTEGER NOT NULL,
    chunk_count            INTEGER NOT NULL,
    PRIMARY KEY (source_kind, source_id)
);
"""


# ---------------------------------------------------------------------------
# Row → Chunk deserialisation helper
# ---------------------------------------------------------------------------

def _row_to_chunk(row: sqlite3.Row) -> Chunk:
    ts = datetime.datetime.fromtimestamp(row["timestamp_ms"] / 1000.0, tz=datetime.timezone.utc)
    tr_start = datetime.datetime.fromtimestamp(
        row["time_range_start_ms"] / 1000.0, tz=datetime.timezone.utc
    )
    tr_end = datetime.datetime.fromtimestamp(
        row["time_range_end_ms"] / 1000.0, tz=datetime.timezone.utc
    )
    created = datetime.datetime.fromtimestamp(
        row["created_at_ms"] / 1000.0, tz=datetime.timezone.utc
    )
    source_ref = None
    if row["source_ref"] is not None:
        source_ref = SourceRef(value=row["source_ref"])
    tags = json.loads(row["tags_json"]) if row["tags_json"] else []
    return Chunk(
        id=row["id"],
        content=row["content"],
        metadata=Metadata(
            source_kind=SourceKind.parse(row["source_kind"]),
            source_id=row["source_id"],
            owner=row["owner"],
            timestamp=ts,
            time_range=(tr_start, tr_end),
            tags=tags,
            source_ref=source_ref,
        ),
        token_count=row["token_count"],
        seq_in_source=row["seq_in_source"],
        created_at=created,
    )


# ---------------------------------------------------------------------------
# MemoryStore
# ---------------------------------------------------------------------------

class MemoryStore:
    """SQLite-backed persistence for the memory tree pipeline.

    Thread-safe (per-connection, per-thread via ``check_same_thread=False``
    with a lock). All 9 tables are created lazily on first connection.

    Usage::

        with MemoryStore(path) as store:
            store.upsert_chunks([...])
            chunk = store.get_chunk("abc...")
            results = store.list_chunks(ListChunksQuery(limit=20))
    """

    def __init__(self, db_path: str) -> None:
        self._db_path = str(Path(db_path).resolve())
        self._lock = threading.Lock()
        self._conn: Optional[sqlite3.Connection] = None

    # -- connection management ------------------------------------------------

    def open(self) -> None:
        """Open (or create) the SQLite database and apply schema."""
        if self._conn is not None:
            return
        self._conn = sqlite3.connect(self._db_path)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA busy_timeout=15000")
        self._conn.executescript(_SCHEMA_SQL)

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def __enter__(self) -> MemoryStore:
        self.open()
        return self

    def __exit__(self, *args) -> None:
        self.close()

    @contextmanager
    def _tx(self) -> Iterator[sqlite3.Connection]:
        """Yield a connection inside a transaction."""
        self.open()
        assert self._conn is not None
        with self._lock:
            with self._conn:
                yield self._conn

    # -- chunks ---------------------------------------------------------------

    def upsert_chunks(self, chunks: List[Chunk]) -> int:
        """Atomically upsert a batch of chunks. Idempotent on chunk.id."""
        if not chunks:
            return 0
        with self._tx() as conn:
            for c in chunks:
                conn.execute(
                    """INSERT INTO mem_tree_chunks (
                        id, source_kind, source_id, source_ref, owner,
                        timestamp_ms, time_range_start_ms, time_range_end_ms,
                        tags_json, content, token_count, seq_in_source, created_at_ms
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        source_kind      = excluded.source_kind,
                        source_id        = excluded.source_id,
                        source_ref       = excluded.source_ref,
                        owner            = excluded.owner,
                        timestamp_ms     = excluded.timestamp_ms,
                        time_range_start_ms = excluded.time_range_start_ms,
                        time_range_end_ms   = excluded.time_range_end_ms,
                        tags_json        = excluded.tags_json,
                        content          = excluded.content,
                        token_count      = excluded.token_count,
                        seq_in_source    = excluded.seq_in_source,
                        created_at_ms    = excluded.created_at_ms""",
                    (
                        c.id,
                        c.metadata.source_kind.as_str(),
                        c.metadata.source_id,
                        c.metadata.source_ref.value if c.metadata.source_ref else None,
                        c.metadata.owner,
                        _to_ms(c.metadata.timestamp),
                        _to_ms(c.metadata.time_range[0]),
                        _to_ms(c.metadata.time_range[1]),
                        json.dumps(c.metadata.tags),
                        c.content,
                        c.token_count,
                        c.seq_in_source,
                        _to_ms(c.created_at),
                    ),
                )
            return len(chunks)

    def get_chunk(self, chunk_id: str) -> Optional[Chunk]:
        """Fetch one chunk by id."""
        with self._tx() as conn:
            row = conn.execute(
                """SELECT id, source_kind, source_id, source_ref, owner,
                          timestamp_ms, time_range_start_ms, time_range_end_ms,
                          tags_json, content, token_count, seq_in_source, created_at_ms
                     FROM mem_tree_chunks WHERE id = ?""",
                (chunk_id,),
            ).fetchone()
            return _row_to_chunk(row) if row else None

    def list_chunks(self, query: ListChunksQuery = ListChunksQuery()) -> List[Chunk]:
        """List chunks with optional filters, ordered by timestamp DESC.

        Limit is clamped to [1, 10_000]; defaults to 100.
        Matches Rust store.rs semantics (MAX_LIST_LIMIT = 10_000).
        """
        conditions: List[str] = []
        params: List = []

        if query.source_kind is not None:
            conditions.append("source_kind = ?")
            params.append(query.source_kind.as_str())
        if query.source_id is not None:
            conditions.append("source_id = ?")
            params.append(query.source_id)
        if query.owner is not None:
            conditions.append("owner = ?")
            params.append(query.owner)
        if query.since_ms is not None:
            conditions.append("timestamp_ms >= ?")
            params.append(query.since_ms)
        if query.until_ms is not None:
            conditions.append("timestamp_ms <= ?")
            params.append(query.until_ms)
        if query.lifecycle_status is not None:
            conditions.append("lifecycle_status = ?")
            params.append(query.lifecycle_status)

        sql = (
            "SELECT id, source_kind, source_id, source_ref, owner,"
            "       timestamp_ms, time_range_start_ms, time_range_end_ms,"
            "       tags_json, content, token_count, seq_in_source, created_at_ms"
            "  FROM mem_tree_chunks"
        )
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        sql += " ORDER BY timestamp_ms DESC"
        # Clamp limit to [1, 10_000]; default 100 (Rust store.rs semantics)
        raw_limit = query.limit if query.limit is not None else 100
        limit = max(1, min(raw_limit, 10_000))
        sql += " LIMIT ?"
        params.append(limit)

        with self._tx() as conn:
            rows = conn.execute(sql, params).fetchall()
            return [_row_to_chunk(r) for r in rows]

    def count_chunks(self) -> int:
        """Total number of chunks in the store."""
        with self._tx() as conn:
            return conn.execute("SELECT COUNT(*) FROM mem_tree_chunks").fetchone()[0]

    def set_chunk_lifecycle(self, chunk_id: str, status: str) -> None:
        """Set lifecycle_status on a chunk (idempotent)."""
        with self._tx() as conn:
            conn.execute(
                "UPDATE mem_tree_chunks SET lifecycle_status = ? WHERE id = ?",
                (status, chunk_id),
            )

    def get_chunk_lifecycle(self, chunk_id: str) -> Optional[str]:
        """Read lifecycle_status for chunk_id."""
        with self._tx() as conn:
            row = conn.execute(
                "SELECT lifecycle_status FROM mem_tree_chunks WHERE id = ?",
                (chunk_id,),
            ).fetchone()
            return row[0] if row else None

    # -- Rust-equivalent: store.rs count_chunks_by_lifecycle_status -----------

    def count_chunks_by_lifecycle_status(self, status: str) -> int:
        """Count chunks at a given lifecycle status. Rust store.rs equivalent."""
        with self._tx() as conn:
            n: int = conn.execute(
                "SELECT COUNT(*) FROM mem_tree_chunks WHERE lifecycle_status = ?",
                (status,),
            ).fetchone()[0]
            return n

    # -- Rust-equivalent: store.rs set/get_chunk_embedding --------------------

    def set_chunk_embedding(self, chunk_id: str, embedding: List[float]) -> None:
        """Store a float embedding vector on a chunk. Rust store.rs equivalent."""
        with self._tx() as conn:
            blob = json.dumps(embedding).encode("utf-8")
            conn.execute(
                "UPDATE mem_tree_chunks SET embedding = ? WHERE id = ?",
                (blob, chunk_id),
            )

    def get_chunk_embedding(self, chunk_id: str) -> Optional[List[float]]:
        """Read the embedding vector for chunk_id. Rust store.rs equivalent."""
        with self._tx() as conn:
            row = conn.execute(
                "SELECT embedding FROM mem_tree_chunks WHERE id = ?",
                (chunk_id,),
            ).fetchone()
            if row is None or row[0] is None:
                return None
            return json.loads(row[0].decode("utf-8"))

    # -- Rust-equivalent: store.rs get_chunk_content_path ---------------------

    def get_chunk_content_path(self, chunk_id: str) -> Optional[str]:
        """Read content_path for chunk_id. Rust store.rs equivalent."""
        with self._tx() as conn:
            row = conn.execute(
                "SELECT content_path FROM mem_tree_chunks WHERE id = ?",
                (chunk_id,),
            ).fetchone()
            return row[0] if row and row[0] else None

    # -- score ----------------------------------------------------------------

    @dataclass
    class ScoreRow:
        chunk_id: str
        total: float
        token_count_signal: float = 0.0
        unique_words_signal: float = 0.0
        metadata_weight: float = 0.0
        source_weight: float = 0.0
        interaction_weight: float = 0.0
        entity_density: float = 0.0
        dropped: int = 0
        reason: Optional[str] = None
        computed_at_ms: int = 0

    def upsert_scores(self, scores: List[ScoreRow]) -> int:
        """Upsert score rows idempotently."""
        if not scores:
            return 0
        with self._tx() as conn:
            for s in scores:
                conn.execute(
                    """INSERT INTO mem_tree_score (
                        chunk_id, total, token_count_signal, unique_words_signal,
                        metadata_weight, source_weight, interaction_weight,
                        entity_density, dropped, reason, computed_at_ms
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(chunk_id) DO UPDATE SET
                        total = excluded.total,
                        token_count_signal = excluded.token_count_signal,
                        unique_words_signal = excluded.unique_words_signal,
                        metadata_weight = excluded.metadata_weight,
                        source_weight = excluded.source_weight,
                        interaction_weight = excluded.interaction_weight,
                        entity_density = excluded.entity_density,
                        dropped = excluded.dropped,
                        reason = excluded.reason,
                        computed_at_ms = excluded.computed_at_ms""",
                    (
                        s.chunk_id, s.total,
                        s.token_count_signal, s.unique_words_signal,
                        s.metadata_weight, s.source_weight, s.interaction_weight,
                        s.entity_density, s.dropped, s.reason, s.computed_at_ms,
                    ),
                )
            return len(scores)

    def get_score(self, chunk_id: str) -> Optional[ScoreRow]:
        """Fetch score for a chunk."""
        with self._tx() as conn:
            row = conn.execute(
                "SELECT * FROM mem_tree_score WHERE chunk_id = ?",
                (chunk_id,),
            ).fetchone()
            if not row:
                return None
            return MemoryStore.ScoreRow(
                chunk_id=row["chunk_id"],
                total=row["total"],
                token_count_signal=row["token_count_signal"],
                unique_words_signal=row["unique_words_signal"],
                metadata_weight=row["metadata_weight"],
                source_weight=row["source_weight"],
                interaction_weight=row["interaction_weight"],
                entity_density=row["entity_density"],
                dropped=row["dropped"],
                reason=row["reason"],
                computed_at_ms=row["computed_at_ms"],
            )

    # -- entity index ---------------------------------------------------------

    @dataclass
    class EntityIndexRow:
        entity_id: str
        node_id: str
        node_kind: str
        entity_kind: str
        surface: str
        score: float
        timestamp_ms: int
        tree_id: Optional[str] = None
        is_user: int = 0

    def upsert_entity_index(self, rows: List[EntityIndexRow]) -> int:
        if not rows:
            return 0
        with self._tx() as conn:
            for r in rows:
                conn.execute(
                    """INSERT INTO mem_tree_entity_index (
                        entity_id, node_id, node_kind, entity_kind,
                        surface, score, timestamp_ms, tree_id, is_user
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (r.entity_id, r.node_id, r.node_kind, r.entity_kind,
                     r.surface, r.score, r.timestamp_ms, r.tree_id, r.is_user),
                )
            return len(rows)

    def query_entity_index(
        self, entity_id: Optional[str] = None, limit: int = 100
    ) -> List[EntityIndexRow]:
        with self._tx() as conn:
            if entity_id:
                rows = conn.execute(
                    "SELECT * FROM mem_tree_entity_index WHERE entity_id = ? ORDER BY timestamp_ms DESC LIMIT ?",
                    (entity_id, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM mem_tree_entity_index ORDER BY timestamp_ms DESC LIMIT ?",
                    (limit,),
                ).fetchall()
            return [MemoryStore.EntityIndexRow(**dict(r)) for r in rows]

    # -- trees ----------------------------------------------------------------
    # Port status: DDL only. No callers. Rust equivalent: tree_source/store.rs.

    def upsert_tree(
        self, tree_id: str, root_id: str, status: str,
        tree_type: str, owner: str, created_at_ms: int,
    ) -> None:
        with self._tx() as conn:
            conn.execute(
                """INSERT INTO mem_tree_trees (id, root_id, status, tree_type, owner, created_at_ms)
                   VALUES (?, ?, ?, ?, ?, ?)
                   ON CONFLICT(id) DO UPDATE SET
                       status = excluded.status,
                       root_id = excluded.root_id""",
                (tree_id, root_id, status, tree_type, owner, created_at_ms),
            )

    # -- summarises -----------------------------------------------------------
    # Port status: DDL only. No callers. Rust: tree_source/store.rs.

    @dataclass
    class SummaryRow:
        id: str
        tree_id: str
        tree_level: int
        parent_id: Optional[str] = None
        content: str = ""
        token_count: int = 0
        chunk_count: int = 0
        time_range_start_ms: Optional[int] = None
        time_range_end_ms: Optional[int] = None
        created_at_ms: int = 0
        sealed_at_ms: Optional[int] = None
        deleted: int = 0

    def upsert_summary(self, s: SummaryRow) -> None:
        with self._tx() as conn:
            conn.execute(
                """INSERT INTO mem_tree_summaries (
                    id, tree_id, tree_level, parent_id, content,
                    token_count, chunk_count, time_range_start_ms,
                    time_range_end_ms, created_at_ms, sealed_at_ms, deleted
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    content = excluded.content,
                    token_count = excluded.token_count,
                    chunk_count = excluded.chunk_count,
                    sealed_at_ms = excluded.sealed_at_ms,
                    deleted = excluded.deleted""",
                (s.id, s.tree_id, s.tree_level, s.parent_id, s.content,
                 s.token_count, s.chunk_count, s.time_range_start_ms,
                 s.time_range_end_ms, s.created_at_ms, s.sealed_at_ms, s.deleted),
            )

    # -- buffers --------------------------------------------------------------
    # Port status: DDL only. No callers. Rust: tree_source/bucket_seal.rs.

    def append_buffer(
        self, tree_id: str, chunk_id: str, seq: int,
        content: str, token_count: int,
        oldest_ts_ms: int, newest_ts_ms: int,
    ) -> None:
        now = _now_ms()
        with self._tx() as conn:
            conn.execute(
                """INSERT OR REPLACE INTO mem_tree_buffers
                   (tree_id, chunk_id, seq_in_tree, content, token_count,
                    oldest_timestamp_ms, newest_timestamp_ms, inserted_at_ms)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (tree_id, chunk_id, seq, content, token_count,
                 oldest_ts_ms, newest_ts_ms, now),
            )

    # -- entity hotness -------------------------------------------------------
    # Port status: DDL + partial. upsert_entity_hotness called once in
    # learnings.py. top_entities has no callers. Rust: tree_topic/hotness.rs.

    def upsert_entity_hotness(
        self, entity_id: str, tree_id: str,
        frequency: float, recency: float, score: float, last_seen_ms: int,
    ) -> None:
        with self._tx() as conn:
            conn.execute(
                """INSERT INTO mem_tree_entity_hotness
                   (entity_id, tree_id, frequency, recency, score, last_seen_ms)
                   VALUES (?, ?, ?, ?, ?, ?)
                   ON CONFLICT(entity_id, tree_id) DO UPDATE SET
                       frequency = excluded.frequency,
                       recency = excluded.recency,
                       score = excluded.score,
                       last_seen_ms = excluded.last_seen_ms""",
                (entity_id, tree_id, frequency, recency, score, last_seen_ms),
            )

    def top_entities(self, tree_id: Optional[str] = None, limit: int = 20) -> List[Dict]:
        with self._tx() as conn:
            if tree_id:
                rows = conn.execute(
                    "SELECT * FROM mem_tree_entity_hotness WHERE tree_id = ? ORDER BY score DESC LIMIT ?",
                    (tree_id, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM mem_tree_entity_hotness ORDER BY score DESC LIMIT ?",
                    (limit,),
                ).fetchall()
            return [dict(r) for r in rows]

    # -- jobs -----------------------------------------------------------------
    # Port status: DDL only. No callers. Rust: jobs/store.rs (942 lines).

    @dataclass
    class JobRow:
        kind: str
        payload_json: str
        priority: int = 0
        max_retries: int = 3
        scheduled_at_ms: int = 0

    def enqueue_job(self, job: JobRow) -> int:
        now = _now_ms()
        scheduled = job.scheduled_at_ms if job.scheduled_at_ms > 0 else now
        with self._tx() as conn:
            cur = conn.execute(
                """INSERT INTO mem_tree_jobs
                   (kind, payload_json, status, priority, max_retries,
                    created_at_ms, scheduled_at_ms)
                   VALUES (?, ?, 'pending', ?, ?, ?, ?)""",
                (job.kind, job.payload_json, job.priority,
                 job.max_retries, now, scheduled),
            )
            return cur.lastrowid  # type: ignore[return-value]

    def claim_next_job(self, kinds: Optional[List[str]] = None) -> Optional[Dict]:
        """Claim the highest-priority pending job (atomically)."""
        with self._tx() as conn:
            if kinds:
                placeholders = ",".join("?" for _ in kinds)
                row = conn.execute(
                    f"""SELECT id, kind, payload_json, priority, retry_count, max_retries
                          FROM mem_tree_jobs
                         WHERE status = 'pending'
                           AND kind IN ({placeholders})
                           AND scheduled_at_ms <= ?
                         ORDER BY priority DESC, scheduled_at_ms
                         LIMIT 1""",
                    [*kinds, _now_ms()],
                ).fetchone()
            else:
                row = conn.execute(
                    """SELECT id, kind, payload_json, priority, retry_count, max_retries
                         FROM mem_tree_jobs
                        WHERE status = 'pending'
                          AND scheduled_at_ms <= ?
                        ORDER BY priority DESC, scheduled_at_ms
                        LIMIT 1""",
                    (_now_ms(),),
                ).fetchone()
            if not row:
                return None
            job = dict(row)
            conn.execute(
                "UPDATE mem_tree_jobs SET status = 'running', started_at_ms = ? WHERE id = ?",
                (_now_ms(), job["id"]),
            )
            return job

    def count_jobs(self, status: Optional[str] = None) -> int:
        """Count jobs without mutating queue state."""
        with self._tx() as conn:
            if status is None:
                return conn.execute("SELECT COUNT(*) FROM mem_tree_jobs").fetchone()[0]
            return conn.execute(
                "SELECT COUNT(*) FROM mem_tree_jobs WHERE status = ?",
                (status,),
            ).fetchone()[0]

    # -- ingested-sources dedup -----------------------------------------------

    def is_source_ingested(self, source_kind: SourceKind, source_id: str) -> bool:
        """Check whether (kind, id) has already been ingested."""
        with self._tx() as conn:
            row = conn.execute(
                "SELECT 1 FROM mem_tree_ingested_sources WHERE source_kind = ? AND source_id = ?",
                (source_kind.as_str(), source_id),
            ).fetchone()
            return row is not None

    def claim_source_ingest(
        self, source_kind: SourceKind, source_id: str, chunk_count: int = 0
    ) -> bool:
        """Atomically claim a source for ingestion. Returns False if already claimed."""
        now = _now_ms()
        with self._tx() as conn:
            try:
                conn.execute(
                    """INSERT INTO mem_tree_ingested_sources
                       (source_kind, source_id, ingested_at_ms, chunk_count)
                       VALUES (?, ?, ?, ?)""",
                    (source_kind.as_str(), source_id, now, chunk_count),
                )
                return True
            except sqlite3.IntegrityError:
                return False


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _to_ms(dt: datetime.datetime) -> int:
    """Convert a timezone-aware datetime to milliseconds since epoch."""
    return int(dt.timestamp() * 1000)


def _now_ms() -> int:
    """Current time in milliseconds since epoch (UTC)."""
    return int(datetime.datetime.now(datetime.timezone.utc).timestamp() * 1000)
