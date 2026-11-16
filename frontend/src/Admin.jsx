import React, { useEffect, useState } from "react";
import { api } from "./api.js";

const blank = { entry_type: "case", title: "", citation: "", jurisdiction: "India", domain: "consumer", keywords: "", summary: "", steps: "" };
const DOMAINS = ["consumer", "tenancy", "family", "employment", "cyber", "criminal_procedure", "rti"];

export default function Admin() {
  const [tab, setTab] = useState("kb");
  const [refs, setRefs] = useState([]);
  const [fb, setFb] = useState([]);
  const [users, setUsers] = useState([]);
  const [form, setForm] = useState(blank);
  const [editing, setEditing] = useState(null);
  const [error, setError] = useState("");
  const guard = (fn) => async (...a) => { setError(""); try { await fn(...a); } catch (e) { setError(e.message); } };
  const load = guard(async () => {
    setRefs(await api.admin.references()); setFb(await api.admin.feedback()); setUsers(await api.admin.users());
  });
  useEffect(() => { load(); }, []); // eslint-disable-line

  const save = guard(async (e) => {
    e.preventDefault();
    await api.admin.saveReference(form, editing); setForm(blank); setEditing(null); await load();
  });
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });
  return (
    <section>
      <div className="row">
        {["kb", "feedback", "users"].map((t) => <button key={t} onClick={() => setTab(t)} disabled={tab === t}>{t}</button>)}
      </div>
      {error && <p className="error">{error}</p>}
      {tab === "kb" && (<>
        <form onSubmit={save} className="card">
          <select value={form.entry_type} onChange={set("entry_type")}><option>case</option><option>procedure</option></select>
          <select value={form.domain} onChange={set("domain")}>{DOMAINS.map((d) => <option key={d}>{d}</option>)}</select>
          <input placeholder="Title" value={form.title} onChange={set("title")} required />
          <input placeholder="Citation" value={form.citation} onChange={set("citation")} />
          <input placeholder="Keywords (comma separated)" value={form.keywords} onChange={set("keywords")} />
          <textarea placeholder="Summary" value={form.summary} onChange={set("summary")} required />
          <textarea placeholder="Steps (one per line, for procedures)" value={form.steps} onChange={set("steps")} />
          <button>{editing ? "Update" : "Add"} entry</button>
        </form>
        {refs.map((r) => (
          <article key={r.id} className="card">
            <strong>{r.title}</strong> <small>{r.entry_type} · {r.domain}</small>
            <div className="row">
              <button onClick={() => { setForm({ ...blank, ...r }); setEditing(r.id); }}>Edit</button>
              <button onClick={guard(async () => { await api.admin.deleteReference(r.id); await load(); })}>Delete</button>
            </div>
          </article>
        ))}
      </>)}
      {tab === "feedback" && fb.map((f) => (
        <article key={f.id} className="card">
          <p><strong>{f.is_error_report ? "Error report" : `Rating ${f.rating ?? "-"}`}</strong> {f.resolved && "(resolved)"}</p>
          <p>{f.comment}</p><small>{f.response_text?.slice(0, 200)}</small>
          {!f.resolved && <button onClick={guard(async () => { await api.admin.resolveFeedback(f.id, prompt("Note") || ""); await load(); })}>Resolve</button>}
        </article>
      ))}
      {tab === "users" && users.map((u) => (
        <article key={u.id} className="card">
          {u.username} <small>({u.role})</small>
          <div className="row">
            <button onClick={guard(async () => { await api.admin.setRole(u.id, u.role === "admin" ? "user" : "admin"); await load(); })}>Toggle role</button>
            <button onClick={guard(async () => { await api.admin.deleteUser(u.id); await load(); })}>Delete</button>
          </div>
        </article>
      ))}
    </section>
  );
}
