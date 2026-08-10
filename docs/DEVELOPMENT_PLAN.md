# Learning-Agent｜详细开发执行计划 V1.1（第一性原理版）

> 项目：AWKN-Lab/Learning-Agent  
> 目标版本：`v0.1.0-demo`  
> 上位文档：`docs/PRD.md`、`docs/DEMO_ENGINEERING.md`、`docs/FIRST_PRINCIPLES.md`  
> 日期：2026-08-11

---

# 1. 总目标

P0 只完成一条可运行、可验证、可回退的学习修复闭环：

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

最终必须证明：

```text
学生真实操作
↓
系统识别真实逻辑错误
↓
系统给最小必要提示
↓
学生重新推导
↓
新题验证
↓
学习状态改变
↓
下一任务改变
```

---

# 2. 完成定义

以下全部通过才定义为 `v0.1.0-demo` 完成：

- Gold Grammar Loop 在 AI OFF 下可运行；
- LIVE Provider 增强链可运行；
- MOCK 可运行；
- FALLBACK 可运行；
- 页面刷新能恢复 Session；
- 重复提交具有幂等性；
- 客户端无法非法越级修改状态；
- 学习状态可追溯到 Learning Events；
- 第二条 Word Logic Loop 可复用核心内核；
- E2E 全绿；
- CI 全绿；
- Release 成功；
- Deploy Smoke 通过；
- Git 固化；
- Rollback 真实验证；
- `RUN_EVIDENCE.md` 有完整运行证据。

---

# 3. P0-0｜Outcome Contract

## 3.1 目标

冻结“学习真的发生”需要什么证据。

Gold Node：

```text
relative_clause.pointer
```

## 3.2 产出

创建首个内容定义：

```text
content/v1.0_g10_english_u4/
├─ manifest.json
├─ tasks.json
├─ grammar.json
└─ variants.json
```

第一批只要求包含 Gold Loop 必需内容。

## 3.3 Gold Contract

必须明确：

```text
Gold Task
Expected Model
Observable Student Action
Gold Error
Intervention Ladder
Transfer Set
Pass Criteria
```

## 3.4 验收

- 人工可以根据 JSON 完整走一遍流程；
- 不依赖 LLM 得到标准答案；
- 3 道迁移题答案唯一；
- 修复成功条件写死并版本化。

## Gate 0

未通过不得进入 UI / Agent 开发。

---

# 4. P0-1｜Gold Learning Loop（AI OFF）

## 4.1 目标

用纯确定性逻辑完成：

```text
FAIL
→ HINT
→ RETRY
→ VERIFY
→ VERIFIED / NOT_VERIFIED
```

## 4.2 模块

创建：

```text
apps/api/app/
├─ task_models/
├─ evaluator/
├─ intervention/
└─ verification/
```

## 4.3 实现顺序

1. `load_task_model()`；
2. `build_student_model()`；
3. `evaluate()`；
4. `choose_intervention()`；
5. `verify_transfer()`。

## 4.4 单测

必须覆盖：

- 正确 pointer；
- 错误 pointer；
- 第一次错提示 P1；
- 多次错误逐级提示；
- 迁移 3/3 通过；
- 迁移失败；
- P5 后依然需要验证。

## Gate 1

AI OFF 模式下测试全绿，才进入交互。

---

# 5. P0-2｜Interaction Model

## 5.1 目标

确保交互能暴露学生思维，不只收最终答案。

## 5.2 Grammar Gold Interaction

至少支持：

```text
框选从句
选择先行词
which 连线
确认
```

系统必须能生成：

```text
StudentModel
```

示例：

```json
{
  "task_id": "rc_pointer_gold_001",
  "pointer": "which->trapped"
}
```

## 5.3 前端原型

此阶段只做最小 `/task` 页面。

不做：

- Topology；
- Assets；
- 复杂动效；
- 多主题；
- 多单元。

## Gate 2

同一个错误可以通过 UI 操作稳定还原成同一个 StudentModel。

---

# 6. P0-3｜Evidence Model

## 6.1 目标

