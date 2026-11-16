import React, { useEffect, useState } from "react";
import { api } from "./api.js";

function download(blob, name) {
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob); a.download = name; a.click();
  URL.revokeObjectURL(a.href);
}

export default function Templates() {
  const [list, setList] = useState([]);
  const [q, setQ] = useState("");
  const [sel, setSel] = useState(null);
  const [vals, setVals] = useState({});
  const [error, setError] = useState("");
  const load = () => api.templates(q).then(setList).catch((e) => setError(e.message));
  useEffect(() => { load(); }, []); // eslint-disable-line

  const open = async (id) => { setSel(await api.template(id)); setVals({}); setError(""); };
  const fill = async (fmt) => {
    setError("");
    try {
      const res = await api.fillTemplate(sel.id, vals, fmt);
      download(await res.blob(), `${sel.title}.${fmt}`);
    } catch (e) { setError(e.message); }
  };
  return (
    <section>
      <form className="row" onSubmit={(e) => { e.preventDefault(); load(); }}>
        <input placeholder="Search templates" value={q} onChange={(e) => setQ(e.target.value)} />
        <button>Search</button>
      </form>
      {error && <p className="error">{error}</p>}
      {!sel && list.map((t) => (
        <article key={t.id} className="card clickable" onClick={() => open(t.id)}>
          <h3>{t.title}</h3><small>{t.category}</small><p>{t.description}</p>
        </article>
      ))}
      {sel && (
        <div className="card">
          <h3>{sel.title}</h3>
          {sel.placeholders.map((p) => (
            <label key={p}>{p.replaceAll("_", " ")}
              <input value={vals[p] || ""} onChange={(e) => setVals({ ...vals, [p]: e.target.value })} />
            </label>
          ))}
          <div className="row">
            <button onClick={() => fill("txt")}>Download .txt</button>
            <button onClick={() => fill("docx")}>Download .docx</button>
            <button onClick={() => setSel(null)}>Back</button>
          </div>
          <p className="disclaimer">Drafts are for general use. Have important documents reviewed by a lawyer.</p>
        </div>
      )}
    </section>
  );
}
