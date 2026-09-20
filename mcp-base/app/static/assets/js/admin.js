// MagicStar MCP (Modular Configuration Platform) Control Console Core JS
// Supports direct Base service (8000) and Portal Reverse Proxy (/admin)

const API_BASE = '/api/v1';

function setAuthCookie(name, value, days = 7) {
  const isOnline = window.location.hostname.endsWith('dreamclip.cn');
  const domainPart = isOnline ? '; domain=.dreamclip.cn' : '';
  let maxAgePart = '';
  if (typeof days === 'number' && days > 0) {
    maxAgePart = `; max-age=${days * 24 * 60 * 60}`;
  }
  document.cookie = `${name}=${encodeURIComponent(value)}${domainPart}; path=/; SameSite=Lax${maxAgePart}`;
}

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

function clearAuthCookie(name) {
  const isOnline = window.location.hostname.endsWith('dreamclip.cn');
  const domainPart = isOnline ? '; domain=.dreamclip.cn' : '';
  document.cookie = `${name}=; path=/; domain=.dreamclip.cn; max-age=0; expires=Thu, 01 Jan 1970 00:00:00 GMT`;
  document.cookie = `${name}=; path=/; max-age=0; expires=Thu, 01 Jan 1970 00:00:00 GMT`;
}

function getToken() {
  const isOnline = window.location.hostname.endsWith('dreamclip.cn');
  if (isOnline) {
    const cookieToken = getAuthCookie('mcp_token') || getAuthCookie('dreamclip_token');
    if (!cookieToken) {
      // 线上环境若主域 SSO Cookie 已被注销，彻底清理本地孤立缓存并视作未登录
      localStorage.removeItem('mcp_token');
      localStorage.removeItem('mcp_user');
      localStorage.removeItem('dreamclip_token');
      localStorage.removeItem('dreamclip_user');
      return null;
    }
    return cookieToken;
  }
  return localStorage.getItem('mcp_token') || localStorage.getItem('dreamclip_token');
}

function getUser() {
  const isOnline = window.location.hostname.endsWith('dreamclip.cn');
  if (isOnline && !(getAuthCookie('mcp_token') || getAuthCookie('dreamclip_token'))) {
    return null;
  }
  try {
    const rawCookie = getAuthCookie('mcp_user') || getAuthCookie('dreamclip_user');
    const raw = rawCookie || localStorage.getItem('mcp_user') || localStorage.getItem('dreamclip_user');
    return raw ? (typeof raw === 'object' ? raw : JSON.parse(raw)) : null;
  } catch (e) {
    return null;
  }
}

function getLoginUrl(isLogout = false) {
  const isOnline = window.location.hostname.endsWith('dreamclip.cn');
  const base = isOnline ? 'https://login.dreamclip.cn/' : '/login';
  return isLogout ? `${base}?logout=true` : base;
}

function redirectToLogin(isLogout = false) {
  clearAuthCookie('mcp_token');
  clearAuthCookie('mcp_user');
  clearAuthCookie('dreamclip_token');
  clearAuthCookie('dreamclip_user');
  localStorage.removeItem('mcp_token');
  localStorage.removeItem('mcp_user');
  localStorage.removeItem('dreamclip_token');
  localStorage.removeItem('dreamclip_user');
  sessionStorage.clear();
  window.location.href = getLoginUrl(isLogout);
}

function handleLogout() {
  redirectToLogin(true);
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
      redirectToLogin();
      return null;
    }

    let data;
    try {
      data = await resp.json();
    } catch (parseErr) {
      data = null;
    }

    if (!resp.ok) {
      let errMsg = "请求失败";
      if (data) {
        if (typeof data.message === 'string' && data.message) {
          errMsg = data.message;
        } else if (typeof data.detail === 'string' && data.detail) {
          errMsg = data.detail;
        } else if (Array.isArray(data.detail) && data.detail.length > 0) {
          errMsg = data.detail.map(d => (d.loc ? d.loc.join('.') + ': ' : '') + (d.msg || JSON.stringify(d))).join('; ');
        } else if (typeof data === 'object') {
          errMsg = JSON.stringify(data);
        }
      } else {
        errMsg = `网络响应错误 (${resp.status})`;
      }
      return { code: resp.status, message: errMsg, data: null };
    }

    if (data && typeof data === 'object') {
      if (data.code === undefined) data.code = resp.status;
      if (data.message === undefined) data.message = "success";
    }

    return data;
  } catch (e) {
    console.error("API Request error:", e);
    showToast("接口请求失败: " + e.message, "danger");
    return { code: 500, message: e.message, data: null };
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
    'tab-dashboard': '控制台总览大盘',
    'tab-services': '微服务接入与健康治理',
    'tab-users': '用户与角色权限中心',
    'tab-configs': '字典与全局参数设置'
  };
  const titleIcons = {
    'tab-dashboard': '📊',
    'tab-services': '🔌',
    'tab-users': '👥',
    'tab-configs': '⚙️'
  };
  if (titles[tabId]) {
    const titleEl = document.getElementById('pageTitle');
    const iconEl = document.getElementById('pageTitleIcon');
    if (titleEl) titleEl.innerText = titles[tabId];
    if (iconEl && titleIcons[tabId]) iconEl.innerText = titleIcons[tabId];
  }

  if (tabId === 'tab-dashboard') loadDashboard();
  if (tabId === 'tab-services') loadMicroservices();
  if (tabId === 'tab-users') {
    loadUsers();
    loadRoles();
  }
  if (tabId === 'tab-configs') loadConfigs();
}

