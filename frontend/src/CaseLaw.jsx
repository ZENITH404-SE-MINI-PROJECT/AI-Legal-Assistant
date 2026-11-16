import React, { useState } from "react";
import { api } from "./api.js";

export default function CaseLaw() {
  const [f, setF] = useState({ q: "", jurisdiction: "", citation: "" });
  const [rows, setRows] = useState(null);
  const [error, setError] = useState("");
  const search = async (e) => {
    e.preventDefault(); setError("");
    try {
      const params = Object.fromEntries(Object.entries(f).filter(([, v]) => v.trim()));
      setRows(await api.caseLaw(params));
    } catch (err) { setError(err.message); }
  };
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value });
  return (
    <section>
      <form onSubmit={search} className="row">
        <input placeholder="Keyword" value={f.q} onChange={set("q")} />
        <input placeholder="Jurisdiction" value={f.jurisdiction} onChange={set("jurisdiction")} />
        <input placeholder="Citation" value={f.citation} onChange={set("citation")} />
        <button>Search</button>
      </form>
      {error && <p className="error">{error}</p>}
      {rows && rows.length === 0 && <p>No matching cases found.</p>}
      {rows?.map((r) => (
        <article key={r.id} className="card">
          <h3>{r.title}</h3>
          <small>{r.citation} · {r.jurisdiction} · {r.domain}</small>
          <p>{r.summary}</p>
        </article>
      ))}
    </section>
  );
}
