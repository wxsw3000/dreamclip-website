/**
 * DreamClip 客户端统一 API 与状态管理
 */
const DreamClipAPI = {
  // 基础请求封装
  async request(endpoint, options = {}) {
    const token = localStorage.getItem("dreamclip_token") || localStorage.getItem("mcp_token");
    const headers = {
      "Content-Type": "application/json",
      ...(options.headers || {})
    };
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    try {
      const resp = await fetch(endpoint, {
        ...options,
        headers
      });
      const data = await resp.json();
      return data;
    } catch (err) {
      console.error("API Request Error:", endpoint, err);
      return { code: 500, message: "网络连接异常，请稍后重试" };
    }
  },

  // 认证与用户 API
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
      return await DreamClipAPI.request("/api/base/auth/me");
    },

    logout() {
      localStorage.removeItem("dreamclip_token");
      localStorage.removeItem("dreamclip_user");
      localStorage.removeItem("mcp_token");
      localStorage.removeItem("mcp_user");
      window.location.href = DreamClipAPI.auth.getLoginUrl('login');
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

    async getCapsules(params = {}) {
      const query = new URLSearchParams(params).toString();
      return await DreamClipAPI.request(`/api/universe/capsules?${query}`);
    },

    async getCapsuleDetail(idOrSlug) {
      return await DreamClipAPI.request(`/api/universe/capsules/${idOrSlug}`);
    },

    async likeCapsule(id) {
      return await DreamClipAPI.request(`/api/universe/capsules/${id}/like`, { method: "POST" });
    },

    async getAvgChapters(params = {}) {
      const query = new URLSearchParams(params).toString();
      return await DreamClipAPI.request(`/api/universe/avg/chapters?${query}`);
    }
  }
};

// 全局 UI 辅助函数
document.addEventListener("DOMContentLoaded", () => {
  initUserSessionUI();
});

function initUserSessionUI() {
  const userJson = localStorage.getItem("dreamclip_user") || localStorage.getItem("mcp_user");
  const authContainer = document.getElementById("header-auth-area");
  if (!authContainer) return;

  if (userJson) {
    try {
      const user = JSON.parse(userJson);
      authContainer.innerHTML = `
        <a href="/portal" class="btn btn-outline" style="padding:0.35rem 0.75rem; font-size:0.82rem; margin-right:6px;" title="进入应用工作台">📱 平台桌面</a>
        <div class="user-badge" style="display:inline-flex; align-items:center; gap:0.4rem; background:rgba(255,255,255,0.06); padding:0.25rem 0.6rem; border-radius:20px; border:1px solid rgba(255,255,255,0.12);">
          <img class="user-avatar-mini" style="width:22px; height:22px; border-radius:50%;" src="${user.avatar || 'https://api.dicebear.com/7.x/bottts/svg?seed=' + user.username}" alt="avatar">
          <span style="font-size:0.85rem; font-weight:600; color:#fff;">${user.real_name || user.username}</span>
          <span style="font-size:0.7rem; color:#818cf8; background:rgba(99,102,241,0.15); border:1px solid rgba(99,102,241,0.3); padding:0.1rem 0.4rem; border-radius:6px;">会员</span>
        </div>
        <button class="btn btn-outline" style="padding:0.35rem 0.65rem; font-size:0.8rem; margin-left:6px;" onclick="DreamClipAPI.auth.logout()">退出</button>
      `;
    } catch (e) {
      localStorage.removeItem("dreamclip_user");
      localStorage.removeItem("mcp_user");
    }
  } else {
    const loginUrl = DreamClipAPI.auth.getLoginUrl('login');
    const registerUrl = DreamClipAPI.auth.getLoginUrl('register');
    authContainer.innerHTML = `
      <a href="/portal" class="btn btn-outline" style="padding:0.35rem 0.75rem; font-size:0.82rem; margin-right:6px;">📱 平台桌面</a>
      <a href="${loginUrl}" class="btn btn-outline" style="padding:0.35rem 0.75rem; font-size:0.82rem; margin-right:6px;">登录</a>
      <a href="${registerUrl}" class="btn btn-primary" style="padding:0.35rem 0.75rem; font-size:0.82rem;">✨ 立即注册</a>
    `;
  }
}

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
