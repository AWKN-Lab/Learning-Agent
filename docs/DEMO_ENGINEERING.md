# 文科实验室 H5 DEMO 工程母文档｜V2.5 闭环基线

> 目标版本：`v0.1.0-demo`  
> 状态：**P0 DEMO CODE CLOSED / CI GREEN / DOCKER GREEN**  
> 更新：2026-08-11  
> 主分支验证 Commit：`5bd2a49d8b481377c5e048c3b024b078bb6da727`  
> GitHub Actions Run：`31412516711`

---

# 1. 系统层

## 1.1 系统目标

当前版本验证一个明确学习结果：

> 系统观察学生的真实操作，定位一个明确逻辑错误，用最小提示帮助学生自己修正，再通过表层不同的新题证明修复成立，并把全过程沉淀为可追踪学习证据。

P0 Gold Node：

```text
relative_clause.pointer
```

第二能力：

```text
eruption → e + rupt + ion
```

## 1.2 学习闭环

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
↓
Next Capability
```

固定演示路径：

```text
TASK
↓
wrong: trapped
↓
POINTER_ERROR
↓
minimum hint
↓
correct: ruins
↓
pointer-v1: house PASS
↓
pointer-v2: city PASS
↓
pointer-v3: room PASS
↓
relative_clause.pointer VERIFIED
↓
WORD_TASK eruption
↓
rupt PASS
↓
word.root.rupt VERIFIED
↓
DONE / CLOSED_LOOP
```

完成条件：

- Controller 状态到 `DONE`；
- pointer 迁移验证 `3/3`；
- word root 任务通过；
- Learning Events 至少包含 `error_diagnosed`、`patch_completed`、`word_verified`、`demo_completed`。

## 1.3 系统架构

```text
Browser H5
    │
    ▼
FastAPI
    │
    ▼
LearningController
    │
    ├─ Task Model
    ├─ Evaluator
    ├─ Intervention Policy
    └─ Transfer Verification
    │
    ▼
SQLite Store
    ├─ sessions
    └─ learning_events
          │
          ▼
     Learning State
