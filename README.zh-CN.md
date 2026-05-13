# AdaHarness

语言：[English](README.md) | [简体中文](README.zh-CN.md)

面向 LLM agent 项目的 harness drift analyzer 与 calibration advisor。

AdaHarness 读取 agent traces 和 eval results，判断当前 harness 对模型是控制过强、控制不足，还是基本合适，并输出有证据支撑的 policy 调整建议。

当模型、工具、prompt 或任务分布发生变化时，合适的 harness 控制强度也可能变化。AdaHarness 优先回答一个工程问题：

> 这次变化之后，我们现有的 harness 是太重、太弱，还是仍然合适？

## 研究问题

很多 agent 系统在更换模型、prompt、工具或任务后，仍然沿用同一套 planning、verification、retry 和 tool-control 逻辑。AdaHarness 的出发点是：

> agent 系统变化后，harness controls 也可能需要重新校准。

较弱模型可能需要更严格的控制。较强模型可能会被旧的强控制拖慢，而这些控制不再明显提升成功率。AdaHarness 先从真实 traces 中暴露这种 drift，而不是一开始就试图接管用户 runtime。

## 核心思路

- 从现有 agent 项目读取 traces
- 计算 verifier catch rate、retry success rate、cost share、latency overhead 等 harness metrics
- 诊断 overconstraint 和 underconstraint
- 基于 trace evidence 输出 suggested policy diff
- 支持后续 model migration 和 harness drift report
- 为用户项目提供轻量 TraceRecorder SDK

## 当前状态

早期实验性 MVP。

当前代码库仍保留早期 policy compiler、adapter 和 reference runtime 基础代码，但它们已经被降级为 experimental code。当前 MVP 被收敛为更轻的流程：

```text
traces -> metrics -> diagnosis -> suggested policy diff -> report
```

## 安装

从 GitHub `main` 安装当前开发版：

```bash
uv tool install git+https://github.com/ShenAC-SAC/AdaHarness.git
# 或者在源码目录中：
uv run adaharness --help
```

等发布 tagged PyPI release 后，可以使用：

```bash
uv tool install adaharness
# 或：pipx install adaharness
```

本地开发：

```bash
uv sync --group dev
```

安装后，可以创建起步文件：

```bash
adaharness init
```

如果你是在源码目录中开发，命令前加 `uv run`：

```bash
uv run adaharness init
uv run adaharness capture --help
```

这会生成 `.adaharness/diagnostics/default.toml`、`.adaharness/policies/current-policy.json`、内置 workload suites、示例 traces 和 reports 目录。真实数据应该用 `capture` 调你的单任务 agent 入口生成：

```bash
adaharness capture \
  --out .adaharness/traces/run.jsonl \
  --analyze-out .adaharness/reports/harness-drift.md \
  --current-policy .adaharness/policies/current-policy.json \
  --diagnostics-config .adaharness/diagnostics/default.toml \
  -- python your_agent.py --prompt "{prompt}"
```

仍然可以运行内置 trace demo：

```bash
adaharness analyze \
  --traces .adaharness/traces/overconstrained_harness.jsonl \
  --current-policy .adaharness/policies/current-policy.json \
  --diagnostics-config .adaharness/diagnostics/default.toml \
  --out .adaharness/reports/harness-drift.md
```

## MVP 用法

当前推荐的 MVP 流程是 trace-first，但 AdaHarness 应该帮助用户生成 traces。它不假设用户项目里已经有一个叫 `agent eval` 的指令，也不要求用户先准备测试集。`capture` 自带 workload suites，可以逐条调用一个普通的单任务 agent 入口，做确定性判断，并写出 AdaHarness traces。

内置 suites：

- `connectivity-smoke`：只做接入链路自检，确认命令能跑通。
- `ifeval-lite`：受 IFEval 式可验证指令约束启发的 instruction-following workload，但不是官方 IFEval 数据集。

内置测试集本质上就是下面这种 JSONL，后续可以替换：

```json
{"task_id":"t1","prompt":"Answer with OK.","expected_contains":"OK"}
```

采集命令：

```bash
adaharness capture \
  --out .adaharness/traces/run.jsonl \
  -- python your_agent.py --prompt "{prompt}"
```

可以用 `--list-suites` 查看内置测试集。接入自检用 `--suite connectivity-smoke`；只有当你要替换成业务任务时，才需要传 `--tasks my-tasks.jsonl`。

如果你的 agent 输出带 `ADAHARNESS_EVENT ` 前缀的行，`capture` 会把它们记录成更详细的 harness events：

```text
ADAHARNESS_EVENT {"event":"tool_call","tool":"search_docs","status":"success","latency_ms":180}
```

