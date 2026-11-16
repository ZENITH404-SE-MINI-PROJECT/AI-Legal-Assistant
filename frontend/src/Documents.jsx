import React, { useEffect, useState } from "react";
import { api } from "./api.js";

export default function Documents() {
  const [docs, setDocs] = useState([]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const load = () => api.documents().then(setDocs).catch((e) => setError(e.message));
  useEffect(() => { load(); }, []);

  const onFile = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setError(""); setBusy(true);
    try { await api.upload(file); await load(); } catch (err) { setError(err.message); }
    setBusy(false); e.target.value = "";
  };
  return (
    <section>
      <label>Upload a PDF, TXT or DOCX (max 5 MB)
        <input type="file" accept=".pdf,.txt,.docx" onChange={onFile} disabled={busy} />
      </label>
      {busy && <p>Analysing…</p>}
      {error && <p className="error">{error}</p>}
      {docs.map((d) => (
        <article key={d.id} className="card">
          <h3>{d.name} <small>({d.file_type})</small></h3>
          <p>{d.summary}</p>
          {d.key_clauses.length > 0 && <><strong>Key clauses</strong><ul>{d.key_clauses.map((c, i) => <li key={i}>{c}</li>)}</ul></>}
          <p className="disclaimer">{d.disclaimer}</p>
          <button onClick={async () => { await api.deleteDocument(d.id); load(); }}>Delete</button>
        </article>
      ))}
    </section>
  );
}
