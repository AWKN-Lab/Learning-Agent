# Learning-Agent｜文科实验室

面向理科思维型高中生的 AI 学习 Agent / 学习调试系统。

核心问题：**学生为什么做错，系统能否定位推理链中断的位置，用最小信息帮助他自己修复，再用新题证明修复成立。**

## 当前状态

`v0.1.0-demo` 的 P0 Gold Loop 已实现并完成真实运行验证：

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

当前统一门禁回执：

```text
pytest                     3 passed
static H5 contract         STATIC_H5_OK
node --check app.js        PASS
smoke closed loop          DONE
learning events            19
```

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
- 部署形态：FastAPI 同时托管 API 与静态 H5；
- 容器：Python 3.12 Dockerfile。

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
- [工程母文档 V2.4](docs/DEMO_ENGINEERING.md)
- [详细开发计划](docs/DEVELOPMENT_PLAN.md)
- [运行证据](docs/RUN_EVIDENCE.md)

## P0 依赖门禁

默认不引入 LangGraph、pyKT Runtime、FSRS Optimizer、LlamaIndex、Chroma、Qdrant、Neo4j、Redis、Kafka、Celery、Kubernetes、多 Agent、全教材 RAG、OCR、账号系统、教师后台。

## 当前外部基础设施状态

代码闭环已经实测完成。远端基础设施仍有两个环境限制：

1. 当前 GitHub 集成无法读取 Actions 权限，Actions API 返回 `403 Resource not accessible by integration`，仓库未产生远端 Workflow Run；
2. 当前 Vercel 连接没有 Team/Project 上下文，部署工具契约也缺少可用的项目创建入口。

因此：**代码运行闭环已完成；远端 CI/公网 Deploy 尚未取得真实成功回执，不标记为通过。**
