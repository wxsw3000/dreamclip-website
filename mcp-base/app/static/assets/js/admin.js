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
  document.getElementById('svc_code').disabled = true;
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
    showToast(svcId ? "微服务配置修改成功" : "微服务已成功接入", "success");
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

async function loadUsers() {
  const res = await api('/system/users?size=50');
  const tbody = document.getElementById('userListTable');
  if (!res || res.code !== 200 || res.data.records.length === 0) {
    tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;color:#94a3b8;">暂无用户数据</td></tr>';
    return;
  }

  tbody.innerHTML = res.data.records.map(u => {
    const rolesStr = (u.roles && u.roles.length > 0)
      ? u.roles.map(r => `<span class="badge badge-tech">${r.role_name}</span>`).join(' ')
      : '<span class="badge badge-outline">未分配角色</span>';

    return `
      <tr>
        <td><code>${u.username}</code></td>
        <td><strong>${u.real_name || u.username}</strong></td>
        <td>${rolesStr}</td>
        <td>${u.is_superadmin ? '<span class="badge badge-danger">👑 超级管理员</span>' : '<span class="badge badge-outline">常规用户</span>'}</td>
        <td><span class="badge ${u.status === 'ACTIVE' ? 'badge-success' : 'badge-danger'}">${u.status}</span></td>
        <td>${u.created_at ? u.created_at.replace('T', ' ').substring(0, 19) : '-'}</td>
        <td style="white-space:nowrap;">
          <button class="btn btn-outline btn-sm" onclick="openEditUserModal(${u.id})">✏️ 编辑/改密</button>
          ${u.username !== 'superadmin' ? `<button class="btn btn-outline btn-sm" style="color:var(--danger)" onclick="deleteUser(${u.id})">🗑️ 删除</button>` : ''}
        </td>
      </tr>
    `;
  }).join('');
}

async function openEditUserModal(userId) {
  // 先获取所有角色
  const rolesRes = await api('/system/roles');
  if (rolesRes && rolesRes.code === 200) {
    cachedRolesList = rolesRes.data;
  }

  const res = await api(`/system/users?size=100`);
  const user = res.data.records.find(u => u.id === userId);
  if (!user) {
    showToast("未找到该用户信息", "danger");
    return;
  }

  document.getElementById('edit_user_id').value = user.id;
  document.getElementById('edit_user_username').value = user.username;
  document.getElementById('edit_user_realname').value = user.real_name || '';
  document.getElementById('edit_user_email').value = user.email || '';
  document.getElementById('edit_user_pwd').value = ''; // 留空则不修改
  document.getElementById('edit_user_status').value = user.status;
  document.getElementById('edit_user_superadmin').checked = Boolean(user.is_superadmin);

  // 渲染角色选择多选框
  const rolesContainer = document.getElementById('edit_user_roles_box');
  const userRoleIds = (user.roles || []).map(r => r.id);
  rolesContainer.innerHTML = cachedRolesList.map(r => `
    <label style="display:inline-flex; align-items:center; gap:5px; margin-right:12px; font-size:13px; cursor:pointer;">
      <input type="checkbox" name="editUserRole" value="${r.id}" ${userRoleIds.includes(r.id) ? 'checked' : ''}>
      ${r.role_name} (${r.role_code})
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

  const res = await api('/system/users', {
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

// ---------------- 角色与应用权限管理 ----------------
async function loadRoles() {
  const res = await api('/system/roles');
  const tbody = document.getElementById('roleListTable');
  if (!res || res.code !== 200 || res.data.length === 0) {
    tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;color:#94a3b8;">暂无角色数据</td></tr>';
    return;
  }
  cachedRolesList = res.data;

  tbody.innerHTML = res.data.map(r => {
    const menusStr = (r.menus && r.menus.length > 0)
      ? r.menus.map(m => `<span class="badge badge-tenant">${m.menu_name}</span>`).join(' ')
      : '<span style="color:#94a3b8;">未配置应用权限</span>';

    return `
      <tr>
        <td><code>${r.role_code}</code></td>
        <td><strong>${r.role_name}</strong></td>
        <td>${r.remark || '-'}</td>
        <td>${menusStr}</td>
        <td><span class="badge ${r.status === 'ACTIVE' ? 'badge-success' : 'badge-danger'}">${r.status}</span></td>
        <td style="white-space:nowrap;">
          <button class="btn btn-primary btn-sm" onclick="openRolePermissionsModal(${r.id})">🔑 赋予应用权限</button>
          <button class="btn btn-outline btn-sm" onclick="openEditRoleModal(${r.id})">✏️ 编辑</button>
          ${!['ROLE_SUPERADMIN', 'ROLE_OPERATOR'].includes(r.role_code) ? `<button class="btn btn-outline btn-sm" style="color:var(--danger)" onclick="deleteRole(${r.id})">🗑️ 删除</button>` : ''}
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
    showToast(roleId ? "角色修改成功" : "角色创建成功", "success");
    closeModal('roleModal');
    loadRoles();
  } else {
    showToast(res ? res.message : "保存失败", "danger");
  }
}

