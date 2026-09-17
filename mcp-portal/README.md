# 制造能力平台 - 统一主门户框架 (MCP-Portal)

专为工业制造数字化打造的**统一应用主门户与微前端多标签页工作台**。

---

## 🌟 核心职责与架构

1. **统一单点登录 (SSO)**：
   - 用户在门户登录一次（`http://localhost:3000/login`），通过服务底座（`mcp-base / 8000`）集中鉴权，自动获取并透传 JWT 身份凭据。
2. **动态多级业务目录树**：
   - 自动与底座同步全平台业务菜单（MDM 主数据、MES 生产执行、WMS 仓储物流、QC 质量管理、DEV 设备工装、Base 平台治理）。
3. **微服务无缝页面挂载与多标签页 (Multi-Tabs)**：
   - 支持同时打开多个微服务页面并在顶部 Tab 自由切换，页面状态不丢失；
   - 自动匹配微服务注册表中的 Base URL 并完成页面调度。
4. **服务自注册与健康联动**：
   - 门户服务启动时自动向底座 `mcp-base` 登记注册，接受底座的心跳健康监测。

---

## 🚀 启动与访问

```powershell
.\run_portal.ps1
```

* **🖥️ 统一数字化工作台**：[http://localhost:3000](http://localhost:3000)
* **🔐 统一登录页面**：[http://localhost:3000/login](http://localhost:3000/login) （账号 `superadmin` / 密码 `123456`）
* **🩺 健康检查接口**：[http://localhost:3000/health](http://localhost:3000/health)
