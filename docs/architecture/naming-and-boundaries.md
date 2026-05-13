```md
# EGM 架构模块命名工业化检查与建议

## 背景

当前 EGM 顶层目录结构大致如下：

```text
egm/
  analysis/
  datastore/
  domain/
  execution/
  foundation/
  intelligence/
  protocols/
  reporting/
  schemas/
  server/
  suites/
```

其中，原先的 `experiments/` 已经收敛重命名为 `protocols/`。从最新架构设计意图来看，系统已经从“研究型实验代码组织”逐步转向“工业级平台化软件分层”。

本检查的目标是：从工业软件级别标准出发，评估每个顶层模块的命名是否准确、稳定、边界清晰，并判断其是否适合长期演化。

---

## 总体结论

整体上，当前架构命名已经明显优于普通研究型代码库，尤其是将 `experiments` 重命名为 `protocols` 这一点，非常符合工业化方向。

但从长期工业软件治理角度看，当前模块命名可分为三类：

### 第一类：命名成熟、边界清晰，建议保留

- `protocols`
- `execution`
- `analysis`
- `reporting`
- `suites`

### 第二类：方向正确，但需要进一步约束边界或优化内部结构

- `domain`
- `datastore`
- `schemas`
- `server`

### 第三类：命名过泛，未来容易演化成“杂物层”或语义不清模块

- `foundation`
- `intelligence`

因此，当前架构的整体方向是正确的，但仍需对部分命名进行收紧和治理，以符合工业级长期维护标准。

---

## 顶层模块逐项检查

---

## 1. `protocols`

### 评价

`protocols` 是当前整个架构中最清晰、最工业化的模块命名之一。

### 适合承载的内容

- 原子 protocol 定义
- 参数规范化
- 配置校验
- 线路/任务描述生成
- protocol metadata
- capability declaration
- analyzer binding hints

### 不应承载的内容

- 运行状态
- engine 调用
- 分析实现
- 绘图
- 报告生成
- 多步骤 workflow 编排

### 结论

> **`protocols` 命名非常合理，建议保留，并作为架构核心概念之一长期使用。**

---

## 2. `execution`

### 评价

`execution` 是标准工业分层术语，语义稳定，建议保留。

### 适合承载的内容

- execution request / run / job 抽象
- backend / engine adapter
- scheduling / submission
- execution plan
- raw result collection
- lifecycle state 管理

### 结论

> **`execution` 命名成熟、专业，适合长期扩展。**

---

## 3. `analysis`

### 评价

`analysis` 命名准确，边界清晰，是工业系统中非常标准的模块名。

### 适合承载的内容

- analyzers
- fitters
- estimators
- uncertainty / statistics
- result stitching
- post-processing
- interpretation logic

### 结论

> **`analysis` 建议保留。**

---

## 4. `reporting`

### 评价

`reporting` 比单纯的 `visualization` 更工业化，因为它可以覆盖更完整的输出能力。

### 适合承载的内容

- report builder
- summary formatter
- artifact generation
- dashboard export
- plot composition
- markdown / html / json 报告导出

### 结论

> **`reporting` 命名合理，建议保留。**

---

## 5. `suites`

### 评价

`suites` 是非常好的补充层，适合表达原子 protocol 的组合包、模板化套件和标准评估集合。

### 适合承载的内容

- predefined protocol bundles
- benchmark suites
- reusable assessment packages
- static campaign templates

### 与 `protocols` 的区别

- `protocols` 表示原子协议单元
- `suites` 表示组合型协议集合或模板

### 结论

> **`suites` 命名合理，建议保留。**

---

## 6. `domain`

### 评价

`domain` 顶层命名方向是对的，符合工业软件对“核心领域模型层”的命名习惯。

### 理想职责

- 核心业务实体
- 值对象
- 领域规则
- 领域服务
- 稳定的概念模型
- 不依赖外部基础设施的核心本体层

### 当前问题

从现有结构看，`domain/` 中包含：

```text
domain/
  error_analysis/
  error_inference/
  error_modeling/
  error_propagation/
  system/
