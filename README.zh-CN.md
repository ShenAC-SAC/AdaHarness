# AdaHarness

语言：[English](README.md) | [简体中文](README.zh-CN.md)

AdaHarness 是一个给 agent 开发者使用的轻量 trace 分析工具。它帮助你在更换底层
LLM、prompt、工具或任务分布之后，重新判断 harness 层是否还合适。

核心问题是：

> 这次变化之后，原有的 planning、verification、retry、tool control 是否太重、
> 太弱，还是仍然合适？

AdaHarness 不运行你的 agent，不包装你的工具，不管理模型凭证，也不控制你的
runtime。你照常运行自己的 eval，导出 JSONL trace，然后用 AdaHarness 分析证据。

## MVP 流程

```text
exported traces -> validation -> metrics -> diagnosis -> policy diff -> report
```

AdaHarness 输出：

- trace 质量警告
- verifier catch rate、retry success rate、verifier cost share、planner latency
  share、tool failure rate 等 harness 指标
- overconstraint / underconstraint 诊断
- 带证据的 policy diff 建议
- Markdown 报告和结构化 JSON sidecar

## 安装

本地开发：

```bash
uv sync --group dev
uv run adaharness --help
```

从 GitHub 安装：

```bash
uv tool install git+https://github.com/ShenAC-SAC/AdaHarness.git
```

## 快速开始

在源码 checkout 中运行内置 trace 示例：

```bash
uv run adaharness analyze \
  --traces examples/traces/overconstrained_harness.jsonl \
  --current-policy examples/policies/heavy_policy.json \
  --diagnostics-config examples/diagnostics/default.toml \
  --out runs/harness-drift.md
```

输出文件：

```text
runs/harness-drift.md
runs/harness-drift.analysis.json
runs/harness-drift.metrics.json
runs/harness-drift.diagnosis.json
runs/harness-drift.policy-diff.json
```

## Trace 格式

trace 协议刻意保持很小。JSONL 每一行是一条事件，必需字段只有 `task_id` 和
`event`。

```json
{"task_id":"t1","event":"planner","latency_ms":320}
{"task_id":"t1","event":"verifier","status":"pass","cost":0.002}
{"task_id":"t1","event":"retry","reason":"tool_failure"}
{"task_id":"t1","event":"final","success":true,"cost":0.012,"latency_ms":2200}
```

常用可选字段包括 `status`、`success`、`cost`、`latency_ms`、`tokens`、
`model`、`policy`、`control` 和 `reason`。

推荐事件名：

- `planner`
- `verifier`
- `retry`
- `tool_call`
- `tool_result_ignored`
- `model_call`
- `context`
- `subagent`
- `final`

未知事件会变成 validation warning，而不是直接失败。这样宿主项目可以先从少量
事件开始，再逐步丰富 trace。

## 集成方式

推荐三种轻量方式：

- 在你的项目中直接写 AdaHarness 兼容 JSONL。
- 使用可选的 `TraceRecorder`。
- 把现有日志或 observability export 转成 AdaHarness JSONL，再运行 `analyze`。

使用 recorder：

```python
from adaharness.trace import TraceRecorder

trace = TraceRecorder("traces/run.jsonl", model="gpt-example", policy="current")
task = trace.task("support_001")

task.planner(latency_ms=320)
task.tool_call(tool="search_docs", status="success", latency_ms=180)
task.verifier(status="pass", cost=0.002)
task.final(success=True, cost=0.012, latency_ms=2200)
```

计时一个代码块：

```python
with task.timed("tool_call", tool="search_docs"):
    search_docs(query)
```

这个 context manager 只记录延迟和失败状态，然后重新抛出原异常。它不会修改宿主
runtime。

## Policy Diff

`--current-policy` 是可选的。传入时，它应该是一个简单 JSON 对象：

```json
{
  "planning_control": "explicit",
  "verification_control": "always",
  "retry_control": "bounded",
  "tool_control": "moderate"
}
```

AdaHarness 可能给出这样的建议：

```json
{
  "field": "verification_control",
  "from": "always",
  "to": "selective",
  "reason": "Verifier appears expensive but rarely catches failures.",
  "evidence": ["verifier_catch_rate=0.00", "verifier_cost_share=0.25"],
  "confidence": "medium",
  "evidence_count": 20
}
```

这些建议只用于辅助判断。AdaHarness 不会自动修改你的项目。

## Python API

```python
from adaharness import analyze_traces

result = analyze_traces(
    ["traces/run.jsonl"],
    current_policy={"verification_control": "always"},
)

print(result["report"])
print(result["policy_diff"])
```

## 项目边界

AdaHarness 不是 LangChain、LangGraph、OpenAI Agents SDK 或其他 agent runtime 的
替代品。它不是模型 provider wrapper，不是 policy compiler，不是 reference
harness，也不是 project adapter system。

当前维护的 MVP 表面是：

- `adaharness/analysis/`
- `adaharness/trace/`
- `adaharness/api.py`
- `adaharness/cli.py`

## 开发

```bash
uv sync --group dev
uv run pytest -q
uv run ruff check .
uv run python -m compileall adaharness tests
```
