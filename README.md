# Learning-Agent｜文科实验室

面向理科思维型高中生的 AI 学习 Agent。

文科实验室把英语等非结构化知识转化为可拆解、可推导、可验证、可积累的逻辑系统，并围绕“学习 → 作答 → 归因 → 扰动 → 验证 → 状态更新 → 下一任务”形成学习闭环。

## 当前范围

- MVP：高一英语，必修一 Unit 4 `Natural Disasters`
- 产品形态：移动端 H5 + Learning Agent
- 前端：Vue 3 + Vite + TypeScript + Pinia + ECharts + GSAP
- 后端：FastAPI + Pydantic v2 + SQLAlchemy/SQLModel + SQLite
- Agent：SimpleAgentRuntime + 显式状态机 + Tool Registry + Reason Code
- 数据底座：Content Pack + Learning Events + User Node State

## 母文档

- [产品 PRD V2.2](docs/PRD.md)
- [DEMO 开发工程文档 V2.2](docs/DEMO_ENGINEERING.md)

## P0 开发顺序

```text
P0-0 数据契约
↓
P0-1 Unit 4 Content Pack
↓
P0-2 Deterministic Tools
↓
P0-3 Validation / Grade Scope Guard / Provider
↓
P0-4 Learning Events / State
↓
P0-5 SimpleAgentRuntime
↓
P0-6 H5 接线
↓
P0-7 GOAI 固定闭环
```

## P0 依赖门禁

当前不引入：LangGraph、pyKT Runtime、FSRS Optimizer、LlamaIndex、Chroma、Qdrant、Neo4j、Redis、Kafka、Celery、Kubernetes、多 Agent、全教材 RAG、OCR、教师后台。

只有出现明确、可复现的阻塞问题并通过技术评审后才解禁。

## 核心 DEMO 链路

```text
eruption
→ relative clause
→ pointer_error
→ 分层提示
→ 错一订三
→ PATCHED
→ topology update
→ next_task
```

## 工程原则

1. Data Contract 先于页面和 Agent。
2. Content Pack 先于 RAG。
3. Deterministic Tool 先于自由 Prompt。
4. Learning Events 先于 Knowledge Tracing 算法。
5. SimpleAgentRuntime 先于 LangGraph。
6. 所有生成内容经过 Schema、业务规则和 Grade Scope Guard。
7. 所有 LIVE 能力都必须提供 MOCK / FALLBACK。
8. 每次提交保持可运行、可验证、可回退。
