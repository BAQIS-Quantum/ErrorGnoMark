  当前系统真实层级结构                                                                                                                                 
                                                                                                                                                       
  ┌─────────────────────────────────────────────────────┐                                                                                              
  │  Layer 5: Suites / Orchestration                    │                                                                                              
  │  egm/suites/                                        │                        
  │  CampaignSubmitFetch → JobSubmitFetch               │
  │  campaign_runner (alias)                            │
  └──────────────────────┬──────────────────────────────┘
                         │ 调用
  ┌──────────────────────▼──────────────────────────────┐
  │  Layer 4: Reporting                                 │
  │  egm/reporting/                                     │
  │  generators/ · visualizers/ · formatters/           │
  └──────────────────────┬──────────────────────────────┘
                         │ 消费
  ┌──────────────────────▼──────────────────────────────┐
  │  Layer 3: Experiments                               │
  │  egm/core/experiments/                              │
  │  base.BaseExperiment (ABC)                          │
  │  ├── physical/benchmarking/ (rb, xeb, mrb, ...)     │
  │  ├── physical/characterization/ (rabi, ramsey, ...) │
  │  ├── algorithmic/ (vqe, qaoa, grover, ...)          │
  │  └── logical/ (空)                                  │
  └──────────────────────┬──────────────────────────────┘
                         │ 依赖
  ┌──────────────────────▼──────────────────────────────┐
  │  Layer 2: Core Engine / Analysis                    │
  │  egm/core/engine/executor.py → QuantumEngine        │
  │  egm/core/analysis/ (rb, xeb, mrb, tomo, ...)      │
  │  egm/core/data/ (models, storage, context)          │
  │  egm/schemas/ (configs, plan, results/*)            │
  └──────────────────────┬──────────────────────────────┘
                         │ 依赖
  ┌──────────────────────▼──────────────────────────────┐
  │  Layer 1: Physical / Primitives                     │
  │  egm/core/circuits/ (circuit, gate_sets, native_gates)│
  │  egm/core/backends/ (base_backend → real/sim/dummy) │
  │  egm/core/backends/direct/quark.py (硬件接口)       │
  │  egm/core/backends/cloud/quafu.py                   │
  └─────────────────────────────────────────────────────┘

## 关于suite 设计
  "关于当前系统真实层级结构，suites 和reporting你觉得设计合理么？其实我当时设想的就是，suite 调用core层各种实验库，坐专门用于编"

    当前 suites/ 实际上是硬件 job 管理层，不是通用编排层：                                                                                               
  # job_submit_fetch.py line 9
  from egm.core.backends.Real_Quark_Backend import RealQuarkBackend

  它硬绑定了 RealQuarkBackend，JobSubmitFetch 完全无法用于 simulator 或 cloud backend。这导致：
  - 想用 simulator 跑实验 → 只能绕过 suites，直接用 engine.execute_with_ideal()
  - 想换硬件 → suites 整层要重写

  原本 suite 应该是什么：调 BaseExperiment.circuits() 拿线路，扔给任意 backend 执行，收结果回来做 stitch/store —— 是个与 backend
  无关的流程编排者。现在它变成了 Quark 专用的 I/O 适配器。



  │                                                                                                                                                                                                                                                       
❯ ├── __init__.py                    # 导出公共接口
  │                                                                                                                                                    
  ├── adapters/upt                   # 【新增】执行适配器层（核心改动）
  │   ├── __init__.py                                                                                                          │   ├── base.py                    # AsyncBackend 接口定义
  │   │                              #   submit(circuit, shots, args) → remote_id
  │   │                              #   fetch(remote_id) → counts
  │   ├── sync_adapter.py            # 包装任意 BaseBackend，伪造 submit/fetch
  │   │                              #   submit() → 立即 run()，把结果存内存
  │   │                              #   fetch() → 从内存取出
  │   └── quark_adapter.py           # 包装 RealQuarkBackend（把现有逻辑搬过来）
  │
  ├── job/                           # 【重构】单任务层
  │   ├── __init__.py
  │   ├── job_submit_fetch.py        # 改为依赖 adapters.base.AsyncBackend
  │   │                              # （不再直接 import RealQuarkBackend）
  │   └── job_store.py               # 单 job 的文件读写（从现有拆出）
  │
  ├── campaign/                      # 【重构】批次编排层
  │   ├── __init__.py
  │   ├── campaign_runner.py         # 高层入口：接收 experiment 列表，驱动 job 层
  │   ├── campaign_submit_fetch.py   # 现有逻辑基本保留，依赖改 job/
  │   └── campaign_store_sqlite.py   # SQLite 持久化（基本不动）
  │
  └── analysis_bridge/               # 【现有 quark_analysis_bridge 归位】
      ├── __init__.py
      └── quark_analysis_bridge.py   # raw result → stitch → analysis 的胶水层

  ---
  各层职责边界（给实习生的说明）

  ┌──────────────────┬───────────────────────────────────────┬──────────────────────────┐
  │        层        │                 职责                  │        不该做的事        │
  ├──────────────────┼───────────────────────────────────────┼──────────────────────────┤
  │ adapters/        │ 屏蔽同步/异步差异                     │ 不知道 experiment 是什么 │
  ├──────────────────┼───────────────────────────────────────┼──────────────────────────┤
  │ job/             │ 单批线路的 submit/fetch/存文件        │ 不知道 campaign 是什么   │
  ├──────────────────┼───────────────────────────────────────┼──────────────────────────┤
  │ campaign/        │ 编排多个 job，聚合结果                │ 不直接碰 backend         │
  ├──────────────────┼───────────────────────────────────────┼──────────────────────────┤
  │ analysis_bridge/ │ 把 raw counts stitch 成 analysis 输入 │ 不做 fitting/plotting    │
  └──────────────────┴───────────────────────────────────────┴──────────────────────────┘

  ---
  关键约束（设计红线）

  1. campaign/ 和 job/ 都只依赖 adapters.base.AsyncBackend，不 import 任何具体 backend
  2. sync_adapter.py 让 simulator 用户完全不感知 submit/fetch 机制
  3. analysis_bridge 不是必选路径——用户可以拿到 raw counts 自己处理

  ---
  用户侧使用形态对比

  # 现在（只能用 Quark）：
  job = JobSubmitFetch(backend=RealQuarkBackend(...))

  # 改后（任意 backend）：
  adapter = SyncAdapter(DummyBackend())        # 本地测试
  adapter = QuarkAdapter(RealQuarkBackend(...)) # 真机
  job = JobSubmitFetch(adapter=adapter)        # 接口一致


## 关于execution 设计
那我还有一个问题，关于处于v3架构的execution逻辑，请问之前的engin，现在是不是要隶属于execution，而且backends应该是独立存在， 
  还是处于execution 下面呢？你的想法是                                                                                        

⏺ 我的看法是：engine 归入 execution，backends 保持独立。

  理由如下：

  ---
  backends 的本质是基础设施，不是执行逻辑

  backends/ = "硬件接口契约"
              ← 定义怎么和一个量子设备对话
              ← 是最底层的 primitive

  execution/ = "执行编排逻辑"
              ← 定义怎么协调 ideal + noisy 两路运行
              ← 是比 backends 高一层的调度者

  如果 backends 放在 execution 下面，依赖方向就乱了：

  # 如果 backends 在 execution/ 下：
  suites/adapters/ → execution/backends/   ← 奇怪，adapter 要穿过 execution 才能拿到 backend
  experiments/     → execution/backends/   ← 实验层要感知执行层内部结构

  # backends 独立时：
  suites/adapters/ → core/backends/        ← 干净
  experiments/     → core/backends/        ← 干净
  execution/       → core/backends/        ← 干净，execution 消费 backends

  ---
  建议的 v3 结构

  core/
  ├── circuits/          # 原语：线路表示
  ├── backends/          # 原语：硬件接口（独立存在）
  │   ├── base_backend.py
  │   ├── simulators/
  │   ├── cloud/
  │   └── direct/
  ├── execution/         # 编排：engine 归入这里
  │   ├── __init__.py
  │   └── executor.py    # QuantumEngine（从 engine/ 搬来）
  ├── experiments/       # 实验库
  └── analysis/          # 分析库

  core/engine/ 这个目录可以直接废弃，内容并入 execution/。

  ---
  依赖方向一条线

  circuits  ←──  backends  ←──  execution  ←──  experiments
                      ↑
                 suites/adapters 也在这里接入

  backends 是被多个上层共同依赖的节点，独立放才能避免循环依赖。