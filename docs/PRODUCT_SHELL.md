# 文科实验室 Product Shell 工程文档｜V1.0

> 对应 PRD：V3.0 完整产品框架版  
> 日期：2026-08-11  
> 原则：完整产品框架存在；只有当前 MVP 内容可以真实改变学习状态。

---

# 1. 系统层

## 1.1 目标

把原来的 Gold Loop 单页运行器升级成完整文科实验室产品外壳，同时保持 Learning Runtime 不变。

系统分成两个明确层次：

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

职责：统一维护产品能力、状态、文案和课程拓扑。

能力状态：

```text
live
limited
preview
locked
```

禁止把功能清单散落硬编码到多个页面。

当前 Manifest 必须至少包含：

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

所有历史功能都必须有产品入口。

点击行为：

- `gold_loop` → 进入真实 Learning Stage；
- `repair` → 进入 Repair；
- `assets` → 进入 Assets；
- `preview / locked` → 进入只读 Capability Preview。

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

只展示：

- 课程；
- Product Shell 版本；
- Learning Agent 当前状态；
- Session 摘要；
- AI OFF / Deterministic Core 状态。

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

Product Shell 不允许增加第二套前端状态机。

遇到 `409 state_conflict`：重新拉取服务器状态。

网络失败：只重试原 Command。

---

# 5. 静态门禁

`scripts/check_static.py` 除原 Gold Loop Token 外，还必须检查：

```text
product-manifest.json
Dashboard
Today
Lab
Repair
Topology
Assets
Profile
```

并检查历史产品能力仍存在于 Manifest：

```text
MECE
5 Whys
指令流转
物理还原
错题归因
错一订三
逻辑解谜
逻辑组件库
学习效果报告
```

这条门禁防止后续版本再次因 MVP 收缩把完整产品能力删掉。

---

# 6. 验收

Product Shell V1 必须满足：

1. 首屏不再出现“只有一个 Demo”的产品感；
2. 用户可以理解文科实验室完整功能结构；
3. 旧版已定义能力全部至少有展示入口；
4. LIVE / LIMITED / PREVIEW / LOCKED 清晰；
5. PREVIEW 页面不调用学习 Mutation；
6. 当前 Gold Loop 从 Dashboard / Today / Lab 均可进入；
7. Session 刷新恢复仍成立；
8. Gold Loop 完成后 Dashboard / Repair / Topology / Assets 能投影真实结果；
9. 后端学习规则零修改；
10. pytest / Smoke / Static / JS / Docker Runtime 全绿。

---

# 7. 后续扩展规则

以后新增真实内容时：

```text
先新增 Content / Runtime Evidence
↓
再把 Manifest 状态
preview / locked
升级为 limited / live
```

禁止先把页面标为 LIVE，再补真实内容。

完整框架长期保持稳定，内容能力按节点逐步填充。