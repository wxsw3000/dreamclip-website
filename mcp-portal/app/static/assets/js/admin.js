// MagicStar MCP (Modular Configuration Platform) Control Console Core JS
// Supports direct Base service (8000) and Portal Reverse Proxy (/admin)

const API_BASE = '/api/v1';

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

async function api(path, options = {}) {
  const token = getToken();
  const headers = {
    'Content-Type': 'application/json',
    ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
    ...(options.headers || {})
  };

  try {
    const resp = await fetch(API_BASE + path, { ...options, headers });
    if (resp.status === 401) {
      localStorage.removeItem('mcp_token');
      localStorage.removeItem('mcp_user');
      window.location.href = '/login?redirect=' + encodeURIComponent(window.location.pathname);
      return null;
    }
    return await resp.json();
  } catch (e) {
    console.error("API Request error:", e);
    showToast("接口请求失败: " + e.message, "danger");
    return null;
  }
}

function showToast(msg, type = 'info') {
  const c = document.getElementById('toastContainer');
  if (!c) return;
  const t = document.createElement('div');
  t.className = `toast toast-${type}`;
  t.innerText = msg;
  c.appendChild(t);
  setTimeout(() => t.remove(), 3200);
}

function switchTab(tabId, el) {
  document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  
  const target = document.getElementById(tabId);
  if (target) target.classList.add('active');
  if (el) el.classList.add('active');

  const titles = {
    'tab-dashboard': '<span>📊</span> MagicStar MCP 模块化配置平台大盘',
    'tab-services': '<span>🔌</span> 微服务接入与健康治理',
    'tab-users': '<span>👥</span> 用户与权限中心',
    'tab-configs': '<span>⚙️</span> 字典与全局参数设置'
  };
  if (titles[tabId]) {
    document.getElementById('pageTitle').innerHTML = titles[tabId];
  }

  if (tabId === 'tab-dashboard') loadDashboard();
  if (tabId === 'tab-services') loadMicroservices();
  if (tabId === 'tab-users') loadUsers();
  if (tabId === 'tab-configs') loadConfigs();
}

function refreshCurrentTab() {
  const activeTab = document.querySelector('.tab-pane.active');
  if (activeTab) switchTab(activeTab.id);
  showToast("数据已实时刷新", "info");
}

function handleLogout() {
  localStorage.removeItem('mcp_token');
  localStorage.removeItem('mcp_user');
  window.location.href = '/login';
}

function openModal(id) {
  const m = document.getElementById(id);
  if (m) m.classList.add('show');
}

function closeModal(id) {
  const m = document.getElementById(id);
  if (m) m.classList.remove('show');
}

// ---------------- 1. Dashboard ----------------
async function loadDashboard() {
  const res = await api('/dashboard/stats');
  if (!res || res.code !== 200) return;

  const d = res.data;
  document.getElementById('statServicesTotal').innerText = d.microservices.total;
  document.getElementById('statServicesHealthy').innerText = d.microservices.healthy;
  document.getElementById('statUsersTotal').innerText = d.users.total;

  // 渲染大盘微服务简表
  const svcRes = await api('/microservices?size=10');
  if (svcRes && svcRes.code === 200) {
    const tbody = document.getElementById('dashboardServicesTable');
    if (svcRes.data.records.length === 0) {
      tbody.innerHTML = '<tr><td colspan="9" style="text-align:center;color:#94a3b8;">暂无接入的微服务</td></tr>';
    } else {
      tbody.innerHTML = svcRes.data.records.map(s => `
        <tr>
          <td><code>${s.service_code}</code></td>
          <td><strong>${s.service_name}</strong></td>
          <td><span class="badge badge-tenant">${s.category || 'BASE'}</span></td>
          <td><span class="badge badge-tech">${s.tech_stack || 'PYTHON'}</span></td>
          <td><code>${s.base_url}</code></td>
          <td>${getHealthBadge(s.health_status)}</td>
          <td>${s.response_time_ms ? s.response_time_ms + 'ms' : '-'}</td>
          <td>${s.last_heartbeat ? s.last_heartbeat.replace('T', ' ').substring(0, 19) : '-'}</td>
          <td style="white-space:nowrap;">
            <button class="btn btn-outline btn-sm" onclick="probeService(${s.id})">🔍 探测</button>
          </td>
        </tr>
      `).join('');
    }
  }

  // 渲染登录日志
  const lbody = document.getElementById('dashboardLoginsTable');
  if (d.recent_logins && d.recent_logins.length > 0) {
    lbody.innerHTML = d.recent_logins.map(l => `
      <tr>
        <td><strong>${l.username}</strong></td>
        <td><span class="badge ${l.status === 'SUCCESS' ? 'badge-success' : 'badge-danger'}">${l.status}</span></td>
        <td>${l.login_time}</td>
        <td>${l.msg || '-'}</td>
      </tr>
    `).join('');
  }
}

