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

  function getLoginUrl() {
    const isOnline = window.location.hostname.endsWith('dreamclip.cn');
    return isOnline ? 'https://login.dreamclip.cn/' : '/login';
  }

  function goToLogin() {
    window.location.href = getLoginUrl();
  }

  async function api(path, options = {}) {
    const token = getToken();
    const headers = {
      'Content-Type': 'application/json',
      ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
      ...(options.headers || {})
    };
    try {
      let resp = await fetch('/api/v1' + path, { ...options, headers });
      if (!resp.ok && resp.status === 404) {
        resp = await fetch('/api/base' + path, { ...options, headers });
      }
      if (resp.status === 401) {
        // Token expired
        localStorage.removeItem('mcp_token');
        localStorage.removeItem('mcp_user');
        localStorage.removeItem('dreamclip_token');
        localStorage.removeItem('dreamclip_user');
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
      const roleText = isSuper ? '超级管理员' : (user.role_name || (user.roles && user.roles[0]) || '探索者');
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
      const isOnline = window.location.hostname.endsWith('dreamclip.cn');
      authArea.innerHTML = `
        <span style="font-size:12px; color:var(--text-dim);">访客模式</span>
        <button class="ios-capsule-btn" onclick="${isOnline ? 'PortalOS.goToLogin()' : "PortalOS.openAuthModal('login')"}" style="background:var(--ios-blue); border-color:transparent;">登 录</button>
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

  async function renderApps() {
    const appGrid = document.getElementById('springboardAppGrid');
    const adminGridSection = document.getElementById('adminAppsSection');
    const adminAppGrid = document.getElementById('adminAppGrid');
    if (!appGrid) return;

    // 动态从底座 IAM /auth/my-apps 获取当前登录用户被授权的全部微服务应用 (1 微服务 = 1 应用)
    let myApps = [];
    try {
      const res = await api('/auth/my-apps');
      if (res && res.code === 200 && Array.isArray(res.data)) {
        myApps = res.data;
      }
    } catch (e) {
      console.warn("Failed to fetch my-apps:", e);
    }

    const user = getUser();
    // 只有在未登录访客且接口异常时才使用兜底业务应用
    if (myApps.length === 0 && !user) {
      myApps = [
        {
          id: 'app-mcp-service-universe',
          service_code: 'mcp-service-universe',
          name: 'DreamClip 角色宇宙',
          sub: 'mcp-service-universe',
          icon: '🌌',
          gradient: 'linear-gradient(135deg, #4f46e5, #06b6d4)',
          url: 'https://universe.dreamclip.cn/',
          is_admin: false,
          description: '汇聚世界观、角色档案、情绪胶囊与沉浸式 AVG 互动剧场的独立业务应用',
          health_status: 'HEALTHY'
        }
      ];
    }

    const businessApps = myApps.filter(a => !a.is_admin);
    const adminApps = myApps.filter(a => a.is_admin);

    if (businessApps.length === 0 && adminApps.length === 0 && user) {
      appGrid.innerHTML = `
        <div style="grid-column: 1 / -1; padding: 48px 20px; text-align: center; color: rgba(255,255,255,0.7); font-size: 14px; background: rgba(255,255,255,0.06); border-radius: 18px; border: 1px dashed rgba(255,255,255,0.2);">
          📭 当前角色暂未分配微服务应用权限<br>
          <span style="font-size: 12px; color: rgba(255,255,255,0.45); margin-top: 6px; display: inline-block;">请联系超级管理员在底座控制台为您的角色赋予应用访问权限</span>
        </div>
      `;
    } else {
      appGrid.innerHTML = businessApps.map(app => `
        <div class="app-item" onclick="PortalOS.launchApp('${app.url}')" title="${app.description || app.name}">
          <div class="squircle-icon" style="background:${app.gradient || 'linear-gradient(135deg, #4f46e5, #06b6d4)'};">
            ${app.icon || '📱'}
            <span class="app-status-badge" style="background:${app.health_status === 'HEALTHY' ? '#10b981' : '#f59e0b'};" title="微服务状态: ${app.health_status || 'HEALTHY'}"></span>
          </div>
          <div class="app-label">${app.name}</div>
          <div class="app-sublabel">${app.sub || app.service_code || ''}</div>
        </div>
      `).join('');
    }

    if (adminGridSection && adminAppGrid) {
      if (adminApps.length > 0) {
        adminGridSection.style.display = 'block';
        adminAppGrid.innerHTML = adminApps.map(app => `
          <div class="app-item" onclick="PortalOS.launchAdminApp('${app.url}')" title="${app.description || app.name}">
            <div class="squircle-icon" style="background:${app.gradient || 'linear-gradient(135deg, #6366f1, #3b82f6)'};">
              ${app.icon || '⭐'}
              <span class="app-status-badge" style="background:#6366f1; box-shadow:0 0 6px #6366f1;" title="微服务状态: ${app.health_status || 'HEALTHY'}"></span>
            </div>
            <div class="app-label">${app.name}</div>
            <div class="app-sublabel">${app.sub || app.service_code || ''}</div>
          </div>
        `).join('');
      } else {
        adminGridSection.style.display = 'none';
      }
    }
  }

  function resolveAppLaunchUrl(targetUrl) {
    const isOnline = window.location.hostname.endsWith('dreamclip.cn');
    if (!isOnline) {
      if (targetUrl.includes('universe.dreamclip.cn')) return '/universe';
      if (targetUrl.includes('base.dreamclip.cn')) return '/admin';
      if (targetUrl.includes('portal.dreamclip.cn')) return '/portal';
    }
    return targetUrl;
  }

  function launchApp(url) {
    const targetUrl = resolveAppLaunchUrl(url);
    const token = getToken();
    const user = getUser();

    if (targetUrl.startsWith('http://') || targetUrl.startsWith('https://')) {
      const u = new URL(targetUrl, window.location.origin);
      if (token) {
        u.searchParams.set('mcp_token', token);
        if (user) {
          u.searchParams.set('mcp_user', encodeURIComponent(JSON.stringify(user)));
        }
      }
      window.open(u.toString(), '_blank');
    } else {
      let jump = targetUrl;
      if (token) {
        const join = jump.includes('?') ? '&' : '?';
        jump = `${jump}${join}mcp_token=${encodeURIComponent(token)}`;
      }
      window.location.href = jump;
    }
  }

  function launchAdminApp(url) {
    const token = getToken();
    const user = getUser();
    if (!token) {
      showToast("请先以管理员身份登录", "info");
      goToLogin();
      return;
    }
    const targetUrl = resolveAppLaunchUrl(url);
    if (targetUrl.startsWith('http://') || targetUrl.startsWith('https://')) {
      const u = new URL(targetUrl, window.location.origin);
      u.searchParams.set('mcp_token', token);
      if (user) {
        u.searchParams.set('mcp_user', encodeURIComponent(JSON.stringify(user)));
      }
      window.open(u.toString(), '_blank');
    } else {
      let jump = targetUrl;
      const join = jump.includes('?') ? '&' : '?';
      jump = `${jump}${join}mcp_token=${encodeURIComponent(token)}`;
      window.location.href = jump;
    }
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
    const isOnline = window.location.hostname.endsWith('dreamclip.cn');
    setTimeout(() => {
      window.location.href = isOnline ? 'https://login.dreamclip.cn/' : '/login';
    }, 400);
  }

  function init() {
    const urlParams = new URLSearchParams(window.location.search);
    const tokenFromUrl = urlParams.get('mcp_token') || urlParams.get('token');
    const userFromUrl = urlParams.get('mcp_user') || urlParams.get('user');

    if (tokenFromUrl) {
      localStorage.setItem('mcp_token', tokenFromUrl);
      localStorage.setItem('dreamclip_token', tokenFromUrl);
      if (userFromUrl) {
        localStorage.setItem('mcp_user', decodeURIComponent(userFromUrl));
        localStorage.setItem('dreamclip_user', decodeURIComponent(userFromUrl));
      }
      urlParams.delete('mcp_token');
      urlParams.delete('token');
      urlParams.delete('mcp_user');
      urlParams.delete('user');
      const newSearch = urlParams.toString();
      const newUrl = window.location.pathname + (newSearch ? '?' + newSearch : '') + window.location.hash;
      window.history.replaceState({}, document.title, newUrl);
    }

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
    goToLogin,
    getLoginUrl,
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
