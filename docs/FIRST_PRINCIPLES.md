# 文科实验室｜第一性原理重构决策

> 日期：2026-08-11  
> 状态：Accepted  
> 影响范围：PRD、工程架构、MVP、开发顺序、测试、AI 边界

---

# 1. 原始问题

放下既有 Agent 框架、开源项目架构、教育产品习惯和比赛展示习惯后，只保留用户真实目标：

> 学生为什么做错？系统能否找到推理链中断的具体位置，用最少的信息帮助他自己修复，并通过新题证明他真的会了？

因此产品主循环定义为：

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

---

# 2. 核心判断

## 2.1 文科实验室本质

文科实验室是一套学习调试系统。

类比软件调试：

```text
Expected Logic
vs
Student Logic
↓
Diff
↓
Logic Bug
↓
Patch
↓
Regression Test
```

## 2.2 产品核心资产

长期核心资产收敛为：

1. Error Model：什么学生行为代表什么逻辑 Bug；
2. Intervention Policy：出现该 Bug 时最少应该告诉什么；
3. Transfer Verification：如何证明该 Bug 已经修复。

通用 LLM 的解释能力不是核心壁垒。

---

# 3. 对旧方案的修正

## 修正 A：Agent 降级为 LearningController

P0 不围绕开放式 Agent Planning 建设。

对外仍称 Learning Agent，内部只回答：

```text
当前处于什么状态？
下一步执行什么动作？
```

P0 状态先压缩为：

```text
TASK
ANSWER
HINT
RETRY
VERIFY
DONE
```

## 修正 B：不从 Data Contract 开始

旧顺序：

```text
Data Contract → Content → Tools → Agent
```

新顺序：

```text
Outcome Contract
→ Gold Learning Loop
→ Interaction
→ Evidence Model
→ Controller
```

原因：先观察真实产品行为，再冻结数据，降低凭空设计 Schema 的风险。

## 修正 C：无 AI 闭环先行

第一条学习闭环必须在 AI OFF 时成立。

```text
固定 Task Model
+
确定性 Evaluator
+
固定 Intervention Ladder
+
审核 Transfer Set
```

如果这条链无法让学生完成“错误 → 修复 → 验证”，增加 LLM 没有价值。

## 修正 D：LLM 移出主干

主架构：

```text
Deterministic Core
+
Generative Enhancement
```

LLM 只负责：

- Explanation；
- Variant Candidate；
- Ambiguous Diagnosis。

## 修正 E：Tool Registry 推迟

P0 不需要为了 Agent 形式把所有业务函数包装成 Tool。

先建立五个原子能力：

```text
Task Model
Evaluator
Intervention
Transfer Verification
Learning State
```

出现多学科、多执行器、多外部系统后再评估正式 Tool Registry。

## 修正 F：Topology 降级为 Projection

事实源：

```text
Learning Events
```

派生：

```text
Learning State
```

显示：

```text
Topology View
```

Topology 不作为事实源。

## 修正 G：Grade Scope Guard 分层

静态 Content Pack 在构建期完成范围和版权校验。

只有动态 AI 内容需要运行时 Scope Guard。

这样减少重复运行逻辑。

## 修正 H：P0 不做伪精确知识评分

使用：

```text
UNKNOWN
LEARNING
WEAK
PATCHING
VERIFIED
REVIEW_DUE
```

不向用户展示缺乏数据依据的 mastery=0.xxx / fragility=0.xxx。

---

# 4. 首个 Gold Loop

知识节点：

```text
relative_clause.pointer
```

Gold Task：

```text
The ruins in which they were trapped were dangerous.
```

关键结构：

```text
which → the ruins
```

错误示例：

```text
which → trapped
```

诊断：

```text
POINTER_ERROR
```

干预：

```text
P1 LOCATION
→ P2 STRUCTURE
→ P3 RELATION
→ P4 PARTIAL_DERIVATION
→ P5 FULL_EXPLANATION
```

修复成功必须经过新的 pointer 题验证。

---

# 5. 第二条能力

完成 Grammar Gold Loop 后接：

```text
eruption → e + rupt + ion
```

用途：验证同一学习调试内核能否迁移到单词逻辑拆解。

第二条能力仍必须具备：

```text
Task Model
Student Action
Evaluator
Intervention
Transfer Verification
State Update
```

---

# 6. 最终开发路线

```text
P0-0 Outcome Contract
↓
P0-1 Gold Learning Loop（AI OFF）
↓
P0-2 Interaction Model
↓
P0-3 Evidence Model
↓
P0-4 LearningController
↓
P0-5 H5 Vertical Slice
↓
P0-6 AI Enhancement
↓
P0-7 Word Logic Loop
↓
P0-8 Learning State + Topology
↓
P0-9 Reliability / E2E / CI
↓
Release
↓
Deploy
↓
Git
↓
Rollback
```

---

# 7. 解禁原则

以下能力进入 P0 前必须证明它解决了真实阻塞：

```text
LangGraph
RAG
Vector DB
Neo4j
Redis
pyKT Runtime
FSRS Optimizer
Multi-Agent
OCR
Auth
Teacher Admin
```

解禁条件：

1. 当前闭环存在可复现阻塞；
2. 当前最小架构无法解决；
3. 新依赖能直接解决阻塞；
4. 有测试与回退路径；
5. 不破坏 Gold Loop。

---

# 8. 决策结论

所有后续工程选择先回答：

> 它是否让 Observe → Diagnose → Intervene → Verify → Update 更准确、更简单、更可验证？

如果不能，默认不进入 P0。