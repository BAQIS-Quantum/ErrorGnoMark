# Phase 1 已落地表清单（`001_schema.sql`）

与 `db/phase1/001_schema.sql` 中 **`CREATE TABLE IF NOT EXISTS`** 一致；用于评审、对照 `p1-step1` 草案与打勾清单 **B.31**。  
视图、扩展、枚举另见同文件；本表仅列**核心业务表**。

| 表名 | 简述 |
|------|------|
| `chip` | 芯片主实体 |
| `qubit` | 芯片上量子比特 |
| `coupler` | 耦合器 |
| `coupler_endpoint` | 耦合器与 qubit 端点 |
| `scope` | 作用域（chip / qubit_set 等） |
| `scope_member` | 作用域成员 |
| `source` | 数据来源 |
| `version` | 版本元数据（可选外键） |
| `metric_definition` | 指标定义 |
| `structure_event` | 结构变更事件 |
| `calibration_run` | 校准运行 |
| `calibration_artifact` | 校准产物 |
| `benchmark_run` | Benchmark 运行信封 |
| `observation_record` | 观测记录 |
| `structure_snapshot` | 结构快照 |
| `calibration_snapshot` | 校准参数快照 |
| `system_state` | 系统状态快照 |
| `lineage` | 血缘头（下游对象 → lineage） |
| `lineage_edge` | 血缘边（上游 → lineage） |

**Seed 覆盖**：`seed/010`～`040` 对上述子集写入演示行；并非每表在 demo 中都有业务行（如 `version` 可为空引用）。
