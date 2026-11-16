import React, { useState } from "react";
import { api, hasToken, setToken } from "./api.js";
import Chat from "./Chat.jsx";
import CaseLaw from "./CaseLaw.jsx";
import Templates from "./Templates.jsx";
import Documents from "./Documents.jsx";
import Admin from "./Admin.jsx";

function Login({ onDone }) {
  const [mode, setMode] = useState("login");
  const [u, setU] = useState("");
  const [p, setP] = useState("");
  const [error, setError] = useState("");
  const submit = async (e) => {
    e.preventDefault(); setError("");
    try {
      const r = await (mode === "login" ? api.login(u, p) : api.register(u, p));
      setToken(r.access_token); onDone({ username: r.username, role: r.role });
    } catch (err) { setError(err.message); }
  };
  return (
    <form onSubmit={submit} className="card login">
      <h2>{mode === "login" ? "Sign in" : "Create account"}</h2>
      <input placeholder="Username" value={u} onChange={(e) => setU(e.target.value)} autoComplete="username" required />
      <input type="password" placeholder="Password (8+ chars, letter + digit)" value={p} onChange={(e) => setP(e.target.value)} autoComplete="current-password" required />
      {error && <p className="error" role="alert">{error}</p>}
      <button>{mode === "login" ? "Login" : "Register"}</button>
      <a href="#" onClick={(e) => { e.preventDefault(); setMode(mode === "login" ? "register" : "login"); }}>
        {mode === "login" ? "Need an account? Register" : "Have an account? Login"}
      </a>
    </form>
  );
}

const TABS = [["chat", "Ask"], ["case", "Case law"], ["templates", "Templates"], ["docs", "My documents"]];

export default function App() {
  const [user, setUser] = useState(() => {
    try { return hasToken() ? JSON.parse(sessionStorage.getItem("user")) : null; } catch (_) { return null; }
  });
  const [tab, setTab] = useState("chat");
  const done = (u) => { sessionStorage.setItem("user", JSON.stringify(u)); setUser(u); };
  const logout = () => { setToken(""); sessionStorage.removeItem("user"); setUser(null); };

  if (!user) return <main><h1>⚖️ AI Legal Assistant</h1><Login onDone={done} /></main>;
  const tabs = user.role === "admin" ? [...TABS, ["admin", "Admin"]] : TABS;
  return (
    <main>
      <header>
        <h1>⚖️ AI Legal Assistant</h1>
        <span>{user.username} <button onClick={logout}>Logout</button></span>
      </header>
      <p className="banner">Informational only — not a lawyer and not legal advice.</p>
      <nav>{tabs.map(([k, l]) => <button key={k} onClick={() => setTab(k)} className={tab === k ? "active" : ""}>{l}</button>)}</nav>
      {tab === "chat" && <Chat userKey={user.username} />}
      {tab === "case" && <CaseLaw />}
      {tab === "templates" && <Templates />}
      {tab === "docs" && <Documents />}
      {tab === "admin" && user.role === "admin" && <Admin />}
      <footer>
        <button onClick={async () => { if (confirm("Delete all your conversations and documents?")) { await api.deleteMyData(); alert("Deleted."); } }}>
          Delete my data
        </button>
      </footer>
    </main>
  );
}
