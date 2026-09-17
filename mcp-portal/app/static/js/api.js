/**
 * DreamClip 客户端统一 API 与状态管理
 */
const DreamClipAPI = {
  // 基础请求封装
  async request(endpoint, options = {}) {
    const token = localStorage.getItem("dreamclip_token");
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
  auth: {
    async register(username, password, realName, personalityColor, zodiac) {
      return await DreamClipAPI.request("/api/base/auth/register", {
        method: "POST",
        body: JSON.stringify({
          username,
          password,
          real_name: realName,
          personality_color: personalityColor,
          zodiac: zodiac
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
      window.location.reload();
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
  const userJson = localStorage.getItem("dreamclip_user");
  const authContainer = document.getElementById("header-auth-area");
  if (!authContainer) return;

  if (userJson) {
    try {
      const user = JSON.parse(userJson);
      const colorMap = {
        RED: { label: "烈焰开拓", color: "var(--accent-red)" },
        BLUE: { label: "静谧理性", color: "var(--accent-blue)" },
        YELLOW: { label: "璀璨治愈", color: "var(--accent-yellow)" },
        GREEN: { label: "深林共情", color: "var(--accent-green)" }
      };
      const colorInfo = colorMap[user.personality_color] || colorMap.BLUE;

      authContainer.innerHTML = `
        <div class="user-badge" onclick="toggleUserDropdown()">
          <img class="user-avatar-mini" src="${user.avatar || 'https://api.dicebear.com/7.x/bottts/svg?seed=' + user.username}" alt="avatar">
          <span style="font-size:0.85rem; font-weight:600;">${user.real_name || user.username}</span>
          <span style="font-size:0.7rem; color:${colorInfo.color}; background:rgba(255,255,255,0.08); padding:0.1rem 0.4rem; border-radius:6px;">${user.zodiac || colorInfo.label}</span>
        </div>
        <button class="btn btn-outline" style="padding:0.35rem 0.65rem; font-size:0.8rem;" onclick="DreamClipAPI.auth.logout()">退出</button>
      `;
    } catch (e) {
      localStorage.removeItem("dreamclip_user");
    }
  } else {
    authContainer.innerHTML = `
      <button class="btn btn-outline" onclick="openAuthModal('login')">登录</button>
      <button class="btn btn-primary" onclick="openAuthModal('register')">加入宇宙</button>
    `;
  }
}

// 登录/注册弹窗控制
function openAuthModal(mode = 'login') {
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
    ? `还没有角色身份？<a href="javascript:void(0)" onclick="switchAuthTab('register')" style="color:var(--accent-indigo);">立即加入宇宙</a>`
    : `已有账号？<a href="javascript:void(0)" onclick="switchAuthTab('login')" style="color:var(--accent-indigo);">直接登录</a>`;
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
    if (res.code === 200) {
      localStorage.setItem("dreamclip_token", res.data.access_token);
      localStorage.setItem("dreamclip_user", JSON.stringify(res.data.user_info));
      closeAuthModal();
      window.location.reload();
    } else {
      showAuthError(res.message);
    }
  } else {
    const u = document.getElementById("reg-username").value.trim();
    const p = document.getElementById("reg-password").value.trim();
    const n = document.getElementById("reg-nickname").value.trim();
    const color = document.getElementById("reg-color").value;
    const zodiac = document.getElementById("reg-zodiac").value;

    if (!u || !p) return showAuthError("请填写用户名和密码");

    const res = await DreamClipAPI.auth.register(u, p, n, color, zodiac);
    if (res.code === 200) {
      localStorage.setItem("dreamclip_token", res.data.access_token);
      localStorage.setItem("dreamclip_user", JSON.stringify(res.data.user_info));
      closeAuthModal();
      window.location.reload();
    } else {
      showAuthError(res.message);
    }
  }
}

function showAuthError(msg) {
  const msgEl = document.getElementById("auth-error-msg");
  msgEl.innerText = msg;
  msgEl.style.display = "block";
}
