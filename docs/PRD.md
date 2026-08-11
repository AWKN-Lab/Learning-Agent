# 文科实验室 H5 产品需求文档（PRD）｜V3.0 完整产品框架版

> 项目：AWKN-Lab/Learning-Agent  
> 版本：V3.0  
> 日期：2026-08-11  
> 当前真实内容范围：高一英语必修一 Unit 4  
> 产品形态：移动端 H5 + Learning Agent  
> 核心原则：**完整产品框架先成立；只有当前 MVP 内容进入真实学习闭环。**

---

# 1. 产品定义

文科实验室是一套面向理科思维型高中生的 **AI 学习调试系统**。

系统把英语等非结构化知识转换成可拆解、可推导、可验证、可积累的逻辑系统，并持续执行：

```text
Observe
↓
Diagnose
↓
Intervene
↓
Verify
↓
Update
```

学生做题时，系统关注的不只是最终选项，还关注学生怎样建立逻辑关系、在哪一步发生错误，以及修复后能否迁移到新问题。

核心价值：

> 看到学生怎么想，定位推理链中断的位置，用最少信息帮助学生自己修复，再用新问题证明修复成立。

---

# 2. V3.0 产品策略

V3.0 明确区分：

```text
完整产品能力地图
≠
当前已经制作好的学习内容
```

因此所有已定义产品能力都保留在信息架构中，但按照真实完成度标记状态。

## 2.1 功能状态

### LIVE

真实可进入、真实产生学习状态和证据。

### LIMITED

能力真实存在，但当前只开放部分内容、节点或流程。

### PREVIEW

保留完整产品入口、说明和页面结构；当前没有真实训练内容，不伪造学习结果。

### LOCKED

能力和内容存在于产品结构中，但需要先完成前置节点或进入后续内容版本。

### PLANNED

仅在路线图展示，不进入当前产品主导航。

---

# 3. 当前 MVP 内容边界

当前只有以下内容能够真实使用：

```text
高一英语必修一
└─ Unit 4 · Natural Disasters
   ├─ Grammar
   │  └─ relative_clause.pointer
   │       主任务
   │       → POINTER_ERROR
   │       → 最小提示
   │       → 重试
   │       → 3 道迁移验证
   │       → VERIFIED
   │
   └─ Vocabulary
      └─ word.root.rupt
           eruption → e + rupt + ion
           → VERIFIED
```

当前任何 PREVIEW / LOCKED 功能都不得生成假成绩、假掌握度或假训练记录。

---

# 4. 完整产品信息架构

```text
文科实验室
│
├─ 首页 Dashboard
├─ 今日学习 Today
├─ 学习实验室 Lab
│  ├─ 逻辑解码
│  ├─ 因果推演
│  └─ 逻辑修复
├─ 学习资产 Assets
├─ 知识拓扑 Topology
└─ 我的 Profile
```

Learning Agent 贯穿上述入口，负责读取当前状态、选择当前动作、解释推荐原因和组织学习闭环。

---

# 5. 首页 Dashboard

状态：**LIVE / LIMITED**

首页是完整产品驾驶舱，不再以“开始 Gold Demo”为产品主入口。

页面展示：

- 今日优先任务；
- 当前课程：高一英语必修一 Unit 4；
- 当前学习状态；
- 待修复节点；
- 待验证节点；
- 最近一次 Logic Bug；
- 最近修复；
- Learning Agent 推荐原因；
- 学习实验室入口；
- 知识拓扑摘要；
- 学习资产摘要。

当前真实数据只来自已有 Gold Loop、Learning Events 和 Session State。

---

# 6. 今日学习 Today

状态：**LIMITED**

目标：把“系统下一步为什么让学生学这个”变成可见产品能力。

完整框架：

```text
今日优先任务
待修复
待验证
到期复习
新知识
下一任务
```

当前实际仅开放：

- `relative_clause.pointer` 修复任务；
- `word.root.rupt` 后续能力；
- 已有 Controller 的 next task 结果。

未来调度优先级：

```text
阻断错误
>
重复错误
>
高脆弱节点
>
到期复习
>
新知识
```

---

# 7. 学习实验室 Lab

学习实验室保留此前所有核心学习能力。

## 7.1 逻辑解码

### A. MECE 结构骨架器

状态：**PREVIEW**

目标：把文章、段落或知识点拆成互斥且完整的逻辑结构。

未来典型交互：

- 文章分层；
- 主干 / 分支识别；
- 结构拖拽；
- 逻辑骨架复原；
- 缺项 / 重复项识别。

### B. 词根逻辑拆解器

状态：**LIMITED**

当前真实内容：

```text
eruption → e + rupt + ion
```

当前真实节点：`word.root.rupt`。

后续扩展：词根、前缀、后缀、构词关系、同源词迁移。

### C. 长难句公式翻译

