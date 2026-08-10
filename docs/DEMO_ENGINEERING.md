# 文科实验室 H5 DEMO 工程母文档｜V2.4 实际实现版

> 状态：P0 Gold Loop 已实现并实测  
> 目标版本：`v0.1.0-demo`  
> 更新：2026-08-11  
> 核心原则：先证明学习修复闭环，再扩 AI、框架和内容规模。

---

# 1. 系统层

## 1.1 系统目标

文科实验室当前只证明一件事：

> 系统可以观察学生操作，定位一个明确的逻辑错误，用最小提示让学生自己修正，再通过表层不同的新题证明修复成立，并把证据写入学习状态。

P0 Gold Node：

```text
relative_clause.pointer
```

第二能力：

```text
eruption → e + rupt + ion
```

## 1.2 完成判定

```text
TASK
↓
错误行为
↓
POINTER_ERROR
↓
最小提示
↓
主任务修正
↓
3/3 Transfer Verification
↓
relative_clause.pointer VERIFIED
↓
Word Logic Task
↓
word.root.rupt VERIFIED
↓
DONE
```

只有 `DONE` 且 Learning Events 包含 `error_diagnosed / patch_completed / word_verified / demo_completed`，才算 DEMO 闭环。

## 1.3 系统架构

```text
Browser H5
    │
    ▼
FastAPI
    │
    ▼
LearningController
 ┌──┼──────────────────────┐
 ▼  ▼                      ▼
Task Model             Evaluator
                         │
                         ▼
                Intervention Policy
                         │
                         ▼
                Transfer Verification
                         │
                         ▼
                    SQLite Store
                  ┌──────┴──────┐
                  ▼             ▼
             Sessions     Learning Events
                                  │
                                  ▼
                           Learning State
```

LLM 当前不参与正确性判断。

---

# 2. 组件层

## 2.1 Content / Task Model

目录：

```text
content/
├─ gold_relative_clause_pointer.json
└─ word_eruption.json
```

Gold Content 固定：

- 主任务 1 道；
- `POINTER_ERROR` 1 个目标错误；
- 分层提示 5 级；
- Transfer Variant 3 道；
- 成功条件 `3/3`；
- 第二能力 `word.root.rupt`。

正确答案和迁移标准全部由 Content 定义，不依赖 LLM 自由生成。

## 2.2 Evaluator

主任务：

```text
expected = ruins
actual != ruins
→ POINTER_ERROR
```

迁移题分别验证：

```text
house
city
room
```

任何迁移题失败都停留在当前 Variant，不允许跳过。

## 2.3 Intervention Policy

主任务每失败一次只提升一级提示：

```text
P1 错误位置
P2 结构线索
P3 回指关系
P4 先行词定义
P5 完整结构
```

第一次错误不直接给完整答案。

## 2.4 Transfer Verification

成功标准：

```text
pointer-v1 PASS
pointer-v2 PASS
pointer-v3 PASS
```

全部通过后：

```text
relative_clause.pointer:
LEARNING → VERIFIED
```

## 2.5 LearningController

当前状态：

```text
TASK
RETRY
VERIFY
WORD_TASK
DONE
```

允许事件：

```text
TASK / RETRY + ANSWER_SUBMITTED
VERIFY      + VERIFY_ANSWER
WORD_TASK   + WORD_ANSWER
```

非法状态跳转返回 HTTP `409`，且不得写入 Learning Events。

## 2.6 幂等

客户端每次提交携带：

```text
event_id
```

Controller 保存：

```text
processed_event_ids
```

相同 `event_id` 重复提交：

```text
ui_action = NOOP
attempt 不增加
hint_level 不增加
Learning Event 不重复
```

---

# 3. 模块层

## 3.1 API

### 健康检查

```http
GET /api/v1/health
```

### 开始 Session

```http
POST /api/v1/session/start
```

### 恢复 Session

```http
GET /api/v1/session/{session_id}
```

返回 Session、当前任务与完整 Events。

### 推进学习状态

```http
POST /api/v1/learning/step
```

请求：

```json
{
  "session_id": "...",
  "event": "ANSWER_SUBMITTED",
  "event_id": "uuid",
  "payload": {
    "answer": "trapped"
  }
}
```

## 3.2 Persistence

SQLite 两张核心表：

```text
sessions
learning_events
```

`learning_events` 是事实源。

当前 `node_status / word_status` 是 Session 派生状态；后续扩展长期用户状态时，优先由 Events 重建。

## 3.3 H5

P0 前端实际实现：

```text
apps/web/
├─ index.html
├─ app.js
└─ style.css
```

采用零依赖 H5，原因：Gold Demo 的目标与 npm/Vite/Vue 无关；真实构建验证中外部 npm 镜像无法解析 Vue/Vite，继续保留该依赖只会增加不可控故障面。

