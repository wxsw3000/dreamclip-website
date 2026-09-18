/**
 * ==========================================================================
 * PortalOS: Apple iOS / iPadOS Springboard Engine & RBAC Launcher
 * ==========================================================================
 */

window.PortalOS = (function() {
  let registeredServices = [];

  function getToken() {
    return localStorage.getItem('mcp_token') || localStorage.getItem('dreamclip_token');
  }

  function getUser() {
    try {
      const raw = localStorage.getItem('mcp_user') || localStorage.getItem('dreamclip_user');
      return raw ? JSON.parse(raw) : null;
    } catch (e) {
      return null;
    }
  }

  function showToast(msg, type = 'info') {
    const c = document.getElementById('toastContainer');
    if (!c) return;
    const t = document.createElement('div');
    t.className = 'ios-toast';
    t.innerText = msg;
    c.appendChild(t);
    setTimeout(() => t.remove(), 3000);
  }

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
        // Token expired
        localStorage.removeItem('mcp_token');
        localStorage.removeItem('mcp_user');
        renderStatusBar();
        renderApps();
        return null;
      }
      return await resp.json();
    } catch (e) {
      console.warn("Portal API failed:", path, e);
      return null;
    }
  }

  function startClock() {
    function update() {
      const now = new Date();
      const timeStr = now.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', hour12: false });
      const dateStr = now.toLocaleDateString('zh-CN', { month: 'numeric', day: 'numeric', weekday: 'short' });
      
      const timeEl = document.getElementById('iosClock');
      const dateEl = document.getElementById('iosDate');
      if (timeEl) timeEl.innerText = timeStr;
      if (dateEl) dateEl.innerText = dateStr;
    }
    update();
    setInterval(update, 1000);
  }

  function renderStatusBar() {
    const user = getUser();
    const authArea = document.getElementById('statusAuthArea');
    if (!authArea) return;

    if (user) {
      const isSuper = Boolean(user.is_superadmin);
      const roleText = isSuper ? '超级管理员' : (user.role_name || '探索者');
      const avatarLetters = (user.username || 'U').substring(0, 2).toUpperCase();

      authArea.innerHTML = `
        <div class="user-identity-capsule">
          <div class="user-avatar-tag">${avatarLetters}</div>
          <span class="user-name-tag">${user.real_name || user.username}</span>
          <span class="user-role-badge">${roleText}</span>
        </div>
        <button class="ios-capsule-btn" onclick="PortalOS.openChangePasswordModal()" title="修改登录密码">🔑 密码</button>
        <button class="ios-capsule-btn" onclick="PortalOS.logout()" title="安全退出">退出</button>
      `;
    } else {
      authArea.innerHTML = `
        <span style="font-size:12px; color:var(--text-dim);">访客模式</span>
        <button class="ios-capsule-btn" onclick="PortalOS.openAuthModal('login')" style="background:var(--ios-blue); border-color:transparent;">登 录</button>
        <button class="ios-capsule-btn" onclick="PortalOS.openAuthModal('register')">注 册</button>
      `;
    }
  }

  async function fetchClusterHealth() {
    try {
      const res = await api('/microservices');
      if (res && res.code === 200 && res.data) {
        registeredServices = res.data.records || res.data || [];
        updateClusterWidget();
      }
    } catch (e) {
      console.warn("Failed to fetch cluster health", e);
    }
  }

  function updateClusterWidget() {
    const container = document.getElementById('clusterNodesWidgetList');
    if (!container) return;

    const baseSvc = registeredServices.find(s => s.service_code === 'mcp-base');
    const universeSvc = registeredServices.find(s => s.service_code === 'mcp-service-universe');
    const portalSvc = registeredServices.find(s => s.service_code === 'mcp-portal');

    const nodes = [
      { name: 'mcp-base (底座治理)', status: baseSvc ? baseSvc.health_status : 'HEALTHY', port: '8000', ms: baseSvc ? baseSvc.response_time_ms : 1 },
      { name: 'mcp-service-universe (主站业务)', status: universeSvc ? universeSvc.health_status : 'HEALTHY', port: '8081', ms: universeSvc ? universeSvc.response_time_ms : 1 },
      { name: 'mcp-portal (统一网关/SSO)', status: 'HEALTHY', port: '80', ms: 0 }
    ];

    container.innerHTML = nodes.map(n => `
      <div class="cluster-node-item">
        <span class="node-name">${n.name}</span>
        <span class="node-status">
          <span class="signal-dot" style="background:${n.status === 'HEALTHY' ? '#34d399' : '#f87171'}; box-shadow:0 0 6px ${n.status === 'HEALTHY' ? '#34d399' : '#f87171'};"></span>
          ${n.status === 'HEALTHY' ? '在线' : '离线'} (${n.port})
        </span>
      </div>
    `).join('');
  }

  function renderApps() {
    const user = getUser();
    const isSuper = Boolean(user && user.is_superadmin);
    const appGrid = document.getElementById('springboardAppGrid');
    const adminGridSection = document.getElementById('adminAppsSection');
    const adminAppGrid = document.getElementById('adminAppGrid');
    if (!appGrid) return;

    // 1. 公开与业务应用 (所有用户及访客可见)
    const publicApps = [
      {
        id: 'app-universe',
        name: '角色宇宙',
        sub: 'DreamClip Universe',
        icon: '🌌',
        gradient: 'linear-gradient(135deg, #4f46e5, #06b6d4)',
        url: '/universe',
        badge: '主站'
      },
      {
        id: 'app-capsules',
        name: '情绪胶囊',
        sub: 'Emotion Lab',
        icon: '💊',
        gradient: 'linear-gradient(135deg, #0ea5e9, #6366f1)',
        url: '/universe#capsules-section',
        badge: '文学'
      },
      {
        id: 'app-theatre',
        name: 'AVG 沉浸剧场',
        sub: 'DreamClip Theatre',
        icon: '🎮',
        gradient: 'linear-gradient(135deg, #8b5cf6, #ec4899)',
        url: '/games',
        badge: '互动'
      },
      {
        id: 'app-docs',
        name: 'API 开放文档',
        sub: 'OpenAPI Swagger',
        icon: '📖',
        gradient: 'linear-gradient(135deg, #10b981, #059669)',
        url: '/base/docs',
        badge: '接口'
      }
    ];

    if (user) {
      publicApps.push({
        id: 'app-vault',
        name: '星际背包',
        sub: 'Capsule Vault',
        icon: '🎒',
        gradient: 'linear-gradient(135deg, #f59e0b, #d97706)',
        url: '/universe',
        badge: '资产'
      });
    }

    appGrid.innerHTML = publicApps.map(app => `
      <div class="app-item" onclick="PortalOS.launchApp('${app.url}')">
        <div class="squircle-icon" style="background:${app.gradient};">
          ${app.icon}
          <span class="app-status-badge"></span>
        </div>
        <div class="app-label">${app.name}</div>
        <div class="app-sublabel">${app.sub}</div>
      </div>
    `).join('');

    // 2. 超管专属技术应用 (RBAC 动态解锁)
    if (adminGridSection && adminAppGrid) {
      if (isSuper) {
        adminGridSection.style.display = 'block';
        const adminApps = [
          {
            id: 'app-base',
            name: 'MCP Base 控制台',
            sub: '底座运维与治理',
            icon: '⭐',
            gradient: 'linear-gradient(135deg, #6366f1, #3b82f6)',
            url: 'https://base.dreamclip.cn/',
            isBase: true
          },
          {
            id: 'app-users',
            name: '用户权限中心',
            sub: '平台用户与角色',
            icon: '👥',
            gradient: 'linear-gradient(135deg, #8b5cf6, #a855f7)',
            url: 'https://base.dreamclip.cn/?tab=tab-users',
            isBase: true
          },
          {
            id: 'app-configs',
            name: '全局参数字典',
            sub: '系统运行参数',
            icon: '⚙️',
            gradient: 'linear-gradient(135deg, #64748b, #475569)',
            url: 'https://base.dreamclip.cn/?tab=tab-configs',
            isBase: true
          }
        ];

        adminAppGrid.innerHTML = adminApps.map(app => `
          <div class="app-item" onclick="PortalOS.launchAdminApp('${app.url}')">
            <div class="squircle-icon" style="background:${app.gradient};">
              ${app.icon}
              <span class="app-status-badge" style="background:#6366f1; box-shadow:0 0 6px #6366f1;"></span>
            </div>
            <div class="app-label">${app.name}</div>
            <div class="app-sublabel">${app.sub}</div>
          </div>
        `).join('');
      } else {
        adminGridSection.style.display = 'none';
      }
    }
  }

  function launchApp(url) {
    window.location.href = url;
  }

  function launchAdminApp(url) {
    const token = getToken();
    const user = getUser();
    if (!token) {
      showToast("请先以管理员身份登录", "info");
      openAuthModal('login');
      return;
    }
    // 跨子域名自动携带 Token 免密握手
    const u = new URL(url, window.location.origin);
    u.searchParams.set('mcp_token', token);
    if (user) {
      u.searchParams.set('mcp_user', encodeURIComponent(JSON.stringify(user)));
    }
    window.open(u.toString(), '_blank');
  }

  // ---------------- 模态弹窗与认证 ----------------
  function openAuthModal(tab = 'login') {
    const modal = document.getElementById('authModal');
    if (!modal) return;
    switchAuthTab(tab);
    modal.classList.add('show');
  }

  function closeAuthModal() {
    const modal = document.getElementById('authModal');
    if (modal) modal.classList.remove('show');
  }

  function switchAuthTab(tab) {
    const loginFields = document.getElementById('authLoginFields');
    const regFields = document.getElementById('authRegisterFields');
    const title = document.getElementById('authModalTitle');
    const btn = document.getElementById('authSubmitBtn');
    const switchBtn = document.getElementById('authSwitchTabBtn');

    if (tab === 'login') {
      if (loginFields) loginFields.style.display = 'block';
      if (regFields) regFields.style.display = 'none';
      if (title) title.innerText = '登录 DreamClip 统一门户';
      if (btn) btn.innerText = '登 录 账 户';
      if (switchBtn) {
        switchBtn.innerText = '还没有账号？立即加入宇宙注册';
        switchBtn.onclick = () => switchAuthTab('register');
      }
    } else {
      if (loginFields) loginFields.style.display = 'none';
      if (regFields) regFields.style.display = 'block';
      if (title) title.innerText = '加入 DreamClip 角色宇宙';
      if (btn) btn.innerText = '创 建 账 号';
      if (switchBtn) {
        switchBtn.innerText = '已有账号？返回直接登录';
        switchBtn.onclick = () => switchAuthTab('login');
      }
    }
  }

  async function handleAuthSubmit(e) {
    e.preventDefault();
    const isLogin = document.getElementById('authLoginFields').style.display !== 'none';
    const btn = document.getElementById('authSubmitBtn');
    btn.disabled = true;

    if (isLogin) {
      const payload = {
        username: document.getElementById('authUsername').value.trim(),
        password: document.getElementById('authPassword').value
      };
      btn.innerText = '正在验证凭证...';
      const res = await api('/auth/login', {
        method: 'POST',
        body: JSON.stringify(payload)
      });
      if (res && res.code === 200 && res.data) {
        localStorage.setItem('mcp_token', res.data.access_token);
        localStorage.setItem('mcp_user', JSON.stringify(res.data.user_info));
        localStorage.setItem('dreamclip_token', res.data.access_token);
        localStorage.setItem('dreamclip_user', JSON.stringify(res.data.user_info));
        showToast("登录成功！", "success");
        closeAuthModal();
        renderStatusBar();
        renderApps();
      } else {
        showToast(res ? res.message : "登录失败，请检查用户名和密码", "danger");
      }
    } else {
      const payload = {
        username: document.getElementById('regUsername').value.trim(),
        password: document.getElementById('regPassword').value,
        real_name: document.getElementById('regRealName').value.trim() || undefined,
        email: document.getElementById('regEmail').value.trim() || undefined,
        personality_color: document.getElementById('regColor').value,
        zodiac: document.getElementById('regZodiac').value
      };
      btn.innerText = '正在创建宇宙身份...';
      const res = await api('/auth/register', {
        method: 'POST',
        body: JSON.stringify(payload)
      });
      if (res && res.code === 200 && res.data) {
        localStorage.setItem('mcp_token', res.data.access_token);
        localStorage.setItem('mcp_user', JSON.stringify(res.data.user_info));
        localStorage.setItem('dreamclip_token', res.data.access_token);
        localStorage.setItem('dreamclip_user', JSON.stringify(res.data.user_info));
        showToast("注册成功！欢迎开启角色宇宙", "success");
        closeAuthModal();
        renderStatusBar();
        renderApps();
      } else {
        showToast(res ? res.message : "注册失败", "danger");
      }
    }
    btn.disabled = false;
    btn.innerText = isLogin ? '登 录 账 户' : '创 建 账 号';
  }

  function openChangePasswordModal() {
    const modal = document.getElementById('passwordModal');
    if (modal) {
      document.getElementById('pwdForm').reset();
      modal.classList.add('show');
    }
  }

  function closePasswordModal() {
    const modal = document.getElementById('passwordModal');
    if (modal) modal.classList.remove('show');
  }

  async function handlePasswordSubmit(e) {
    e.preventDefault();
    const oldPwd = document.getElementById('oldPassword').value;
    const newPwd = document.getElementById('newPassword').value;
    const confirmPwd = document.getElementById('confirmPassword').value;

    if (newPwd !== confirmPwd) {
      showToast("两次输入的新密码不一致", "danger");
      return;
    }

    const res = await api('/auth/change-password', {
      method: 'POST',
      body: JSON.stringify({ old_password: oldPwd, new_password: newPwd })
    });

    if (res && res.code === 200) {
      showToast("密码修改成功，请使用新密码重新登录", "success");
      closePasswordModal();
      logout();
    } else {
      showToast(res ? res.message : "密码修改失败", "danger");
    }
  }

  function logout() {
    localStorage.removeItem('mcp_token');
    localStorage.removeItem('mcp_user');
    localStorage.removeItem('dreamclip_token');
    localStorage.removeItem('dreamclip_user');
    showToast("已安全退出登录", "info");
    renderStatusBar();
    renderApps();
  }

  function init() {
    startClock();
    renderStatusBar();
    renderApps();
    fetchClusterHealth();
    setInterval(fetchClusterHealth, 20000);
  }

  return {
    init,
    launchApp,
    launchAdminApp,
    openAuthModal,
    closeAuthModal,
    switchAuthTab,
    handleAuthSubmit,
    openChangePasswordModal,
    closePasswordModal,
    handlePasswordSubmit,
    logout
  };
})();

window.addEventListener('DOMContentLoaded', () => {
  PortalOS.init();
});
