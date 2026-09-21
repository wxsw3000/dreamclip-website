/**
 * DreamClip 客户端统一 API 与状态管理
 */
function getAuthCookie(name) {
  if (!document.cookie) return null;
  const prefix = name + '=';
  const cookies = document.cookie.split(';');
  for (let i = 0; i < cookies.length; i++) {
    const c = cookies[i].trim();
    if (c.startsWith(prefix)) {
      return decodeURIComponent(c.substring(prefix.length));
    }
  }
  return null;
}

function setAuthCookie(name, value, days = 7) {
  const isOnline = window.location.hostname.endsWith('dreamclip.cn');
  const domainPart = isOnline ? '; domain=.dreamclip.cn' : '';
  let maxAgePart = '';
  if (typeof days === 'number' && days > 0) {
    maxAgePart = `; max-age=${days * 24 * 60 * 60}`;
  }
  document.cookie = `${name}=${encodeURIComponent(value)}${domainPart}; path=/; SameSite=Lax${maxAgePart}`;
}

function clearAuthCookie(name) {
  document.cookie = `${name}=; path=/; domain=.dreamclip.cn; max-age=0; expires=Thu, 01 Jan 1970 00:00:00 GMT`;
  document.cookie = `${name}=; path=/; max-age=0; expires=Thu, 01 Jan 1970 00:00:00 GMT`;
}

function getStoredToken() {
  return (
    getAuthCookie("mcp_token") ||
    getAuthCookie("dreamclip_token") ||
    sessionStorage.getItem("mcp_token") ||
    sessionStorage.getItem("dreamclip_token") ||
    localStorage.getItem("mcp_token") ||
    localStorage.getItem("dreamclip_token") ||
    null
  );
}

function getStoredUser() {
  const raw = (
    getAuthCookie("mcp_user") ||
    getAuthCookie("dreamclip_user") ||
    sessionStorage.getItem("mcp_user") ||
    sessionStorage.getItem("dreamclip_user") ||
    localStorage.getItem("mcp_user") ||
    localStorage.getItem("dreamclip_user") ||
    null
  );
  if (!raw) return null;
  try {
    return typeof raw === 'object' ? raw : JSON.parse(raw);
  } catch (e) {
    return null;
  }
}