```

这里存在两个潜在问题：

#### 问题 1：与 `analysis` 边界重叠

诸如：

- `error_analysis`
- `error_inference`
- `error_modeling`

这些名字天然带有方法、推断、计算过程意味，容易和 `analysis` 模块职责重叠。

如果这些目录中放的是：
- 拟合算法
- 估计器
- 推断流程

那么它们应属于 `analysis`，而不是 `domain`。

如果这些目录中放的是：
- error channel object
- noise source model
- propagation graph
- inferred error model representation

则可以保留在 `domain`，但最好重新命名为更“对象化”的子域名称。

#### 问题 2：`system` 命名过宽

`domain/system/` 下包含：

- `chip_topology.py`
- `cost_model.py`
- `event.py`
- `hardware_snapshot.py`
- `hardware_state.py`
- `types.py`
- `version.py`

这里的内容更像：

- hardware/platform domain
- topology model
- snapshot/state model
- versioned system representation

因此，`system` 这个名字过于宽泛，不利于工业化长期维护。

### 建议

保留 `domain/` 顶层，但对内部结构进行明确 bounded context 化，例如：

```text
domain/
  hardware/
  error/
  versioning/
```

例如：

- `system/` 可以考虑改为 `hardware/`
- `version.py` 可以考虑进入 `versioning/`
- `event.py` 需要区分是领域事件还是系统事件
- `cost_model.py` 需要根据其性质决定是 domain service 还是 planning/execution 逻辑

### 结论

> **`domain` 顶层命名合理，但内部子目录建议进一步工业化收敛。**

---

## 7. `datastore`

### 评价

`datastore` 可以用，但比工业软件中常见的命名略偏“实现层感”。

### 适合承载的内容

- persistence adapters
- repositories
- object stores
- metadata store
- result storage
- cache backends

### 优点

- 直观
- 不易和 `domain` 混淆

### 风险

如果未来这里要承载：
- lineage
- indexing
- query interface
- artifact management
- versioned storage

则 `datastore` 会显得语义偏窄。

### 替代候选

长期可考虑：

- `storage`
- `persistence`

### 结论

> **`datastore` 当前可保留，但如果未来数据层职责持续扩展，更推荐 `storage` 或 `persistence`。**

---

## 8. `schemas`

### 评价

`schemas` 是常见命名，但在工业项目里极容易演化成“所有数据类的收纳盒”，需要强约束。

### 常见承载内容

- request / response DTO
- API schema
- execution plan schema
- config schema
- serialization contract
- persisted manifest schema

### 风险

如果没有清晰规则，`schemas` 很容易和以下对象混用：

- domain model
- API DTO
- persistence schema
- event schema
- config schema

最终导致同一个概念在多个地方有多套表达。

### 建议边界

建议明确规定：

> `schemas` 只放“边界数据契约对象”，不放核心领域模型。

例如适合放入：

- API request/response schema
- execution request schema
- manifest schema
- serialized contract schema

不适合放入：

- 核心业务实体
- 领域对象
- 分析核心模型

### 结论

> **`schemas` 可保留，但必须严格限定其职责，否则极易成为垃圾桶模块。**

---

## 9. `server`

### 评价

`server` 可以使用，但它表达的是“部署/进程形态”，而不是“软件接口层”的职责语义。

### 适合承载的内容

如果这里主要放的是：

- FastAPI / Flask app
- routers
- endpoint wiring
- dependency injection
- API app startup

那它是可用的。

### 风险

随着系统扩展，可能还会增加：

- CLI
- gRPC
- batch interface
- notebook bridge
- webhooks

这时 `server` 作为统一接口层命名就显得偏窄。

### 更工业的候选名

长期更推荐：

- `api`
- `interfaces`
- `interfaces/http`

### 结论

> **`server` 当前可接受，但长期工业化更推荐使用 `api` 或 `interfaces`。**

---

## 10. `foundation`

### 评价

`foundation` 是一个危险但常见的命名。它的问题不在于错误，而在于过于宽泛，极易沦为“高级版 utils”。

### 常见风险

未来凡是“不知道放哪”的东西，都可能被塞进 `foundation`：

- helper
- constants
- common types
- exceptions
- base classes
- shared utilities

最终形成一个难以维护的杂物层。

### 如果必须保留，应限定为

- truly cross-cutting minimal abstractions
- shared exceptions
- low-level primitives
- non-domain-specific common interfaces

### 建议

优先策略是：

- 能拆则拆
- 能放回具体模块则不放 foundation
- 尽量避免 foundation 承担模糊职责

### 结论

> **`foundation` 不是不能用，但非常容易腐化，必须严控职责，必要时考虑逐步拆除。**

---

## 11. `intelligence`

### 评价

`intelligence` 是当前最不工业化的命名之一。

### 问题

它听起来很高级，但语义极宽，不同人可能理解为：

- AI / ML
- diagnostics
- recommendation
- heuristic engine
- strategy selection
- optimization
- inference engine
- adaptive control

也就是说，它几乎没有稳定边界。

### 风险

任何“看起来聪明”的功能，未来都可能被塞进这个目录，最终形成高度语义污染。

### 建议

应根据真实职责改成更具体的名字，例如：

- `diagnostics`
- `optimization`
- `planning`
- `recommendation`
- `inference`
- `strategies`
- `ml`

具体取决于模块实际承载内容。

### 结论

> **`intelligence` 不推荐作为工业级长期模块命名，建议优先改为更具体的业务语义名称。**

---

## 工业级命名评估总表

| 模块 | 当前评价 | 建议 |
|---|---|---|
| `protocols` | 很好 | 保留 |
| `execution` | 很好 | 保留 |
| `analysis` | 很好 | 保留 |
| `reporting` | 很好 | 保留 |
| `suites` | 很好 | 保留 |
| `domain` | 好，但内部需收敛 | 保留顶层，优化子结构 |
| `datastore` | 可用 | 长期可考虑 `storage` / `persistence` |
| `schemas` | 可用但高风险 | 明确只放 contract / DTO |
| `server` | 可用 | 长期建议改为 `api` / `interfaces` |
| `foundation` | 危险 | 严格限责，必要时拆除 |
| `intelligence` | 不推荐 | 优先改为更具体名称 |

---

## 推荐的工业化演化方向

从长期工业软件标准出发，推荐逐步演化到类似以下结构：

```text
egm/
  protocols/
  suites/
  execution/
  analysis/
  reporting/
  domain/
  storage/         # 或 persistence
  api/             # 替代 server
  contracts/       # 若 schemas 主要是边界 DTO
