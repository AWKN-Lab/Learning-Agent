# Learning-Agent｜PRD V3.0 开发执行计划｜Closure Baseline

> 更新：2026-08-11  
> 目标：完成 PRD V3.0 已定义的 Product Shell 与 MVP 真实学习闭环，不把后续 PREVIEW 内容伪装成 LIVE。

---

# 1. 系统层｜V3.0 Definition of Done

PRD V3.0 的完成标准固定为：

```text
完整 Product Shell
+
完整产品能力母表
+
当前 Unit 4 MVP 真实 Gold Loop
+
Dashboard / Repair / Topology / Assets 真实投影
+
PREVIEW / LOCKED 不写学习事实
+
Session Restore / Atomic Command / Receipt / Version 保持
+
CI / Docker Runtime 全绿
```

V3.0 不要求把 MECE、5 Whys、逻辑解谜等后续内容全部开发成 LIVE。它们必须保留真实产品入口和状态，但没有 Content / Runtime Evidence 时只能保持 PREVIEW。

---

# 2. 组件层｜当前完成状态

```text
V3-0 PRD 完整产品框架                 DONE
V3-1 Product Shell 七页导航             DONE
V3-2 Product Manifest 能力母表           DONE
V3-3 MVP Gold Loop 嵌入 Product Shell    DONE
V3-4 Dashboard 真实状态投影              DONE
V3-5 Repair 真实错误/提示/修复投影        DONE
V3-6 Topology 真实节点状态投影           DONE
V3-7 Assets 真实 Learning Events 投影    DONE
V3-8 Session Restore / Subpath Safe      DONE
V3-9 Baseline Diagnostic 产品入口        DONE
V3-10 V3 Machine Contract / Tests        DONE
V3-11 CI / Docker Final Gate             DONE
V3-12 V3 Run Evidence 收敛               DONE
```

验证代码 HEAD：

```text
6795e1f3bcab76224c3270e67d65100796b68383
```

验证 CI：

```text
GitHub Actions 31462567705
Test    SUCCESS
Docker  SUCCESS
pytest  21 passed
Static  STATIC_H5_V3_OK
```

当前真实可改变学习状态的节点仍只有：

```text
relative_clause.pointer
word.root.rupt
```

---

# 3. 模块层｜V3 Product Contract

`apps/web/product-manifest.json` 是 V3 产品能力母表。

必须明确：

```text
prd_version = 3.0
product_shell_version
runtime_scope
allowed_runtime_nodes
preview_can_mutate_learning_state = false
shell_pages
```

能力状态：

```text
live
limited
preview
locked
```

规则：

1. `preview` capability 不允许存在 learning runtime `action`；
2. `preview` capability 不允许绑定 runtime `node`；
3. `gold_loop / repair` 入口只能绑定 `allowed_runtime_nodes`；
4. Topology 的 `runtime` 节点集合必须与 `allowed_runtime_nodes` 完全一致；
5. 新增真实内容时先提供 Content / Runtime Evidence，再提升 Manifest 状态。

---

# 4. V3 完整功能母表

## 4.1 逻辑解码

- MECE 结构骨架器：PREVIEW
- 词根逻辑拆解：LIMITED
- 长难句公式翻译：LIVE

## 4.2 因果推演

- 5 Whys：PREVIEW
- 指令流转：PREVIEW
- 物理逻辑还原：PREVIEW

## 4.3 逻辑修复

- 错题归因：LIMITED
- 错一订三：LIVE
- 逻辑解谜：PREVIEW

## 4.4 学习资产

- 错误档案：LIMITED
- 修复日志：LIVE
- 学习记录：LIVE
- 逻辑组件库：LIMITED
- 学习效果报告：PREVIEW

## 4.5 基线诊断

- 基线测试与诊断：PREVIEW

该入口属于 PRD V3 产品结构，但当前不建设大规模基线题库，因此不得生成学习事实。

---

# 5. V3 自动门禁

所有变更必须通过：

```text
pip check
↓
compileall
↓
pytest
  ├─ Gold Loop
  ├─ Atomic Transaction
  ├─ Runtime Governance
  └─ PRD V3 Product Contract
↓
authenticated smoke
↓
static H5 V3 contract
↓
cleanup dry-run
↓
JS syntax
↓
Docker build
↓
Docker runtime
```

V3 Product Contract 重点防止：

- 功能因 MVP 收缩再次被删除；
- PREVIEW 偷接 learning mutation；
- 未开发节点被冒充为 runtime node；
- `/xueba/` 子路径部署再次被根绝对 URL 破坏；
- Product Shell 与 Learning Runtime 各自维护第二套状态真相。

---

# 6. 当前真实学习闭环

```text
Dashboard
↓
Today / Lab
↓
relative_clause.pointer
↓
POINTER_ERROR
↓
minimum hint
↓
retry
↓
3 × transfer verification
↓
relative_clause.pointer = VERIFIED
↓
word.root.rupt
↓
VERIFIED
↓
DONE
↓
Dashboard / Repair / Topology / Assets 投影
```

该闭环是 V3 唯一正确性主链，不允许为了扩 Product Shell 修改 reducer 规则。

---

# 7. V3 停止条件

以下条件已全部达到：

1. PRD V3 能力母表完整；
2. Product Shell 七个核心页面存在；
3. Baseline Diagnostic 产品入口存在；
4. Preview/Runtime 边界有机器契约；
5. Gold Loop 仍闭环；
6. Session Restore 与 `/xueba/` 子路径安全；
7. GitHub Test SUCCESS；
8. GitHub Docker SUCCESS；
9. RUN_EVIDENCE 已记录验证 HEAD 与 CI。

因此当前判定：

```text
PRD V3.0 Development = DONE
```

最终仍需通过文档收敛后的 PR CI 和合并后的 `main` CI，作为 Git 交付门禁；若其中任何一步失败，状态自动退回 NOT DONE 并继续修复。

公网 Deployment、Release、生产 Rollback 属于部署闭环；如果没有可用公网目标，保持 `BLOCKED_EXTERNAL`，不能伪造完成。

---

# 8. V3 之后

V3 完成后停止继续扩大 Product Shell。下一阶段只允许沿真实 Content Node 推进：

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

每个节点必须走：

```text
Content / Runtime Evidence
→ Tests
→ Manifest preview/locked → limited/live
→ CI
→ Evidence
```