const DreamClipAPI = {
  // 基础请求封装
  async request(endpoint, options = {}) {
    const isOnline = window.location.hostname.endsWith('dreamclip.cn');
    const token = getStoredToken();

    const headers = {
      "Content-Type": "application/json",
      ...(options.headers || {})
    };
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    try {
      let resp = await fetch(endpoint, {
        ...options,
        headers
      });
      if (!resp.ok && resp.status === 404 && endpoint.startsWith('/api/base/')) {
        const altEndpoint = endpoint.replace('/api/base/', '/api/v1/');
        resp = await fetch(altEndpoint, { ...options, headers });
      }
      if (!resp.ok && resp.status === 404 && endpoint.startsWith('/api/v1/')) {
        const altEndpoint = endpoint.replace('/api/v1/', '/api/base/');
        resp = await fetch(altEndpoint, { ...options, headers });
      }
      if (!resp.ok && resp.status === 404 && endpoint.startsWith('/api/universe/')) {
        const altEndpoint = endpoint.replace('/api/universe/', '/api/v1/');
        resp = await fetch(altEndpoint, { ...options, headers });
      }
      if (!resp.ok && resp.status === 404 && endpoint.startsWith('/api/dreamclip/')) {
        const altEndpoint = endpoint.replace('/api/dreamclip/', '/api/v1/');
        resp = await fetch(altEndpoint, { ...options, headers });
      }
      if (resp.status === 401) {
        if (token) {
          if (isOnline) {
            clearAuthCookie("mcp_token");
            clearAuthCookie("mcp_user");
            clearAuthCookie("dreamclip_token");
            clearAuthCookie("dreamclip_user");
          }
          localStorage.removeItem("dreamclip_token");
          localStorage.removeItem("dreamclip_user");
          localStorage.removeItem("mcp_token");
          localStorage.removeItem("mcp_user");
          sessionStorage.clear();
          initUserSessionUI();
        }
        return { code: 401, message: "登录凭据已过期" };
      }
      const data = await resp.json();
      return data;
    } catch (err) {
      console.error("API Request Error:", endpoint, err);
      return { code: 500, message: "网络连接异常，请稍后重试" };
    }
  },

  auth: {
    getLoginUrl(mode = 'login') {
      const isOnline = window.location.hostname.endsWith('dreamclip.cn');
      const ssoHost = isOnline ? 'https://login.dreamclip.cn/' : '/login';
      const redirectParam = encodeURIComponent(window.location.href);
      return `${ssoHost}?mode=${mode}&redirect=${redirectParam}`;
    },

    async register(username, password, realName, email) {
      return await DreamClipAPI.request("/api/base/auth/register", {
        method: "POST",
        body: JSON.stringify({
          username,
          password,
          real_name: realName || username,
          email: email || undefined
        })
      });
    },

    async login(username, password) {
      return await DreamClipAPI.request("/api/base/auth/login", {
        method: "POST",
        body: JSON.stringify({ username, password })
      });
    },

    async getMe() {
      let res = await DreamClipAPI.request("/api/v1/auth/me");
      if (!res || res.code !== 200) {
        res = await DreamClipAPI.request("/api/base/auth/me");
      }
      return res;
    },

    logout() {
      clearAuthCookie("mcp_token");
      clearAuthCookie("mcp_user");
      clearAuthCookie("dreamclip_token");
      clearAuthCookie("dreamclip_user");
      localStorage.removeItem("dreamclip_token");
      localStorage.removeItem("dreamclip_user");
      localStorage.removeItem("mcp_token");
      localStorage.removeItem("mcp_user");
      sessionStorage.clear();
      const isOnline = window.location.hostname.endsWith('dreamclip.cn');
      window.location.href = isOnline ? 'https://login.dreamclip.cn/?logout=true' : '/login?logout=true';
    }
  },

  // 角色宇宙与内容 API
  universe: {
    async getWorldviews() {
      return await DreamClipAPI.request("/api/universe/worldviews");
    },

    async getCharacters(params = {}) {
      const query = new URLSearchParams(params).toString();
      return await DreamClipAPI.request(`/api/universe/characters?${query}`);
    },

    async createCharacter(data) {
      return await DreamClipAPI.request("/api/universe/characters", {
        method: "POST",
        body: JSON.stringify(data)
      });
    },

    async updateCharacter(id, data) {
      return await DreamClipAPI.request(`/api/universe/characters/${id}`, {
        method: "PUT",
        body: JSON.stringify(data)
      });
    },

    async toggleCharacter(id) {
      return await DreamClipAPI.request(`/api/universe/characters/${id}/toggle`, {
        method: "POST"
      });
    },

    async deleteCharacter(id) {
      return await DreamClipAPI.request(`/api/universe/characters/${id}`, {
        method: "DELETE"
      });
    },

    async getCapsules(params = {}) {
      const query = new URLSearchParams(params).toString();
      return await DreamClipAPI.request(`/api/universe/capsules?${query}`);
    },

    async getCapsuleDetail(idOrSlug) {
      return await DreamClipAPI.request(`/api/universe/capsules/${idOrSlug}`);
    },

    async createCapsule(data) {
      return await DreamClipAPI.request("/api/universe/capsules", {
        method: "POST",
        body: JSON.stringify(data)
      });
    },

    async updateCapsule(id, data) {
      return await DreamClipAPI.request(`/api/universe/capsules/${id}`, {
        method: "PUT",
        body: JSON.stringify(data)
      });
    },

    async toggleCapsule(id) {
      return await DreamClipAPI.request(`/api/universe/capsules/${id}/toggle`, {
        method: "POST"
      });
    },

    async deleteCapsule(id) {
      return await DreamClipAPI.request(`/api/universe/capsules/${id}`, {
        method: "DELETE"
      });
    },

    async likeCapsule(id) {
      return await DreamClipAPI.request(`/api/universe/capsules/${id}/like`, { method: "POST" });
    },

    async getAvgChapters(params = {}) {
      const query = new URLSearchParams(params).toString();
      return await DreamClipAPI.request(`/api/universe/avg/chapters?${query}`);
    },

    async createAvgChapter(data) {
      return await DreamClipAPI.request("/api/universe/avg/chapters", {
        method: "POST",
        body: JSON.stringify(data)
      });
    },

    async updateAvgChapter(id, data) {
      return await DreamClipAPI.request(`/api/universe/avg/chapters/${id}`, {
        method: "PUT",
        body: JSON.stringify(data)
      });
    },

    async toggleAvgChapter(id) {
      return await DreamClipAPI.request(`/api/universe/avg/chapters/${id}/toggle`, {
        method: "POST"
      });
    },

    async deleteAvgChapter(id) {
      return await DreamClipAPI.request(`/api/universe/avg/chapters/${id}`, {
        method: "DELETE"
      });
    }
  },

  // 梦之厅跑马灯与焦点图文 API
  hall: {
    async getBanners(allStatus = false) {
      return await DreamClipAPI.request(`/api/universe/hall/banners?all_status=${allStatus}`);
    },
    async createBanner(data) {
      return await DreamClipAPI.request(`/api/universe/hall/banners`, {
        method: "POST",
        body: JSON.stringify(data)
      });
    },
    async updateBanner(id, data) {
      return await DreamClipAPI.request(`/api/universe/hall/banners/${id}`, {
        method: "PUT",
        body: JSON.stringify(data)
      });
    },
    async toggleBanner(id) {
      return await DreamClipAPI.request(`/api/universe/hall/banners/${id}/toggle`, {
        method: "POST"
      });
    },
    async deleteBanner(id) {
      return await DreamClipAPI.request(`/api/universe/hall/banners/${id}`, {
        method: "DELETE"
      });
    }
  }
};

