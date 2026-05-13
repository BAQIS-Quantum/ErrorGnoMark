"""
Phase 1 Postgres **验收入口**（数据库已 apply + seed 之后）。

顺序执行与 ``scripts/postgres/verify_seed_counts.py``、``scripts/postgres/run_p0_queries.py``
相同的逻辑，作为「最终 Phase 1 验收」的**单一模块面**：CI、本地、或被其它 Python 代码 import。

前置：环境变量 ``EGM_PG_DSN``；已安装 ``psycopg``；仓库根下存在 ``db/phase1``、``sql/queries/p0``。

用法：

.. code-block:: bash

   export EGM_PG_DSN='postgresql://...'
   PYTHONPATH=src python -m egm.datastore.phase1_acceptance --strict

``--strict``：未设置 ``EGM_PG_DSN`` 或无法导入 ``psycopg`` 时 **退出码 1**（用于 CI，避免静默 skip）。
默认不加 ``--strict`` 时与两个脚本一致：无 DSN / 无 psycopg 时退出码 **0**（本地可跳过）。
"""
from __future__ import annotations

import argparse
import importlib.util
import os
import sys
from pathlib import Path


def _repo_root() -> Path:
    # .../src/egm/datastore/phase1_acceptance.py -> repo root
    return Path(__file__).resolve().parents[3]


def _load_script_main(repo: Path, relative_path: str, module_label: str):
    path = repo / relative_path
    if not path.is_file():
        raise FileNotFoundError(f"Missing acceptance script: {path}")
    spec = importlib.util.spec_from_file_location(module_label, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load spec for {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    main = getattr(mod, "main", None)
    if main is None or not callable(main):
        raise RuntimeError(f"{path} has no callable main()")
    return main


def run_phase1_db_acceptance(*, strict: bool = False) -> int:
    """
    Run verify_seed_counts then run_p0_queries.

    Returns:
        0 on success or skip (non-strict, no DSN).
        Non-zero on failure or strict precondition violation.
    """
    if strict:
        if not os.environ.get("EGM_PG_DSN"):
            print("phase1_acceptance: --strict requires EGM_PG_DSN", file=sys.stderr)
            return 1
        try:
            import psycopg  # noqa: F401
        except ImportError:
            print("phase1_acceptance: --strict requires psycopg to be installed", file=sys.stderr)
            return 1

    repo = _repo_root()
    verify_main = _load_script_main(repo, "scripts/postgres/verify_seed_counts.py", "_egm_verify_seed_counts")
    p0_main = _load_script_main(repo, "scripts/postgres/run_p0_queries.py", "_egm_run_p0_queries")

    r = verify_main()
    if r != 0:
        return r
    return p0_main()


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="Phase 1 Postgres acceptance: verify seed row counts, then run sql/queries/p0 checks.",
    )
    p.add_argument(
        "--strict",
        action="store_true",
        help="Require EGM_PG_DSN and psycopg (exit 1 if missing; use in CI).",
    )
    args = p.parse_args(argv)
    return run_phase1_db_acceptance(strict=args.strict)


if __name__ == "__main__":
    raise SystemExit(main())
