# `scripts/postgres/` — 操作 Postgres 的脚本（不是 SQL 本体）

本目录与仓库根下的 **`db/phase1/`** 配套使用：

- **`db/phase1/`**：只放 **`.sql`**（DDL + seed）。说明见 `db/phase1/README.md`。
- **`scripts/postgres/`**：放 **`.sh` / `.py` / `.ipynb`**，用来执行或校验那些 SQL。

`apply_phase1.sh` 通过 `$ROOT/db/phase1/...` 引用根目录的 SQL，两处**不是重复备份**，职责分开。

## 常用命令（仓库根目录）

```bash
export EGM_PG_DSN='postgresql://USER:PASS@HOST:5432/DBNAME'
./scripts/postgres/apply_phase1.sh
pip install 'psycopg[binary]>=3.2'   # 若尚未安装
python scripts/postgres/verify_seed_counts.py
PYTHONPATH=src python scripts/postgres/run_p0_queries.py
```

**验收入口（推荐）**：一次跑完 verify + P0 SQL；CI 使用 ``--strict``（无 ``EGM_PG_DSN`` 或缺 psycopg 则失败，避免静默 skip）。实现见 ``src/egm/datastore/phase1_acceptance.py``。

```bash
PYTHONPATH=src python -m egm.datastore.phase1_acceptance --strict
```

## 本目录脚本

| 文件 | 作用 |
|------|------|
| `apply_phase1.sh` | 顺序执行 `001_schema.sql` + `seed/*.sql` |
| `verify_seed_counts.py` | 断言 seed 后关键表行数（及 `benchmark_run` / `observation_record` 下限） |
| `run_p0_queries.py` | 跑 `sql/queries/p0/` 下 Phase 1 demo SQL（Q1～Q23；含 **API-06 Q7**、**API-07 Q8**、**API-10 Q12** 过滤/分页、**API-11 Q14**、API-15/16 带参变体） |
| `phase1_database_checks.ipynb` | 与 verify / run 同逻辑的笔记本入口 |

## CI

推送到 **`main` / `develop` / `feature/**` / `exp/**`**，或向 **`main` / `develop`** 开 PR 时，GitHub Actions 会运行 **`.github/workflows/phase1-postgres.yml`**（Postgres 15 + apply，然后 **`python -m egm.datastore.phase1_acceptance --strict`**）。可在 Actions 里 **手动重跑**（`workflow_dispatch`）。

## 与 `scripts/db/` 的关系

遗留 notebook 可能仍在 **`scripts/db/phase1_database_checks.ipynb`**；路径应指向 **`../postgres/`**。新工作以本目录为准；见 **`scripts/db/README.md`**。
