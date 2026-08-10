# 文科实验室 H5 产品需求文档（PRD）｜V2.2 开源对标增强版

> 完整 PRD 母文档请以仓库后续补充版本为准。

## 产品定位

文科实验室是一款面向理科思维型高中生的 AI 学习 Agent，把英语等非结构化知识转化为可拆解、可推导、可验证、可积累的逻辑系统。

## MVP

- 高一英语
- 必修一 Unit 4 Natural Disasters
- 单词逻辑拆解
- 定语从句结构解算
- 学习 → 作答 → 归因 → 扰动 → 验证 → 拓扑更新 → 下一任务

## V2.2 核心架构决策

1. 保留 Vue H5。
2. 使用 SimpleAgentRuntime + 显式状态机。
3. 新增 Pedagogy Policy 控制提示深度。
4. 新增 Grade Scope Guard 限制知识范围。
5. 新增 Learning Events 作为学习事实数据层。
6. 使用 LLM Provider Adapter 解耦模型。
7. P0 不引入 RAG、向量数据库、图数据库。
8. 为未来 FSRS、pyKT、LangGraph 保留接口。

## Agent 核心链路

```text
读取状态
↓
规划任务
↓
调用 Tool
↓
用户作答
↓
错误归因
↓
错一订三
↓
迁移验证
↓
状态更新
↓
下一任务
```

## P0 顺序

```text
数据契约
↓
Content Pack
↓
Deterministic Tools
↓
Validation / Guard
↓
Learning Events
↓
SimpleAgentRuntime
↓
H5
↓
Demo 闭环
```