function refreshCurrentTab() {
  const activeTab = document.querySelector('.tab-pane.active');
  if (activeTab) switchTab(activeTab.id);
  showToast("数据已实时刷新", "info");
}

function handleLogout() {
  redirectToLogin(true);
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
  if (!res || res.code !== 200 || !res.data) return;

  const d = res.data;
  document.getElementById('statServicesTotal').innerText = d.microservices.total;
  document.getElementById('statServicesHealthy').innerText = d.microservices.healthy;
  document.getElementById('statUsersTotal').innerText = d.users.total;

  // 渲染大盘微服务简表
  const svcTable = document.getElementById('dashboardServicesTable');
  if (svcTable && d.microservices.list) {
    if (d.microservices.list.length === 0) {
      svcTable.innerHTML = '<tr><td colspan="5" style="text-align:center; color:#94a3b8;">暂无注册微服务</td></tr>';
    } else {
      svcTable.innerHTML = d.microservices.list.map(s => `
        <tr>
          <td><strong>${s.service_name}</strong></td>
          <td><code>${s.service_code}</code></td>
          <td><span class="badge ${s.health_status === 'HEALTHY' ? 'badge-success' : 'badge-danger'}">${s.health_status}</span></td>
          <td>${s.response_time_ms ? s.response_time_ms.toFixed(1) + 'ms' : '-'}</td>
          <td>${s.last_heartbeat ? s.last_heartbeat.replace('T', ' ').substring(0, 19) : '-'}</td>
        </tr>
      `).join('');
    }
  }

  // 渲染登录日志
  const loginTable = document.getElementById('dashboardLoginsTable');
  if (loginTable && d.recent_logins) {
    if (d.recent_logins.length === 0) {
      loginTable.innerHTML = '<tr><td colspan="4" style="text-align:center; color:#94a3b8;">暂无登录日志</td></tr>';
    } else {
      loginTable.innerHTML = d.recent_logins.map(l => `
        <tr>
          <td><code>${l.username}</code></td>
          <td><span class="badge ${l.status === 'SUCCESS' ? 'badge-success' : 'badge-danger'}">${l.status}</span></td>
          <td>${l.created_at ? l.created_at.replace('T', ' ').substring(0, 19) : '-'}</td>
          <td>${l.msg || '-'}</td>
        </tr>
      `).join('');
    }
  }
}

// ---------------- 2. Microservices Management ----------------
let cachedServicesList = [];

async function loadMicroservices() {
  const res = await api('/microservices');
  const tbody = document.getElementById('serviceListTable');
  if (!tbody) return;
  if (!res || res.code !== 200 || !res.data || res.data.length === 0) {
    tbody.innerHTML = '<tr><td colspan="8" style="text-align:center;color:#94a3b8;">暂未注册任何微服务节点</td></tr>';
    return;
  }
  cachedServicesList = res.data;

  tbody.innerHTML = res.data.map(s => `
    <tr>
      <td><code>${s.service_code}</code></td>
      <td><strong>${s.service_name}</strong></td>
      <td><a href="${s.base_url}" target="_blank" style="color:var(--primary); text-decoration:none;">${s.base_url}</a></td>
      <td>
        <span class="badge ${s.health_status === 'HEALTHY' ? 'badge-success' : (s.health_status === 'DOWN' ? 'badge-danger' : 'badge-warning')}">
          ${s.health_status}
        </span>
      </td>
      <td>${s.response_time_ms ? s.response_time_ms.toFixed(1) + 'ms' : '-'}</td>
      <td>${s.last_heartbeat ? s.last_heartbeat.replace('T', ' ').substring(0, 19) : '-'}</td>
      <td>
        ${s.docs_url ? `<a href="${(s.base_url.endsWith('/') ? s.base_url.slice(0, -1) : s.base_url) + s.docs_url}" target="_blank" class="btn btn-outline btn-sm">Swagger</a>` : '-'}
      </td>
      <td style="white-space:nowrap;">
        <button class="btn btn-outline btn-sm" onclick="probeService(${s.id})">⚡ 探活</button>
        <button class="btn btn-outline btn-sm" onclick="openEditServiceModal(${s.id})">✏️ 编辑</button>
        ${!['mcp-base', 'mcp-portal'].includes(s.service_code) ? `<button class="btn btn-outline btn-sm" style="color:var(--danger)" onclick="deleteService(${s.id})">注销</button>` : ''}
      </td>
    </tr>
  `).join('');
}

