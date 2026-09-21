# MagicStarPlatform - 开放服务底座 (平台治理与认证中心)

专为微服务生态打造的**轻量、高效、开放式微服务基础底座**。该底座由 **Python (FastAPI + SQLAlchemy 2.0)** 构建，支持预置 `superadmin` 集中管理、多租户与 IAM 角色分配、微服务应用接入 (如 `dreamclip-service`) 与异步健康心跳实时探测。

---

## 🌟 核心特性

1. **预置 SuperAdmin 与 RBAC 权限中心**：
   - 预置 `superadmin` 最高特权管理员账号（初始密码 `123456`）；
   - 支持多角色（超管、租户管理员、车间操作员）与动态菜单树控制。
2. **多企业租户管理中心**：
   - 预置 5 家企业租户档案（四川康利光学、北方夜视昆明、北方夜视西安、四川新筑交科、四川新锚机电）；
   - 支持动态开通租户、配置个性化 JSON 扩展属性。
3. **异构微服务接入与健康心跳治理**：
   - **技术栈无关**：支持对接 Java (Spring Boot)、Python (FastAPI/PyTorch)、Go (Golang IoT)、Node.js (Vue)、C# (.NET) 等任何语言开发的独立微服务；
   - **主动/被动注册**：支持第三方微服务启动时调用 `/api/v1/microservices/register` 主动上报，或由超管在后台录入；
   - **异步健康心跳探测**：后台协程每 20s 自动轮询探测已接入微服务的 `/actuator/health` 或 `/health`，统计响应毫秒数与在线/异常/离线状态。
4. **平台通用字典与全局配置参数**：
   - 支持行业分类、技术栈、微服务业务分类等多维字典维护；
   - 支持系统运行参数在线动态修改。
5. **开箱即用原生 API 文档**：
   - 原生内置 Swagger UI (`/docs`) 与 ReDoc 规范文档 (`/redoc`)。

---

## 🚀 快速启动

### 方式 1：双击批处理脚本
双击运行根目录下的 `run_server.bat`。

### 方式 2：PowerShell 运行
```powershell
.\run_server.ps1
```

### 方式 3：Python 命令行运行
```bash
python run_server.py
```

启动成功后，浏览器访问：
* **🖥️ 超级管理员控制台**：[http://localhost:8000](http://localhost:8000)
* **🔐 控制台登录页**：[http://localhost:8000/login](http://localhost:8000/login) （账号 `superadmin` / 密码 `123456`）
* **📖 原生 Swagger API 文档**：[http://localhost:8000/docs](http://localhost:8000/docs)
* **📑 ReDoc 接口规范**：[http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 🔌 异构微服务接入指南

任何新微服务（无论是 Java、Python、Go 还是 C#）启动后，只需向底座发起一个 HTTP 注册请求：

```http
POST http://localhost:8000/api/v1/microservices/register
Content-Type: application/json

{
  "service_code": "mcp-service-mes",
  "service_name": "生产执行微服务 (MES)",
  "tech_stack": "JAVA",
  "category": "MES",
  "base_url": "http://127.0.0.1:8081",
  "health_url": "/actuator/health",
  "docs_url": "/doc.html",
  "description": "车间工单排产、报工与质量追溯服务"
}
```
注册成功后，底座会自动开始心跳探测，并在大盘中显示该服务的运行状态与接口文档链接。