async function deleteRole(roleId) {
  if (!confirm("确定要删除该平台角色吗？")) return;
  const res = await api(`/system/roles/${roleId}`, { method: 'DELETE' });
  if (res && res.code === 200) {
    showToast("角色已删除", "success");
    loadRoles();
  } else {
    showToast(res ? res.message : "删除失败", "danger");
  }
}

async function openRolePermissionsModal(roleId) {
  const role = cachedRolesList.find(r => r.id === roleId);
  if (!role) return;

  document.getElementById('perm_role_id').value = role.id;
  document.getElementById('permRoleModalTitle').innerText = `为角色 [${role.role_name}] 赋予应用与菜单权限`;

  // 获取所有可分配的扁平菜单和应用
  const menusRes = await api('/system/menus/flat');
  const container = document.getElementById('permissionsCheckboxContainer');
  if (!menusRes || menusRes.code !== 200) {
    showToast("获取权限列表失败", "danger");
    return;
  }

  const assignedMenuIds = (role.menus || []).map(m => m.id);

  container.innerHTML = menusRes.data.map(m => `
    <div style="display:flex; align-items:center; justify-content:space-between; padding:8px 12px; background:#f8fafc; border:1px solid #e2e8f0; border-radius:6px; margin-bottom:6px;">
      <label style="display:flex; align-items:center; gap:8px; cursor:pointer; font-weight:600; font-size:13px; color:#0f172a;">
        <input type="checkbox" name="rolePermissionCheckbox" value="${m.id}" ${assignedMenuIds.includes(m.id) ? 'checked' : ''}>
        <span>${m.icon || '📱'} ${m.menu_name}</span>
      </label>
      <span class="badge badge-tech" style="font-size:11px;">${m.service_code || 'MCP-BASE'}</span>
    </div>
  `).join('');

  openModal('rolePermissionModal');
}

async function saveRolePermissions(e) {
  e.preventDefault();
  const roleId = document.getElementById('perm_role_id').value;
  const selectedMenuIds = Array.from(document.querySelectorAll('input[name="rolePermissionCheckbox"]:checked'))
    .map(cb => parseInt(cb.value));

  const res = await api(`/system/roles/${roleId}/permissions`, {
    method: 'PUT',
    body: JSON.stringify({ menu_ids: selectedMenuIds })
  });

  if (res && res.code === 200) {
    showToast("角色应用权限配置成功！", "success");
    closeModal('rolePermissionModal');
    loadRoles();
  } else {
    showToast(res ? res.message : "配置失败", "danger");
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
  const urlParams = new URLSearchParams(window.location.search);
  const tokenFromUrl = urlParams.get('mcp_token');
  const userFromUrl = urlParams.get('mcp_user');
  const tabFromUrl = urlParams.get('tab');

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
      document.getElementById('userRoleTag').innerText = "超级管理员";
    } else {
      document.getElementById('userRoleTag').innerText = user.role_name || "普通用户";
    }
  }

  if (tabFromUrl && document.getElementById(tabFromUrl)) {
    const tabEl = Array.from(document.querySelectorAll('.nav-item')).find(el => el.getAttribute('onclick')?.includes(tabFromUrl));
    switchTab(tabFromUrl, tabEl);
  } else {
    loadDashboard();
  }
});
