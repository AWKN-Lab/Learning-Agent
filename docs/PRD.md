# 文科实验室 H5 产品需求文档（PRD）｜V2.3 第一性原理版

> 项目：AWKN-Lab/Learning-Agent  
> 版本：V2.3  
> 日期：2026-08-11  
> MVP：高一英语 Unit 4  
> 产品形态：移动端 H5 + Learning Agent

---

# 1. 产品定义

文科实验室是一套面向理科思维型高中生的**学习调试系统**。

系统把文科学习任务转成可观察的逻辑过程：

```text
知识规则
+
题目条件
+
学生操作
=
学生当前推理模型
```

当学生出错时，系统完成：

```text
Expected Logic
vs
Student Logic
↓
Difference
↓
Logic Bug
↓
最小干预
↓
重新推导
↓
迁移验证
↓
更新学习状态
```

产品核心价值：**看到学生怎么想，定位逻辑关系在哪一步断裂，用最小提示促使学生自己修复，再用新问题验证修复是否成立。**

---

# 2. 第一性目标

MVP 不以“AI 能解释题目”作为完成标准。

唯一核心目标：

> 对一个明确知识节点，系统能够可靠完成“观察 → 诊断 → 干预 → 验证 → 更新”。

首个 Gold Node：

```text
relative_clause.pointer
```

首个 Gold Loop：

```text
任务
↓
学生错误
↓
pointer_error
↓
最低级提示
↓
学生重试
↓
3 道单变量迁移题
↓
验证成功
↓
VERIFIED
```

---

# 3. 产品核心能力

## 3.1 Task Model

把题目表示为显式逻辑模型。

示例：

```text
The ruins in which they were trapped were dangerous.
```

内部结构：

```text
main_clause
├─ subject: the ruins
└─ predicate: were dangerous

relative_clause
├─ antecedent: the ruins
├─ relative_word: which
├─ prep: in
└─ pointer: which → ruins
```

Task Model 是判定学生操作对错的基准。

## 3.2 Evaluator

学生通过点击、连线、框选等操作表达自己的逻辑模型。

Evaluator 比较：

```text
Expected Model
vs
Student Model
```

输出明确差异，例如：

```text
POINTER_ERROR
CONSTRAINT_OMISSION
VARIABLE_SUBSTITUTION
CAUSAL_CHAIN_BREAK
OVERLOAD
```

## 3.3 Intervention Policy

系统根据错误和尝试次数决定最低必要提示。

提示阶梯：

```text
P0 独立作答
P1 指出错误位置
P2 给结构提示
P3 给关系提示
P4 半步推导
P5 完整解释
```

规则：

- 第一次错误禁止直接 P5；
- 每次最多升级一级；
- 完整解释后仍必须安排迁移验证。

## 3.4 Transfer Verification

“学生说懂了”不计为修复成功。

同一知识节点必须进入新题验证：

```text
原题错误
↓
干预
↓
表层不同、底层变量相同的新题
↓
验证
```

MVP 默认 3 道单变量扰动题。

## 3.5 Learner State

P0 使用可解释状态：

```text
UNKNOWN
LEARNING
WEAK
PATCHING
VERIFIED
REVIEW_DUE
```

不使用缺乏数据依据的伪精确 mastery 小数作为产品结论。

---

# 4. Learning Agent 定义

对外称 Learning Agent，P0 内核采用轻量 `LearningController`。

职责仅包含：

```text
当前在哪个状态
+
下一步执行什么动作
```

P0 不需要自由规划。

主状态：

```text
TASK
ANSWER
HINT
RETRY
VERIFY
DONE
```

随着真实需求增加再扩展。

---

# 5. AI 边界

系统主干必须在 AI 关闭时仍然成立。

核心结构：

```text
Deterministic Core
+
Generative Enhancement
```

LLM P0 只进入：

1. Explanation：把已确定逻辑结构转换成学生可理解语言；
2. Variant Candidate Generation：生成候选变式，必须经过确定性验证；
3. Ambiguous Diagnosis：规则无法确定时提供辅助诊断。

LLM 不负责：

- 决定题目标准答案；
- 自由修改知识规则；
- 直接决定长期学习状态；
- 绕过验证层写入 VERIFIED。

---

# 6. MVP 范围

P0 必须完成两条能力链：

## A. Grammar Gold Loop

首要证明学习调试闭环成立：

```text
relative_clause.pointer
```

## B. Word Logic Loop

第二条能力证明内核可以复用：

```text
eruption → e + rupt + ion
```

当前暂缓：

- 英语全册；
- 多学科；
- 教师后台；
- 家长端；
- 用户账号体系；
- RAG；
- Neo4j；
- Redis；
- LangGraph；
- pyKT Runtime；
- FSRS Optimizer；
- 多 Agent。

---

# 7. 数据原则

事实来源：

```text
Learning Events
↓
Derived Learning State
↓
Topology View
```

知识拓扑属于状态可视化，不作为事实源。

关键事件：

```text
session_started
task_presented
answer_submitted
error_detected
hint_given
retry_submitted
verification_started
verification_answered
patch_completed
state_updated
next_task_selected
```

所有长期状态必须能够追溯到事件证据。

---

# 8. 成功标准

## 学习成功

对于 `relative_clause.pointer`：

```text
Before: FAIL
Intervention: 最小必要提示
Transfer: 3 个新题达到既定通过条件
After: VERIFIED
```

## 产品成功

- 学生操作能暴露推理过程；
- 不同错误会触发不同处理；
- 提示不会默认泄露答案；
- 修复必须经过迁移验证；
- 学习状态有可追溯证据；
- AI 关闭后 Gold Loop 仍可运行。

## 工程成功

- LIVE / MOCK / FALLBACK 可运行；
- 刷新可恢复当前会话；
- 重复提交幂等；
- 状态跳转受控；
- CI 全绿；
- Release / Deploy / Rollback 均经过真实验证。

---

# 9. 开发顺序

```text
P0-0 Outcome Contract
↓
P0-1 Gold Learning Loop（无 AI）
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
Release → Deploy → Git → Rollback
```

---

# 10. 产品最终闭环

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

文科实验室的核心资产长期沉淀为：

1. Error Model；
2. Intervention Policy；
3. Transfer Verification。

后续扩展到其他英语知识点或其他学科时，优先复用这三层。