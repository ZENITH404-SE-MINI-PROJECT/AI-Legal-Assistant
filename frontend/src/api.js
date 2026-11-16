// Thin REST client. The JWT is kept in memory + sessionStorage (cleared when the tab closes).
const BASE = import.meta.env.VITE_API_BASE || "/api";
let token = sessionStorage.getItem("token") || "";

export const setToken = (t) => {
  token = t || "";
  t ? sessionStorage.setItem("token", t) : sessionStorage.removeItem("token");
};
export const hasToken = () => !!token;

async function request(path, { method = "GET", body, form, raw } = {}) {
  const headers = token ? { Authorization: `Bearer ${token}` } : {};
  if (body) headers["Content-Type"] = "application/json";
  const res = await fetch(BASE + path, {
    method,
    headers,
    body: form || (body ? JSON.stringify(body) : undefined),
  });
  if (res.status === 401 && token) {
    setToken("");
    window.location.reload();
  }
  if (!res.ok) {
    let msg = res.statusText;
    try {
      const j = await res.json();
      msg = typeof j.detail === "string" ? j.detail : JSON.stringify(j.detail);
    } catch (_) { /* ignore */ }
    throw new Error(msg);
  }
  if (raw) return res;
  return res.status === 204 ? null : res.json();
}

export const api = {
  login: (username, password) => request("/auth/login", { method: "POST", body: { username, password } }),
  register: (username, password) => request("/auth/register", { method: "POST", body: { username, password } }),
  ask: (question, conversation_id) => request("/chat/ask", { method: "POST", body: { question, conversation_id } }),
  conversations: () => request("/chat/conversations"),
  conversation: (id) => request(`/chat/conversations/${id}`),
  deleteConversation: (id) => request(`/chat/conversations/${id}`, { method: "DELETE" }),
  feedback: (b) => request("/feedback", { method: "POST", body: b }),
  caseLaw: (params) => request("/case-law?" + new URLSearchParams(params)),
  templates: (q = "") => request("/templates?" + new URLSearchParams(q ? { q } : {})),
  template: (id) => request(`/templates/${id}`),
  fillTemplate: (id, values, fmt) => request(`/templates/${id}/fill?fmt=${fmt}`, { method: "POST", body: { values }, raw: true }),
  upload: (file) => { const f = new FormData(); f.append("file", file); return request("/documents", { method: "POST", form: f }); },
  documents: () => request("/documents"),
  deleteDocument: (id) => request(`/documents/${id}`, { method: "DELETE" }),
  deleteMyData: () => request("/auth/me/data", { method: "DELETE" }),
  admin: {
    references: () => request("/admin/references"),
    saveReference: (b, id) => request(id ? `/admin/references/${id}` : "/admin/references", { method: id ? "PUT" : "POST", body: b }),
    deleteReference: (id) => request(`/admin/references/${id}`, { method: "DELETE" }),
    feedback: () => request("/admin/feedback"),
    resolveFeedback: (id, admin_note) => request(`/admin/feedback/${id}`, { method: "PUT", body: { resolved: true, admin_note } }),
    users: () => request("/admin/users"),
    setRole: (id, role) => request(`/admin/users/${id}/role`, { method: "PUT", body: { role } }),
    deleteUser: (id) => request(`/admin/users/${id}`, { method: "DELETE" }),
  },
};