状态：**LIVE**

当前真实内容：`relative_clause.pointer`。

完整能力框架：

- 主句识别；
- 从句边界；
- 先行词；
- 指向关系；
- 约束关系；
- 变量替换；
- 句子结构公式化。

当前只开放指向关系节点。

---

## 7.2 因果推演

### A. 5 Whys 因果破译机

状态：**PREVIEW**

目标：连续追问“为什么”，从表面事实追到因果链和底层条件。

### B. 指令流转模拟

状态：**PREVIEW**

目标：把语言、历史、生物等知识过程还原成输入 → 状态变化 → 输出的执行链。

### C. 物理逻辑还原

状态：**PREVIEW**

目标：将抽象叙述还原成角色、条件、空间、时间和动作关系。

以上三个入口必须出现在完整产品中，但当前不产生真实训练结果。

---

## 7.3 逻辑修复

### A. 错题归因 / Logic Bug Diagnosis

状态：**LIVE / LIMITED**

完整错误模型：

```text
POINTER_ERROR
CONSTRAINT_OMISSION
VARIABLE_SUBSTITUTION
CAUSAL_CHAIN_BREAK
OVERLOAD
```

当前真实支持：`POINTER_ERROR`。

### B. 错一订三

状态：**LIVE**

产品定义：错误修复后的 Regression Test。

流程：

```text
原题错误
↓
最小干预
↓
重新推导
↓
3 个表层不同、底层变量一致的新题
↓
迁移验证
↓
VERIFIED / 继续修复
```

### C. 逻辑解谜挑战

状态：**PREVIEW**

目标：以挑战、线索、有限提示形式训练结构识别、因果推导和约束推理。

---

# 8. 学习资产 Assets

## 8.1 Bug / 错误档案

状态：**LIVE / LIMITED**

展示：

- 错误类型；
- 出现时间；
- 对应知识节点；
- 触发证据；
- 提示级别；
- 是否完成修复；
- 迁移验证结果。

当前可真实展示 `POINTER_ERROR` 记录。

## 8.2 修复日志

状态：**LIVE**

基于 Learning Events 展示：

```text
发现错误
→ 给出提示
→ 重试
→ 迁移验证
→ PATCHED / VERIFIED
```

## 8.3 学习记录

状态：**LIVE**

显示真实 Session 与 Learning Events，不伪造累计学习天数、分数或题量。

## 8.4 逻辑组件库

状态：**PREVIEW / LIMITED**

用于沉淀学生已经掌握、可复用的认知组件，例如：

- `relative_clause.pointer`；
- `word.root.rupt`；
- 后续结构骨架；
- 因果链；
- 常见约束模式。

当前只允许把真实 VERIFIED 节点展示为已获得组件。

## 8.5 学习效果报告

状态：**PREVIEW**

未来展示：错误变化、迁移成功率、复习表现、节点稳定性。

当前数据量不足，不输出伪精确百分比。

---

# 9. 知识拓扑 Topology

状态：**LIMITED**

事实关系：

```text
Learning Events
↓
Derived Learning State
↓
Topology View
```

拓扑只是状态投影，不作为事实源。

完整课程框架可展示：

```text
English 必修一
└─ Unit 4
   ├─ Vocabulary
   │  ├─ word.root.rupt          LIMITED / VERIFIED when passed
   │  ├─ suffix.ion              LOCKED
   │  └─ word.structure          LOCKED
   │
   ├─ Grammar
   │  └─ relative_clause
   │     ├─ pointer              LIVE
   │     ├─ constraint           LOCKED
   │     └─ substitution         LOCKED
   │
   └─ Reading
      ├─ causal_chain            PREVIEW
      └─ article_structure       PREVIEW
```

节点状态采用可解释枚举：

```text
UNKNOWN
LEARNING
WEAK
PATCHING
VERIFIED
REVIEW_DUE
LOCKED
```

---

# 10. 自适应调度 / Learning Agent

状态：**LIMITED**

对外称 Learning Agent。

当前内核采用轻量 `LearningController`，负责：

```text
当前状态
+
合法下一步
+
当前任务
+
推荐原因
```

当前不需要自由规划。

完整产品未来负责：

- 读取学习状态；
- 识别阻断节点；
- 选择当前学习任务；
- 决定是否提示；
- 决定是否进入修复；
- 决定是否进行迁移验证；
- 更新学习状态；
- 调度下一任务；
- 安排复习。

---

# 11. 我的 Profile

状态：**LIMITED / PREVIEW**

完整框架：

- 当前课程；
- 当前年级；
- 当前单元；
- 学习目标；
- Learning Agent 状态；
- 内容版本；
- 学习设置；
- 数据与隐私说明。

当前不建设完整账号体系，只展示本地 Demo Session 范围的信息。

---

# 12. 基线测试与诊断入口

状态：**PREVIEW**

