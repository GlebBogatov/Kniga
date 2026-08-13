import { useState } from "react";

import { api } from "../api/client";
import { copy } from "../copy";
import type { ApiError, ChatTurn } from "../types";

export function FollowUpChat({ readingId }: { readingId: number }) {
  const [history, setHistory] = useState<ChatTurn[]>([]);
  const [input, setInput] = useState("");
  const [remaining, setRemaining] = useState(5);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const disabled = remaining <= 0;

  async function send() {
    const msg = input.trim();
    if (!msg || loading || disabled) return;
    setLoading(true);
    setError(null);
    setHistory((h) => [...h, { role: "user", content: msg }]);
    setInput("");
    try {
      const res = await api.chat(readingId, msg);
      setHistory((h) => [...h, { role: "assistant", content: res.reply }]);
      setRemaining(res.remaining);
    } catch (e) {
      setError((e as ApiError).detail ?? copy.errors.generic);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="follow-chat">
      <h3>{copy.chat.title}</h3>
      {history.length > 0 && (
        <div className="fc-history">
          {history.map((t, i) => (
            <div key={i} className={"fc-msg " + t.role}>
              {t.content}
            </div>
          ))}
        </div>
      )}
      {error && <div className="plash error">{error}</div>}
      <div className="fc-input">
        <input
          type="text"
          value={input}
          maxLength={500}
          placeholder={disabled ? copy.chat.done : copy.chat.placeholder}
          disabled={disabled || loading}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") send();
          }}
        />
        <button
          type="button"
          className="btn-secondary"
          onClick={send}
          disabled={disabled || loading || input.trim().length === 0}
        >
          {loading ? copy.chat.sending : copy.chat.send}
        </button>
      </div>
      <div className="muted">{copy.chat.remaining(remaining)}</div>
    </div>
  );
}
