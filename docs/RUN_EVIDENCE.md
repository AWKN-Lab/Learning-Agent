# RUN EVIDENCE｜Learning-Agent v0.1.0-demo

> 验证日期：2026-08-11  
> 模式：Deterministic / AI OFF  
> 主分支已验证 Commit：`5bd2a49d8b481377c5e048c3b024b078bb6da727`

## 1. 本地统一门禁

执行：

```bash
python -m pytest -q
python scripts/check_static.py
node --check apps/web/app.js
python scripts/smoke.py
```

真实回执：

```text
...                                                                      [100%]
3 passed
STATIC_H5_OK
ANSWER_SUBMITTED -> RETRY
ANSWER_SUBMITTED -> VERIFY
VERIFY_ANSWER -> VERIFY
VERIFY_ANSWER -> VERIFY
VERIFY_ANSWER -> WORD_TASK
WORD_ANSWER -> DONE
CLOSED_LOOP ... events=19
```

`node --check apps/web/app.js` exit code：`0`。

## 2. API / Static Integration

```text
GET /                  200
GET /api/v1/health     200  {status: ok, mode: deterministic}
```

## 3. Remote CI

### 首轮 PR 探针

PR #1 用于真实触发远端 Actions。

首轮 Run：`31412237285`

结果：

```text
test = FAILURE
```

根因：

```text
pytest collection
→ ModuleNotFoundError: No module named 'apps'
```

修复：增加 `tests/conftest.py`，显式将 repository root 加入 Python import path。

### 修复后 PR 验证

Run：`31412407887`

```text
test    SUCCESS
docker  SUCCESS
```

### 主分支最终验证

Run：`31412516711`

Head：

```text
5bd2a49d8b481377c5e048c3b024b078bb6da727
```

Jobs：

```text
test    SUCCESS   93533711270
docker  SUCCESS   93533799332
```

`test` Job 内部：

```text
checkout                         SUCCESS
setup-python                     SUCCESS
setup-node                       SUCCESS
pip install -r requirements.txt  SUCCESS
pytest -q                        SUCCESS
python scripts/smoke.py          SUCCESS
python scripts/check_static.py   SUCCESS
node --check apps/web/app.js     SUCCESS
```

`docker` Job 内部：

```text
checkout                         SUCCESS
docker/setup-buildx-action       SUCCESS
docker/build-push-action         SUCCESS
```

## 4. 闭环证据

```text
TASK
→ wrong: trapped
→ POINTER_ERROR
→ RETRY
→ correct: ruins
→ VERIFY
→ pointer-v1: house PASS
→ pointer-v2: city PASS
→ pointer-v3: room PASS
→ relative_clause.pointer VERIFIED
→ WORD_TASK
→ rupt PASS
→ word.root.rupt VERIFIED
→ DONE
```

Learning Events：19 条。

关键事件包含：

```text
error_diagnosed
hint_given
variant_answered
patch_completed
learning_state_updated
next_task_selected
word_verified
demo_completed
```

## 5. 边界验证

### Illegal Transition

`TASK` 状态直接提交 `VERIFY_ANSWER`：

```text
HTTP 409
Learning Events 数量不变化
```

### Request Idempotency

相同 `event_id` 重复提交：

```text
第二次 ui_action = NOOP
attempt 不增加
hint_level 不增加
raw Learning Event 只有 1 条
```

## 6. 本轮发现并修复

1. Controller 请求级幂等缺口；
2. Smoke Script repository import path；
3. Vue/Vite/npm 对 P0 的不必要外部依赖；
4. GitHub Runner pytest import path。

上述问题均已形成代码修复并经过门禁验证。

## 7. 当前结论

```text
P0 Learning Demo Closed Loop  PASS
Local Tests                   PASS
Local Smoke                   PASS
Remote CI                     PASS
Docker Build                  PASS
Public Deploy                 BLOCKED
```

公网部署尚无真实成功回执：当前 Vercel 连接没有可用 Team/Project 上下文，部署工具 Schema 与运行时参数契约不一致。