function getHealthBadge(status) {
  if (status === 'HEALTHY') return '<span class="badge badge-success">🟢 在线健康</span>';
  if (status === 'UNHEALTHY') return '<span class="badge badge-warning">🟡 响应异常</span>';
  if (status === 'DOWN') return '<span class="badge badge-danger">🔴 离线/不可达</span>';
  return '<span class="badge badge-warning">⚪ 未检测</span>';
}

function getDocsLink(s) {
  if (!s.docs_url) return '<span style="color:#94a3b8;">-</span>';
  let url = s.base_url + s.docs_url;
  if (s.service_code === 'mcp-base') {
    url = '/base/docs';
  } else if (s.service_code === 'mcp-service-universe') {
    url = '/universe/docs';
  }
  return `<a href="${url}" target="_blank" style="color:#2563eb; text-decoration:none; font-weight:600;">📖 文档 ↗</a>`;
}

// ---------------- 2. Microservices ----------------
async function loadMicroservices() {
  const res = await api('/microservices?size=50');
  const tbody = document.getElementById('serviceListTable');
  if (!res || res.code !== 200 || res.data.records.length === 0) {
    tbody.innerHTML = '<tr><td colspan="8" style="text-align:center;color:#94a3b8;">暂无接入的微服务</td></tr>';
    return;
  }

  tbody.innerHTML = res.data.records.map(s => `
    <tr>
      <td><code>${s.service_code}</code></td>
      <td><strong>${s.service_name}</strong></td>
      <td><code>${s.base_url}</code></td>
      <td>${getHealthBadge(s.health_status)}</td>
      <td>${s.response_time_ms ? s.response_time_ms + 'ms' : '-'}</td>
      <td>${s.last_heartbeat ? s.last_heartbeat.replace('T', ' ').substring(0, 19) : '-'}</td>
      <td>
        ${getDocsLink(s)}
      </td>
      <td style="white-space:nowrap;">
        <button class="btn btn-outline btn-sm" onclick="editService(${s.id})">✏️ 编辑</button>
        <button class="btn btn-outline btn-sm" onclick="probeService(${s.id})">🔍 探测</button>
        <button class="btn btn-outline btn-sm" style="color:var(--danger)" onclick="deleteService(${s.id})">注销</button>
      </td>
    </tr>
  `).join('');
}

async function probeService(id) {
  showToast("正在发起健康心跳探测...", "info");
  const res = await api(`/microservices/${id}/probe`, { method: 'POST' });
  if (res && res.code === 200) {
    const d = res.data;
    const msg = `探测结果: ${d.health_status === 'HEALTHY' ? '🟢 正常在线' : '🔴 离线 (' + (d.error_msg || '') + ')'} (耗时: ${d.response_time_ms}ms)`;
    showToast(msg, d.health_status === 'HEALTHY' ? 'success' : 'danger');
    const activeTab = document.querySelector('.tab-pane.active');
    if (activeTab && activeTab.id === 'tab-dashboard') loadDashboard();
    else loadMicroservices();
  } else {
    showToast(res ? res.message : "探测失败", "danger");
  }
}

