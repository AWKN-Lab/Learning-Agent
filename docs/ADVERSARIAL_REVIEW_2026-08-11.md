# Learning-Agent 对抗式审查｜2026-08-11

> 审查基线：`ae76b9b2d62576439a9ec69a0a2d5b3be2d9544d`  
> 范围：API、状态机入口、SQLite 幂等、H5、Docker、CI、静态文件边界。  
> 原则：按攻击、并发、崩溃、异常输入、部署错觉逐项破坏，不以既有测试绿灯替代审查。

## 已确认并修复

### P0-1 Docker 构建绿但运行时可能失败

旧镜像设置 `LEARNING_DB_PATH=/data/learning-agent.db`，但没有创建 `/data`，CI 也只 build、不 run。

修复：
- 镜像显式创建并授权 `/data`；
- 以非 root `app` 用户运行；
- 增加 `VOLUME /data`；
- 增加容器 HEALTHCHECK；
- CI 增加真实 `docker run` + health + H5 smoke。

### P0-2 SPA catch-all 吞掉不存在的 API

旧 catch-all `/{full_path:path}` 会把未匹配的 `/api/*` 返回 `index.html`，导致 API 拼写错误表现为 200 HTML。

修复：`api` / `api/*` 永远返回 404，不进入 SPA fallback。

### P0-3 静态文件候选路径缺少根目录约束

旧代码直接使用 `WEB_DIST / full_path`，缺少 `resolve + relative_to` 边界校验。

修复：所有静态候选路径 resolve 后必须仍位于 web root，否则 404。

### P0-4 Mutation 可以省略 event_id

旧 API 的 `event_id` 可选，客户端或脚本省略后会绕开请求幂等契约；旧 smoke 正是无 event_id 跑通。

修复：
- 所有 mutation 强制 `event_id`；
- event_id 必须以当前 session UUID 为命名空间；
- payload 使用严格 Schema、禁止多余字段并限制长度；
- smoke 全链路使用 namespaced event_id。

### P0-5 同 session 并发状态竞争

FastAPI sync endpoint 可能在多个线程中同时读取同一 session snapshot，旧 Controller 的 processed-event 判定不是原子操作。

修复：P0 单进程部署下所有 mutation 由进程级 `RLock` 串行化；增加并发重复请求测试，要求只推进一次。

### P1-1 崩溃窗口检测

当前 core 的 Learning Event 与 Session Snapshot 仍是多次 SQLite 写入。若进程在“request event 已落库、state 尚未保存”的极窄窗口崩溃，直接重放会有重复推进风险。

本轮增加 fail-closed 检测：如果 request event 已存在但 session 未记录 processed_event_id，返回 `409 incomplete_previous_request`，禁止自动重放污染状态。

## 同步安全加固

- 去除跨域 CORS 放开；P0 H5 与 API 同源；
- H5/API 增加 CSP、nosniff、DENY framing、no-referrer、Permissions-Policy；
- API 响应增加 `Cache-Control: no-store`；
- H5 对 localStorage 不可用场景降级；
- `crypto.randomUUID()` 不可用时提供 request-id fallback；
- CI 增加 `pip check`、Python compileall、Docker runtime smoke。

## 新增对抗门禁

- mutation 缺 event_id → 422；
- event_id 非当前 session namespace → 422；
- oversized answer → 422；
- 非法状态跳转 → 409 且不写 event；
- 同 event_id 重放 → NOOP；
- 并发同 event_id → 状态只推进一次；
- 不存在 API → JSON 404，禁止返回 SPA；
- 编码路径越界 → 404；
- 安全响应头必须存在；
- Docker 必须真正启动并通过 health/H5 smoke。

## 仍保留的边界

1. **P0 只支持单 Uvicorn 进程。** 若未来启用多 worker / 多实例，必须把 mutation 串行化升级为 SQLite/数据库事务或 optimistic concurrency control。
2. **Learning Event + Session State 尚未完全单事务提交。** 本轮先 fail-closed，下一阶段如进入真实用户长期使用，应改为单事务 command/receipt 模型并支持 crash recovery。
3. **无账号和网关限流。** 当前 Demo 数据均为模拟学习数据；取得公网部署目标后，应在入口增加速率限制与会话清理策略，再承载公开流量。
4. **SQLite 会持续累积 Demo session。** 比赛短期演示可接受；公网长期运行前增加 TTL/最大容量清理。

## 判定

本轮优先修复会造成“假绿 CI、状态重复推进、API 错误被掩盖、文件边界不明确”的 P0 风险。剩余项均明确限定在单进程、短周期、无实名数据的 DEMO 边界内，不扩张架构来掩盖当前问题。