```

LLM 当前不参与标准答案、错误类型和学习状态判定。

---

# 2. 组件层

## 2.1 Content / Task Model

```text
content/
├─ gold_relative_clause_pointer.json
└─ word_eruption.json
```

Gold Content：

- 主任务 1 道；
- 目标错误 `POINTER_ERROR`；
- 5 级渐进提示；
- 3 道 Transfer Variants；
- 修复成功标准 `3/3`；
- 第二能力 `word.root.rupt`。

## 2.2 Evaluator

主任务：

```text
expected = ruins
actual != ruins
→ POINTER_ERROR
```

迁移题标准答案：

```text
pointer-v1 → house
pointer-v2 → city
pointer-v3 → room
```

迁移题失败时停留在当前 Variant，禁止跳过。

## 2.3 Intervention Policy

连续失败时提示逐级增加：

```text
P1 错误位置
P2 结构线索
P3 回指关系
P4 先行词定义
P5 完整结构
```

首次错误不会直接展示完整答案。

## 2.4 LearningController

状态：

```text
TASK
RETRY
VERIFY
WORD_TASK
DONE
```

合法事件：

```text
TASK / RETRY + ANSWER_SUBMITTED
VERIFY       + VERIFY_ANSWER
WORD_TASK    + WORD_ANSWER
```

非法状态跳转：HTTP `409`，且不写入 Learning Events。

## 2.5 Request Idempotency

客户端请求携带 `event_id`。

相同 `event_id` 重复请求：

```text
ui_action = NOOP
attempt 不增加
hint_level 不增加
Learning Event 不重复
```

Session 保存 `processed_event_ids` 作为当前 P0 防重复推进机制。

## 2.6 Evidence Store

SQLite：

```text
sessions
learning_events
```

`learning_events` 是事实层。状态和 UI 都不得绕过 Controller 直接改写学习结果。

---

# 3. 模块层

## 3.1 API

```http
GET  /api/v1/health
POST /api/v1/session/start
GET  /api/v1/session/{session_id}
POST /api/v1/learning/step
```

`learning/step` 请求：

```json
{
  "session_id": "...",
  "event": "ANSWER_SUBMITTED",
  "event_id": "uuid",
  "payload": {"answer": "trapped"}
}
```

## 3.2 H5

P0 实际实现：

```text
apps/web/
├─ index.html
├─ app.js
└─ style.css
```

采用零 npm 运行依赖 H5。FastAPI 直接托管静态文件。

页面能力：

- 启动 Gold Demo；
- 显示当前学习阶段；
- 真实提交答案；
- 显示 `POINTER_ERROR`；
- 显示最小提示；
- 完成 3 道迁移验证；
- 进入 `eruption`；
- 展示最终 VERIFIED 状态；
- LocalStorage 保存 Session ID；
- 页面刷新后通过 Session API 恢复。

## 3.3 Static Serving

同一 FastAPI 服务提供：

```text
/
/app.js
/style.css
/api/v1/*
```

## 3.4 Docker

```text
python:3.12-slim
↓
pip install requirements
↓
copy apps + content
↓
uvicorn 0.0.0.0:8000
```

GitHub Actions Docker Build 已成功。

---

# 4. 测试体系

## 4.1 Unit / Integration

`tests/test_gold_loop.py`：

1. 完整闭环；
2. 非法状态跳转不污染 Events；
3. 重复 `event_id` 不重复推进状态。

本地实际：

```text
3 passed
```

远端 GitHub Actions：PASS。

## 4.2 Static Contract

```bash
python scripts/check_static.py
```

结果：

```text
STATIC_H5_OK
```

## 4.3 JS Syntax

```bash
node --check apps/web/app.js
```

本地与 GitHub Runner 均 PASS。

## 4.4 Smoke

```bash
python scripts/smoke.py
```

实际：

```text
ANSWER_SUBMITTED -> RETRY
ANSWER_SUBMITTED -> VERIFY
VERIFY_ANSWER -> VERIFY
VERIFY_ANSWER -> VERIFY
VERIFY_ANSWER -> WORD_TASK
WORD_ANSWER -> DONE
CLOSED_LOOP ... events=19
```

## 4.5 API + Static Integration

本地实测：

```text
GET /                  200
GET /api/v1/health     200
```

---

# 5. CI 真实回执

Workflow：`.github/workflows/ci.yml`

主分支 Run：

```text
Run ID: 31412516711
Head:   5bd2a49d8b481377c5e048c3b024b078bb6da727
Event:  push
```

Jobs：

```text
test    SUCCESS   job 93533711270
docker  SUCCESS   job 93533799332
```

`test` 内部全部成功：

```text
checkout
setup-python
setup-node
pip install
pytest -q
scripts/smoke.py
scripts/check_static.py
node --check apps/web/app.js
```

`docker` 内部全部成功：

```text
checkout
setup-buildx
docker/build-push-action build
```

因此当前 P0 的远端代码与容器门禁均为 PASS。

---

# 6. 故障发现与修复记录

## R1｜Event Store 幂等不足

症状：重复 `event_id` 虽不会重复落 Event，但可重复推进 Controller。

修复：在 Session 中维护 `processed_event_ids`，状态变更前先做请求幂等判断。

## R2｜Smoke import path

症状：

```text
python scripts/smoke.py
ModuleNotFoundError: No module named 'apps'
```

修复：脚本显式加入 repository root。

## R3｜前端 npm 依赖成为 P0 外部故障面

症状：验证环境无法稳定解析 Vue/Vite 依赖。

修复：P0 改成 HTML + ES Module JS + CSS；学习契约与 API 不变。

## R4｜GitHub Runner pytest import path

症状：远端 CI 首轮 `pytest` 收集失败：

```text
ModuleNotFoundError: No module named 'apps'
```

修复：增加 `tests/conftest.py`，把 repository root 显式加入 `sys.path`。

验证：PR Run `31412407887` 的 test + docker 均成功；随后主分支 Run `31412516711` 再次双 Job 成功。

---

# 7. P0 完成度

| Gate | 状态 | 证据 |
|---|---|---|
| Outcome Contract | PASS | Gold Content |
| Deterministic Core | PASS | LearningController |
| Error Diagnosis | PASS | POINTER_ERROR |
| Minimal Intervention | PASS | 5-level hints |
| Transfer Verification | PASS | 3/3 variants |
| Learning Events | PASS | Smoke 19 events |
| Request Idempotency | PASS | local + remote pytest |
| Illegal Transition Guard | PASS | local + remote pytest |
| H5 Vertical Slice | PASS | static contract + root 200 |
| Session Restore Contract | PASS | Session API + LocalStorage |
| Second Capability | PASS | word.root.rupt |
| Smoke Closed Loop | PASS | DONE |
| Remote CI | PASS | Run 31412516711 |
| Docker Build | PASS | Job 93533799332 |
| Public Deploy | BLOCKED | no usable deployment target in current connector |

---

# 8. 工程完成结论

**P0 DEMO 开发闭环已经完成。**

已形成：

```text
需求
→ Gold Outcome Contract
→ Deterministic Learning Core
→ H5 Interaction
→ Learning Evidence
→ Local Tests
→ Smoke
→ Remote CI
→ Docker Build
```

当前唯一未取得真实回执的是公网部署。当前 Vercel 连接没有 Team/Project 上下文，部署工具的暴露 Schema 与运行时要求不一致，因此保持 `BLOCKED`，不伪造成功。

后续新增功能必须保持 Gold Loop、GitHub CI、Docker Build 持续为绿。
