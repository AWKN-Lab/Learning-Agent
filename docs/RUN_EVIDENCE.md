# RUN EVIDENCE｜Learning-Agent v0.1.0-demo

## 验收链

```text
TASK
→ POINTER_ERROR
→ HINT
→ RETRY PASS
→ pointer-v1 PASS
→ pointer-v2 PASS
→ pointer-v3 PASS
→ relative_clause.pointer VERIFIED
→ WORD_TASK eruption
→ rupt VERIFIED
→ DONE / CLOSED_LOOP
```

## 自动化证据

- `tests/test_gold_loop.py`：完整闭环、非法状态跳转、Learning Event event_id 幂等。
- `scripts/smoke.py`：从 Session Start 到 `CLOSED_LOOP` 的真实 API 内存客户端运行。
- `.github/workflows/ci.yml`：Backend pytest + Smoke、Frontend Type Check + Build、Docker Build。

## 当前模式

- 正确性主干：Deterministic Core。
- LLM：P0 Gold Loop 不依赖。
- 状态事实源：SQLite `learning_events`。
- 学习完成标准：pointer 迁移验证 3/3 + word root 任务通过。

## CI 回执

本文件在 CI 首次成功后补充 commit SHA、workflow run、各 Job 结论。
