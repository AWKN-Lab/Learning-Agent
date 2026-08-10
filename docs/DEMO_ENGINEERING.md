# 文科实验室 H5 DEMO 开发工程文档｜V2.3 第一性原理版

> 项目：AWKN-Lab/Learning-Agent  
> 文档类型：工程母文档  
> 上位依据：`docs/PRD.md`  
> 日期：2026-08-11  
> 目标版本：`v0.1.0-demo`

---

# 1. 系统层：工程目标

P0 只证明一件事：

> 系统能够观察学生的真实操作，定位一个明确逻辑 Bug，实施最小干预，再通过迁移题验证修复成立。

首个 Gold Node：

```text
relative_clause.pointer
```

首个 Gold Loop：

```text
TASK
↓
ANSWER
↓
POINTER_ERROR
↓
HINT
↓
RETRY
↓
VERIFY × 3
↓
VERIFIED
↓
UPDATE STATE
```

P0 工程完成必须同时满足：

```text
AI OFF 可运行
LIVE 可运行
MOCK 可运行
FALLBACK 可运行
```

---

# 2. 系统层：第一性架构

```text
                  H5
                   │
                   ▼
          LearningController
                   │
      ┌────────────┼────────────┐
      ▼            ▼            ▼
 Task Model     Evaluator   Intervention
      │            │            │
      └────────────┼────────────┘
                   ▼
            Transfer Verify
                   │
                   ▼
            Evidence Store
                   │
                   ▼
            Learning State
                   │
                   ▼
              Next Task
```

LLM 不处于主干：

```text
                  LLM
          ┌────────┼─────────┐
          ▼        ▼         ▼
     Explanation Variant  Ambiguous
                 Candidate Diagnosis
```

核心原则：

```text
Deterministic Core
+
Generative Enhancement
```

---

# 3. 系统层：技术选型

## 3.1 Frontend

继续使用：

- Vue 3；
- Vite；
- TypeScript；
- Pinia；
- Vue Router；
- ECharts；
- GSAP / CSS Transition。

P0 不迁移 React / Next.js / SvelteKit。

## 3.2 Backend

P0：

```text
Python 3.12
FastAPI
Pydantic v2
SQLAlchemy 2.x
SQLite
```

推荐 SQLAlchemy 2.x，避免 P0 同时维护 SQLModel / SQLAlchemy 两套习惯。

## 3.3 AI Provider

统一接口：

```python
class LLMProvider(Protocol):
    async def generate(self, request): ...
```

实现：

```text
OpenAICompatibleProvider
OllamaProvider
MockProvider
```

业务代码禁止直接调用具体模型 SDK。

## 3.4 P0 禁止依赖

```text
LangGraph
pyKT Runtime
FSRS Optimizer
LlamaIndex
Chroma
Qdrant
Neo4j
Redis
Kafka
Celery
Kubernetes
Multi-Agent
Full-textbook RAG
OCR
Auth System
Teacher Admin
```

---

# 4. 系统层：仓库结构

目标结构：

```text
Learning-Agent/
├─ README.md
├─ docs/
│  ├─ PRD.md
│  ├─ DEMO_ENGINEERING.md
│  ├─ DEVELOPMENT_PLAN.md
│  └─ FIRST_PRINCIPLES.md
│
├─ apps/
│  ├─ web/
│  │  └─ src/
│  │     ├─ views/
│  │     ├─ components/
│  │     ├─ stores/
│  │     ├─ services/
│  │     └─ types/
│  │
│  └─ api/
│     └─ app/
│        ├─ main.py
│        ├─ controller/
│        ├─ task_models/
│        ├─ evaluator/
│        ├─ intervention/
│        ├─ verification/
│        ├─ state/
│        ├─ events/
│        ├─ providers/
│        ├─ validation/
│        └─ repositories/
│
├─ content/
│  └─ v1.0_g10_english_u4/
│     ├─ manifest.json
│     ├─ tasks.json
│     ├─ grammar.json
│     ├─ roots.json
│     ├─ variants.json
│     └─ topology.json
│
├─ schemas/
│  ├─ learning-event.schema.json
│  ├─ task-model.schema.json
│  ├─ student-model.schema.json
│  ├─ evaluation-result.schema.json
│  ├─ intervention.schema.json
│  ├─ verification-result.schema.json
│  └─ learning-state.schema.json
│
└─ tests/
   ├─ gold_loop/
   ├─ evaluator/
   ├─ intervention/
   ├─ verification/
   ├─ api/
   └─ e2e/
```

