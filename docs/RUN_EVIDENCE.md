# RUN EVIDENCE｜Learning-Agent PRD V3.0 Closure

> 验证日期：2026-08-11  
> 模式：Deterministic / AI OFF  
> PRD：V3.0 完整产品框架版  
> 验证代码 HEAD：`6795e1f3bcab76224c3270e67d65100796b68383`  
> PR：#8 `feat: close PRD V3.0 product contract`  
> PR GitHub Actions：`31462567705`

---

# 1. PRD V3.0 产品闭环

V3 当前完成结构：

```text
完整 Product Shell
├─ Dashboard
├─ Today
├─ Lab
├─ Repair
├─ Topology
├─ Assets
└─ Profile

Product Manifest
├─ 完整产品能力母表
├─ LIVE / LIMITED / PREVIEW / LOCKED
├─ Baseline Diagnostic 产品入口
├─ Profile Contract
└─ Runtime Node Allowlist

Learning Runtime
├─ relative_clause.pointer
└─ word.root.rupt
```

V3 机器契约明确：

```text
prd_version = 3.0
product_shell_version = 1.1
runtime_scope = g10_english_u4_mvp
preview_can_mutate_learning_state = false
allowed_runtime_nodes =
  relative_clause.pointer
  word.root.rupt
```

结果：PASS。

---

# 2. Learning Gold Loop 证据

CI authenticated smoke：

```text
ANSWER_SUBMITTED -> RETRY v 1
ANSWER_SUBMITTED -> VERIFY v 2
VERIFY_ANSWER -> VERIFY v 3
VERIFY_ANSWER -> VERIFY v 4
VERIFY_ANSWER -> WORD_TASK v 5
WORD_ANSWER -> DONE v 6
CLOSED_LOOP ... events=19 receipts=6
```

学习闭环：

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

结果：PASS。

---

# 3. V3 Product Contract 证据

新增：

```text
tests/test_product_v3_contract.py
```

验证：

- PRD / Manifest Version = 3.0；
- Product Shell 七页契约；
- 完整 Capability Matrix；
- `baseline_diagnostic = preview`；
- PREVIEW capability 无 `action`；
- PREVIEW capability 无 runtime `node`；
- `gold_loop / repair` 只能绑定允许 Runtime Nodes；
- Topology runtime node 集合与 allowlist 完全一致；
- Profile Contract 持续存在。

CI pytest：

```text
21 passed
1 warning
```

warning 为 Starlette TestClient / httpx 兼容弃用提示，不影响当前测试结果。

结果：PASS。

---

# 4. Static H5 V3 Contract

`scripts/check_static.py` 已升级为可解析的 V3 产品契约门禁。

验证：

- `index.html / app.js / style.css / product-manifest.json` 存在；
- Dashboard / Today / Lab / Repair / Topology / Assets / Profile 存在；
- Product Manifest 可解析；
- V3 Capability Matrix 完整；
- Preview Isolation；
- Runtime Node 精确集合；
- Assets 状态矩阵；
- Profile Contract；
- `/xueba/` 子路径相对 URL 安全。

CI 输出：

```text
STATIC_H5_V3_OK
```

结果：PASS。

---

# 5. PRD V3 功能状态证据

## 5.1 逻辑解码

```text
MECE 结构骨架器       PREVIEW
词根逻辑拆解           LIMITED
长难句公式翻译         LIVE
```

## 5.2 因果推演

```text
5 Whys                PREVIEW
指令流转               PREVIEW
物理逻辑还原           PREVIEW
```

## 5.3 逻辑修复

```text
错题归因               LIMITED
错一订三               LIVE
逻辑解谜               PREVIEW
```

## 5.4 基线诊断

```text
基线测试与诊断         PREVIEW
```

## 5.5 学习资产

```text
错误档案               LIMITED
修复日志               LIVE
学习记录               LIVE
逻辑组件库             LIMITED
学习效果报告           PREVIEW
```

PREVIEW 能力没有伪造 Runtime、成绩或 Learning Events。

结果：PASS。

---

# 6. Hardened Runtime 回归证据

本次 V3 Closure diff 没有修改：

```text
apps/api/app.py
apps/api/domain.py
apps/api/store.py
apps/api/security.py
apps/api/settings.py
apps/api/runtime_errors.py
```

原有 P1 正确性能力继续由现有测试覆盖：

- Pure `LearningController.reduce()`；
- Command / Events / Session / Receipt 单 SQLite Transaction；
- Exact Receipt Replay；
- `expected_version` Optimistic Concurrency；
- Transaction Fault Injection Rollback；
- 多 Store 并发；
- Duplicate Command 并发；
- Event Replay / Integrity；
- Session Token Hash at Rest；
- Session TTL；
- SQLite Shared Rate Limit；
- Cleanup / Capacity；
- Production Trusted Host Guard；
- `/live` / `/ready`。

21-test 全量门禁通过，Gold Loop Smoke 通过。

结果：PASS。

---

# 7. CI / Docker 证据

PR #8 验证代码 HEAD：

```text
6795e1f3bcab76224c3270e67d65100796b68383
```

GitHub Actions：

```text
31462567705
```

Test Job：

```text
pip install                       SUCCESS
pip check                         SUCCESS
compileall                        SUCCESS
pytest -q                         SUCCESS (21 passed)
authenticated Gold Loop smoke     SUCCESS
static H5 V3 contract             SUCCESS
cleanup dry-run                   SUCCESS
node --check                      SUCCESS
```

Docker Job：

```text
Docker build                      SUCCESS
Docker runtime smoke              SUCCESS
```

结果：PASS。

---

# 8. 红灯修复记录

PR 第一轮 CI `31462512468` 曾失败：

```text
20 passed
1 failed
```

失败项来自新 V3 测试误要求 PRD 中包含英文小写字符串 `baseline`，而 PRD 使用中文“基线测试与诊断入口”。

处理：

```text
修正错误测试断言
不修改 PRD 语义
不修改 Learning Runtime
```

第二轮全量门禁恢复双绿。

该记录保留，用于证明门禁没有被跳过或手工忽略。

---

# 9. 当前结论

```text
PRD V3 Product Shell         PASS
Capability Manifest          PASS
Baseline Diagnostic Entry    PASS
Profile Contract             PASS
Preview Isolation            PASS
Runtime Node Allowlist       PASS
Real State Projection        PASS
Learning Gold Loop           PASS
Atomic Transaction           PASS
Receipt Replay               PASS
Optimistic Concurrency       PASS
Crash Rollback               PASS
Event Replay Integrity       PASS
Session Authentication       PASS
Session TTL                  PASS
Shared Rate Limit            PASS
Cleanup / Capacity           PASS
Subpath Safe                 PASS
GitHub PR CI                 PASS
Docker Runtime               PASS
```

**PRD V3.0 Development：代码与产品工程闭环已达到合并门槛。**

仍独立保留：

```text
Public Deploy        BLOCKED_EXTERNAL
Production Release   PENDING_DEPLOY
Production Rollback  PENDING_DEPLOY
```

公网 Deployment 当前没有真实成功回执，因此不伪造 URL、Release 或生产 Rollback。