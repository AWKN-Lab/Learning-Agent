# ADR-002｜Product Shell 必须支持子路径部署

> 日期：2026-08-11  
> 状态：ACCEPTED

## 背景

当前文科实验室可能通过反向代理挂载在：

```text
/xueba/
```

而不是域名根目录 `/`。

若前端使用：

```text
/app.js
/style.css
/api/v1/...
/product-manifest.json
```

浏览器会请求站点根目录，绕过 `/xueba/` 前缀。

## 决策

H5 自有资源与同应用 API 使用相对 URL：

```text
app.js
style.css
product-manifest.json
api/v1/session/start
api/v1/session/{id}
api/v1/learning/step
```

因此同一构建可以工作在：

```text
https://example.com/
```

以及经过前缀保留/反向代理映射的：

```text
https://example.com/xueba/
```

## 边界

本决策假定外部入口以带尾部 `/` 的应用目录提供，例如 `/xueba/`。

反向代理负责把外部前缀正确映射到 FastAPI 服务。应用本身不自行信任或推断任意代理前缀。

## 自动门禁

`scripts/check_static.py` 明确验证：

- `index.html` 的 `app.js` / `style.css` 必须是相对路径；
- Product Manifest 必须使用相对请求；
- API 调用不得硬编码 `/api/...` 根绝对路径。

该门禁用于防止本地根路径运行正常、子路径部署失效的回归。