不提前创建空目录。每个目录在对应阶段有真实代码时建立。

---

# 5. 组件层 A：Outcome Contract

P0 开发第一步不先写数据库 Schema。

先冻结学习结果定义。

Gold Node：

```text
relative_clause.pointer
```

必须定义：

```text
Gold Task
Gold Expected Model
Gold Error
Gold Intervention Ladder
Gold Transfer Set
Gold Pass Criteria
```

建议初始验收：

```text
初始任务 FAIL
↓
最小提示
↓
重试
↓
3 道新题验证
↓
满足预设通过条件
↓
VERIFIED
```

通过条件必须在内容包中显式版本化，不能由 LLM 临时判断。

---

# 6. 组件层 B：Task Model

## 6.1 职责

把每个学习任务表示为机器可比较的逻辑结构。

示例：

```json
{
  "task_id": "rc_pointer_gold_001",
  "node_id": "relative_clause.pointer",
  "prompt": "The ruins in which they were trapped were dangerous.",
  "expected": {
    "antecedent": "the ruins",
    "relative_word": "which",
    "pointer": "which->the ruins"
  }
}
```

## 6.2 原则

- 正确逻辑必须来自受控 Content Pack；
- LLM 不决定标准答案；
- 每个任务必须声明目标知识节点；
- 每个任务必须声明可观察的学生动作。

---

# 7. 组件层 C：Interaction Model

UI 交互的目的不是好看，是暴露学生思维。

P0 支持：

```text
点击
拖动
连线
框选
选择
```

学生动作必须能还原成 `StudentModel`。

例：

```json
{
  "task_id": "rc_pointer_gold_001",
  "action": "link",
  "source": "which",
  "target": "trapped"
}
```

得到：

```text
Student pointer = which → trapped
```

---

# 8. 组件层 D：Evaluator

## 8.1 核心接口

```python
def evaluate(expected_model, student_model) -> EvaluationResult:
    ...
```

## 8.2 输出

```json
{
  "passed": false,
  "error_code": "POINTER_ERROR",
  "node_id": "relative_clause.pointer",
  "expected": "which->the ruins",
  "actual": "which->trapped",
  "confidence": 1.0
}
```

## 8.3 P0 Error Model

```text
POINTER_ERROR
CONSTRAINT_OMISSION
VARIABLE_SUBSTITUTION
CAUSAL_CHAIN_BREAK
OVERLOAD
```

Gold Loop 先真正实现 `POINTER_ERROR`。

其他 Error Code 可定义 Schema，不要求 P0 同时做完全部行为。

## 8.4 门禁

Evaluator 必须独立于：

- Agent；
- LLM；
- Frontend；
- Database。

它必须是可独立单测的确定性函数。

---

# 9. 组件层 E：Intervention Policy

## 9.1 核心接口

```python
def choose_intervention(error, attempts, hint_history) -> Intervention:
    ...
```

## 9.2 提示阶梯

```text
P0 NONE
P1 LOCATION
P2 STRUCTURE
P3 RELATION
P4 PARTIAL_DERIVATION
P5 FULL_EXPLANATION
```

## 9.3 Gold Node 示例

P1：

```text
问题出在 which 的指向。
```

P2：

```text
先找 which 前面的名词性成分。
```

P3：

```text
which 在这里要回指先行词。
```

P4：

```text
先行词位于 relative clause 前面；把候选名词逐个代回检查。
```

P5：

展示完整逻辑结构，但随后强制进入迁移验证。

## 9.4 原则

- 初错不直接给答案；
- 每次最多升级一级；
- 同一级提示不能无限重复；
- P5 后仍不能直接 VERIFIED。

---