此前定义的基线诊断能力保留在产品架构中。

未来用于：

```text
初始任务
↓
识别已有能力 / 薄弱节点
↓
初始化学习拓扑
↓
生成首批 Today Tasks
```

当前 MVP 不制作大规模基线题库。

---

# 13. AI 边界

系统主干必须在 AI OFF 时成立。

```text
Deterministic Core
+
Generative Enhancement
```

LLM 只允许增强：

1. Explanation；
2. Variant Candidate Generation；
3. Ambiguous Diagnosis。

LLM 不负责：

- 标准答案最终判定；
- 自由修改知识规则；
- 直接写 VERIFIED；
- 绕过 Transfer Verification；
- 伪造学习资产。

---

# 14. 完整功能状态矩阵

| 一级能力 | 二级功能 | 当前状态 |
|---|---|---|
| 首页 | Dashboard | LIVE / LIMITED |
| 今日学习 | 今日任务 / 待修复 / 下一任务 | LIMITED |
| 逻辑解码 | MECE 结构骨架 | PREVIEW |
| 逻辑解码 | 词根逻辑拆解 | LIMITED |
| 逻辑解码 | 长难句公式翻译 | LIVE |
| 因果推演 | 5 Whys | PREVIEW |
| 因果推演 | 指令流转 | PREVIEW |
| 因果推演 | 物理还原 | PREVIEW |
| 逻辑修复 | 错题归因 | LIVE / LIMITED |
| 逻辑修复 | 错一订三 | LIVE |
| 逻辑修复 | 逻辑解谜 | PREVIEW |
| 学习资产 | Bug / 错误档案 | LIVE / LIMITED |
| 学习资产 | 修复日志 | LIVE |
| 学习资产 | 学习记录 | LIVE |
| 学习资产 | 逻辑组件库 | LIMITED / PREVIEW |
| 学习资产 | 学习效果报告 | PREVIEW |
| 知识拓扑 | 节点 / 依赖 / 状态 | LIMITED |
| Agent | 自适应调度 | LIMITED |
| 诊断 | 基线测试 | PREVIEW |
| 我的 | 课程 / 目标 / 设置 | LIMITED / PREVIEW |

该矩阵是产品能力母表。后续版本只能改变状态或增加能力，不得因为暂未开发而删除既有能力。

---

# 15. V3.0 MVP Product Shell

完整 H5 框架至少具备：

```text
首页
今日学习
学习实验室
逻辑修复
知识拓扑
学习资产
我的
```

所有页面允许展示完整产品框架。

只有标记为 LIVE / LIMITED 且拥有真实 Content / Runtime 支持的入口可以产生学习行为和状态变化。

PREVIEW 页面点击后应明确显示：

- 能力解决什么问题；
- 未来典型交互；
- 当前内容状态；
- 当前可使用的相关能力。

禁止用不可用按钮、假 loading 或虚构结果模拟真实功能。

---

# 16. 当前真实产品闭环

```text
Dashboard
↓
Today
↓
relative_clause.pointer
↓
ANSWER
↓
POINTER_ERROR
↓
最低必要提示
↓
RETRY
↓
3 × Transfer Verification
↓
VERIFIED
↓
word.root.rupt
↓
VERIFIED
↓
Assets / Error Log / Topology 更新
↓
返回 Dashboard
```

这个闭环必须始终保持可运行。

---

# 17. 成功标准

## 产品层

- 用户第一次进入即可理解完整文科实验室由哪些能力组成；
- 当前不可用能力仍有明确产品位置；
- LIVE / LIMITED / PREVIEW / LOCKED 状态清晰；
- 不把 Preview 功能伪装成可用；
- 当前真实学习内容可以从完整产品框架自然进入。

## 学习层

- 能观察学生操作；
- 能定位真实 Logic Bug；
- 能进行最小干预；
- 修复必须经过迁移验证；
- 状态有 Learning Events 证据；
- AI OFF 后核心闭环仍成立。

## 工程层

- Product Shell 不修改已验证的事务与学习内核正确性；
- Session Restore 正常；
- Atomic Command / Receipt / Version 保持；
- CI、Docker Runtime 持续全绿；
- PREVIEW 内容完全由 Product Manifest 驱动，不需要硬编码散落在多个页面。

---

# 18. 后续路线

当前优先级：

```text
V3.0 Product Shell
↓
把现有 MVP Gold Loop 嵌入完整产品
↓
真实 Dashboard / Assets / Topology 投影
↓
再增加新的 Content Node
```

下一批真实内容建议按能力复用价值扩展：

1. `relative_clause.constraint`；
2. 更多词根逻辑节点；
3. MECE Reading Structure；
4. 5 Whys 因果链；
5. 逻辑解谜挑战。

在已有能力变为 LIVE 之前，不删除其 PREVIEW 产品入口。