// 全局 UI 辅助函数
async function initUserSessionUI() {
  const authContainer = document.getElementById("header-auth-area");
  const heroCtaBtn = document.getElementById("hero-main-cta");
  const token = getStoredToken();
  const cachedUser = getStoredUser();

  function renderUserUI(u) {
    if (!authContainer) return;
    const isSuper = Boolean(u.is_superadmin || u.username === 'superadmin');
    const roleText = isSuper ? '超级管理员' : (u.role_name || (u.roles && u.roles[0]) || '会员');
    const avatarUrl = u.avatar || `https://api.dicebear.com/7.x/bottts/svg?seed=${u.username}`;
    const displayName = u.real_name || u.username;
    const isOnline = window.location.hostname.endsWith('dreamclip.cn');
    const adminBaseUrl = isOnline ? 'https://base.dreamclip.cn/' : 'http://localhost:8000/admin';
    const portalBaseUrl = isOnline ? 'https://portal.dreamclip.cn/' : 'http://localhost:8000/portal';
    const studioLinkHtml = isSuper ? `<a href="/studio" class="btn btn-primary" style="padding:0.35rem 0.85rem; font-size:0.82rem; margin-right:6px; background:linear-gradient(135deg, #ec4899 0%, #8b5cf6 100%); border:none; box-shadow:0 2px 10px rgba(236,72,153,0.35);" title="进入 DreamClip 梦之厅专属内容工坊">🎨 内容工坊</a>` : '';
    const baseAdminLinkHtml = isSuper ? `<a href="${adminBaseUrl}" class="btn btn-outline" style="padding:0.35rem 0.75rem; font-size:0.82rem; margin-right:6px; border-color:rgba(255,255,255,0.18); color:#cbd5e1;" title="进入 MagicStar 平台底座治理" target="_blank">⚙️ 底座治理</a>` : '';

    authContainer.innerHTML = `
      ${studioLinkHtml}
      <a href="${portalBaseUrl}" class="btn btn-outline" style="padding:0.35rem 0.85rem; font-size:0.82rem; margin-right:6px;" title="进入已授权的微服务应用桌面">📱 平台桌面</a>
      ${baseAdminLinkHtml}
      <div class="user-badge" style="display:inline-flex; align-items:center; gap:0.4rem; background:rgba(255,255,255,0.08); padding:0.25rem 0.65rem; border-radius:20px; border:1px solid rgba(255,255,255,0.15);">
        <img class="user-avatar-mini" style="width:22px; height:22px; border-radius:50%; border:1px solid rgba(255,255,255,0.2);" src="${avatarUrl}" alt="avatar" onerror="this.src='data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>👤</text></svg>'">
        <span style="font-size:0.85rem; font-weight:600; color:#fff;">${displayName}</span>
        <span style="font-size:0.7rem; color:${isSuper ? '#c7d2fe' : '#818cf8'}; background:${isSuper ? 'rgba(99,102,241,0.3)' : 'rgba(99,102,241,0.15)'}; border:1px solid rgba(99,102,241,0.4); padding:0.1rem 0.4rem; border-radius:6px;">${roleText}</span>
      </div>
      <button class="btn btn-outline" style="padding:0.35rem 0.65rem; font-size:0.8rem; margin-left:6px;" onclick="DreamClipAPI.auth.logout()">退出</button>
    `;

    if (heroCtaBtn) {
      heroCtaBtn.innerText = "📱 进入平台应用桌面 (已登录)";
      heroCtaBtn.href = portalBaseUrl;
    }
  }

  function renderGuestUI() {
    if (authContainer) {
      const loginUrl = DreamClipAPI.auth.getLoginUrl('login');
      const registerUrl = DreamClipAPI.auth.getLoginUrl('register');
      authContainer.innerHTML = `
        <a href="/portal" class="btn btn-outline" style="padding:0.35rem 0.75rem; font-size:0.82rem; margin-right:6px;">📱 平台桌面</a>
        <a href="${loginUrl}" class="btn btn-outline" style="padding:0.35rem 0.75rem; font-size:0.82rem; margin-right:6px;">登录</a>
        <a href="${registerUrl}" class="btn btn-primary" style="padding:0.35rem 0.75rem; font-size:0.82rem;">✨ 立即注册</a>
      `;
    }
    if (heroCtaBtn) {
      heroCtaBtn.innerText = "✨ 开启探索 (立即注册)";
      heroCtaBtn.href = DreamClipAPI.auth.getLoginUrl('register');
    }
  }

  if (!token) {
    renderGuestUI();
    return;
  }

  // 1. 如果本地或 Cookie 有缓存用户数据，立即渲染，零延迟消除未登录闪烁
  if (cachedUser) {
    renderUserUI(cachedUser);
  }

  // 2. 异步向后端验证并拉取最新用户资料
  try {
    const meRes = await DreamClipAPI.auth.getMe();
    if (meRes && meRes.code === 200 && meRes.data) {
      renderUserUI(meRes.data);
    } else if (meRes && meRes.code === 401) {
      DreamClipAPI.auth.logout();
    }
  } catch (err) {
    console.warn("Failed to fetch fresh user info on main site:", err);
  }
}