```

其中：

- `foundation/` 若保留，应严格限制为极少量跨模块基础抽象
- `intelligence/` 应改成更具体的名称
- `domain/` 内部建议按具体 bounded context 重组
- `schemas/` 若职责始终只是“边界契约”，也可改为 `contracts/`

---

## 最终结论

整体来看，当前 EGM 架构已经具备工业级软件演化的良好基础，尤其是将 `experiments` 收敛为 `protocols`，显著提升了系统概念边界的清晰度。

但要真正达到长期工业级标准，还应继续推进以下几点：

1. 保持 `protocols`、`execution`、`analysis`、`reporting`、`suites` 这些清晰边界模块的稳定性。
2. 对 `domain` 内部结构进行更明确的子域划分，尤其收紧 `system` 这一过宽命名。
3. 对 `schemas` 设立严格边界，避免成为“所有数据结构收纳盒”。
4. 重新审视 `server`、`datastore` 的长期命名，视系统扩展方向考虑演进为 `api` / `interfaces` 与 `storage` / `persistence`。
5. 严格治理 `foundation`，避免其演化为杂物层。
6. 优先重命名 `intelligence`，因为这是当前最不稳定、最不利于工业级长期维护的顶层模块命名。

### 一句话总结

> **当前架构整体方向正确，已具备工业化基础；真正需要重点治理的不是 `protocols` 这类清晰模块，而是 `foundation`、`intelligence`、`schemas`、以及 `domain` 内部过宽命名所带来的边界漂移风险。**
```