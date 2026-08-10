# RUN EVIDENCE｜Learning-Agent v0.2.0-hardening baseline

> 验证日期：2026-08-11  
> 模式：Deterministic / AI OFF  
> 代码基线：`15edeab92a495300a31d6475f865ed9ea5c0f5e0`

## 1. 学习闭环

```text
TASK
→ wrong: trapped
→ POINTER_ERROR
→ minimum hint
→ correct: ruins
→ VERIFY
→ pointer-v1 PASS
→ pointer-v2 PASS
→ pointer-v3 PASS
→ relative_clause.pointer VERIFIED
→ WORD_TASK
→ rupt PASS
→ word.root.rupt VERIFIED
→ DONE
```

Authenticated Smoke：

```text
ANSWER_SUBMITTED -> RETRY v 1
ANSWER_SUBMITTED -> VERIFY v 2
VERIFY_ANSWER -> VERIFY v 3
VERIFY_ANSWER -> VERIFY v 4
VERIFY_ANSWER -> WORD_TASK v 5
WORD_ANSWER -> DONE v 6
CLOSED_LOOP ... events=19 receipts=6
```

## 2. P1-0 / P1-1 / P1-2｜状态完整性

完成：

- Pure `LearningController.reduce()`；
- Command / Events / Session / Receipt 单 SQLite Transaction；
- Exact Receipt Replay；
- `expected_version` Optimistic Concurrency；
- 4 个 Fault Injection Rollback；
- 两个 Store 实例并发；
- Duplicate Command 并发；
- Event Replay / Integrity Check；
- Policy / Content Version Replay Guard。

主分支代码：`d2f00d3f7d7086b69ee612857b65454214553ac0`。

GitHub Actions：`31427875056`。

```text
test    SUCCESS
docker  SUCCESS
```

## 3. P1 Runtime Governance

完成：

- Session Token；
- Token Hash at Rest；
- Session TTL；
- `last_accessed_at`；
- SQLite Shared Rate Limit；
- Session Cleanup；
- max-sessions Capacity；
- Production Trusted Host Guard；
- Request Content-Length Gate；
- `/live` / `/ready`；
- Structured Mutation Logs；
- Docker readiness / auth / cleanup smoke。

代码基线：`15edeab92a495300a31d6475f865ed9ea5c0f5e0`。

PR #4 CI：`31428953782`。

```text
test    SUCCESS
docker  SUCCESS
```

主分支 CI：`31429090745`。

```text
test    SUCCESS
docker  SUCCESS
```

Test Job 已执行：

```text
pip check                         SUCCESS
compileall                        SUCCESS
pytest -q                         SUCCESS (16 tests)
authenticated smoke              SUCCESS
static H5 contract               SUCCESS
cleanup dry-run                  SUCCESS
node --check                     SUCCESS
```

Docker Job 已执行：

```text
Docker build                     SUCCESS
container start                  SUCCESS
GET /api/v1/ready                SUCCESS
GET /api/v1/live                 SUCCESS
GET /                            SUCCESS
POST /api/v1/session/start       SUCCESS + session_token
container cleanup dry-run        SUCCESS
```

## 4. 原子事务证据

故障注入位置：

```text
after_command_event
after_events
before_session_update
before_receipt
```

每个位置均要求：

```text
Session Snapshot 不变化
Learning Events 不残留
Receipt 不残留
```

结果：PASS。

## 5. 并发证据

### 不同 Command / 同旧 Version

两个独立 Store 实例同时提交：

```text
1 个成功
1 个 StateConflict
最终 version = 1
只产生 1 个 Command Receipt
```

结果：PASS。

### 相同 Command 并发

```text
两个请求返回相同 Receipt
状态只推进一次
Receipt 只有一条
```

结果：PASS。

## 6. Session 安全证据

- 不带 Token：401；
- 错 Token：401；
- 正确 Token：200；
- SQLite 中保存值 = SHA-256(token)；
- SQLite 中不存在 Token 明文；
- 过期 Session：410；
- Production `TRUSTED_HOSTS` 缺失：启动配置拒绝；
- Production `TRUSTED_HOSTS=*`：拒绝。

## 7. 生命周期证据

Cleanup：

```text
--dry-run         只返回候选，不删除
expired           可清理
max-sessions      可裁剪历史 Session
FK cascade        Events / Receipts 随 Session 清理
```

CI 与 Docker 内均执行 dry-run 门禁。

## 8. 当前结论

```text
Learning Demo Closed Loop    PASS
Atomic Transaction           PASS
Receipt Replay               PASS
Optimistic Concurrency       PASS
Crash Rollback               PASS
Event Replay Integrity       PASS
Session Authentication       PASS
Session TTL                  PASS
Shared Rate Limit            PASS
Cleanup / Capacity           PASS
Production Config Guard      PASS
Remote CI                    PASS
Docker Runtime               PASS
Public Deploy                BLOCKED_EXTERNAL
```

公网 Deployment 暂无真实成功回执。当前 Vercel 连接无 Team / Project 上下文；因此保持 `BLOCKED_EXTERNAL`，不伪造 URL、Release 或生产 Rollback 回执。
