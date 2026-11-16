
import React, { useEffect, useRef, useState } from "react";
import { api } from "./api.js";
import ResponseView from "./response_view.jsx";

export default function Chat({ userKey = "default" }) {
  const [items, setItems] = useState([]);
  const [text, setText] = useState("");
  const [cid, setCid] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const end = useRef(null);

  const storageKey = `activeConversationId:${userKey}`;

  // Restore the last active conversation from the backend
  useEffect(() => {
    let cancelled = false;

    async function restoreConversation() {
      try {
        let conversationId = sessionStorage.getItem(storageKey);

        // If there is no saved active conversation, load the latest one
        if (!conversationId) {
          const conversations = await api.conversations();
          conversationId = conversations[0]?.id || null;
        }

        if (!conversationId) return;

        const conversation = await api.conversation(conversationId);

        if (cancelled) return;

        setCid(conversation.id);
        sessionStorage.setItem(storageKey, conversation.id);

        setItems(
          conversation.messages.map((m) =>
            m.role === "assistant"
              ? {
                  role: "assistant",
                  answer: m.content,
                  message_id: m.id,
                  sources: m.sources || [],
                  disclaimer: m.disclaimer,
                }
              : {
                  role: "user",
                  content: m.content,
                }
          )
        );
      } catch (err) {
        if (!cancelled) {
          setError("Could not restore conversation: " + err.message);
        }
      }
    }

    restoreConversation();

    return () => {
      cancelled = true;
    };
  }, [storageKey]);

  useEffect(() => {
    end.current?.scrollIntoView({ behavior: "smooth" });
  }, [items]);

  const submit = async (e) => {
    e.preventDefault();

    const q = text.trim();
    if (!q || busy) return;

    setError("");
    setBusy(true);
    setText("");

    setItems((x) => [...x, { role: "user", content: q }]);

    try {
      const r = await api.ask(q, cid);

      setCid(r.conversation_id);
      sessionStorage.setItem(storageKey, r.conversation_id);

      setItems((x) => [
        ...x,
        { role: "assistant", ...r },
      ]);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  const newChat = () => {
    setItems([]);
    setCid(null);
    setError("");
    sessionStorage.removeItem(storageKey);
  };

  return (
    <section>
      <div className="chat">
        {items.length === 0 && (
          <p className="hint">
            Ask about consumer, tenancy, family, employment,
            cyber, criminal procedure or RTI matters in India.
          </p>
        )}

        {items.map((m, i) =>
          m.role === "user" ? (
            <div key={i} className="bubble user">
              {m.content}
            </div>
          ) : (
            <ResponseView key={i} msg={m} />
          )
        )}

        {busy && (
          <div className="bubble assistant">Thinking…</div>
        )}

        <div ref={end} />
      </div>

      {error && (
        <p className="error" role="alert">{error}</p>
      )}

      <form onSubmit={submit} className="row">
        <input
          value={text}
          onChange={(e) => setText(e.target.value)}
          maxLength={1000}
          placeholder="Type your legal question…"
          aria-label="question"
        />

        <button disabled={busy}>Send</button>

        <button type="button" onClick={newChat}>
          New chat
        </button>
      </form>
    </section>
  );
}