内置 demo trace 可以这样跑：

```bash
uv run adaharness analyze \
  --traces examples/traces/overconstrained_harness.jsonl \
  --current-policy examples/policies/heavy_policy.json \
  --diagnostics-config examples/diagnostics/default.toml \
  --out runs/harness-drift.md
```

trace event 可以从很小的格式开始：

```json
{"task_id":"t1","event":"planner","latency_ms":320}
{"task_id":"t1","event":"verifier","status":"pass","cost":0.002}
{"task_id":"t1","event":"retry","reason":"tool_failure"}
{"task_id":"t1","event":"final","success":true,"cost":0.012,"latency_ms":2200}
```

AdaHarness 会生成报告，解释哪些 controls 有用、浪费，或缺失。只有把内置 demo trace 换成你自己 agent 运行产生的 events 后，这份报告才对你的项目有决策价值。

diagnostic rules 是可配置 heuristics，不是 benchmark truth。报告会展示规则阈值、观测值、evidence count、confidence 和 trace quality warnings，让建议可审计。

内置示例应当会标记 likely overconstraint：verifier 很少捕获问题却增加成本，explicit planning 占据较大 latency share。

## 用户项目如何接入

AdaHarness 不连接你的工具，也不执行你的 runtime。它只需要你的 agent 项目把已有运行过程导出成 trace events。

接入方式可以有三种：

- 在项目中直接写 JSONL events。
- 使用 `TraceRecorder` 写出同样的 JSONL 格式。
- 把已有日志或 observability exports 转成 AdaHarness trace events。

例如，用户项目里的一次 tool call 可以记录为：

```json
{"task_id":"t1","event":"tool_call","tool":"search_docs","status":"success","latency_ms":180}
```

AdaHarness 会分析这条 event，但不会运行 `search_docs`。

使用 recorder：

```python
from adaharness.trace import TraceRecorder

trace = TraceRecorder(".adaharness/traces/run.jsonl", model="gpt-example", policy="current")
task = trace.task("support_001")

task.planner(latency_ms=320)
task.tool_call(tool="search_docs", status="success", latency_ms=180)
task.verifier(status="pass", cost=0.002)
task.final(success=True, cost=0.012, latency_ms=2200)
```

如果只想记录某段代码的耗时：

```python
with task.timed("tool_call", tool="search_docs"):
    search_docs(query)
```

这个 context manager 只记录 latency 和失败状态，然后继续抛出被包裹代码中的异常。

当前示例 traces：

```text
examples/traces/overconstrained_harness.jsonl
examples/traces/undercontrolled_tool_use.jsonl
examples/traces/balanced_harness.jsonl
examples/traces/migration_old_model.jsonl
examples/traces/migration_new_model.jsonl
```

## 项目内 CLI

CLI 不是 production agent runner。它是分析工具和 CI 工具，用于处理用户现有 agent 项目导出的 traces。provider credentials 通常应该留在用户自己的项目中。

使用 `--out` 时，`analyze` 会写出 Markdown report 和结构化 sidecars：

```text
runs/harness-drift.md
runs/harness-drift.analysis.json
runs/harness-drift.metrics.json
runs/harness-drift.diagnosis.json
runs/harness-drift.policy-diff.json
```

旧命令如 `profile`、`compare`、`recommend`、`assemble`、`calibrate` 和 reference `run` 仍然可用于实验和 smoke tests，但它们不是当前 MVP 主路径。

当前边界和 release checklist 见 `docs/metrics.md`、`docs/architecture.md`、`docs/roadmap.md`、`docs/use-cases.md`、`docs/experimental.md` 和 `docs/release.md`。

## 为什么需要 AdaHarness

agent 表现不只取决于 base model，也受周围 harness 影响：planning、tools、memory、retries、verification、context management 和 runtime policy 都会改变系统行为。

AdaHarness 把 harness control strength 视为需要从真实 runtime evidence 中诊断的对象，而不是只从抽象模型分数中推断。

## AdaHarness 不是什么

AdaHarness 不是 LangChain、LangGraph、OpenAI Agents SDK 或其他 agent runtimes 的替代品。MVP 不要求用户交出 runtime control。runtime binding 和 adapter-based control 都是 experimental。

## MVP 范围

Version 0.1 聚焦 trace analysis：

- ingest JSONL traces
- 通过可选 `TraceRecorder` 记录 JSONL traces
- compute harness metrics
- flag overconstraint and underconstraint signals
- recommend policy diffs
- render a Markdown report

policy compilers、runtime bindings、project adapters 和 reference runtime 会作为 experimental scaffolding 保留，直到 trace-first MVP 证明自身价值。
