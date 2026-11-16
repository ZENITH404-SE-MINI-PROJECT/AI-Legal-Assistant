// UI renderer for an assistant response: answer + steps + sources + mandatory disclaimer (FR-07).
import React, { useState } from "react";
import { api } from "./api.js";

export default function ResponseView({ msg }) {
  const [sent, setSent] = useState("");
  const send = async (payload) => {
    try {
      await api.feedback({ message_id: msg.message_id, ...payload });
      setSent("Thanks for your feedback.");
    } catch (e) {
      setSent(e.message);
    }
  };
  return (
    <div className="bubble assistant">
      <p style={{ whiteSpace: "pre-wrap" }}>{msg.answer}</p>
      {msg.steps?.length > 0 && (
        <ol className="steps">{msg.steps.map((s, i) => <li key={i}>{s}</li>)}</ol>
      )}
      {msg.sources?.length > 0 && (
        <div className="sources"><strong>Sources:</strong><ul>{msg.sources.map((s, i) => <li key={i}>{s}</li>)}</ul></div>
      )}
      <p className="disclaimer">{msg.disclaimer}</p>
      {msg.message_id && (
        <div className="fb">
          {sent ? <em>{sent}</em> : (
            <>
              <button onClick={() => send({ rating: 5 })} aria-label="helpful">👍</button>
              <button onClick={() => send({ rating: 1 })} aria-label="not helpful">👎</button>
              <button onClick={() => send({ is_error_report: true, comment: prompt("What was wrong?") || "" })}>Report error</button>
            </>
          )}
        </div>
      )}
    </div>
  );
}
