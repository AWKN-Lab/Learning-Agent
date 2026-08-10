# Learning-Agent｜文科实验室

面向理科思维型高中生的 AI 学习 Agent / 学习调试系统。

文科实验室关注一个核心问题：**学生为什么做错，系统能否定位推理链中断的位置，用最小信息帮助他自己修复，再用新题证明修复成立。**

## 核心闭环

```text
Observe
↓
Diagnose
↓
Intervene
↓
Verify
↓
Update
```

工程主干：

```text
Task Model
+
Evaluator
+
Intervention Policy
+
Transfer Verification
+
Learning State
```

LLM 作为增强层，不作为正确性主干。

## 当前范围

- MVP：高一英语，必修一 Unit 4
- Gold Node：`relative_clause.pointer`
- 第二能力：`eruption → e + rupt + ion`
- 产品形态：移动端 H5 + Learning Agent
- 前端：Vue 3 + Vite + TypeScript + Pinia + ECharts
- 后端：FastAPI + Pydantic v2 + SQLAlchemy 2.x + SQLite
- 主控：LearningController
- 数据事实层：Learning Events

## 母文档

- [PRD V2.3 第一性原理版](docs/PRD.md)
- [DEMO 工程母文档 V2.3](docs/DEMO_ENGINEERING.md)
- [第一性原理重构决策](docs/FIRST_PRINCIPLES.md)
- [详细开发执行计划](docs/DEVELOPMENT_PLAN.md)

## P0 开发路线

```text
P0-0 Outcome Contract
↓
P0-1 Gold Learning Loop（AI OFF）
↓
P0-2 Interaction Model
↓
P0-3 Evidence Model
↓
P0-4 Persistence + Learning State
↓
P0-5 LearningController
↓
P0-6 H5 Vertical Slice
↓
P0-7 AI Enhancement
↓
P0-8 Word Logic Loop
↓
P0-9 Topology Projection
↓
P0-10 E2E / Reliability
↓
P0-11 CI
↓
P0-12 Release
↓
P0-13 Deploy
↓
P0-14 Git
↓
P0-15 Rollback
```

## Gold Demo

```text
The ruins in which they were trapped were dangerous.
↓
学生错误连接 which
↓
POINTER_ERROR
↓
最小提示
↓
重试
↓
3 道迁移题
↓
VERIFIED
↓
Learning State 更新
↓
Next Task
```

## AI 边界

P0 要求 AI OFF 时 Gold Loop 仍可成立。

LLM 只用于：

- Explanation；
- Variant Candidate；
- Ambiguous Diagnosis。

LLM 不决定标准答案，不绕过验证层写入长期学习状态。

## P0 依赖门禁

默认不引入：LangGraph、pyKT Runtime、FSRS Optimizer、LlamaIndex、Chroma、Qdrant、Neo4j、Redis、Kafka、Celery、Kubernetes、多 Agent、全教材 RAG、OCR、账号系统、教师后台。

只有出现明确、可复现、阻塞当前 Gold Loop 的问题，并有测试与回退方案时才解禁。

## 工程原则

1. Outcome Contract 先于大规模 Schema。
2. 无 AI Gold Loop 先于 LLM 集成。
3. 交互必须暴露学生思维。
4. 确定性 Evaluator 决定学习正确性。
5. 最小干预先于完整解释。
6. 修复必须经过迁移验证。
7. Learning Events 是事实源；Learning State 和 Topology 是派生结果。
8. 每次提交保持可运行、可验证、可回退。
9. 发布链必须走完 CI → Release → Deploy → Git → Rollback。