// 确保无论在任何 DOM 生命周期阶段加载都能立即初始化 UI
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initUserSessionUI);
} else {
  initUserSessionUI();
}
window.initUserSessionUI = initUserSessionUI;

function ensureAuthModalDOM() {
  if (document.getElementById("auth-modal")) return;
  const modalHTML = `
    <div id="auth-modal" style="position:fixed; top:0; left:0; width:100vw; height:100vh; background:rgba(0,0,0,0.65); backdrop-filter:blur(8px); display:none; align-items:center; justify-content:center; z-index:9999;">
      <div style="background:#111827; border:1px solid rgba(255,255,255,0.15); border-radius:18px; width:90%; max-width:420px; padding:28px 24px; box-shadow:0 25px 50px rgba(0,0,0,0.6); color:#fff; position:relative; box-sizing:border-box;">
        <button onclick="closeAuthModal()" style="position:absolute; top:14px; right:16px; background:none; border:none; color:#94a3b8; font-size:20px; cursor:pointer;">✕</button>
        <h3 id="modal-title" style="margin-bottom:16px; font-size:1.2rem; font-weight:700;">登录 DreamClip 宇宙</h3>
        <div id="auth-error-msg" style="display:none; padding:8px 12px; background:rgba(239,68,68,0.2); border:1px solid rgba(239,68,68,0.4); color:#fca5a5; border-radius:8px; font-size:0.82rem; margin-bottom:14px;"></div>
        <form id="auth-form" onsubmit="handleAuthSubmit(event)">
          <div id="login-fields">
            <div style="margin-bottom:14px;">
              <label style="display:block; font-size:0.82rem; color:#cbd5e1; margin-bottom:5px;">账号 / 用户名</label>
              <input type="text" id="login-username" style="width:100%; height:40px; border-radius:8px; border:1px solid rgba(255,255,255,0.15); background:rgba(255,255,255,0.06); color:#fff; padding:0 12px; font-size:0.9rem; box-sizing:border-box;" placeholder="输入用户名">
            </div>
            <div style="margin-bottom:18px;">
              <label style="display:block; font-size:0.82rem; color:#cbd5e1; margin-bottom:5px;">密码</label>
              <input type="password" id="login-password" style="width:100%; height:40px; border-radius:8px; border:1px solid rgba(255,255,255,0.15); background:rgba(255,255,255,0.06); color:#fff; padding:0 12px; font-size:0.9rem; box-sizing:border-box;" placeholder="输入登录密码">
            </div>
          </div>
          <div id="register-fields" style="display:none;">
            <div style="margin-bottom:12px;">
              <label style="display:block; font-size:0.82rem; color:#cbd5e1; margin-bottom:4px;">设置用户名 *</label>
              <input type="text" id="reg-username" style="width:100%; height:38px; border-radius:8px; border:1px solid rgba(255,255,255,0.15); background:rgba(255,255,255,0.06); color:#fff; padding:0 10px; font-size:0.88rem; box-sizing:border-box;" placeholder="如 dreamer_01">
            </div>
            <div style="margin-bottom:12px;">
              <label style="display:block; font-size:0.82rem; color:#cbd5e1; margin-bottom:4px;">设置密码 *</label>
              <input type="password" id="reg-password" style="width:100%; height:38px; border-radius:8px; border:1px solid rgba(255,255,255,0.15); background:rgba(255,255,255,0.06); color:#fff; padding:0 10px; font-size:0.88rem; box-sizing:border-box;" placeholder="至少 6 位密码">
            </div>
            <div style="margin-bottom:12px;">
              <label style="display:block; font-size:0.82rem; color:#cbd5e1; margin-bottom:4px;">真实称谓 / 昵称</label>
              <input type="text" id="reg-nickname" style="width:100%; height:38px; border-radius:8px; border:1px solid rgba(255,255,255,0.15); background:rgba(255,255,255,0.06); color:#fff; padding:0 10px; font-size:0.88rem; box-sizing:border-box;" placeholder="星穹旅人">
            </div>
            <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px; margin-bottom:16px;">
              <div>
                <label style="display:block; font-size:0.8rem; color:#cbd5e1; margin-bottom:4px;">性格色彩</label>
                <select id="reg-color" style="width:100%; height:36px; border-radius:8px; border:1px solid rgba(255,255,255,0.15); background:#1e293b; color:#fff; padding:0 8px; font-size:0.82rem; box-sizing:border-box;">
                  <option value="BLUE">🔵 静谧理性</option>
                  <option value="YELLOW">🟡 璀璨治愈</option>
                  <option value="RED">🔴 烈焰开拓</option>
                  <option value="GREEN">🟢 深林共情</option>
                </select>
              </div>
              <div>
                <label style="display:block; font-size:0.8rem; color:#cbd5e1; margin-bottom:4px;">星象星座</label>
                <select id="reg-zodiac" style="width:100%; height:36px; border-radius:8px; border:1px solid rgba(255,255,255,0.15); background:#1e293b; color:#fff; padding:0 8px; font-size:0.82rem; box-sizing:border-box;">
                  <option value="天秤座" selected>天秤座</option>
                  <option value="白羊座">白羊座</option>
                  <option value="双子座">双子座</option>
                  <option value="天蝎座">天蝎座</option>
                  <option value="水瓶座">水瓶座</option>
                </select>
              </div>
            </div>
          </div>
          <button type="submit" id="auth-submit-btn" style="width:100%; height:40px; border-radius:8px; border:none; background:#4f46e5; color:#fff; font-weight:600; font-size:0.92rem; cursor:pointer;">立即登录</button>
          <div id="auth-switch-text" style="text-align:center; margin-top:14px; font-size:0.82rem; color:#94a3b8;"></div>
        </form>
      </div>
    </div>
  `;
  document.body.insertAdjacentHTML('beforeend', modalHTML);
}

