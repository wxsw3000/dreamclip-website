# MagicStarPlatform & DreamClip 微服务互动平台

一套基于 **平台底座 (MagicStarPlatform)** 与 **业务微服务 (DreamClip 梦之厅)** 构建的模块化、解耦且可扩展的微服务生态体系。

---

## 🏛️ 一、 核心架构与定位

全平台采用清晰的 **“平台底座 + 业务节点”** 拓扑结构：

```
                              ┌──────────────────────────────────────────────┐
                              │            统一域名流量 / 客户端请求          │
                              └──────────────────────┬───────────────────────┘
                                                     │
                                                     ▼
                              ┌──────────────────────────────────────────────┐
                              │      MagicStarPlatform (平台治理与认证底座)   │
                              │   (Port: 8000 / 统一网关 / SSO / PortalOS)   │
                              │   数据库: magicstar_platform.db / MySQL 库   │
                              └──────────────────────┬───────────────────────┘
                                                     │ 代理转发 / SSO 联动 / 权限控制
                                                     ▼
                              ┌──────────────────────────────────────────────┐
                              │      DreamClip 梦之厅 (第 1 个业务微服务节点) │
                              │   (Port: 8081 / 梦之厅官网 / Studio / AVG)    │
                              │   数据库: dreamclip.db / MySQL 业务库        │
                              └──────────────────────┬───────────────────────┘
                                                     │ 可插拔扩展
                                                     ▼
                                      未来任意新业务微服务节点 (Game / AI / ...)
```

### 1. 平台底座：`MagicStarPlatform` (目录: `magicstar-platform`)
- **智能网关与路由代理**：统一反向代理、虚拟主机分流（`login.dreamclip.cn`, `portal.dreamclip.cn`, `base.dreamclip.cn` 等）；
- **统一 SSO 身份中心**：用户注册/登录、JWT 凭证派发、会话管理；
- **PortalOS 平台桌面**：iOS 风格应用跳板（`/portal`），根据角色权限动态启动已授权微服务；
- **IAM / RBAC 权限中心**：多角色管理、微服务赋权、超级管理员控制台（`/admin`）；
- **微服务注册治理**：服务动态注册、20 秒心跳健康巡检；
- **数据库**：`magicstar_platform.db`（SQLite） / `magicstar_platform_db`（MySQL）。

### 2. 第一个业务服务节点：`dreamclip` (目录: `dreamclip`)
- **梦之厅公众主站**：16:9 电影巨幕焦点轮播、双轨动能跑马灯、三维内容标签、编年时序切片流；
- **DreamClip Studio**：专属站务与内容运营工坊（`/studio`），支持焦点图文、Markdown 情绪胶囊创作、角色信使立绘档案与 AVG 章节编目；
- **独立 AVG 互动剧场**：HTML5 互动冒险游戏、剧情分支与存档；
- **业务 API 与模型**：胶囊、角色、AVG 章节、焦点跑马灯数据引擎；
- **数据库**：`dreamclip.db`（SQLite） / `dreamclip_db`（MySQL）。

---

## 📊 二、 服务矩阵与端口清单

| 模块名称 | 工程目录 | 对应数据库 | 运行端口 | 核心访问路径 |
| :--- | :--- | :--- | :---: | :--- |
| **MagicStarPlatform (平台底座)** | `magicstar-platform` | `magicstar_platform.db` | **8000** | • 平台桌面: `http://localhost:8000/portal`<br/>• 治理控制台: `http://localhost:8000/admin`<br/>• SSO 登录: `http://localhost:8000/login`<br/>• Swagger API: `http://localhost:8000/docs` |
| **DreamClip (梦之厅业务微服务)** | `dreamclip` | `dreamclip.db` | **8081** | • 梦之厅主站: `http://localhost:8081/`<br/>• 内容工坊: `http://localhost:8081/studio`<br/>• AVG 剧场: `http://localhost:8081/games`<br/>• Swagger API: `http://localhost:8081/docs` |

---

## 🚀 三、 快速启动与本地运行

### Windows 环境：
直接双击根目录批处理脚本：
```cmd
start_dreamclip.bat
```
或在 PowerShell 中执行：
```powershell
.\start_dreamclip.ps1
```

### Linux / Docker 环境：
```bash
# 1. 赋予权限并启动脚本
chmod +x start_dreamclip.sh
./start_dreamclip.sh

# 2. 或使用 Docker 构建运行
docker build -t dreamclip-platform:v2.0 .
docker run -d -p 8000:8000 -p 8081:8081 --name dreamclip-app dreamclip-platform:v2.0
```

---

## 🔑 四、 系统初始凭据

| 角色 | 用户名 | 初始密码 | 权限范围 |
| :--- | :--- | :--- | :--- |
| **平台超级管理员** | `superadmin` | `123456` | 拥有平台底座全部治理权限及梦之厅全量内容管理权限 |
| **前台注册会员** | 自行注册 | 注册时设定 | 享有梦之厅探索、情绪胶囊阅读及 AVG 游戏体验权限 |
