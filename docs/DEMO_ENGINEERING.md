# 文科实验室 H5 DEMO 开发工程文档｜V2.2

## 工程目标

以最小依赖跑通真实 Agent 学习闭环：

```text
Content Pack
+
Learning Events
+
Deterministic Tools
+
Stateful Learning Agent
```

## 系统架构

```text
H5
 ↓
FastAPI
 ↓
SimpleAgentRuntime
 ↓
Tool Registry
 ↓
Validation Layer
 ↓
Provider Adapter
 ↓
SQLite + Content Pack
```

## Agent Runtime

P0：

- Planner
- State Machine
- Pedagogy Policy
- Grade Scope Guard
- Tool Registry
- Reason Code

不引入 LangGraph 作为 P0 依赖。

## 数据基座

核心数据：

- LearningEvent
- AgentState
- AgentTask
- ToolResult
- ErrorDiagnosis
- TopologyNodeState

## Content Pack

```text
content/
└─ v1.0_g10_english_u4/
   ├─ roots.json
   ├─ grammar.json
   ├─ sentences.json
   ├─ variants.json
   └─ topology.json
```

## P0 Tool

```text
decode_word
parse_sentence
evaluate_answer
diagnose_error
generate_variants
update_topology
recommend_next
```

## Demo 固定链路

```text
eruption
→ relative clause
→ pointer_error
→ 分层提示
→ 3 variants
→ PATCHED
→ topology update
→ next_task
```

## 工程门禁

- Schema 校验
- Grade Scope Guard
- LIVE / MOCK / FALLBACK
- Learning Events Trace
- 可回退运行

## P0 禁止依赖

LangGraph、pyKT Runtime、FSRS Optimizer、RAG、Neo4j、Redis、Qdrant、Chroma 等暂不进入 MVP。