页面能力：

- 开始 Gold Demo；
- 展示当前学习状态；
- 提交真实选项；
- 展示 `POINTER_ERROR`；
- 展示最小提示；
- 连续完成 3 个 Transfer Variant；
- 进入 `eruption`；
- 展示最终 VERIFIED 状态；
- LocalStorage 保存 `session_id`；
- 刷新后通过 API 恢复当前 Session。

## 3.4 Static Serving

FastAPI 在所有 `/api/v1/*` 路由注册后挂载：

```text
apps/web
```

因此同一服务同时提供：

```text
/
/app.js
/style.css
/api/v1/*
```

不需要单独前端服务器。

---

# 4. 测试与门禁

## 4.1 pytest

`tests/test_gold_loop.py` 当前覆盖：

1. 完整学习闭环；
2. 非法状态跳转不污染 Events；
3. 重复请求 Controller 幂等。

实际回执：

```text
3 passed
```

## 4.2 Static H5 Contract

```bash
python scripts/check_static.py
```

实际回执：

```text
STATIC_H5_OK
```

## 4.3 JavaScript Syntax

```bash
node --check apps/web/app.js
```

实际：exit code `0`。

## 4.4 API + Static Integration

实测：

```text
GET /                  200
GET /api/v1/health     200
```

## 4.5 Smoke

```bash
python scripts/smoke.py
```

实际路径：

```text
ANSWER_SUBMITTED -> RETRY
ANSWER_SUBMITTED -> VERIFY
VERIFY_ANSWER -> VERIFY
VERIFY_ANSWER -> VERIFY
VERIFY_ANSWER -> WORD_TASK
WORD_ANSWER -> DONE
CLOSED_LOOP ... events=19
```

## 4.6 CI

`.github/workflows/ci.yml` 定义：

```text
pytest
↓
smoke
↓
static contract
↓
node syntax
↓
Docker build
```

当前 GitHub 集成无法读取 Actions 权限，远端 Actions 尚无真实 Run 回执；不得写成 CI PASS。

---

# 5. 运行与部署

## 5.1 本地

```bash
pip install -r requirements.txt
uvicorn apps.api.app:app --host 0.0.0.0 --port 8000
```

打开：

```text
http://127.0.0.1:8000
```

## 5.2 Docker

仓库包含 `Dockerfile`：

```text
python:3.12-slim
→ pip install
→ copy apps + content
→ uvicorn :8000
```

当前执行环境没有 Docker CLI，因此 Docker Build 尚未取得真实本地回执。

## 5.3 公网 Deploy

当前 Vercel 连接：

- `list_teams` 返回空；
- 无可用 Project 创建入口；
- deploy 工具运行时要求的参数与暴露 Schema 不一致。

所以公网 Deploy 当前属于**外部工具阻塞**，不伪造成功状态。

---

# 6. P0 当前完成度

| Gate | 状态 | 证据 |
|---|---|---|
| Outcome Contract | PASS | Gold Content |
| Deterministic Core | PASS | Controller + Content |
| Error Diagnosis | PASS | POINTER_ERROR |
| Minimal Intervention | PASS | 5-level hints |
| Transfer Verification | PASS | 3/3 variants |
| Learning Events | PASS | Smoke 19 events |
| Request Idempotency | PASS | pytest |
| Illegal Transition Guard | PASS | pytest |
| H5 Vertical Slice | PASS | root 200 + static check |
| Session Restore Contract | PASS | GET session + LocalStorage |
| Second Capability | PASS | word.root.rupt |
| Smoke Closed Loop | PASS | DONE |
| Remote CI | BLOCKED | GitHub Actions integration permissions |
| Docker Build | UNVERIFIED | current runtime has no Docker CLI |
| Public Deploy | BLOCKED | Vercel connector/project context |

---

# 7. 下一阶段边界

在远端基础设施解锁前，不扩展产品功能。

代码侧下一阶段只允许：

1. 修复真实测试发现的问题；
2. 增加浏览器级 E2E；
3. 增加 Content Validator；
4. 将 Learning State 从 Session JSON 独立成可重建投影；
5. 再评估 LLM Explanation / Variant Candidate。

继续禁止：

```text
LangGraph
Multi-Agent
RAG
Vector DB
Neo4j
Redis
pyKT Runtime
FSRS Optimizer
教师后台
账号系统
```

---

# 8. 工程完成结论

P0 Gold Demo 的**代码学习闭环已经完成并实测通过**：

```text
Observe
→ Diagnose
→ Intervene
→ Verify
→ Update
→ Next Capability
→ DONE
```

当前剩余项属于远端 CI / 容器 / 公网部署基础设施验证，不属于学习闭环功能缺失。任何后续开发都应先保持这条链持续为绿。
