# Learning-Agent｜开发执行计划｜P1 Hardened Baseline

> 更新：2026-08-11  
> 当前代码：`15edeab92a495300a31d6475f865ed9ea5c0f5e0`

# 1. 当前完成状态

```text
P0 Learning Gold Loop             DONE
P1-0 Atomic Transaction           DONE
P1-1 Optimistic Concurrency       DONE
P1-2 Replay / Integrity           DONE
P1-3 Session Auth / Input Guard   DONE
P1-4 TTL / Cleanup / Capacity     DONE
P1-5 Production Config / Health   DONE
P1-6 Structured Observability     DONE
P1-7 Adversarial Full Gate        DONE
P1-8 Public Deploy                BLOCKED_EXTERNAL
P1-9 Release                      PENDING_DEPLOY
P1-10 Production Rollback         PENDING_DEPLOY
```

# 2. 已完成主链

```text
Student Command
↓
HTTP Contract / Token / Input Guard
↓
SQLite Rate Limit
↓
BEGIN IMMEDIATE
↓
Session Authorization
↓
Receipt Check
↓
expected_version Check
↓
Pure LearningController.reduce()
↓
Command Event + Derived Events
↓
Session Snapshot Update
↓
Response Receipt
↓
COMMIT
↓
Exact Retry / Event Replay / Integrity
```

# 3. 当前工程门禁

所有功能变更必须通过：

```text
pip check
↓
compileall
↓
pytest
↓
authenticated closed-loop smoke
↓
static H5 contract
↓
cleanup dry-run
↓
JS syntax
↓
Docker build
↓
Docker runtime
↓
/live
↓
/ready
↓
H5
↓
Session Start + Token
↓
Container cleanup dry-run
```

# 4. 下一步唯一主线｜P1-8 Public Deploy

需要一个真实支持：

```text
Docker/FastAPI
+
persistent /data
+
environment variables
```

的部署目标。

最小生产配置：

```text
APP_ENV=production
TRUSTED_HOSTS=<真实域名>
LEARNING_DB_PATH=/data/learning-agent.db
```

建议首发仍保持：

```text
1 instance
1 process
1 worker
persistent volume
```

暂不为了扩容引入 Redis / PostgreSQL。

# 5. 部署后 Public Smoke

必须执行：

```text
GET /
GET /api/v1/live
GET /api/v1/ready
POST /api/v1/session/start
GET session with token
wrong answer
repair
3 transfer variants
word task
DONE
refresh restore
exact command retry
wrong token
expired session behavior
rate limit probe
```

全部通过才标记 `Public Deploy = PASS`。

# 6. P1-9 Release

Public Smoke 通过后：

```text
版本：v0.2.0-hardening
```

Release Evidence：

```text
commit SHA
CI Run
Docker Runtime Run
Public URL
Gold Loop Trace
Atomicity Tests
Concurrency Tests
Auth / TTL / Rate Tests
Public Smoke
Known Boundaries
```

# 7. P1-10 Rollback

必须真实验证：

```text
稳定版本部署
↓
制造一个可控失败版本
↓
/ready 或 Public Smoke FAIL
↓
回滚稳定版本
↓
重新跑 Public Gold Loop
↓
PASS
```

没有真实部署目标时，只能验证 Git / Docker 可回退性，不能声称完成生产 Rollback。

# 8. 当前明确边界

1. Vercel 连接当前没有 Team / Project；
2. 反向代理真实客户端 IP 策略必须随部署平台明确，应用不自动信任任意 `X-Forwarded-For`；
3. `Content-Length` 应用门禁不能替代代理层 streaming body 硬限制；
4. SQLite 满足当前 Demo；真正进入多实例高并发后再评估 PostgreSQL；
5. 当前不扩新学科、RAG、LangGraph、pyKT、FSRS、教师后台。

# 9. 停止条件

在 Public Deploy / Release / Rollback 闭环完成前，不开启新的产品能力扩张。

当前剩余工作的真实阻塞已经收敛为一个：**取得可用公网部署目标。**
