# Learning-Agent｜文科实验室

面向理科思维型高中生的 AI 学习 Agent / 学习调试系统。

核心问题：**学生为什么做错，系统能否定位推理链中断的位置，用最少信息帮助他自己修复，再用新题证明修复成立。**

## v0.1.0-demo 状态

P0 Gold Loop 已完成开发，并通过本地与 GitHub Runner 双重验证：

```text
TASK
→ 学生错误选择 trapped
→ POINTER_ERROR
→ 最小提示
→ 学生修正 ruins
→ 3 道迁移题全部通过
→ relative_clause.pointer = VERIFIED
→ eruption 词根任务
→ rupt = VERIFIED
→ DONE / CLOSED_LOOP
```

### 验证结果

```text
Local pytest                 3 passed
Local static H5 contract     STATIC_H5_OK
Local node --check           PASS
Local smoke                  CLOSED_LOOP / 19 events
GitHub Actions test job      SUCCESS
GitHub Actions Docker build  SUCCESS
```

主分支验证 Run：`31412516711`。

## 第一性原理架构

```text
Task Model
↓
Observe Student Action
↓
Evaluator
↓
Intervention Policy
↓
Transfer Verification
↓
Learning Events
↓
Learning State
↓
Next Task
```

LLM 不在正确性主干中。P0 即使 AI OFF，Gold Loop 仍完整成立。

## P0 技术基线

- H5：HTML + ES Module JavaScript + CSS，零 npm 运行依赖；
- API：FastAPI + Pydantic；
- 状态：SQLite；
- 主控：Deterministic `LearningController`；
- 事实源：`learning_events`；
- 服务：FastAPI 同时托管 API 与静态 H5；
- 容器：Python 3.12 Dockerfile；
- CI：pytest → smoke → static contract → JS syntax → Docker build。

前端零依赖决策见 [`docs/ADR-001-P0-ZERO-DEPENDENCY-H5.md`](docs/ADR-001-P0-ZERO-DEPENDENCY-H5.md)。

## 本地运行

```bash
pip install -r requirements.txt
uvicorn apps.api.app:app --host 0.0.0.0 --port 8000
```

打开：`http://127.0.0.1:8000`

## 验证

```bash
pytest -q
python scripts/check_static.py
node --check apps/web/app.js
python scripts/smoke.py
```

## 文档

- [PRD](docs/PRD.md)
- [第一性原理决策](docs/FIRST_PRINCIPLES.md)
- [工程母文档 V2.5](docs/DEMO_ENGINEERING.md)
- [详细开发计划](docs/DEVELOPMENT_PLAN.md)
- [运行证据](docs/RUN_EVIDENCE.md)

## P0 依赖门禁

默认不引入 LangGraph、pyKT Runtime、FSRS Optimizer、LlamaIndex、Chroma、Qdrant、Neo4j、Redis、Kafka、Celery、Kubernetes、多 Agent、全教材 RAG、OCR、账号系统、教师后台。

## 当前唯一外部基础设施缺口

**公网 Deployment 尚未取得真实成功回执。** 当前 Vercel 连接没有 Team/Project 上下文，且部署工具暴露的 Schema 与运行时参数要求不一致。

该缺口不影响当前 DEMO 的代码闭环、CI 及 Docker 可部署性；在取得可用部署目标前，不伪造公网部署状态。
