"""PostgreSQL connection and schema for rag_project."""
from __future__ import annotations

from contextlib import contextmanager

import psycopg
from psycopg.rows import dict_row

from app.config import load_config

_MASTER_COLUMNS = """
    state TEXT,
    department TEXT,
    ir_number TEXT,
    document_title TEXT,
    year TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
"""

SCHEMA = f"""
CREATE TABLE IF NOT EXISTS ir_master (
    id SERIAL PRIMARY KEY,
    document_name TEXT NOT NULL UNIQUE,
    source_path TEXT,
    office_name TEXT,
    district TEXT,
    audit_period TEXT,
    auditee TEXT,
    {_MASTER_COLUMNS}
);

CREATE TABLE IF NOT EXISTS criteria_master (
    id SERIAL PRIMARY KEY,
    document_name TEXT NOT NULL UNIQUE,
    source_path TEXT,
    markdown_path TEXT,
    instrument_kind TEXT,
    {_MASTER_COLUMNS}
);

CREATE TABLE IF NOT EXISTS ir_chunks (
    id SERIAL PRIMARY KEY,
    document_id INTEGER NOT NULL
        REFERENCES ir_master(id) ON DELETE CASCADE,
    chunk TEXT NOT NULL,
    embedding DOUBLE PRECISION[],
    chunk_kind TEXT NOT NULL CHECK (chunk_kind IN ('part', 'observation')),
    part TEXT,
    observation_ref TEXT,
    hierarchy_path TEXT,
    metadata JSONB NOT NULL DEFAULT '{{}}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS criteria_chunks (
    id SERIAL PRIMARY KEY,
    document_id INTEGER NOT NULL
        REFERENCES criteria_master(id) ON DELETE CASCADE,
    parent_id INTEGER REFERENCES criteria_chunks(id) ON DELETE CASCADE,
    chunk TEXT NOT NULL,
    embedding DOUBLE PRECISION[],
    role TEXT NOT NULL CHECK (role IN ('parent', 'child')),
    chunk_kind TEXT NOT NULL,
    hierarchy_path TEXT,
    metadata JSONB NOT NULL DEFAULT '{{}}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ir_tables (
    id SERIAL PRIMARY KEY,
    document_id INTEGER NOT NULL
        REFERENCES ir_master(id) ON DELETE CASCADE,
    chunk_id INTEGER REFERENCES ir_chunks(id) ON DELETE CASCADE,
    table_markdown TEXT NOT NULL,
    hierarchy_path TEXT,
    metadata JSONB NOT NULL DEFAULT '{{}}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS criteria_tables (
    id SERIAL PRIMARY KEY,
    document_id INTEGER NOT NULL
        REFERENCES criteria_master(id) ON DELETE CASCADE,
    chunk_id INTEGER REFERENCES criteria_chunks(id) ON DELETE CASCADE,
    table_markdown TEXT NOT NULL,
    hierarchy_path TEXT,
    metadata JSONB NOT NULL DEFAULT '{{}}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ir_chunks_document_id_idx ON ir_chunks (document_id);
CREATE INDEX IF NOT EXISTS ir_chunks_part_idx ON ir_chunks (part);
CREATE INDEX IF NOT EXISTS ir_chunks_observation_ref_idx ON ir_chunks (observation_ref);
CREATE INDEX IF NOT EXISTS criteria_chunks_document_id_idx ON criteria_chunks (document_id);
CREATE INDEX IF NOT EXISTS criteria_chunks_parent_id_idx ON criteria_chunks (parent_id);
CREATE INDEX IF NOT EXISTS ir_tables_document_id_idx ON ir_tables (document_id);
CREATE INDEX IF NOT EXISTS criteria_tables_document_id_idx ON criteria_tables (document_id);
CREATE INDEX IF NOT EXISTS ir_master_state_idx ON ir_master (state);
CREATE INDEX IF NOT EXISTS ir_master_department_idx ON ir_master (department);
CREATE INDEX IF NOT EXISTS ir_master_ir_number_idx ON ir_master (ir_number);
CREATE INDEX IF NOT EXISTS criteria_master_state_idx ON criteria_master (state);
CREATE INDEX IF NOT EXISTS criteria_master_department_idx ON criteria_master (department);
CREATE INDEX IF NOT EXISTS criteria_master_ir_number_idx ON criteria_master (ir_number);
CREATE INDEX IF NOT EXISTS criteria_master_instrument_kind_idx ON criteria_master (instrument_kind);
"""

_CHUNK_TABLES = ("ir_chunks", "criteria_chunks")
_schema_ready = False


def _admin_dsn() -> str:
    db = load_config()["database"]
    return (
        f"host={db['host']} port={db['port']} user={db['user']} "
        f"password={db['password']} dbname=postgres"
    )


def app_dsn() -> str:
    db = load_config()["database"]
    return (
        f"host={db['host']} port={db['port']} user={db['user']} "
        f"password={db['password']} dbname={db['name']}"
    )


def _drop_legacy(cur) -> None:
    cur.execute("DROP TABLE IF EXISTS chunks CASCADE")
    cur.execute("DROP TABLE IF EXISTS extracted_tables CASCADE")
    cur.execute("DROP TABLE IF EXISTS document_master CASCADE")
    cur.execute(
        """
        SELECT column_name FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'ir_chunks'
        """
    )
    columns = {row[0] for row in cur.fetchall()}
    if columns and not {"part", "observation_ref", "chunk_kind"} <= columns:
        for name in (
            "ir_tables",
            "criteria_tables",
            "ir_chunks",
            "criteria_chunks",
            "ir_master",
            "criteria_master",
        ):
            cur.execute(f"DROP TABLE IF EXISTS {name} CASCADE")


def _use_vector_embeddings(cur) -> None:
    cur.execute("SELECT 1 FROM pg_extension WHERE extname = 'vector'")
    if cur.fetchone() is None:
        return
    for table in _CHUNK_TABLES:
        cur.execute(
            """
            SELECT data_type FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = %s AND column_name = 'embedding'
            """,
            (table,),
        )
        row = cur.fetchone()
        if row and row[0] != "USER-DEFINED":
            cur.execute(f"ALTER TABLE {table} DROP COLUMN embedding")
            cur.execute(f"ALTER TABLE {table} ADD COLUMN embedding vector")


def ensure_database() -> None:
    global _schema_ready
    if _schema_ready:
        return
    name = load_config()["database"]["name"]
    with psycopg.connect(_admin_dsn(), autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (name,))
            if cur.fetchone() is None:
                cur.execute(f'CREATE DATABASE "{name}"')
    with psycopg.connect(app_dsn(), autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT 1 FROM pg_available_extensions WHERE name = 'vector'"
            )
            if cur.fetchone():
                cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
            _drop_legacy(cur)
            cur.execute(SCHEMA)
            _use_vector_embeddings(cur)
    _schema_ready = True


@contextmanager
def connect():
    ensure_database()
    with psycopg.connect(app_dsn(), row_factory=dict_row) as conn:
        yield conn
