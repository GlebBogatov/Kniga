import { useEffect, useState } from "react";

import { api } from "../api/client";
import { copy } from "../copy";
import type { ApiError, JournalEntry } from "../types";

export function Journal() {
  const [entries, setEntries] = useState<JournalEntry[] | null>(null);
  const [analysis, setAnalysis] = useState<string | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    try {
      setEntries(await api.getJournal());
    } catch {
      setError(copy.errors.generic);
      setEntries([]);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function remove(id: number) {
    if (!window.confirm(copy.journal.confirmDelete)) return;
    try {
      await api.deleteEntry(id);
      setEntries((prev) => (prev ? prev.filter((e) => e.id !== id) : prev));
    } catch {
      setError(copy.errors.generic);
    }
  }

  async function analyze() {
    setAnalyzing(true);
    setError(null);
    try {
      const a = await api.analyzeJournal();
      setAnalysis(a.analysis_markdown);
    } catch (e) {
      setError((e as ApiError).detail ?? copy.errors.generic);
    } finally {
      setAnalyzing(false);
    }
  }

  if (entries === null) return <p className="muted">{copy.journal.loading}</p>;
  if (entries.length === 0) return <p className="muted">{copy.journal.empty}</p>;

  return (
    <div className="journal">
      <div className="journal-toolbar">
        <button
          type="button"
          className="btn-secondary"
          disabled={entries.length < 2 || analyzing}
          onClick={analyze}
        >
          {analyzing ? copy.journal.analyzing : copy.journal.analyze}
        </button>
        {entries.length < 2 && <span className="muted">{copy.journal.analyzeHint}</span>}
      </div>

      {error && <div className="plash error">{error}</div>}
      {analysis && <div className="journal-analysis">{analysis}</div>}

      <ul className="journal-list">
        {entries.map((e) => (
          <li key={e.id} className="journal-item">
            <div className="ji-head">
              <span className="muted">
                {e.ts ? new Date(e.ts).toLocaleString("ru-RU") : ""}
              </span>
              <button type="button" className="btn-secondary" onClick={() => remove(e.id)}>
                {copy.journal.delete}
              </button>
            </div>
            <div className="ji-symbol">{e.symbol_label}</div>
            <div className="ji-question">{e.question}</div>
            <p className="muted">{e.interpretation}</p>
          </li>
        ))}
      </ul>
    </div>
  );
}
