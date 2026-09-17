# DreamClip 角色宇宙与微服务互动平台 (DreamClip-Platform)

一套面向 C 端用户的**可插拔角色宇宙、情绪胶囊深度文学与独立 AVG 互动游戏**微服务运行底座。

---

## 一、 平台定位与架构理念

**DreamClip (dreamclip.cn)** 采用模块化解耦微服务底座，旨在构建高扩展、易维护的泛娱乐与独立游戏聚合生态：

```
                      ┌──────────────────────────────────────────────┐
                      │        统一主门户框架 (DreamClip-Portal)       │
                      │   (Port: 3000 / 沉浸式C端门户 / AdSense合规)   │
                      └──────────────────────┬───────────────────────┘
                                             │ SSO 鉴权 / 反向代理
                                             ▼
                      ┌──────────────────────────────────────────────┐
                      │        核心底座服务 (DreamClip-Base)         │
                      │   (Port: 8000 / 用户中心 / 性格画像 / 探活治理)  │
                      └─────┬──────────────────────────┬─────────────┘
                            │ 自动注册 / 20s心跳探测     │
                            ▼                          ▼
              ┌───────────────────────────┐ ┌───────────────────────────┐
              │  角色宇宙与内容微服务     │ │    首款独立AVG互动游戏    │
              │(Universe & Capsules)      │ │    (HTML5 Standalone AVG) │
              │ Python/FastAPI (Port 8081)│ │ Web/Canvas (Demo Chapter) │
              └───────────────────────────┘ └───────────────────────────┘
```

### 核心设计原则：
1. **真实服务与可插拔扩展**：所有服务均为真实独立运行的微服务，未来新增第 2 款、第 10 款独立游戏或 AI 互动服务，只需向 Base 注册即可在 Portal 动态呈现。
2. **统一 SSO 身份与性格色彩画像**：支持 4 大性格色彩（红/蓝/黄/绿）与 12 星座画像，在全平台所有子作品中保持无缝单点登录。
3. **Google AdSense 深度合规优化**：
   - 800~1500 字高质量原创图文（情绪胶囊），杜绝“内容匮乏/低价值”拒审；
   - 内置响应式广告位插槽（顶部横幅、文章内部、文末原生推荐）；
   - 必备四大合规页面（关于我们 `/about`、隐私政策 `/privacy`、服务条款 `/terms`、联系我们 `/contact`）。

---

## 二、 核心组件与端口矩阵

| 组件名称 | 目录路径 | 技术栈 | 运行端口 | 说明 |
| :--- | :--- | :--- | :---: | :--- |
| **DreamClip-Base** | `/mcp-base` | Python 3.14 (FastAPI + SQLAlchemy) | **8000** | 用户中心、JWT鉴权、性格画像、微服务注册与20秒心跳探活 |
| **DreamClip-Universe** | `/mcp-service-universe` | Python 3.14 (FastAPI + SQLAlchemy) | **8081** | 世界观、角色档案、情绪胶囊原创图文、AVG游戏章节元数据 |
| **DreamClip-Portal** | `/mcp-portal` | Python 3.14 (FastAPI + 响应式前端) | **3000** | C端沉浸主门户、文章阅读器、AVG游戏启动器、AdSense四大合规页 |
| **Demo-AVG 游戏** | `/mcp-portal/.../games/demo-avg` | HTML5 / Canvas / JavaScript | 嵌入式 | 独立运行的互动 AVG 演示章节（第一章：失落的深空信标） |

---

## 三、 快速启动与本地调试

### Windows 环境：
直接双击根目录下的批处理脚本：
```cmd
start_dreamclip.bat
```

### Linux / Ubuntu 生产服务器：
```bash
chmod +x start_dreamclip.sh
./start_dreamclip.sh
```

---

## 四、 核心访问入口

* 🌐 **C端统一主站门户**：[http://127.0.0.1:3000](http://127.0.0.1:3000)
* 📖 **情绪胶囊阅读器**：[http://127.0.0.1:3000/capsule/rain-at-3am-and-unopened-letters](http://127.0.0.1:3000/capsule/rain-at-3am-and-unopened-letters)
* 🎮 **AVG 游戏专区**：[http://127.0.0.1:3000/games](http://127.0.0.1:3000/games)
* 🛡️ **底座接口文档 (Swagger)**：[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
* 🌌 **宇宙内容接口文档**：[http://127.0.0.1:8081/docs](http://127.0.0.1:8081/docs)

### AdSense 审核合规页面：
* 关于我们：[http://127.0.0.1:3000/about](http://127.0.0.1:3000/about)
* 隐私政策：[http://127.0.0.1:3000/privacy](http://127.0.0.1:3000/privacy)
* 服务条款：[http://127.0.0.1:3000/terms](http://127.0.0.1:3000/terms)
* 联系我们：[http://127.0.0.1:3000/contact](http://127.0.0.1:3000/contact)
