# PRD V3.0 Acceptance Ledger

> 日期：2026-08-11  
> 目标：把 PRD V3.0 的“完成”变成可复核的工程验收，而不是主观宣称。

## 1. 产品层

| 验收项 | 证据 | 状态 |
|---|---|---|
| Dashboard | `homePage` | PASS |
| Today | `todayPage` | PASS |
| Lab | `labPage` | PASS |
| Repair | `repairPage` | PASS |
| Topology | `topologyPage` | PASS |
| Assets | `assetsPage` | PASS |
| Profile | `profilePage` | PASS |
| Capability Preview | Manifest-driven Preview | PASS |
| Baseline Diagnostic 入口 | `baseline_diagnostic` | PASS |

## 2. 学习层

当前 V3 只允许以下 Runtime Nodes：

```text
relative_clause.pointer
word.root.rupt
```

真实闭环：

```text
pointer task
→ POINTER_ERROR
→ minimum hint
→ retry
→ 3 transfer variants
→ pointer VERIFIED
→ rupt task
→ rupt VERIFIED
→ DONE
```

状态来源必须为 Session State + Learning Events。

## 3. Preview 安全边界

PREVIEW capability 必须满足：

```text
status = preview
action = absent
node = absent
```

因此当前：

- MECE；
- 5 Whys；
- 指令流转；
- 物理还原；
- 逻辑解谜；
- 基线诊断；

只能展示产品定义与未来交互，不得进入 `learning/step`。

## 4. 自动门禁

### pytest

`tests/test_product_v3_contract.py`：

- V3 Shell Contract；
- Capability Matrix；
- Preview Isolation；
- Runtime Node Allowlist；
- Profile / Baseline Framework。

### Static

`scripts/check_static.py`：

- 必需 H5 文件；
- Product Shell 页面函数；
- V3 Manifest JSON Contract；
- Capability Matrix；
- Runtime Node 精确集合；
- Assets 状态；
- Profile Contract；
- `/xueba/` 子路径安全。

### Existing Runtime

必须继续通过：

- Gold Loop；
- Atomic Transaction；
- Receipt Replay；
- Optimistic Concurrency；
- Event Replay / Integrity；
- Session Auth / TTL / Rate Limit / Cleanup；
- Docker Runtime Smoke。

## 5. 最终关闭条件

只有当目标分支与最终 `main` 都满足：

```text
Test SUCCESS
Docker SUCCESS
```

并把最终 HEAD / CI Run 回写 `RUN_EVIDENCE.md` 后，才可标记：

```text
PRD V3.0 Development = DONE
```

公网部署如果没有真实可用目标，单独保持 `BLOCKED_EXTERNAL`，不影响 V3 产品代码完成判定，也不得伪造部署回执。