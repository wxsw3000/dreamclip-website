/**
 * MCP-Portal Unified Enterprise Workbench Engine
 * 遵循“开发一个、注册一个、显示一个”原则
 * 点击微服务卡片直接在新标签页打开（带单点登录 SSO Token 授信访问，拒绝双层嵌套）
 */

window.PortalOS = (function() {
  // 真实已注册微服务列表 (100% 来自底座 /api/v1/microservices)
  let registeredServices = [];
  let appsList = [];

  // 1. SSO 统一凭据存取
  function getToken() {
    return localStorage.getItem('mcp_token');
  }

  function getUser() {
    try {
      return JSON.parse(localStorage.getItem('mcp_user'));
    } catch (e) {
      return null;
    }
  }

  // 统一底座 API 调用包装
  async function api(path, options = {}) {
    const token = getToken();
    const headers = {
      'Content-Type': 'application/json',
      ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
      ...(options.headers || {})
    };
    try {
      const resp = await fetch('/api/base' + path, { ...options, headers });
      if (resp.status === 401) {
        logout();
        return null;
      }
      return await resp.json();
    } catch (e) {
      console.warn("API request failed:", path, e);
      return null;
    }
  }

  // 2. 初始化系统
  async function init() {
    const user = getUser();
    if (!user) {
      window.location.href = '/login';
      return;
    }

    // 渲染用户信息
    const nameEl = document.getElementById('topUserName');
    const avatarEl = document.getElementById('topUserAvatar');
    if (nameEl) nameEl.innerText = user.real_name || user.username;
    if (avatarEl) avatarEl.innerText = (user.username || 'SA').substring(0, 2).toUpperCase();

    // 启动系统时钟
    startSystemClock();

    // 加载真实已注册微服务
    await reloadData();

    // 启动后台定时健康探测轮询 (每 20 秒从真实底座同步)
    setInterval(pollHealthStatus, 20000);
  }

  // 3. 从底座拉取真实注册的微服务
  async function reloadData() {
    const gridContainer = document.getElementById('appGridContainer');
    if (gridContainer) {
      gridContainer.innerHTML = `
        <div style="grid-column:1/-1; text-align:center; padding:50px; color:var(--text-muted);">
          <div class="spinner-ring" style="margin:0 auto 16px;"></div>
          <div>正在从服务底座同步微服务...</div>
        </div>
      `;
    }

    try {
      const svcRes = await api('/microservices');
      
      registeredServices = (svcRes && svcRes.code === 200 && svcRes.data && Array.isArray(svcRes.data.records)) 
        ? svcRes.data.records 
        : (svcRes && svcRes.data && Array.isArray(svcRes.data)) ? svcRes.data : [];

      // 1:1 严格构建真实 App 卡片
      buildStrictAppCatalog();

      // 渲染真实应用网格
      renderAppGrid();

      // 更新顶部微服务集群真实健康胶囊
      updateHealthCapsule();
    } catch (err) {
      console.error("Failed to load registered microservices:", err);
      if (gridContainer) {
        gridContainer.innerHTML = `
          <div style="grid-column:1/-1; text-align:center; padding:40px; color:#dc2626;">
            <div style="font-size:32px; margin-bottom:10px;">⚠️</div>
            <div style="font-weight:700; font-size:16px;">无法连接到底座服务 (Port 8000)</div>
            <div style="font-size:12.5px; margin-top:6px; color:var(--text-muted);">请确认 mcp-base 正在运行</div>
          </div>
        `;
      }
    }
  }

  // 4. 严格 1:1 映射：注册了哪个微服务，桌面就只显示哪个 App 卡片
  function buildStrictAppCatalog() {
    appsList = [];

    registeredServices.forEach(s => {
      // 门户自身不作为独立 App 重复打开
      if (s.service_code === 'mcp-portal') return;

      const cat = s.category || 'CORE';

      // 解析入口地址 (底座使用 /login 鉴权直通，其他微服务使用 base_url)
      let launchUrl = s.base_url;
      if (s.service_code === 'mcp-base') {
        launchUrl = 'http://127.0.0.1:8000/login';
      }

      appsList.push({
        id: `app-svc-${s.service_code}`,
        code: s.service_code,
        name: s.service_name,
        category: cat,
        icon: getServiceIcon(s.service_code, cat),
        iconBg: getServiceGradient(s.service_code, cat),
        tech: `${s.tech_stack || 'REST'} · 端口 ${extractPort(s.base_url)}`,
        url: launchUrl,
        docsUrl: s.docs_url,
        status: s.health_status || 'UNKNOWN',
        responseTime: Math.round(s.response_time_ms || 0),
        desc: s.description || `${s.service_name} (${s.base_url})`
      });
    });
  }

  function extractPort(url) {
    try {
      const u = new URL(url);
      return u.port || (u.protocol === 'https:' ? '443' : '80');
    } catch(e) {
      return '8080';
    }
  }

  function getServiceIcon(code, cat) {
    if (code.includes('qa')) return '🤖';
    if (code.includes('data')) return '🪄';
    if (code.includes('base')) return '⚡';
    if (code.includes('mdm')) return '🏭';
    if (code.includes('mes')) return '🚀';
    if (code.includes('wms')) return '📦';
    if (cat === 'MDM') return '🏭';
    if (cat === 'BASE') return '⚡';
    return '🧩';
  }

  function getServiceGradient(code, cat) {
    if (code.includes('qa')) return 'linear-gradient(135deg, #8b5cf6, #3b82f6)';
    if (code.includes('data')) return 'linear-gradient(135deg, #06b6d4, #3b82f6)';
    if (code.includes('base')) return 'linear-gradient(135deg, #0284c7, #2563eb)';
    if (code.includes('mdm')) return 'linear-gradient(135deg, #059669, #10b981)';
    return 'linear-gradient(135deg, #3b82f6, #1d4ed8)';
  }

  // 5. 渲染真实应用网格
  function renderAppGrid() {
    const container = document.getElementById('appGridContainer');
    if (!container) return;

    if (appsList.length === 0) {
      container.innerHTML = `
        <div style="grid-column:1/-1; text-align:center; padding:60px 20px; color:var(--text-muted); background:#fff; border:1px solid var(--surface-border); border-radius:var(--radius-lg);">
          <div style="font-size:36px; margin-bottom:12px;">📭</div>
          <div style="font-size:16px; font-weight:700; color:var(--text-main);">当前底座暂无已注册微服务</div>
          <div style="font-size:12.5px; margin-top:6px;">微服务启动时将自动向底座注册并在此显示</div>
        </div>
      `;
      return;
    }

    container.innerHTML = appsList.map(app => {
      let badgeHtml = '';
      if (app.status === 'HEALTHY') {
        badgeHtml = `<div class="app-health-badge badge-healthy"><span class="pulse-dot"></span> 在线 ${app.responseTime ? app.responseTime + 'ms' : ''}</div>`;
      } else if (app.status === 'DOWN') {
        badgeHtml = `<div class="app-health-badge badge-down">🔴 离线</div>`;
      } else if (app.status === 'WARNING') {
        badgeHtml = `<div class="app-health-badge badge-warning">🟡 迟缓</div>`;
      } else {
        badgeHtml = `<div class="app-health-badge badge-pending">⚪ 未检测</div>`;
      }

      return `
        <div class="app-card" onclick="PortalOS.launchApp('${app.id}')">
          <div class="app-card-top">
            <div class="app-icon-squircle" style="background: ${app.iconBg};">
              ${app.icon}
            </div>
            ${badgeHtml}
          </div>

          <div class="app-meta">
            <div class="app-name">${app.name}</div>
            <div class="app-code">${app.code}</div>
            <div class="app-desc">${app.desc}</div>
          </div>

          <div class="app-card-footer">
            <span class="app-tech-tag">${app.tech}</span>
            <div class="app-launch-action">
              打开微服务 ↗
            </div>
          </div>
        </div>
      `;
    }).join('');
  }

  // 6. 打开微服务：直接新窗口打开并注入 SSO Token (无 iframe 嵌套)
  function launchApp(appId) {
    const app = appsList.find(a => a.id === appId);
    if (!app || !app.url) return;

    // 组装带有 SSO 凭据的完整独立 URL
    const token = getToken();
    let targetUrl = app.url;
    if (token && (targetUrl.startsWith('http://') || targetUrl.startsWith('https://'))) {
      const joinChar = targetUrl.includes('?') ? '&' : '?';
      targetUrl = `${targetUrl}${joinChar}mcp_token=${encodeURIComponent(token)}`;
    }

    // 在独立新标签页中打开微服务
    window.open(targetUrl, '_blank');
  }

  // 7. 实时系统时钟
  function startSystemClock() {
    const timeEl = document.getElementById('topTimeText');
    const dateEl = document.getElementById('topDateText');
    const update = () => {
      const now = new Date();
      if (timeEl) timeEl.innerText = now.toLocaleTimeString('zh-CN', { hour12: false });
      if (dateEl) {
        const weeks = ['周日', '周一', '周二', '周三', '周四', '周五', '周六'];
        dateEl.innerText = `${now.getMonth() + 1}月${now.getDate()}日 ${weeks[now.getDay()]}`;
      }
    };
    update();
    setInterval(update, 1000);
  }

  // 8. 更新顶部真实健康胶囊
  function updateHealthCapsule() {
    const capsule = document.getElementById('topHealthCapsule');
    if (!capsule) return;

    const realServices = registeredServices.filter(s => s.service_code !== 'mcp-portal');
    const onlineCount = realServices.filter(s => s.health_status === 'HEALTHY').length;

    capsule.innerHTML = `
      <span class="pulse-dot"></span>
      <span>${onlineCount}/${realServices.length} 个微服务健康在线</span>
    `;
  }

  // 9. 定时轮询健康状态
  async function pollHealthStatus() {
    try {
      const res = await api('/microservices/active');
      if (res && res.code === 200 && Array.isArray(res.data)) {
        registeredServices = res.data;
        buildStrictAppCatalog();
        renderAppGrid();
        updateHealthCapsule();
      }
    } catch (e) {
      console.warn("Heartbeat poll failed", e);
    }
  }

  // 10. 安全退出
  function logout() {
    localStorage.removeItem('mcp_token');
    localStorage.removeItem('mcp_user');
    window.location.href = '/login';
  }

  return {
    init,
    launchApp,
    reloadData,
    logout
  };
})();

window.addEventListener('DOMContentLoaded', () => {
  PortalOS.init();
});
