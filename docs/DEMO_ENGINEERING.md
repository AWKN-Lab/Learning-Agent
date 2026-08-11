# 文科实验室 H5 工程母文档｜V3.0 Product Shell + Hardened Runtime

> 对应 PRD：V3.0 完整产品框架版  
> 更新：2026-08-11  
> 工程基线：`8fb4fb3609ccf30b8da05a377fd7dfe7bea702e8` 起始，V3 Closure 分支继续收敛  
> 核心原则：**Product Shell 可以完整，Learning Runtime 只能依据真实 Content / Evidence 改变学习状态。**

---

# 1. 系统层

## 1.1 系统目标

文科实验室当前工程同时保护两件事：

```text
A. 完整产品框架
Dashboard / Today / Lab / Repair / Topology / Assets / Profile

B. 一条真实可验证学习修复闭环
Observe → Diagnose → Intervene → Verify → Update
```

当前 Gold Node：`relative_clause.pointer`。

第二真实能力：`word.root.rupt`，当前内容为：

```text
eruption → e + rupt + ion
```

真实闭环完成条件：

- 主任务真实发生 `POINTER_ERROR`；
- 最小提示后学生修正；
- 3 道迁移题全部通过；
- `relative_clause.pointer = VERIFIED`；
- `word.root.rupt = VERIFIED`；
- Controller 到 `DONE`；
- Learning Events 包含 diagnosis / patch / state update / completion 证据；
- Product Shell 的 Dashboard / Repair / Topology / Assets 能投影这些真实结果。

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
↓
Product Projection
```

LLM 不负责标准答案、错误类型和长期状态正确性。AI OFF 时主链完整成立。

## 1.3 V3 系统架构

```text
Product Manifest
完整能力母表 / 状态 / 课程拓扑 / V3 Contract
        │
        ▼
Browser H5 Product Shell
        │
        ├─ PREVIEW / LOCKED → 只读产品展示
        │
        └─ LIVE / LIMITED + Runtime Evidence
                         │
                         ▼
FastAPI HTTP Boundary
        │
        ▼
LearningController
pure deterministic reducer
        │
        ▼
Transactional Store / SQLite
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

## 1.4 V3 真相源

系统严格区分：

```text
Product Capability Truth → product-manifest.json
Learning Fact Truth       → Learning Events
Current Session Truth     → SQLite Session Snapshot
Derived Product View      → H5 Projection
```

Product Shell 不得直接制造学习事实；Topology 也只是投影，不是事实源。

---

# 2. 组件层

## 2.1 Product Manifest

文件：`apps/web/product-manifest.json`

职责：

- 维护 PRD V3 功能母表；
- 维护能力状态；
- 维护课程拓扑框架；
- 声明当前 Runtime Scope；
- 声明允许进入学习 Runtime 的节点；
- 声明 Preview 不可修改学习状态。

V3 Contract：

```text
contract.prd_version
contract.product_shell_version
contract.runtime_scope
contract.allowed_runtime_nodes
contract.preview_can_mutate_learning_state
contract.shell_pages
```

当前允许 Runtime Node：

```text
relative_clause.pointer
word.root.rupt
```

任何 PREVIEW capability：

```text
action = absent
node   = absent
```

## 2.2 Product Shell

文件：

```text
apps/web/index.html
apps/web/app.js
apps/web/style.css
apps/web/product-manifest.json
```

页面：

```text
Dashboard
Today
Lab
Repair
Topology
Assets
Profile
Learning Stage
Capability Preview
```

保持零 npm 运行依赖。

Product Shell 职责：

- 展示完整产品架构；
- 读取 Manifest；
- 读取真实 Session / Learning Events；
- 把真实状态投影到产品页面；
- 对 PREVIEW / LOCKED 只展示能力说明；
- 只有受允许的 LIVE / LIMITED 能进入真实 Learning Runtime。

禁止：

- 建立第二套学习状态机；
- 浏览器自行推进学习状态；
- Preview 写 Learning Events；
- 生成假成绩、假掌握度、假累计学习量。

## 2.3 Domain｜LearningController

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

## 2.4 Persistence｜Store

文件：`apps/api/store.py`

职责：

- SQLite Schema；
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

同一 `command_id` + 完全相同请求：直接返回原 `response_json`。

同一 `command_id` + 不同请求：`409 command_id_conflict`。

### Optimistic Concurrency