function openRegisterServiceModal() {
  document.getElementById('serviceForm').reset();
  document.getElementById('svc_id').value = '';
  document.getElementById('svc_code').disabled = false;
  document.getElementById('serviceModalTitle').innerText = '登记接入新微服务';
  document.getElementById('svcSubmitBtn').innerText = '提 交 接入';
  openModal('serviceModal');
}

async function editService(id) {
  const res = await api(`/microservices/${id}`);
  if (!res || res.code !== 200) {
    showToast("获取微服务信息失败", "danger");
    return;
  }
  const s = res.data;
  document.getElementById('svc_id').value = s.id;
  document.getElementById('svc_code').value = s.service_code;
  document.getElementById('svc_code').disabled = true; // 编码不可修改
  document.getElementById('svc_name').value = s.service_name;
  document.getElementById('svc_url').value = s.base_url;
  document.getElementById('svc_health').value = s.health_url;
  document.getElementById('svc_docs').value = s.docs_url || '';
  document.getElementById('svc_desc').value = s.description || '';
  document.getElementById('serviceModalTitle').innerText = `编辑微服务配置: ${s.service_code}`;
  document.getElementById('svcSubmitBtn').innerText = '保存微服务配置';
  openModal('serviceModal');
}

async function saveService(e) {
  e.preventDefault();
  const svcId = document.getElementById('svc_id').value;
  const payload = {
    service_code: document.getElementById('svc_code').value.trim(),
    service_name: document.getElementById('svc_name').value.trim(),
    base_url: document.getElementById('svc_url').value.trim(),
    health_url: document.getElementById('svc_health').value.trim(),
    docs_url: document.getElementById('svc_docs').value.trim(),
    description: document.getElementById('svc_desc').value.trim()
  };

  let res;
  if (svcId) {
    res = await api(`/microservices/${svcId}`, {
      method: 'PUT',
      body: JSON.stringify(payload)
    });
  } else {
    res = await api('/microservices/register', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  }

  if (res && res.code === 200) {
    showToast(svcId ? "微服务配置修改成功并已完成重新探测" : "微服务已成功接入并完成初始健康探测", "success");
    closeModal('serviceModal');
    loadMicroservices();
  } else {
    showToast(res ? res.message : "保存失败", "danger");
  }
}

async function deleteService(id) {
  if (!confirm("确定要下线并注销该微服务吗？")) return;
  const res = await api(`/microservices/${id}`, { method: 'DELETE' });
  if (res && res.code === 200) {
    showToast("微服务已注销", "success");
    loadMicroservices();
  }
}

// ---------------- 3. Users ----------------
async function loadUsers() {
  const res = await api('/system/users?size=50');
  const tbody = document.getElementById('userListTable');
  if (!res || res.code !== 200 || res.data.records.length === 0) {
    tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;color:#94a3b8;">暂无用户数据</td></tr>';
    return;
  }

  tbody.innerHTML = res.data.records.map(u => `
    <tr>
      <td><code>${u.username}</code></td>
      <td><strong>${u.real_name || u.username}</strong></td>
      <td>${u.personality_color ? `<span class="badge" style="background:${u.personality_color}22; color:${u.personality_color}; border:1px solid ${u.personality_color}55;">🎨 ${u.personality_color}</span>` : '<span style="color:#94a3b8;">-</span>'}</td>
      <td>${u.zodiac ? `<span class="badge badge-tenant">✨ ${u.zodiac}</span>` : '<span style="color:#94a3b8;">-</span>'}</td>
      <td>${u.is_superadmin ? '<span class="badge badge-danger">👑 超级管理员</span>' : '<span class="badge badge-outline">注册用户</span>'}</td>
      <td><span class="badge ${u.status === 'ACTIVE' ? 'badge-success' : 'badge-danger'}">${u.status}</span></td>
      <td>${u.created_at ? u.created_at.replace('T', ' ').substring(0, 19) : '-'}</td>
    </tr>
  `).join('');
}

function openUserModal() {
  document.getElementById('userForm').reset();
  openModal('userModal');
}

async function saveNewUser(e) {
  e.preventDefault();
  const payload = {
    username: document.getElementById('new_username').value.trim(),
    password: document.getElementById('new_password').value,
    real_name: document.getElementById('new_real_name').value.trim(),
    email: document.getElementById('new_email').value.trim() || undefined,
    personality_color: document.getElementById('new_personality').value.trim() || undefined,
    zodiac: document.getElementById('new_zodiac').value.trim() || undefined
  };

  const res = await api('/auth/register', {
    method: 'POST',
    body: JSON.stringify(payload)
  });

  if (res && res.code === 200) {
    showToast("用户创建成功！", "success");
    closeModal('userModal');
    loadUsers();
  } else {
    showToast(res ? res.message : "创建失败", "danger");
  }
}

// ---------------- 4. Configs ----------------
async function loadConfigs() {
  const res = await api('/system/configs');
  const tbody = document.getElementById('configListTable');
  if (!res || res.code !== 200 || res.data.length === 0) {
    tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;color:#94a3b8;">暂无全局参数</td></tr>';
    return;
  }

  tbody.innerHTML = res.data.map(c => `
    <tr>
      <td><code>${c.config_key}</code></td>
      <td><strong>${c.config_name}</strong></td>
      <td><input type="text" class="form-control" style="width:280px; display:inline-block;" value="${c.config_value}" id="cfg_${c.id}"></td>
      <td>${c.is_system ? '<span class="badge badge-tenant">系统核心</span>' : '业务参数'}</td>
      <td>
        <button class="btn btn-primary btn-sm" onclick="updateConfig('${c.config_key}', 'cfg_${c.id}')">💾 保存</button>
      </td>
    </tr>
  `).join('');
}

async function updateConfig(key, inputId) {
  const val = document.getElementById(inputId).value;
  const res = await api(`/system/configs/${key}`, {
    method: 'PUT',
    body: JSON.stringify({ config_value: val })
  });
  if (res && res.code === 200) {
    showToast("参数保存成功", "success");
  } else {
    showToast(res ? res.message : "保存失败", "danger");
  }
}

// ---------------- 初始化 ----------------
window.addEventListener('DOMContentLoaded', () => {
  // 支持跨子域名重定向时携带 Token 自动存入当前域 localStorage
  const urlParams = new URLSearchParams(window.location.search);
  const tokenFromUrl = urlParams.get('mcp_token');
  const userFromUrl = urlParams.get('mcp_user');
  if (tokenFromUrl) {
    localStorage.setItem('mcp_token', tokenFromUrl);
    if (userFromUrl) {
      localStorage.setItem('mcp_user', decodeURIComponent(userFromUrl));
    }
    urlParams.delete('mcp_token');
    urlParams.delete('mcp_user');
    const newSearch = urlParams.toString();
    const newUrl = window.location.pathname + (newSearch ? '?' + newSearch : '') + window.location.hash;
    window.history.replaceState({}, document.title, newUrl);
  }

  const token = getToken();
  if (!token) {
    window.location.href = '/login?redirect=' + encodeURIComponent(window.location.pathname);
    return;
  }
  const user = getUser();
  if (user) {
    document.getElementById('userName').innerText = user.username || 'superadmin';
    document.getElementById('avatarText').innerText = (user.username || 'SA').substring(0, 2).toUpperCase();
    if (user.is_superadmin) {
      document.getElementById('userRoleTag').innerText = "平台超级管理员";
    }
  }
  loadDashboard();
});
