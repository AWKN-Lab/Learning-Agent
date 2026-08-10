# RUN EVIDENCE｜Learning-Agent v0.1.0-demo

> 验证日期：2026-08-11  
> 代码基线提交：`8e1b3ec1327e021f5b1b1b2df02dabd0538d3602`  
> 模式：Deterministic / AI OFF

## 1. 统一门禁

执行：

```bash
python -m pytest -q
python scripts/check_static.py
node --check apps/web/app.js
python scripts/smoke.py
```

实际回执：

```text
...                                                                      [100%]
3 passed in 0.63s
STATIC_H5_OK
ANSWER_SUBMITTED -> RETRY
ANSWER_SUBMITTED -> VERIFY
VERIFY_ANSWER -> VERIFY
VERIFY_ANSWER -> VERIFY
VERIFY_ANSWER -> WORD_TASK
WORD_ANSWER -> DONE
CLOSED_LOOP d97eca6c-40e0-4085-a6fc-1088b1ed2f06 events= 19
```

`node --check apps/web/app.js` exit code：`0`。

## 2. API / Static Integration

实测：

```text
GET /                  200  index contains app.js
GET /api/v1/health     200  {status: ok, mode: deterministic}
```

## 3. 测试覆盖

### Complete Closed Loop

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

### Illegal Transition

在 `TASK` 状态直接提交 `VERIFY_ANSWER`：

```text
HTTP 409
Learning Events 数量不变化
```

### Request Idempotency

同一 `event_id` 重复提交：

```text
第二次 ui_action = NOOP
attempt 不增加
hint_level 不增加
raw Learning Event 只有 1 条
```

## 4. 已发现并修复的问题

### R1｜请求幂等只停留在 Event Store

初版重复 `event_id` 虽不会重复落 Event，但可能重复推进 Controller。

修复：Session 保存 `processed_event_ids`，Controller 在状态变更前执行幂等检查。

### R2｜Smoke Script Import Path

初版直接运行：

```bash
python scripts/smoke.py
```

失败：

```text
ModuleNotFoundError: No module named 'apps'
```

修复：Smoke Script 显式把 repository root 加入 `sys.path`。

### R3｜Vue/Vite npm 依赖不可解析

真实 npm 验证时当前镜像无法解析 `vue` / `@vitejs/plugin-vue`。

处理：依据第一性原理，将 P0 H5 收敛为零 npm 依赖静态实现；API/学习契约保持不变。

## 5. 未验证 / 外部阻塞

### GitHub Actions

Actions Runs 查询返回：

```text
total_count = 0
```

Actions Permission API：

```text
403 Resource not accessible by integration
```

所以远端 CI 不标 PASS。

### Docker

当前执行环境：

```text
docker: command not found
```

Dockerfile 已存在，构建尚无真实回执。

### Vercel

当前 Vercel 连接没有 Team/Project 上下文，部署工具暴露 Schema 与运行时参数要求不一致，无法取得公网部署成功回执。

## 6. 结论

**P0 Demo 学习代码闭环：PASS。**

**Remote CI / Docker Build / Public Deploy：尚未取得成功回执，保持 BLOCKED / UNVERIFIED。**
