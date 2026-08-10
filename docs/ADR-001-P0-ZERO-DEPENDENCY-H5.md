# ADR-001｜P0 DEMO 前端采用零依赖 H5

## 状态

Accepted — 2026-08-11

## 问题

Gold Demo 的目标是证明：学生错误可以被观察、定位、最小干预、迁移验证并形成状态更新。Vue/Vite/npm 并不参与这个学习正确性闭环。

实际构建验证中，npm 镜像无法解析 Vue / Vite 依赖，导致“前端工具链”成为 DEMO 可运行性的外部阻塞。

## 决策

P0 DEMO 改为：

```text
HTML
+ ES Module JavaScript
+ CSS
+ FastAPI StaticFiles
```

不需要 npm install，不需要前端编译。

## 保留边界

- API Contract 不变；
- LearningController 不变；
- Learning Events 不变；
- 未来产品化可以重新使用 Vue 3；
- P0 先证明学习闭环和交互价值。

## 验证门禁

```text
node --check apps/web/app.js
python scripts/check_static.py
pytest
python scripts/smoke.py
Docker build
```

## 回退

若后续确认 Vue/Vite 环境稳定且需要组件规模化，再单独建立前端迁移提交；不得修改学习内核契约来迁就前端框架。