// 登录/注册弹窗控制
function openAuthModal(mode = 'login') {
  ensureAuthModalDOM();
  const modal = document.getElementById("auth-modal");
  if (!modal) return;
  modal.style.display = "flex";
  switchAuthTab(mode);
}

function closeAuthModal() {
  const modal = document.getElementById("auth-modal");
  if (modal) modal.style.display = "none";
}

function switchAuthTab(mode) {
  const isLogin = mode === 'login';
  document.getElementById("modal-title").innerText = isLogin ? "登录 DreamClip 宇宙" : "开启你的角色宇宙身份";
  document.getElementById("login-fields").style.display = isLogin ? "block" : "none";
  document.getElementById("register-fields").style.display = isLogin ? "none" : "block";
  document.getElementById("auth-submit-btn").innerText = isLogin ? "立即登录" : "创建专属身份";
  document.getElementById("auth-switch-text").innerHTML = isLogin 
    ? `还没有角色身份？<a href="javascript:void(0)" onclick="switchAuthTab('register')" style="color:#818cf8; text-decoration:none; font-weight:600;">立即加入宇宙</a>`
    : `已有账号？<a href="javascript:void(0)" onclick="switchAuthTab('login')" style="color:#818cf8; text-decoration:none; font-weight:600;">直接登录</a>`;
  document.getElementById("auth-form").dataset.mode = mode;
}

