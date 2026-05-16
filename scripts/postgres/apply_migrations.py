#!/usr/bin/env python3
"""
Apply pending SQL migrations under db/migrations/.

Reads target version from db/schema_version.txt. Records applied versions in
egm_schema_migration. Idempotent: skips already-applied versions.

Requires: psycopg, EGM_PG_DSN.
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _target_version(root: Path) -> str:
    raw = (root / "db" / "schema_version.txt").read_text(encoding="utf-8").strip()
    if not re.fullmatch(r"\d{4}", raw):
        raise ValueError(f"Invalid schema_version.txt: {raw!r} (expected 4 digits)")
    return raw


def _migration_files(root: Path) -> list[tuple[str, Path]]:
    mig_dir = root / "db" / "migrations"
    out: list[tuple[str, Path]] = []
    for path in sorted(mig_dir.glob("*.sql")):
        m = re.match(r"^(\d{4})_", path.name)
        if not m:
            continue
        out.append((m.group(1), path))
    return out


def main() -> int:
    dsn = os.environ.get("EGM_PG_DSN")
    if not dsn:
        print("EGM_PG_DSN is not set", file=sys.stderr)
        return 1

    try:
        from psycopg import Connection
    except ImportError:
        print("psycopg not installed; pip install 'psycopg[binary]>=3.2'", file=sys.stderr)
        return 1

    root = _repo_root()
    target = _target_version(root)
    files = _migration_files(root)
    if not files:
        print("No migration files found", file=sys.stderr)
        return 1

    pending = [(v, p) for v, p in files if v <= target]
    if not pending:
        print("Nothing to apply", file=sys.stderr)
        return 0

    with Connection.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables
                    WHERE table_schema = 'public'
                      AND table_name = 'egm_schema_migration'
                )
                """
            )
            row = cur.fetchone()
            has_registry = row[0] if row else False

            applied: set[str] = set()
            if has_registry:
                cur.execute("SELECT version FROM egm_schema_migration")
                applied = {r[0] for r in cur.fetchall()}

        for version, path in pending:
            if version in applied:
                print(f"skip {version} (already applied)")
                continue
            sql = path.read_text(encoding="utf-8")
            print(f"apply {version} from {path.name}")
            with conn.cursor() as cur:
                cur.execute(sql)
            conn.commit()
            applied.add(version)

    print(f"Migrations complete (target {target}, phase1_v1.1 when target >= 0002).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