# 10. 组件层 F：Transfer Verification

## 10.1 定义

修复成功必须由新任务证据支持。

```text
Original Error
↓
Intervention
↓
Transfer Set
↓
Verification Result
```

## 10.2 Gold Transfer Set

首版固定 3 道人工审核变式。

要求：

- 表面句子不同；
- 目标节点相同；
- 一次只扰动一个关键变量；
- 答案唯一；
- 不复制原题；
- 可确定性判定。

## 10.3 AI 生成

后续 LLM 可以生成 Candidate，但只能走：

```text
LLM Candidate
↓
Schema
↓
Grammar Rule
↓
Target Node Check
↓
Answer Uniqueness
↓
Scope Check
↓
PASS 后入题
```

---

# 11. 组件层 G：Evidence Model

Gold Loop 跑通后再冻结数据 Schema。

核心事实类型：

```text
LearningEvent
TaskAttempt
EvaluationResult
Intervention
VerificationResult
LearningStateChange
```

## 11.1 LearningEvent

建议字段：

```text
event_id
schema_version
user_id
session_id
task_id
node_id
event_type
attempt_id
correct
error_code
hint_level
time_ms
payload
content_pack_version
policy_version
timestamp
```

## 11.2 幂等

`event_id` 与 `attempt_id` 必须可去重。

浏览器重试不得重复：

- 计入错误；
- 增加提示次数；
- 修改学习状态。

---

# 12. 组件层 H：Learning State

P0 状态：

```text
UNKNOWN
LEARNING
WEAK
PATCHING
VERIFIED
REVIEW_DUE
```

状态更新只能由明确事件触发。

示例：

```text
POINTER_ERROR
→ WEAK

开始迁移验证
→ PATCHING

Transfer Pass
→ VERIFIED
```

P0 不输出没有足够数据依据的小数 mastery / fragility 作为正式学习结论。

如果为内部调试保留 score，必须标记为 heuristic，并带 policy_version。

---

# 13. 组件层 I：LearningController

对外产品名保持 Learning Agent。

P0 内部主控：

```text
LearningController
```

## 13.1 六状态模型

```text
TASK
ANSWER
HINT
RETRY
VERIFY
DONE
```

## 13.2 主逻辑

```python
if state == TASK:
    present_task()

elif state == ANSWER:
    result = evaluate()
    if result.passed:
        enter_verify_if_needed()
    else:
        enter_hint()

elif state == HINT:
    intervention = choose_intervention()

elif state == RETRY:
    result = evaluate()

elif state == VERIFY:
    result = verify_transfer()

elif state == DONE:
    update_state_and_select_next()
```

P0 不做开放式自主 Planning。

---

# 14. API 设计

H5 正式主接口收敛为：

```text
POST /api/v1/session/start
POST /api/v1/learning/step
GET  /api/v1/session/{session_id}
GET  /api/v1/health
```

## 14.1 learning/step

输入：

```json
{
  "session_id": "s1",
  "event": "ANSWER_SUBMITTED",
  "attempt_id": "a1",
  "payload": {
    "source": "which",
    "target": "trapped"
  }
}
```

输出：

```json
{
  "state": "HINT",
  "evaluation": {
    "passed": false,
    "error_code": "POINTER_ERROR"
  },
  "intervention": {
    "level": "P1",
    "message": "问题出在 which 的指向。"
  },
  "next_expected_event": "RETRY_SUBMITTED",
  "trace_id": "..."
}
```

客户端不得直接修改学习状态。

---

# 15. AI Enhancement

AI 接入发生在无 AI Gold Loop 通过之后。

## 15.1 Explanation

输入已确认结构，输出自然语言说明。

## 15.2 Variant Candidate

只生成候选题，不直接进入正式验证集。

## 15.3 Ambiguous Diagnosis

只有规则置信度不足时调用。

低置信度 AI 诊断不能直接改变长期状态。

## 15.4 Runtime Scope Guard

静态 Content Pack 在构建期校验。

运行期 Grade Scope Guard 只拦截动态 AI 内容，避免所有路径重复做不必要检查。

---

# 16. Content Pack