async function handleAuthSubmit(event) {
  event.preventDefault();
  const form = document.getElementById("auth-form");
  const mode = form.dataset.mode;
  const msgEl = document.getElementById("auth-error-msg");
  msgEl.style.display = "none";

  if (mode === 'login') {
    const u = document.getElementById("login-username").value.trim();
    const p = document.getElementById("login-password").value.trim();
    if (!u || !p) return showAuthError("请输入账号和密码");

    const res = await DreamClipAPI.auth.login(u, p);
    if (res.code === 200 && res.data) {
      setAuthCookie('mcp_token', res.data.access_token, 7);
      setAuthCookie('mcp_user', JSON.stringify(res.data.user_info), 7);
      setAuthCookie('dreamclip_token', res.data.access_token, 7);
      setAuthCookie('dreamclip_user', JSON.stringify(res.data.user_info), 7);
      localStorage.setItem("dreamclip_token", res.data.access_token);
      localStorage.setItem("dreamclip_user", JSON.stringify(res.data.user_info));
      localStorage.setItem("mcp_token", res.data.access_token);
      localStorage.setItem("mcp_user", JSON.stringify(res.data.user_info));
      closeAuthModal();
      window.location.reload();
    } else {
      showAuthError(res.message || "登录失败，请检查账号密码");
    }
  } else {
    const u = document.getElementById("reg-username").value.trim();
    const p = document.getElementById("reg-password").value.trim();
    const n = document.getElementById("reg-nickname").value.trim();
    const color = document.getElementById("reg-color").value;
    const zodiac = document.getElementById("reg-zodiac").value;

    if (!u || !p) return showAuthError("请填写用户名和密码");

    const res = await DreamClipAPI.auth.register(u, p, n, color, zodiac);
    if (res.code === 200 && res.data) {
      setAuthCookie('mcp_token', res.data.access_token, 7);
      setAuthCookie('mcp_user', JSON.stringify(res.data.user_info), 7);
      setAuthCookie('dreamclip_token', res.data.access_token, 7);
      setAuthCookie('dreamclip_user', JSON.stringify(res.data.user_info), 7);
      localStorage.setItem("dreamclip_token", res.data.access_token);
      localStorage.setItem("dreamclip_user", JSON.stringify(res.data.user_info));
      localStorage.setItem("mcp_token", res.data.access_token);
      localStorage.setItem("mcp_user", JSON.stringify(res.data.user_info));
      closeAuthModal();
      window.location.reload();
    } else {
      showAuthError(res.message || "注册失败");
    }
  }
}

function showAuthError(msg) {
  const msgEl = document.getElementById("auth-error-msg");
  msgEl.innerText = msg;
  msgEl.style.display = "block";
}
