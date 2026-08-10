# Learning-Agent｜文科实验室

面向理科思维型高中生的 AI 学习 Agent / 学习调试系统。

核心问题：**学生为什么做错，系统能否定位推理链中断的位置，用最少信息帮助他自己修复，再用新题证明修复成立。**

## 当前状态｜v0.2.0-hardening baseline

当前 `main` 已完成 P0 学习闭环与 P1 状态/运行治理加固。

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

Gold Demo：

```text
TASK
→ wrong: trapped
→ POINTER_ERROR
→ minimum hint
→ correct: ruins
→ pointer-v1 / v2 / v3 PASS
→ relative_clause.pointer VERIFIED
→ eruption
→ rupt VERIFIED
→ DONE / CLOSED_LOOP
```

## 当前工程架构

```text
H5
 ↓
FastAPI HTTP Boundary
 ↓
LearningController (pure reducer)
 ↓
Transactional SQLite Store
 ├─ sessions
 ├─ learning_events
 ├─ command_receipts
 └─ rate_limits
```

核心约束：

- `LearningController` 只计算状态迁移，不写数据库；
- Command + Events + Session State + Response Receipt 单 SQLite 事务提交；
- `expected_version` + SQLite `BEGIN IMMEDIATE` 处理并发冲突；
- 相同 `command_id` 重试返回原始 Receipt，不重复推进；
- Event Replay 可验证 Session Snapshot 完整性；
- Session Token 只返回客户端一次，数据库只保存 SHA-256 哈希；
- Session 有 TTL、清理与最大容量治理；
- Rate Limit 使用 SQLite，共享于多个 Store/进程；
- `/api/v1/live` 用于存活探针；`/api/v1/ready` 验证数据库 Schema 与 Content Pack；
- P0/P1 仍保持 AI OFF 可完整运行。

## 验证基线

当前代码基线：

```text
15edeab92a495300a31d6475f865ed9ea5c0f5e0
```

主分支 GitHub Actions：

```text
Run 31429090745
Test Job    SUCCESS
Docker Job  SUCCESS
```

门禁包含：

```text
pip check
compileall
pytest 16 tests
Authenticated closed-loop smoke
Static H5 contract
Session cleanup dry-run
JS syntax
Docker build
Docker /ready
Docker /live
Docker H5
Docker Session Token start
Docker cleanup dry-run
```

## 本地运行

```bash
pip install -r requirements.txt
uvicorn apps.api.app:app --host 0.0.0.0 --port 8000
```

打开：`http://127.0.0.1:8000`

## 本地验证

```bash
pytest -q
python scripts/smoke.py
python scripts/check_static.py
python scripts/cleanup_sessions.py --dry-run --max-sessions 100
node --check apps/web/app.js
```

## 生产配置

生产模式至少设置：

```bash
APP_ENV=production
TRUSTED_HOSTS=your-domain.example.com
LEARNING_DB_PATH=/data/learning-agent.db
```

可调参数：

```text
SESSION_TTL_SECONDS
MAX_BODY_BYTES
RATE_WINDOW_SECONDS
START_RATE_LIMIT
STEP_RATE_LIMIT
```

生产环境禁止 `TRUSTED_HOSTS=*`。

## 文档

- [PRD](docs/PRD.md)
- [第一性原理决策](docs/FIRST_PRINCIPLES.md)
- [工程母文档](docs/DEMO_ENGINEERING.md)
- [开发执行计划](docs/DEVELOPMENT_PLAN.md)
- [对抗式审查](docs/ADVERSARIAL_REVIEW_2026-08-11.md)
- [建设性 / 传统审查](docs/CONSTRUCTIVE_REVIEW_2026-08-11.md)
- [运行证据](docs/RUN_EVIDENCE.md)

## 依赖门禁

当前不引入 LangGraph、pyKT Runtime、FSRS Optimizer、LlamaIndex、Chroma、Qdrant、Neo4j、Redis、Kafka、Celery、Kubernetes、多 Agent、全教材 RAG、OCR、教师后台。

## 当前外部阻塞

公网 Deployment 仍缺真实成功回执。当前已连接的 Vercel 上下文没有可用 Team / Project，因此代码、CI、Docker 可部署性均已验证，但不把公网部署标记为完成。

反向代理部署时还必须明确真实客户端 IP / trusted proxy 策略；应用不会自行信任任意 `X-Forwarded-For`。