```text
content/v1.0_g10_english_u4/
```

首期包含：

```text
Gold grammar task
Gold transfer set
Unit4 roots
Word task: eruption
必要 grammar rules
knowledge nodes
knowledge edges
```

公开仓库优先使用自编、模拟或授权内容。

---

# 17. H5 Vertical Slice

第一版只要求四个核心页面：

```text
/today
/task
/repair
/result
```

## /today

显示：

- 当前学习节点；
- 为什么出现这个任务；
- 当前状态。

## /task

承载真实操作，输出 StudentModel。

## /repair

显示当前错误位置、提示、重试、迁移验证。

## /result

显示：

- 本轮修复结果；
- 支持结果的验证证据；
- 下一任务。

等垂直切片完成后再拆出 `/lab/word`、`/topology`、`/assets`。

---

# 18. 第二条能力：Word Logic

Gold Grammar Loop 稳定后接：

```text
eruption
→ e + rupt + ion
```

目的：验证同一系统内核可以服务另一种学习任务。

Word Task 同样必须存在：

```text
Task Model
Student Action
Evaluator
Intervention
Transfer Verification
Learning State
```

禁止为了展示丰富度做一堆只可观看、不可诊断的动画。

---

# 19. Topology

Topology 的数据流：

```text
Learning Events
↓
Learning State
↓
Topology Projection
```

P0 SQLite 表即可：

```text
knowledge_nodes
knowledge_edges
user_node_state
```

前端 ECharts 展示。

Topology 不是事实源。

---

# 20. 测试体系

## 20.1 Gold Loop Unit Test

至少覆盖：

- 正确 pointer；
- 错误 pointer；
- 第一次错误提示 P1；
- 连续错误提示升级；
- 迁移题通过；
- 迁移题失败；
- P5 后仍需验证。

## 20.2 API Test

覆盖：

- session start；
- answer submit；
- retry；
- verify；
- 重复 attempt_id；
- 非法状态跳转。

## 20.3 E2E

E2E-001：AI OFF Gold Loop  
E2E-002：LIVE 模型增强成功  
E2E-003：LLM timeout → FALLBACK  
E2E-004：低置信度 AI 诊断不污染状态  
E2E-005：WAIT/REPAIR/VERIFY 刷新恢复  
E2E-006：重复提交幂等  
E2E-007：客户端越级更新状态被拒绝。

---

# 21. 可观测性

每次学习步骤记录 Trace：

```text
trace_id
session_id
state_before
event
state_after
evaluation
intervention
provider
mode
duration_ms
ok
error
```

建立：

```text
docs/RUN_EVIDENCE.md
```

正式演示必须能证明一条链是真实 LIVE、MOCK 或 FALLBACK。

---

# 22. CI

顺序：

```text
Lint
↓
Type Check
↓
Gold Content Validation
↓
Evaluator Unit Test
↓
Intervention Unit Test
↓
Verification Unit Test
↓
State Test
↓
API Test
↓
Frontend Build
↓
E2E
↓
Demo Smoke
```

任何门禁失败停止 Release。

---

# 23. Release / Deploy / Git / Rollback

发布链：

```text
CI
↓
Release
↓
Deploy
↓
Git 固化
↓
Rollback 验证
```

目标版本：

```text
v0.1.0-demo
```

Release 记录：

```text
commit
schema_version
content_pack_version
policy_version
provider
CI result
E2E result
known limitations
```

Rollback 必须真实演练，不能只写文档。

---

# 24. 工程完成定义

只有下列闭环全部真实成立才算 P0 完成：

```text
Outcome Contract
↓
Gold Task
↓
Observable Student Action
↓
Deterministic Evaluation
↓
Minimal Intervention
↓
Retry
↓
Transfer Verification
↓
Evidence Event
↓
Learning State Update
↓
Next Task
↓
AI OFF / LIVE / MOCK / FALLBACK
↓
E2E
↓
CI
↓
Release
↓
Deploy
↓
Git
↓
Rollback
↓
Run Evidence
```

到这里停止扩功能，用真实学生操作和比赛演示验证产品。