每个 Session 有 `version`。

客户端 mutation 必须携带 `expected_version`。

旧版本请求：`409 state_conflict`。

正确性不依赖 Python 进程锁。

## 2.5 Runtime Security

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

## 2.6 Runtime Governance

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

---

# 3. 模块层

## 3.1 API Contract

```http
GET  /api/v1/live
GET  /api/v1/ready
GET  /api/v1/health
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

## 3.2 Frontend Session Contract

浏览器本地只保存：

```text
session_id
session_token
```

Mutation 使用：

```text
command_id / event_id
expected_version
X-Session-Token
```

网络错误只使用原 Command 重试一次。

`409 state_conflict` 时刷新服务器 Session，不在浏览器自行推进状态。

## 3.3 Subpath Deployment Contract

H5 必须可以挂在类似：

```text
/xueba/
```

的子路径。

因此：

```text
app.js
style.css
product-manifest.json
api/v1/...
```

必须使用相对 URL。

`check_static.py` 明确禁止根绝对前端 URL 回归。

## 3.4 Health Contract

`/live`：只证明进程可响应。

`/ready`：验证：

- SQLite 可查询；
- 必要表存在；
- Content Pack 已加载；
- 当前 Policy 可识别。

Docker HEALTHCHECK 使用 `/live`。

部署流量切入前检查 `/ready`。

## 3.5 Replay / Integrity

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

## 3.6 Structured Logs

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

## 3.7 Baseline Diagnostic

PRD V3 要求保留基线诊断入口。

当前状态：`PREVIEW`。

Manifest 必须包含：

```text
baseline_diagnostic
```

当前不建设大规模基线题库，因此：

- 不进入 Learning Runtime；
- 不初始化假拓扑；
- 不输出假诊断分数；
- 只展示未来交互与产品位置。

---

# 4. 测试与工程门禁

## 4.1 Core Test Suite

覆盖：

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

V2.6 基线为 `16 passed`。

## 4.2 PRD V3 Product Contract Tests

新增：`tests/test_product_v3_contract.py`。

验证：

1. `prd_version = 3.0`；
2. Product Shell 七页契约；
3. 完整 Capability Matrix；
4. Preview 不得进入 Runtime；
5. Runtime Node 集合只能是允许集合；
6. Topology Runtime Node 与 Contract 完全一致；
7. Profile Contract 存在；
8. Baseline Diagnostic 产品入口存在。

## 4.3 Static H5 V3 Contract

`scripts/check_static.py` 验证：

- H5 必需文件；
- Product Shell 页面函数；
- V3 Manifest 可解析；
- V3 功能母表完整；
- Preview/Runtime 边界；
- Runtime Node 精确集合；
- Assets 状态矩阵；
- Profile Contract；
- 子路径 URL 安全。

## 4.4 CI

```text
pip install
pip check
compileall
pytest
authenticated smoke
static H5 V3 contract
cleanup dry-run
JS syntax
Docker build
Docker runtime
/ready
/live
H5
Session Token Start
Container Cleanup Dry-run
```

任何一步失败：STOP，不合并。

---

# 5. PRD V3 完成判定

必须同时满足：

```text
PRD V3 Product Shell      PASS
Capability Manifest       PASS
Baseline Entry            PASS
Gold Learning Loop        PASS
Real State Projection     PASS
Preview Isolation         PASS
Subpath Safe              PASS
Atomic State              PASS
Idempotent Receipt        PASS
Optimistic Concurrency    PASS
Event Replay Integrity    PASS
Session Auth / TTL        PASS
Runtime Governance        PASS
GitHub CI                 PASS
Docker Runtime            PASS
```

公网 Deployment 不属于 V3 产品代码完成的必要条件；若没有可用公网目标，继续标记 `BLOCKED_EXTERNAL`，不得伪造 URL、Release 或生产 Rollback。

---

# 6. V3 后续唯一扩展方向

V3 完成后停止继续扩 Product Shell。

下一阶段按真实内容证据逐个解锁：

```text
relative_clause.constraint
↓
更多词根节点
↓
MECE Reading Structure
↓
5 Whys causal_chain
↓
logic_puzzle
```

每个节点固定执行：

```text
Content / Runtime Evidence
→ Test
→ Manifest State Upgrade
→ CI
→ Run Evidence
```

在 Evidence 成立前，PREVIEW / LOCKED 不升级为 LIVE。