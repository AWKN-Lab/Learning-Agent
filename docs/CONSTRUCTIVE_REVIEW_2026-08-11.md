# Learning-Agent｜建设性审查 + 传统代码审查｜2026-08-11

> 审查范围：P1 Atomic State、Runtime Governance、H5、CI、Docker。  
> 当前代码基线：`15edeab92a495300a31d6475f865ed9ea5c0f5e0`。

# 1. 建设性审查目标

关注：

```text
职责是否清晰
模块是否可替换
代码是否容易理解
状态是否可追踪
后续扩展是否需要推翻当前实现
```

# 2. 已发现并修复的结构问题

## C1｜Controller 同时做业务和数据库写入

问题：学习规则与持久化耦合，导致测试、故障注入、未来换数据库都困难。

修复：

```text
domain.py
└─ LearningController = pure reducer

store.py
└─ Transaction / Event / Receipt / State
```

Controller 输入旧状态与 Command，只返回 Transition，不产生副作用。

## C2｜core.py 持续膨胀

问题：兼容入口开始承载业务、数据库、运行治理。

修复：`core.py` 降为兼容导出；真实职责分别进入：

```text
domain.py
store.py
settings.py
security.py
runtime_errors.py
```

## C3｜Python RLock 承担状态正确性

问题：单进程有效，多 Worker / 多 Store 失效。

修复：

```text
SQLite BEGIN IMMEDIATE
+
Session version
+
WHERE version = expected_version
```

状态正确性下沉到共享数据层。

## C4｜重试语义不完整

旧行为：重复请求返回 `NOOP`。

问题：客户端网络超时后无法得到第一次请求的原响应。

修复：`command_receipts` 持久化完整 Response；完全相同 Command 重试返回原 Receipt。

## C5｜Replay 默认使用当前策略

问题：未来 policy/content 升级后，新 Reducer 重放旧 Session 可能制造假“不一致”。

修复：Replay 前比较：

```text
agent_policy_version
content_pack_version
```

版本不同返回 `replay_supported=false`。

## C6｜Runtime Error 污染 Learning Domain

问题：认证、过期、限流属于运行治理，继续进入 domain 会让核心学习逻辑越来越依赖部署策略。

修复：新增 `runtime_errors.py`。

## C7｜测试存在 import 顺序隐性依赖

问题：哪个测试文件先 import `apps.api.app` 会影响全局 Store 使用哪一个临时数据库。

修复：统一由 `tests/conftest.py` 在 App import 前设置环境。

# 3. 传统代码审查

## 3.1 命名

通过：

- `LearningController.reduce` 明确表达 reducer 语义；
- `execute_command` 表达事务命令边界；
- `command_receipts` 表达幂等回执；
- `expected_version` 表达 optimistic concurrency；
- `/live` 与 `/ready` 语义分离。

## 3.2 异常处理

已形成明确 HTTP 语义：

```text
401 session_unauthorized
404 session_not_found
409 command_id_conflict
409 state_conflict
409 invalid_transition
410 session_expired
413 request_too_large
422 schema validation
429 rate_limit_exceeded
503 not_ready
```

禁止异常被 SPA 页面吞成 200 HTML。

## 3.3 安全

已检查：

- Session Token 明文不入 SQLite；
- Token 不进入结构化日志；
- Answer 不进入运行日志；
- Trusted Host production fail-fast；
- CORS 未全开放；
- CSP / nosniff / frame deny；
- 静态文件 root boundary；
- API 路径不进入 SPA fallback。

## 3.4 数据一致性

已检查：

- Command + Events + State + Receipt 单事务；
- 4 个故障点注入后全部 rollback；
- command_id exact replay；
- command_id payload conflict；
- optimistic version；
- 两 Store 并发；
- Snapshot Replay Integrity。

## 3.5 可测试性

当前自动门禁包含：

```text
16 pytest tests
Authenticated closed-loop smoke
Static H5 contract
Cleanup dry-run
JS syntax
Docker build
Docker runtime
/live
/ready
Session Token start
Container cleanup dry-run
```

## 3.6 可维护性

当前没有引入：

```text
Redis
PostgreSQL
Kafka
Celery
LangGraph
Multi-Agent
```

这些依赖在当前 Demo 规模没有证据表明必要。

# 4. 当前仍保留的工程边界

## B1｜反向代理真实 IP

Start Rate Limit 当前使用应用看到的 client host。

公网部署到反向代理后，必须由具体平台明确 trusted proxy / forwarded header 策略。

应用当前不会自行相信任意 `X-Forwarded-For`，以免攻击者伪造 IP 绕限流。

## B2｜Streaming Body

应用 `Content-Length` 门禁覆盖常规请求；真正公网入口还应由反向代理设置 body size hard limit，覆盖 chunked/streaming 请求。

## B3｜SQLite 扩展边界

当前 SQLite 已能保证：

- 原子事务；
- 多 Store version conflict；
- shared rate limit；
- TTL cleanup。

只有出现真实多实例高并发需求后，再以测试数据决定是否迁移 PostgreSQL。

## B4｜公网部署

当前没有真实部署目标，因此：

```text
Public Deploy = BLOCKED_EXTERNAL
Production Rollback = PENDING_DEPLOY
```

不把 Docker 可运行等同于公网部署成功。

# 5. 审查结论

当前代码已经从“比赛 Demo 能跑”推进到：

```text
Pure Domain
+
Atomic State
+
Replayable Evidence
+
Session Isolation
+
Lifecycle Governance
+
Runtime Gates
```

代码规范、职责边界、异常语义、可测试性和可维护性均已形成自动门禁。

下一轮只有在取得真实部署目标后继续：

```text
Proxy Boundary
→ Production Env
→ Public Smoke
→ Release
→ Rollback
```
