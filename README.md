# Learning-Agent｜文科实验室

面向理科思维型高中生的 AI 学习 Agent / 学习调试系统。

核心问题：**学生为什么做错，系统能否定位推理链中断的位置，用最少信息帮助他自己修复，再用新题证明修复成立。**

## 当前产品形态｜完整框架 + MVP 真实内容

文科实验室现在采用两层结构：

```text
Product Shell
完整产品导航 / 页面 / 功能地图
        │
        ▼
Learning Runtime
当前真实 MVP 学习闭环
```

完整产品框架已经恢复：

```text
首页 Dashboard
今日学习 Today
学习实验室 Lab
 ├─ 逻辑解码
 │  ├─ MECE 结构骨架
 │  ├─ 词根逻辑拆解
 │  └─ 长难句公式翻译
 ├─ 因果推演
 │  ├─ 5 Whys
 │  ├─ 指令流转
 │  └─ 物理还原
 └─ 逻辑修复
    ├─ 错题归因
    ├─ 错一订三
    └─ 逻辑解谜
知识拓扑 Topology
学习资产 Assets
我的 Profile
```

能力统一使用：

```text
LIVE      真实可用
LIMITED   部分内容可用
PREVIEW   产品入口存在，内容未开放
LOCKED    等待前置节点或后续内容
```

**当前只有高一英语必修一 Unit 4 的 MVP 内容可以真实改变学习状态。**

```text
relative_clause.pointer
→ POINTER_ERROR
→ 最小提示
→ 3 道迁移验证
→ VERIFIED
→ word.root.rupt
→ VERIFIED
→ DONE / CLOSED LOOP
```

PREVIEW / LOCKED 页面不会生成假题目、假成绩或假 Learning Events。

## 第一性原理学习闭环

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

LLM 不负责标准答案、错误类型和长期学习状态正确性。AI OFF 时当前 Gold Loop 仍完整运行。

## 当前工程架构

```text
Product Shell
apps/web/product-manifest.json
        │
        ▼
H5
        │
        ▼
FastAPI HTTP Boundary
        │
        ▼
LearningController (pure reducer)
        │
        ▼
Transactional SQLite Store
 ├─ sessions
 ├─ learning_events
 ├─ command_receipts
 └─ rate_limits
```

核心约束：

- Product Manifest 是完整产品能力母表；
- Product Shell 不建立第二套学习状态机；
- `LearningController` 只计算状态迁移，不写数据库；
- Command + Events + Session State + Response Receipt 单 SQLite 事务提交；
- `expected_version` + SQLite `BEGIN IMMEDIATE` 处理并发冲突；
- 相同 `command_id` 重试返回原始 Receipt，不重复推进；
- Event Replay 可验证 Session Snapshot 完整性；
- Session Token 数据库只保存 SHA-256 哈希；
- Session 有 TTL、清理、容量与 SQLite 共享 Rate Limit；
- `/api/v1/live` 与 `/api/v1/ready` 分离；
- Preview 页面不能调用 `learning/step`。

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

静态门禁同时验证完整产品能力没有因 MVP 收缩再次被删除。

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

- [PRD V3.0｜完整产品框架版](docs/PRD.md)
- [Product Shell 工程文档](docs/PRODUCT_SHELL.md)
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
