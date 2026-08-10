# 文科实验室 H5 DEMO 工程母文档｜V2.6 Hardened Baseline

> 目标版本：`v0.2.0-hardening`  
> 更新：2026-08-11  
> 代码基线：`15edeab92a495300a31d6475f865ed9ea5c0f5e0`  
> 主分支 CI：`31429090745`，Test / Docker 双绿

---

# 1. 系统层

## 1.1 系统目标

当前版本证明并保护一条真实学习修复闭环：

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

Gold Node：`relative_clause.pointer`。

第二能力：`eruption → e + rupt + ion`。

完成条件：

- 主任务真实发生 `POINTER_ERROR`；
- 最小提示后学生修正；
- 3 道迁移题全部通过；
- `relative_clause.pointer = VERIFIED`；
- `word.root.rupt = VERIFIED`；
- Controller 到 `DONE`；
- Learning Events 包含 diagnosis / patch / state update / completion 证据。

## 1.2 第一性原理工程主干

```text
Task Model
↓
Student Action
↓
Pure Learning Reducer
↓
Atomic Persistence
↓
Evidence / Receipt
↓
Learning State
```

LLM 不负责标准答案、错误类型和长期状态正确性。AI OFF 时主链完整成立。

## 1.3 当前系统架构

```text
Browser H5
    │
    ▼
FastAPI HTTP Boundary
    │
    ▼
LearningController
pure deterministic reducer
    │
    ▼
Transactional Store
SQLite
 ├─ sessions
 ├─ learning_events
 ├─ command_receipts
 └─ rate_limits
    │
    ├─ Event Replay / Integrity
    ├─ Session Token / TTL
    ├─ Optimistic Version
    └─ Cleanup / Capacity
```

---

# 2. 组件层

## 2.1 Domain｜LearningController

文件：`apps/api/domain.py`

职责：

- 读取旧状态；
- 验证合法事件；
- 计算新状态；
- 产生 Domain Events；
- 返回 StepResult。

禁止：

- SQL；
- HTTP；
- Token；
- Rate Limit；
- 文件系统写入。

核心接口：

```text
initial_state()
initial_result()
initial_events()
current_task()
reduce(state, event, payload)
```

状态：

```text
TASK
RETRY
VERIFY
WORD_TASK
DONE
```

## 2.2 Persistence｜Store

文件：`apps/api/store.py`

职责：

- SQLite Schema / migration；
- Atomic Command；
- Learning Events；
- Session Snapshot；
- Response Receipt；
- Session Version；
- Event Replay；
- Session Token Hash；
- TTL / last_accessed；
- SQLite Rate Limit；
- Session Cleanup；
- Readiness。

### Atomic Command

Mutation 固定执行：

```text
BEGIN IMMEDIATE
↓
Authorize Session
↓
Check existing Receipt
↓
Check expected_version
↓
LearningController.reduce()
↓
Write Command Event
↓
Write Derived Events
↓
Update Session WHERE version = expected_version
↓
Write Response Receipt
↓
COMMIT
```

任何异常：`ROLLBACK`。

### Idempotent Receipt

同一 `command_id` + 完全相同请求：

```text
直接返回原 response_json
```

同一 `command_id` + 不同请求：

```text
409 command_id_conflict
```

### Optimistic Concurrency

每个 Session 有 `version`。

客户端 mutation 必须携带 `expected_version`。

旧版本请求：

```text
409 state_conflict
```

正确性不再依赖 Python 进程锁。

## 2.3 Runtime Security

文件：

```text
apps/api/security.py
apps/api/settings.py
apps/api/runtime_errors.py
```

Session Start：

```text
随机 token
↓
明文只返回客户端一次
↓
SQLite 只保存 SHA-256(token)
```

后续 Session Read / Mutation：

```http
X-Session-Token: ...
```

Token 错误：`401 session_unauthorized`。

Session 过期：`410 session_expired`。

## 2.4 Runtime Governance

### TTL

默认 Demo Session TTL：由 `SESSION_TTL_SECONDS` 配置。

Session 保存：

```text
created_at
updated_at
last_accessed_at
expires_at
```

### Rate Limit

SQLite fixed-window limiter：

```text
Session Start → client identity
Learning Step → token hash
```

Rate Limit 状态在 SQLite 中共享，不依赖单个 Python 进程内存。

### Cleanup

```bash
python scripts/cleanup_sessions.py --dry-run --max-sessions 100
```

支持：

- 过期 Session；
- 最大 Session 数；
- dry-run；
- FK cascade 清理 Events / Receipts。

## 2.5 H5

文件：

```text
apps/web/index.html
apps/web/app.js
apps/web/style.css
```

保持零 npm 运行依赖。

客户端保存：

```text
session_id
session_token
```

Mutation 保存并发送：

```text
command_id
expected_version
X-Session-Token
```