基于真实 Gold Loop 行为定义数据，不凭空扩张模型。

## 6.2 Schema

创建：

```text
schemas/
├─ learning-event.schema.json
├─ task-model.schema.json
├─ student-model.schema.json
├─ evaluation-result.schema.json
├─ intervention.schema.json
├─ verification-result.schema.json
└─ learning-state.schema.json
```

## 6.3 Learning Events

第一版事件：

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

## 6.4 版本字段

所有关键事实携带：

```text
schema_version
content_pack_version
policy_version
```

## 6.5 幂等字段

```text
event_id
attempt_id
```

## Gate 3

- Contract Test 全绿；
- 重复 attempt 不重复更新；
- 同一 Session 的完整学习过程可从 Events 回放。

---

# 7. P0-4｜Persistence + Learning State

## 7.1 技术

```text
SQLite
SQLAlchemy 2.x
```

## 7.2 表

```text
sessions
learning_events
user_node_state
error_logs
agent_traces
knowledge_nodes
knowledge_edges
```

## 7.3 学习状态

```text
UNKNOWN
LEARNING
WEAK
PATCHING
VERIFIED
REVIEW_DUE
```

## 7.4 重建测试

执行：

```text
清除派生 user_node_state
↓
只读取 learning_events
↓
重建状态
↓
与原结果一致
```

## Gate 4

刷新、进程重启后 Gold Session 仍可恢复。

---

# 8. P0-5｜LearningController

## 8.1 状态

```text
TASK
ANSWER
HINT
RETRY
VERIFY
DONE
```

## 8.2 状态保护

每个状态只接受允许事件。

示例：

```text
ANSWER
接受 ANSWER_SUBMITTED

VERIFY
接受 VERIFICATION_ANSWERED
```

非法状态跳转返回 409 或明确业务错误。

## 8.3 API

实现：

```text
POST /api/v1/session/start
POST /api/v1/learning/step
GET  /api/v1/session/{id}
GET  /api/v1/health
```

## Gate 5

不同学生答案必须产生真实不同路径。

禁止所有用户都被固定脚本强行推进。

---

# 9. P0-6｜H5 Vertical Slice

## 9.1 页面

第一版：

```text
/today
/task
/repair
/result
```

## 9.2 `/today`

显示：

- 当前知识节点；
- 当前状态；
- 为什么安排这个任务。

## 9.3 `/task`

执行真实操作并提交 StudentModel。

## 9.4 `/repair`

显示：

- 错误位置；
- 当前提示级别；
- 重试；
- 迁移验证进度。

## 9.5 `/result`

显示：

- VERIFIED / NOT_VERIFIED；
- 支持结果的验证记录；
- 下一任务。

## Gate 6

人工从首页开始能完整走通 Gold Loop，刷新后不中断。

---

# 10. P0-7｜AI Enhancement

AI 必须在 Gold Loop 稳定后接入。

## 10.1 Provider

```text
OpenAICompatibleProvider
OllamaProvider
MockProvider
```

## 10.2 Explanation

只把确定性结构转成自然语言。

## 10.3 Variant Candidate

AI 输出必须经过：

```text
Schema
→ Grammar Validation
→ Target Node Validation
→ Answer Validation
→ Scope Validation
```

不通过直接丢弃。

## 10.4 Ambiguous Diagnosis

只有规则无法确定时调用。

低置信度输出不能直接改变长期状态。

## 10.5 Fallback

```text
LLM timeout
→ structured retry once
→ local rule
→ reviewed content
```

## Gate 7

LIVE / MOCK / FALLBACK 三种模式均能完成 Gold Loop。

---

# 11. P0-8｜第二条能力：Word Logic

## 11.1 目标

证明学习调试内核可复用到另一个学习任务。

目标：

```text
eruption → e + rupt + ion
```

## 11.2 必须复用

- Task Model；
- Student Model；
- Evaluator；
- Intervention；
- Verification；
- Learning Events；
- Learning State；
- Controller。

## 11.3 禁止

如果为了 Word Loop 必须复制一整套平行框架，先停下来重构公共内核。

