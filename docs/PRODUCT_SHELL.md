# 文科实验室 Product Shell 工程文档｜V1.1 / PRD V3.0

> 对应 PRD：V3.0 完整产品框架版  
> 日期：2026-08-11  
> 原则：完整产品框架存在；只有当前 MVP 内容可以真实改变学习状态。

---

# 1. 系统层

## 1.1 目标

把原来的 Gold Loop 单页运行器升级成完整文科实验室产品外壳，同时保持 Learning Runtime 的正确性主链不变。

```text
Product Shell
完整导航 / 页面 / 能力地图 / 状态展示
        │
        ▼
Learning Runtime
当前真实 Gold Loop / Learning Events / State
```

Product Shell 可以展示未来能力，但不能伪造训练结果。

## 1.2 核心边界

```text
PREVIEW / LOCKED
→ 只读展示
→ 不调用 learning/step
→ 不写 Learning Events
→ 不改变 Session State

LIVE / LIMITED + 有真实 Runtime
→ 才能进入学习流程
```

现有事务、Receipt、Version、Token、TTL、Rate Limit、Replay 均不因 Product Shell 改造而改变。

## 1.3 V3 Machine Contract

`apps/web/product-manifest.json` 必须显式声明：

```text
contract.prd_version = 3.0
contract.product_shell_version
contract.runtime_scope
contract.allowed_runtime_nodes
contract.preview_can_mutate_learning_state = false
contract.shell_pages
```

当前允许进入学习 Runtime 的节点只有：

```text
relative_clause.pointer
word.root.rupt
```

任何 PREVIEW capability 都不得绑定 `action` 或 runtime `node`。

---

# 2. 组件层

## 2.1 App Shell

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

移动端主导航：

```text
首页
今日
实验室
修复
拓扑
资产
```

`我的`从顶部入口进入。

## 2.2 Product Manifest

文件：

```text
apps/web/product-manifest.json
```

职责：统一维护产品能力、状态、文案、课程拓扑和 V3 产品契约。

能力状态：

```text
live
limited
preview
locked
```

禁止把产品能力母表散落硬编码到多个页面。

当前 Manifest 必须包含：

### 逻辑解码

- MECE 结构骨架器；
- 词根逻辑拆解；
- 长难句公式翻译。

### 因果推演

- 5 Whys；
- 指令流转；
- 物理还原。

### 逻辑修复

- 错题归因；
- 错一订三；
- 逻辑解谜挑战。

### 基线诊断

- 基线测试与诊断。

### 学习资产

- 错误档案；
- 修复日志；
- 学习记录；
- 逻辑组件库；
- 学习效果报告。

## 2.3 Runtime Projection

Product Shell 只投影真实状态：

```text
Session State
Learning Events
        ↓
Dashboard
Repair
Topology
Assets
```

当前真实节点：

```text
relative_clause.pointer
word.root.rupt
```

其他节点只能显示 `preview / locked`。

## 2.4 Profile Contract

当前没有账号体系。

Manifest 保留：

```text
learning_goal
content_version
learning_settings
data_privacy
```

页面只展示当前 Demo Session 范围内的真实信息，不生成假累计数据。

---

# 3. 模块层

## 3.1 Dashboard

展示：

- 当前课程；
- 今日优先任务；
- pointer / rupt 真实状态；
- Learning Events 数量；
- 最近 Logic Bug；
- 学习实验室能力入口；
- Topology / Assets 摘要。

不得构造虚假完成率。

## 3.2 Today

显示：

```text
当前任务
→ 下一真实能力
→ 后续锁定能力
```

当前 only-live path：

```text
relative_clause.pointer
↓
word.root.rupt
```

## 3.3 Lab

所有 PRD V3 能力必须有产品入口。

点击行为：

- `gold_loop` → 进入真实 Learning Stage；
- `repair` → 进入 Repair；
- `assets` → 进入 Assets；
- `preview / locked` → 进入只读 Capability Preview。

基线诊断当前为 PREVIEW，因此只展示产品定义和未来交互，不生成诊断结果。

## 3.4 Repair

从真实 Events 读取：

```text
error_diagnosed
hint_given
patch_completed
```

当前真实错误：`POINTER_ERROR`。

其余错误类型只展示框架状态。

## 3.5 Topology

数据关系：

```text
Product Manifest 定义课程节点框架
+
Session State 提供当前真实节点状态
```

Runtime 节点：读取真实状态。

非 Runtime 节点：固定 Preview / Locked，不产生学习事实。

Manifest 中 `status = runtime` 的节点集合必须与 `contract.allowed_runtime_nodes` 完全一致。

## 3.6 Assets

真实数据来源：Learning Events。

当前可生成：

- 错误档案；
- 修复日志；
- 学习记录；
- VERIFIED 逻辑组件。

学习效果报告保持 Preview，直到真实数据量满足要求。

## 3.7 Profile

当前没有账号体系。

只展示真实可解释信息：

- 课程；
- Product Shell 版本；
- Learning Agent 当前状态；
- Session 摘要；
- 内容范围；
- AI OFF / Deterministic Core 状态；
- 数据边界说明。

---

# 4. Learning Runtime 保持不变

真实学习仍使用：

```http
POST /api/v1/session/start
GET  /api/v1/session/{id}
POST /api/v1/learning/step
```

Mutation 继续携带：

```text
X-Session-Token
command_id / event_id
expected_version
```

Product Shell 不允许增加第二套前端学习状态机。

遇到 `409 state_conflict`：重新拉取服务器状态。

网络失败：只重试原 Command。

---

# 5. 静态与自动门禁

`scripts/check_static.py` 必须检查：

```text
Product Manifest 可解析
PRD V3 contract 存在
Product Shell 七页存在
子路径 URL 安全
V3 功能母表完整
Preview 不绑定 Runtime
Runtime Node 集合精确
Assets 状态矩阵精确
Profile Contract 存在
```

`tests/test_product_v3_contract.py` 再从 pytest 层验证：

1. V3 Shell Contract；
2. Capability Matrix；
3. Preview 不能进入 Learning Runtime；
4. Runtime Node 只能来自允许集合；
5. Profile 与 Baseline Framework 持续存在。

这两道门禁防止：

- MVP 收缩误删产品能力；
- PREVIEW 假装 LIVE；
- 新节点无 Evidence 就进入 Runtime；
- Product Shell 与 Runtime 状态真相漂移；
- `/xueba/` 子路径再次被根绝对 URL 破坏。

---

# 6. 验收

Product Shell V3 必须满足：

1. 首屏不再出现“只有一个 Demo”的产品感；
2. 用户可以理解文科实验室完整功能结构；
3. PRD V3 已定义能力全部至少有展示入口；
4. LIVE / LIMITED / PREVIEW / LOCKED 清晰；
5. PREVIEW 页面不调用学习 Mutation；
6. 当前 Gold Loop 从 Dashboard / Today / Lab 均可进入；
7. Session 刷新恢复仍成立；
8. Gold Loop 完成后 Dashboard / Repair / Topology / Assets 能投影真实结果；
9. 基线测试与诊断入口存在但保持 PREVIEW；
10. 后端学习规则零修改；
11. pytest / Smoke / Static / JS / Docker Runtime 全绿。

---

# 7. 后续扩展规则

以后新增真实内容时：

```text
先新增 Content / Runtime Evidence
↓
补测试
↓
再把 Manifest 状态
preview / locked
升级为 limited / live
```

禁止先把页面标为 LIVE，再补真实内容。

完整框架长期保持稳定，内容能力按节点逐步填充。