网络错误只使用原 Command 重试一次。409 时刷新服务器 Session，不在浏览器自行推进状态。

---

# 3. 模块层

## 3.1 API Contract

```http
GET  /api/v1/live
GET  /api/v1/ready
GET  /api/v1/health          # compatibility
POST /api/v1/session/start
GET  /api/v1/session/{id}
POST /api/v1/learning/step
GET  /api/v1/internal/session/{id}/integrity   # non-production only
```

Learning Step：

```json
{
  "session_id": "uuid",
  "event": "ANSWER_SUBMITTED",
  "event_id": "<session-id>:<request-id>",
  "expected_version": 0,
  "payload": {
    "answer": "trapped"
  }
}
```

Header：

```http
X-Session-Token: <token>
```

## 3.2 Health Contract

`/live`：只证明进程可响应。

`/ready`：验证：

- SQLite 可查询；
- 必要表存在；
- Content Pack 已加载；
- 当前 Policy 可识别。

Docker HEALTHCHECK 使用 `/live`。

部署流量切入前检查 `/ready`。

## 3.3 Replay / Integrity

非生产环境：

```http
GET /api/v1/internal/session/{id}/integrity
```

按 Command Events 重放 Reducer，并比较存储 Snapshot。

Replay 只有在以下版本与当前 Reducer 一致时才执行：

```text
agent_policy_version
content_pack_version
```

版本不匹配：

```text
replay_supported = false
```

避免拿新策略错误重放旧 Session。

## 3.4 Structured Logs

成功 Mutation 记录：

```text
command_id
session_id
learning_event
state_after
version_after
duration_ms
result
```

禁止记录：

```text
answer 原文
session_token
```

---

# 4. 测试与审查门禁

## 4.1 当前 Test Suite

主分支当前覆盖至少：

- Gold Loop；
- Receipt Exact Replay；
- Command ID 冲突；
- stale version；
- 非法状态跳转；
- 输入 Schema；
- SPA / API 边界；
- 4 个 Transaction Fault Injection；
- 两个 Store 并发；
- Duplicate Command 并发；
- Snapshot Tamper Detection；
- Session Token；
- Session Expiry；
- SQLite Shared Rate Limit；
- Cleanup / FK Cascade；
- Capacity Cleanup；
- Request Body Limit；
- Production Trusted Hosts。

当前 pytest：`16 passed`。

## 4.2 CI

```text
pip install
pip check
compileall
pytest
Authenticated Smoke
Static Contract
Cleanup Dry-run
JS Syntax
Docker Build
Docker Runtime
/ready
/live
H5
Session Token Start
Container Cleanup Dry-run
```

主分支 Run：`31429090745`。

Test / Docker 均 SUCCESS。

---

# 5. 建设性 / 传统审查结论

本轮已经修正的维护性问题：

1. Controller 与数据库写入耦合 → `domain.py` / `store.py` 分离；
2. `core.py` 继续膨胀 → 降为兼容导出；
3. Python `RLock` 承担正确性 → SQLite Transaction + Version；
4. 重试只返回 NOOP → 持久化 Response Receipt；
5. Replay 默认相信当前策略 → 增加 Policy / Content Version Guard；
6. Runtime Error 污染 Domain → 独立 `runtime_errors.py`；
7. 测试依赖 import 顺序 → 统一 `tests/conftest.py`；
8. Docker 只 build → runtime smoke；
9. `/health` 混合 live/ready → 明确拆分；
10. 无 Session 生命周期 → Token / TTL / Rate / Cleanup。

---

# 6. 当前边界

仍未伪装成完成的事项：

1. 公网 Deployment 尚无真实 URL；
2. 当前 Vercel 连接无可用 Team / Project；
3. 反向代理后的真实客户端 IP 策略需随具体部署平台配置；应用不会任意信任 `X-Forwarded-For`；
4. Content-Length 中间件不能替代入口代理对 chunked/streaming body 的硬上限；
5. SQLite 适用于当前 Demo 规模，真正多实例高并发后再评估 PostgreSQL。

这些边界不会通过引入 Redis / Kafka / 微服务来提前复杂化。

---

# 7. 当前完成判定

```text
Learning Closed Loop      PASS
Atomic State              PASS
Idempotent Receipt        PASS
Optimistic Concurrency    PASS
Crash Rollback            PASS
Event Replay Integrity    PASS
Session Auth              PASS
Session TTL               PASS
Shared Rate Limit         PASS
Session Cleanup           PASS
Production Config Guard   PASS
Local Gates               PASS
GitHub CI                 PASS
Docker Runtime            PASS
Public Deployment         BLOCKED_EXTERNAL
```

下一工程动作只剩：取得真实部署目标 → 配置持久 `/data`、`APP_ENV=production`、`TRUSTED_HOSTS` → Public Smoke → Release / Rollback。