## Gate 8

Grammar 与 Word 两种任务共享同一 Controller / Evidence / State 基础。

---

# 12. P0-9｜Topology Projection

有两个真实节点后再做 Topology。

## 数据流

```text
Events
↓
State
↓
Topology View
```

## UI

ECharts 展示：

```text
UNKNOWN
WEAK
PATCHING
VERIFIED
REVIEW_DUE
```

状态旁显示证据摘要，避免只有颜色。

---

# 13. P0-10｜E2E 与可靠性

必须建立以下场景：

## E2E-001

AI OFF 标准 Gold Loop。

## E2E-002

LIVE Provider 成功。

## E2E-003

LLM Timeout → FALLBACK。

## E2E-004

低置信度 AI 诊断不污染 State。

## E2E-005

在 ANSWER / REPAIR / VERIFY 刷新均可恢复。

## E2E-006

重复 attempt_id 只处理一次。

## E2E-007

非法状态跳转被拒绝。

## E2E-008

Word Loop 共享核心内核。

---

# 14. P0-11｜CI

CI 顺序：

```text
Lint
↓
Type Check
↓
Content Validation
↓
Schema Contract Test
↓
Evaluator Test
↓
Intervention Test
↓
Verification Test
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

任何一层失败立即停止。

---

# 15. P0-12｜Release

目标：

```text
v0.1.0-demo
```

Release 必须记录：

```text
commit_sha
schema_version
content_pack_version
policy_version
provider configuration
CI result
E2E result
known limitations
```

---

# 16. P0-13｜Deploy

部署最小依赖：

```text
H5 static build
FastAPI
SQLite
Content Pack
```

部署后 Smoke：

```text
/health
→ session/start
→ complete Gold Loop
→ fallback test
```

---

# 17. P0-14｜Git 固化

发布成功后执行：

```text
确认工作树 clean
确认 Release commit
确认 Tag
确认 README
确认 docs
确认无 secrets
确认内容版权边界
Push
```

提交应保持原子：

```text
feat(gold): add outcome contract and gold content
feat(core): implement deterministic evaluator
feat(intervention): add hint ladder
feat(verification): add transfer verification
feat(events): add evidence model and persistence
feat(controller): add learning controller
feat(web): add H5 vertical slice
feat(ai): add provider enhancements and fallback
feat(word): add word logic vertical slice
feat(topology): add learning state projection
test(e2e): close P0 scenarios
ci: add release gates
```

---

# 18. P0-15｜Rollback

必须真实演练：

```text
部署 v0.1.0-demo
↓
部署一个可控失败版本
↓
Smoke 失败
↓
回滚 v0.1.0-demo
↓
重新 Smoke
↓
成功
```

没有实际 Rollback 证据，不算发布闭环。

---

# 19. 运行证据

建立：

```text
docs/RUN_EVIDENCE.md
```

每次正式验收记录：

```text
commit
release
environment
schema_version
content_pack_version
policy_version
provider
runtime_mode
Gold Loop trace
Fallback trace
E2E result
screenshots/video reference
known issues
```

---

# 20. P0 依赖门禁

默认禁止：

```text
LangGraph
RAG
LlamaIndex
Chroma
Qdrant
Neo4j
Redis
Kafka
Celery
Kubernetes
Multi-Agent
pyKT Runtime
FSRS Optimizer
OCR
Auth
Teacher Admin
```

解禁必须满足：

1. 有真实阻塞；
2. 可复现；
3. 当前最小架构无法解决；
4. 新依赖能直接解决；
5. 有测试和回退；
6. 不破坏 Gold Loop。

---

# 21. 最终闭环

```text
Outcome Contract
↓
Gold Learning Loop
↓
Observable Interaction
↓
Evidence Model
↓
Learning State
↓
LearningController
↓
H5 Vertical Slice
↓
AI Enhancement
↓
Second Capability
↓
Topology Projection
↓
LIVE / MOCK / FALLBACK
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

达到这一状态后停止 P0 扩功能，进入真实学生测试和比赛演示验证。