async function probeService(id) {
  showToast("正在执行微服务健康探活...", "info");
  const res = await api(`/microservices/${id}/health-check`, { method: 'POST' });
  if (res && res.code === 200) {
    showToast(`探活完成: ${res.data.health_status} (${res.data.response_time_ms.toFixed(1)}ms)`, res.data.health_status === 'HEALTHY' ? 'success' : 'danger');
    loadMicroservices();
  } else {
    showToast(res ? res.message : "探活失败", "danger");
  }
}

function openRegisterServiceModal() {
  document.getElementById('serviceForm').reset();
  document.getElementById('svc_id').value = '';
  document.getElementById('svc_code').disabled = false;
  document.getElementById('serviceModalTitle').innerText = '登记接入新微服务节点';
  openModal('serviceModal');
}

function openEditServiceModal(id) {
  const s = cachedServicesList.find(item => item.id === id);
  if (!s) return;

  document.getElementById('svc_id').value = s.id;
  document.getElementById('svc_code').value = s.service_code;
  document.getElementById('svc_code').disabled = true; // 编码不可修改
  document.getElementById('svc_name').value = s.service_name;
  document.getElementById('svc_base_url').value = s.base_url;
  document.getElementById('svc_health_url').value = s.health_url || '/health';
  document.getElementById('svc_docs_url').value = s.docs_url || '/docs';
  document.getElementById('svc_gateway_prefix').value = s.gateway_prefix || '';
  document.getElementById('svc_tech_stack').value = s.tech_stack || 'PYTHON';
  document.getElementById('svc_category').value = s.category || 'BIZ';
  document.getElementById('svc_status').value = s.status || 'ACTIVE';
  document.getElementById('svc_desc').value = s.description || '';

  document.getElementById('serviceModalTitle').innerText = `编辑微服务: ${s.service_name}`;
  openModal('serviceModal');
}

async function saveService(e) {
  e.preventDefault();
  const svcId = document.getElementById('svc_id').value;
  const payload = {
    service_code: document.getElementById('svc_code').value.trim(),
    service_name: document.getElementById('svc_name').value.trim(),
    base_url: document.getElementById('svc_base_url').value.trim(),
    health_url: document.getElementById('svc_health_url').value.trim(),
    docs_url: document.getElementById('svc_docs_url').value.trim() || undefined,
    gateway_prefix: document.getElementById('svc_gateway_prefix').value.trim() || undefined,
    tech_stack: document.getElementById('svc_tech_stack').value,
    category: document.getElementById('svc_category').value,
    status: document.getElementById('svc_status').value,
    description: document.getElementById('svc_desc').value.trim() || undefined
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
    showToast(svcId ? "微服务配置修改成功" : "微服务接入注册成功！", "success");
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

// ---------------- 3. Users & Roles Management ----------------
let cachedRolesList = [];
let currentUserFilterRole = '';
let currentUserFilterStatus = '';
let currentUserSearchKeyword = '';

function filterUsersByRole(roleCode, btnEl) {
  currentUserFilterRole = roleCode;
  
  const buttons = document.querySelectorAll('#userRoleFilterBar button');
  buttons.forEach(b => {
    b.classList.remove('btn-primary');
    b.classList.add('btn-outline');
  });
  if (btnEl) {
    btnEl.classList.remove('btn-outline');
    btnEl.classList.add('btn-primary');
  }
  loadUsers();
}

function applyUserSearch() {
  const kwInput = document.getElementById('userSearchKeyword');
  const statusSelect = document.getElementById('userSearchStatus');
  currentUserSearchKeyword = kwInput ? kwInput.value.trim() : '';
  currentUserFilterStatus = statusSelect ? statusSelect.value : '';
  loadUsers();
}

async function toggleUserStatus(userId, currentStatus) {
  const newStatus = currentStatus === 'ACTIVE' ? 'DISABLED' : 'ACTIVE';
  const actionName = newStatus === 'ACTIVE' ? '启用/解封' : '停用/封禁';
  if (!confirm(`确定要${actionName}该用户账号吗？`)) return;

  const res = await api(`/system/users/${userId}`, {
    method: 'PUT',
    body: JSON.stringify({ status: newStatus })
  });

  if (res && res.code === 200) {
    showToast(`账号已成功${actionName}`, 'success');
    loadUsers();
  } else {
    showToast(res ? res.message : `${actionName}失败`, 'danger');
  }
}

async function loadUsers() {
  const params = new URLSearchParams({ size: '50' });
  if (currentUserFilterRole) params.append('role_code', currentUserFilterRole);
  if (currentUserFilterStatus) params.append('status', currentUserFilterStatus);
  if (currentUserSearchKeyword) params.append('keyword', currentUserSearchKeyword);

  const res = await api(`/system/users?${params.toString()}`);
  const tbody = document.getElementById('userListTable');
  const countBadge = document.getElementById('userCountBadge');
  if (!tbody) return;

  if (!res || res.code !== 200 || !res.data || !res.data.records) {
    tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;color:#94a3b8;">暂无用户数据</td></tr>';
    if (countBadge) countBadge.innerText = '共 0 位用户';
    return;
  }

  const total = res.data.total || res.data.records.length;
  if (countBadge) {
    const roleNameMap = {
      '': '全平台',
      'ROLE_MEMBER': '注册会员',
      'ROLE_OPERATOR': '系统运维',
      'ROLE_SUPER_ADMIN': '平台超管'
    };
    const prefix = roleNameMap[currentUserFilterRole] || currentUserFilterRole;
    countBadge.innerText = `${prefix}共 ${total} 位用户`;
  }

  if (res.data.records.length === 0) {
    tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;padding:24px;color:#94a3b8;">🔍 未找到符合条件的用户</td></tr>';
    return;
  }

  tbody.innerHTML = res.data.records.map(u => {
    const rolesStr = (u.roles && u.roles.length > 0)
      ? u.roles.map(r => {
          let badgeClass = 'badge-tech';
          if (r.role_code === 'ROLE_MEMBER') badgeClass = 'badge-tenant';
          if (r.role_code === 'ROLE_SUPER_ADMIN') badgeClass = 'badge-danger';
          if (r.role_code === 'ROLE_OPERATOR') badgeClass = 'badge-success';
          return `<span class="badge ${badgeClass}" title="${r.role_code}">${r.role_name}</span>`;
        }).join(' ')
      : '<span class="badge badge-outline">未分配角色</span>';

    const avatarUrl = u.avatar || `https://api.dicebear.com/7.x/bottts/svg?seed=${u.username}`;
    const isSuperAdmin = Boolean(u.is_superadmin || u.username === 'superadmin');

    return `
      <tr>
        <td>
          <div style="display:flex; align-items:center; gap:8px;">
            <img src="${avatarUrl}" style="width:26px; height:26px; border-radius:50%; background:#f1f5f9; border:1px solid #cbd5e1;" onerror="this.src='data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>👤</text></svg>'">
            <code>${u.username}</code>
          </div>
        </td>
        <td><strong>${u.real_name || u.username}</strong></td>
        <td>${u.email ? `<span style="font-size:12px; color:#475569;">${u.email}</span>` : '<span style="color:#94a3b8; font-size:12px;">-</span>'}</td>
        <td>${rolesStr}</td>
        <td>
          <span class="badge ${u.status === 'ACTIVE' ? 'badge-success' : 'badge-danger'}">
            ${u.status === 'ACTIVE' ? '🟢 正常' : '🔴 已禁用'}
          </span>
        </td>
        <td>${u.created_at ? u.created_at.replace('T', ' ').substring(0, 19) : '-'}</td>
        <td style="white-space:nowrap;">
          <button class="btn btn-outline btn-sm" onclick="openEditUserModal(${u.id})">✏️ 编辑/改密</button>
          ${!isSuperAdmin ? `
            <button class="btn btn-outline btn-sm" style="color:${u.status === 'ACTIVE' ? 'var(--warning-text)' : 'var(--success-text)'}" onclick="toggleUserStatus(${u.id}, '${u.status}')">
              ${u.status === 'ACTIVE' ? '🚫 封禁' : '🔓 解封'}
            </button>
            <button class="btn btn-outline btn-sm" style="color:var(--danger)" onclick="deleteUser(${u.id})">🗑️ 删除</button>
          ` : ''}
        </td>
      </tr>
    `;
  }).join('');
}

async function openEditUserModal(userId) {
  // 先获取全量角色列表
  const rolesRes = await api('/system/roles');
  if (rolesRes && rolesRes.code === 200 && rolesRes.data) {
    cachedRolesList = rolesRes.data;
  }

  const res = await api(`/system/users?size=100`);
  if (!res || res.code !== 200 || !res.data || !res.data.records) {
    showToast("获取用户列表失败", "danger");
    return;
  }

  const user = res.data.records.find(u => u.id === userId);
  if (!user) {
    showToast("未找到该用户信息", "danger");
    return;
  }

  document.getElementById('edit_user_id').value = user.id;
  document.getElementById('edit_user_username').value = user.username;
  document.getElementById('edit_user_realname').value = user.real_name || '';
  document.getElementById('edit_user_email').value = user.email || '';
  document.getElementById('edit_user_pwd').value = ''; // 留空则不修改密码
  document.getElementById('edit_user_status').value = user.status;
  document.getElementById('edit_user_superadmin').checked = Boolean(user.is_superadmin);

  // 渲染平台角色复选框
  const rolesContainer = document.getElementById('edit_user_roles_box');
  const userRoleIds = (user.roles || []).map(r => r.id);
  rolesContainer.innerHTML = cachedRolesList.map(r => `
    <label style="display:inline-flex; align-items:center; gap:6px; margin-right:14px; margin-bottom:6px; font-size:13px; font-weight:600; cursor:pointer;">
      <input type="checkbox" name="editUserRole" value="${r.id}" ${userRoleIds.includes(r.id) ? 'checked' : ''}>
      ${r.role_name} <span style="font-size:11px; color:#64748b; font-weight:normal;">(${r.role_code})</span>
    </label>
  `).join('');

  openModal('editUserModal');
}

async function saveEditUser(e) {
  e.preventDefault();
  const userId = document.getElementById('edit_user_id').value;
  const pwdVal = document.getElementById('edit_user_pwd').value.trim();
  
  const selectedRoleIds = Array.from(document.querySelectorAll('input[name="editUserRole"]:checked'))
    .map(cb => parseInt(cb.value));

  const payload = {
    real_name: document.getElementById('edit_user_realname').value.trim(),
    email: document.getElementById('edit_user_email').value.trim() || undefined,
    status: document.getElementById('edit_user_status').value,
    role_ids: selectedRoleIds
  };

  if (pwdVal) {
    payload.password = pwdVal;
  }

  const res = await api(`/system/users/${userId}`, {
    method: 'PUT',
    body: JSON.stringify(payload)
  });

  if (res && res.code === 200) {
    showToast("用户信息与密码修改成功！", "success");
    closeModal('editUserModal');
    loadUsers();
  } else {
    showToast(res ? res.message : "修改失败", "danger");
  }
}

async function deleteUser(userId) {
  if (!confirm("确定要删除该用户账号吗？")) return;
  const res = await api(`/system/users/${userId}`, { method: 'DELETE' });
  if (res && res.code === 200) {
    showToast("用户已删除", "success");
    loadUsers();
  } else {
    showToast(res ? res.message : "删除失败", "danger");
  }
}

async function openUserModal() {
  document.getElementById('userForm').reset();
  const rolesRes = await api('/system/roles');
  if (rolesRes && rolesRes.code === 200 && rolesRes.data) {
    cachedRolesList = rolesRes.data;
  }
  const container = document.getElementById('new_user_roles_box');
  if (container) {
    container.innerHTML = cachedRolesList.map(r => `
      <label style="display:inline-flex; align-items:center; gap:6px; margin-right:14px; margin-bottom:6px; font-size:13px; font-weight:600; cursor:pointer;">
        <input type="checkbox" name="newUserRole" value="${r.id}" ${r.role_code === 'ROLE_MEMBER' ? 'checked' : ''}>
        ${r.role_name} <span style="font-size:11px; color:#64748b; font-weight:normal;">(${r.role_code})</span>
      </label>
    `).join('');
  }
  openModal('userModal');
}

async function saveNewUser(e) {
  e.preventDefault();
  const selectedRoleIds = Array.from(document.querySelectorAll('input[name="newUserRole"]:checked'))
    .map(cb => parseInt(cb.value));

  const payload = {
    username: document.getElementById('new_username').value.trim(),
    password: document.getElementById('new_password').value,
    real_name: document.getElementById('new_real_name').value.trim(),
    email: document.getElementById('new_email').value.trim() || undefined,
    role_ids: selectedRoleIds
  };

  const res = await api('/system/users', {
    method: 'POST',
    body: JSON.stringify(payload)
  });

  if (res && res.code === 200) {
    showToast("平台用户创建成功！", "success");
    closeModal('userModal');
    loadUsers();
  } else {
    showToast(res ? res.message : "创建失败", "danger");
  }
}

// ---------------- 角色与应用权限管理 ----------------
async function loadRoles() {
  const res = await api('/system/roles');
  const tbody = document.getElementById('roleListTable');
  if (!tbody) return;
  if (!res || res.code !== 200 || !res.data || res.data.length === 0) {
    tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;color:#94a3b8;">暂无角色数据</td></tr>';
    return;
  }
  cachedRolesList = res.data;

  tbody.innerHTML = res.data.map(r => {
    const isSuperAdminRole = (r.role_code === 'ROLE_SUPER_ADMIN' || r.role_code === 'ROLE_SUPERADMIN' || r.role_level === 1);
    const isSystemPresetRole = (r.is_system === 1 || ['ROLE_SUPER_ADMIN', 'ROLE_SUPERADMIN', 'ROLE_OPERATOR', 'ROLE_MEMBER'].includes(r.role_code));

    let appBadges = '';
    if (isSuperAdminRole) {
      appBadges = '<span class="badge" style="background:#e0e7ff; color:#4338ca; font-weight:700; font-size:12px; padding:3px 8px; border-radius:6px;">👑 天生拥有全量应用权限</span>';
    } else if (r.assigned_apps && r.assigned_apps.length > 0) {
      appBadges = r.assigned_apps.map(app => `<span class="badge badge-tenant" style="margin:2px 3px 2px 0; font-size:11.5px; display:inline-block;">📱 ${app}</span>`).join(' ');
    } else if (r.menus && r.menus.length > 0) {
      appBadges = r.menus.map(m => `<span class="badge badge-tenant" style="margin:2px 3px 2px 0; font-size:11.5px; display:inline-block;">${m.icon || '📱'} ${m.menu_name}</span>`).join(' ');
    } else {
      appBadges = '<span style="color:#94a3b8; font-size:12px;">未配置应用权限</span>';
    }

    const systemTag = isSystemPresetRole ? '<span class="badge" style="background:#f1f5f9; color:#475569; font-size:11px; margin-left:6px; border:1px solid #cbd5e1;">🔒 内置</span>' : '';

    return `
      <tr>
        <td><code>${r.role_code}</code></td>
        <td><strong>${r.role_name}</strong>${systemTag}</td>
        <td>${r.remark || '-'}</td>
        <td style="max-width:320px;">${appBadges}</td>
        <td><span class="badge ${r.status === 'ACTIVE' ? 'badge-success' : 'badge-danger'}">${r.status}</span></td>
        <td style="white-space:nowrap;">
          ${!isSuperAdminRole ? `<button class="btn btn-primary btn-sm" onclick="openRolePermissionsModal(${r.id})">🔑 赋予应用权限</button>` : ''}
          <button class="btn btn-outline btn-sm" onclick="openEditRoleModal(${r.id})">✏️ 编辑</button>
          ${!isSystemPresetRole ? `<button class="btn btn-outline btn-sm" style="color:var(--danger)" onclick="deleteRole(${r.id})">🗑️ 删除</button>` : `<span style="display:inline-block; font-size:12px; color:#94a3b8; margin-left:6px; user-select:none;">🔒 不可删除</span>`}
        </td>
      </tr>
    `;
  }).join('');
}

function openCreateRoleModal() {
  document.getElementById('roleForm').reset();
  document.getElementById('role_id').value = '';
  document.getElementById('role_code').disabled = false;
  document.getElementById('roleModalTitle').innerText = '新增平台角色';
  openModal('roleModal');
}

function openEditRoleModal(roleId) {
  const role = cachedRolesList.find(r => r.id === roleId);
  if (!role) return;

  document.getElementById('role_id').value = role.id;
  document.getElementById('role_code').value = role.role_code;
  document.getElementById('role_code').disabled = true; // 编码不可修改
  document.getElementById('role_name').value = role.role_name;
  document.getElementById('role_level').value = role.role_level || 10;
  document.getElementById('role_status').value = role.status;
  document.getElementById('role_remark').value = role.remark || '';
  document.getElementById('roleModalTitle').innerText = `编辑角色: ${role.role_name}`;
  openModal('roleModal');
}

async function saveRole(e) {
  e.preventDefault();
  const roleId = document.getElementById('role_id').value;
  const payload = {
    role_code: document.getElementById('role_code').value.trim(),
    role_name: document.getElementById('role_name').value.trim(),
    role_level: parseInt(document.getElementById('role_level').value) || 10,
    status: document.getElementById('role_status').value,
    remark: document.getElementById('role_remark').value.trim()
  };

  let res;
  if (roleId) {
    res = await api(`/system/roles/${roleId}`, {
      method: 'PUT',
      body: JSON.stringify(payload)
    });
  } else {
    res = await api('/system/roles', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  }

  if (res && res.code === 200) {
    showToast(roleId ? "角色已更新" : "角色创建成功", "success");
    closeModal('roleModal');
    loadRoles();
  } else {
    showToast(res ? res.message : "操作失败", "danger");
  }
}

async function deleteRole(roleId) {
  if (!confirm("确定要删除该角色吗？")) return;
  const res = await api(`/system/roles/${roleId}`, { method: 'DELETE' });
  if (res && res.code === 200) {
    showToast("角色已删除", "success");
    loadRoles();
  } else {
    showToast(res ? res.message : "删除失败", "danger");
  }
}

function toggleAppCardHighlight(checkbox) {
  const card = document.getElementById(`app_perm_card_${checkbox.value}`);
  if (!card) return;
  if (checkbox.checked) {
    card.style.background = '#f0fdf4';
    card.style.borderColor = '#86efac';
  } else {
    card.style.background = '#ffffff';
    card.style.borderColor = '#e2e8f0';
  }
}

function selectAllApps(checked) {
  const checkboxes = document.querySelectorAll('input[name="roleAppCheckbox"]');
  checkboxes.forEach(cb => {
    cb.checked = checked;
    toggleAppCardHighlight(cb);
  });
}

async function openRolePermissionsModal(roleId) {
  const role = cachedRolesList.find(r => r.id === roleId);
  if (!role) return;
  const roleName = role.role_name || `ID: ${roleId}`;

  document.getElementById('perm_role_id').value = roleId;
  document.getElementById('permRoleModalTitle').innerText = `🔑 为角色 [${roleName}] 赋予微服务应用权限`;

  const container = document.getElementById('permissionsAppsContainer');
  if (container) {
    container.innerHTML = '<div style="text-align:center; padding:24px; color:#94a3b8;">正在加载平台微服务应用清单...</div>';
  }
  openModal('rolePermissionModal');

  // 获取该角色已绑定的权限以及全量可分配应用清单
  const permRes = await api(`/system/roles/${roleId}/permissions`);
  if (!permRes || permRes.code !== 200 || !permRes.data) {
    showToast(permRes ? permRes.message : "获取角色应用权限失败", "danger");
    if (container) {
      container.innerHTML = '<div style="text-align:center; padding:24px; color:#ef4444;">加载应用清单失败，请重试</div>';
    }
    return;
  }

  const { assigned_service_codes = [], assigned_menu_ids = [], all_apps = [] } = permRes.data;

  if (all_apps.length === 0) {
    container.innerHTML = '<div style="text-align:center; padding:24px; color:#94a3b8;">暂无可分配的微服务应用</div>';
    return;
  }

  container.innerHTML = all_apps.map(app => {
    const isPortalRequired = (app.service_code === 'mcp-portal');
    const isChecked = isPortalRequired ||
                      (assigned_service_codes && assigned_service_codes.includes(app.service_code)) ||
                      (assigned_menu_ids && assigned_menu_ids.includes(app.id));
    const bgStyle = isChecked ? 'background:#f0fdf4; border-color:#86efac;' : 'background:#ffffff; border-color:#e2e8f0;';
    const statusBadge = isPortalRequired
      ? '<span class="badge badge-info" style="font-size:11px; background:#e0e7ff; color:#4338ca; font-weight:600;">🔒 基础必备 (不可取消)</span>'
      : (app.health_status === 'HEALTHY' 
          ? '<span class="badge badge-success" style="font-size:11px;">🟢 正常</span>'
          : '<span class="badge badge-warning" style="font-size:11px;">🟡 ' + (app.health_status || 'UNKNOWN') + '</span>');

    return `
      <div class="app-perm-card" id="app_perm_card_${app.service_code}" style="display:flex; align-items:flex-start; gap:12px; padding:12px 14px; border:1.5px solid #e2e8f0; border-radius:10px; transition:all 0.2s ease; ${bgStyle}">
        <input type="checkbox" name="roleAppCheckbox" id="chk_app_${app.id}" value="${app.service_code}" data-menuid="${app.id}" ${isChecked ? 'checked' : ''} ${isPortalRequired ? 'disabled title="门户应用为平台基础入口，所有角色必须勾选且不可取消"' : ''} onchange="toggleAppCardHighlight(this)" style="margin-top:4px; width:18px; height:18px; cursor:${isPortalRequired ? 'not-allowed' : 'pointer'}; accent-color:var(--primary);">
        <label for="chk_app_${app.id}" style="flex:1; cursor:${isPortalRequired ? 'default' : 'pointer'}; margin-bottom:0;">
          <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:4px;">
            <div style="display:flex; align-items:center; gap:8px;">
              <span style="font-size:18px;">${app.icon || '📱'}</span>
              <strong style="font-size:14px; color:#0f172a;">${app.service_name}</strong>
              <code style="font-size:11.5px; background:#f1f5f9; padding:2px 6px; border-radius:4px; color:#475569;">${app.service_code}</code>
            </div>
            <div style="display:flex; align-items:center; gap:6px;">
              <span class="badge badge-tech" style="font-size:11px;">${app.tech_stack || 'PYTHON'}</span>
              ${statusBadge}
            </div>
          </div>
          <div style="font-size:12.5px; color:#64748b; line-height:1.4;">
            ${app.description || '平台微服务节点'}
          </div>
          <div style="font-size:11px; color:#94a3b8; font-family:monospace; margin-top:4px;">
            🔗 访问路由/端点: <strong>${app.gateway_prefix || app.base_url}</strong>
          </div>
        </label>
      </div>
    `;
  }).join('');
}

async function saveRolePermissions(e) {
  e.preventDefault();
  const roleId = document.getElementById('perm_role_id').value;
  if (!roleId) return;

  const btn = document.getElementById('savePermBtn');
  const originalBtnText = btn ? btn.innerText : '确 认 保 存 赋 权';
  if (btn) {
    btn.disabled = true;
    btn.innerText = '正在保存应用权限...';
  }

  try {
    const checkedBoxes = Array.from(document.querySelectorAll('input[name="roleAppCheckbox"]:checked'));
    const selectedServiceCodes = checkedBoxes.map(cb => cb.value);
    const selectedMenuIds = checkedBoxes.map(cb => parseInt(cb.dataset.menuid)).filter(Boolean);

    // 门户应用每个角色都必须包含且不可取消
    if (!selectedServiceCodes.includes('mcp-portal')) {
      selectedServiceCodes.push('mcp-portal');
    }

    const res = await api(`/system/roles/${roleId}/permissions`, {
      method: 'PUT',
      body: JSON.stringify({
        service_codes: selectedServiceCodes,
        menu_ids: selectedMenuIds
      })
    });

    if (res && res.code === 200) {
      showToast("角色微服务应用权限配置成功！", "success");
      closeModal('rolePermissionModal');
      await loadRoles();
    } else {
      showToast(res ? res.message : "配置失败", "danger");
    }
  } catch (err) {
    showToast("保存失败: " + err.message, "danger");
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerText = originalBtnText;
    }
  }
}

// ---------------- 管理员自身修改密码 ----------------
function openAdminPwdModal() {
  document.getElementById('adminPwdForm').reset();
  openModal('adminPwdModal');
}

async function handleAdminPwdSubmit(e) {
  e.preventDefault();
  const oldPwd = document.getElementById('admin_old_pwd').value;
  const newPwd = document.getElementById('admin_new_pwd').value;
  const confirmPwd = document.getElementById('admin_confirm_pwd').value;

  if (newPwd !== confirmPwd) {
    showToast("两次输入的新密码不一致", "danger");
    return;
  }

  const res = await api('/auth/change-password', {
    method: 'POST',
    body: JSON.stringify({ old_password: oldPwd, new_password: newPwd })
  });

  if (res && res.code === 200) {
    showToast("密码修改成功！请使用新密码重新登录", "success");
    closeModal('adminPwdModal');
    setTimeout(handleLogout, 1200);
  } else {
    showToast(res ? res.message : "修改失败", "danger");
  }
}

// ---------------- 4. Configs ----------------
async function loadConfigs() {
  const res = await api('/system/configs');
  const tbody = document.getElementById('configListTable');
  if (!tbody) return;
  if (!res || res.code !== 200 || !res.data || res.data.length === 0) {
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
  const urlParams = new URLSearchParams(window.location.search);
  const tokenFromUrl = urlParams.get('mcp_token') || urlParams.get('token');
  const userFromUrl = urlParams.get('mcp_user') || urlParams.get('user');
  const tabFromUrl = urlParams.get('tab');

  if (tokenFromUrl) {
    const isOnline = window.location.hostname.endsWith('dreamclip.cn');
    if (!isOnline) {
      setAuthCookie('mcp_token', tokenFromUrl, 7);
      setAuthCookie('dreamclip_token', tokenFromUrl, 7);
      localStorage.setItem('mcp_token', tokenFromUrl);
      localStorage.setItem('dreamclip_token', tokenFromUrl);
      if (userFromUrl) {
        const decodedUser = decodeURIComponent(userFromUrl);
        setAuthCookie('mcp_user', decodedUser, 7);
        setAuthCookie('dreamclip_user', decodedUser, 7);
        localStorage.setItem('mcp_user', decodedUser);
        localStorage.setItem('dreamclip_user', decodedUser);
      }
    }
    urlParams.delete('mcp_token');
    urlParams.delete('token');
    urlParams.delete('mcp_user');
    urlParams.delete('user');
    const newSearch = urlParams.toString();
    const newUrl = window.location.pathname + (newSearch ? '?' + newSearch : '') + window.location.hash;
    window.history.replaceState({}, document.title, newUrl);
  }

  const token = getToken();
  if (!token) {
    redirectToLogin();
    return;
  }

  // 严格调用 /auth/me 校验当前在线凭证的合法性
  api('/auth/me').then(res => {
    if (!res || res.code !== 200 || !res.data) {
      redirectToLogin();
      return;
    }
    const freshUser = res.data;
    const isOnline = window.location.hostname.endsWith('dreamclip.cn');
    if (!isOnline) {
      setAuthCookie('mcp_user', JSON.stringify(freshUser), 7);
      setAuthCookie('dreamclip_user', JSON.stringify(freshUser), 7);
      localStorage.setItem('mcp_user', JSON.stringify(freshUser));
      localStorage.setItem('dreamclip_user', JSON.stringify(freshUser));
    }

    document.getElementById('userName').innerText = freshUser.username || 'superadmin';
    document.getElementById('avatarText').innerText = (freshUser.username || 'SA').substring(0, 2).toUpperCase();
    if (freshUser.is_superadmin) {
      document.getElementById('userRoleTag').innerText = "超级管理员";
    } else {
      document.getElementById('userRoleTag').innerText = (freshUser.roles && freshUser.roles.length > 0) ? freshUser.roles[0] : (freshUser.role_name || "平台用户");
    }
  }).catch(() => {
    redirectToLogin();
  });

  if (tabFromUrl && document.getElementById(tabFromUrl)) {
    const tabEl = Array.from(document.querySelectorAll('.nav-item')).find(el => el.getAttribute('onclick')?.includes(tabFromUrl));
    switchTab(tabFromUrl, tabEl);
  } else {
    loadDashboard();
  }
});
