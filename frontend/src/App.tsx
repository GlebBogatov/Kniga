import { useState } from "react";

import { api } from "./api/client";
import { CoinsInput } from "./components/CoinsInput";
import { FollowUpChat } from "./components/FollowUpChat";
import { HexagramPicker } from "./components/HexagramPicker";
import { Journal } from "./components/Journal";
import { QuestionInput } from "./components/QuestionInput";
import { ReadingResult } from "./components/ReadingResult";
import { TrigramGrid } from "./components/TrigramGrid";
import { copy } from "./copy";
import { coinsPreview, hexagramPreview, trigramPreview } from "./data/symbol";
import { canSubmit } from "./lib/validation";
import type { ApiError, DivinationSymbol, Mode, QuestionCheck, ReadingResponse } from "./types";

const EMPTY_TOSSES: (number | null)[] = [null, null, null, null, null, null];

export default function App() {
  const [tab, setTab] = useState<"reading" | "journal">("reading");
  const [mode, setMode] = useState<Mode>("8");
  const [question, setQuestion] = useState("");

  const [trigramId, setTrigramId] = useState<string | null>(null);
  const [lowerId, setLowerId] = useState<string | null>(null);
  const [upperId, setUpperId] = useState<string | null>(null);
  const [tosses, setTosses] = useState<(number | null)[]>(EMPTY_TOSSES);

  const [check, setCheck] = useState<QuestionCheck | null>(null);
  const [checking, setChecking] = useState(false);

  const [preview, setPreview] = useState<DivinationSymbol | null>(null);
  const [result, setResult] = useState<ReadingResponse | null>(null);
  const [streamText, setStreamText] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);

  const tossesComplete = tosses.every((t) => t !== null);
  const hasSymbol =
    mode === "8" ? !!trigramId : mode === "64" ? !!(lowerId && upperId) : tossesComplete;

  function resetResult() {
    setPreview(null);
    setResult(null);
    setError(null);
  }

  function switchMode(m: Mode) {
    setMode(m);
    resetResult();
  }

  async function runCheck() {
    setChecking(true);
    try {
      setCheck(await api.checkQuestion(question));
    } catch {
      setCheck(null);
    } finally {
      setChecking(false);
    }
  }

  async function submit(virtual = false) {
    if (question.trim().length < 3) return;
    setLoading(true);
    setError(null);
    setResult(null);
    setStreamText("");

    // Мгновенное превью символа (классика видна даже при сбое API).
    let localPreview: DivinationSymbol | null = null;
    if (mode === "8" && trigramId) localPreview = trigramPreview(trigramId);
    else if (mode === "64" && lowerId && upperId) localPreview = hexagramPreview(lowerId, upperId);
    else if (mode === "coins" && !virtual && tossesComplete)
      localPreview = coinsPreview(tosses as number[]);
    setPreview(localPreview);

    const body = {
      mode,
      question,
      trigram_id: mode === "8" ? trigramId ?? undefined : undefined,
      lower_id: mode === "64" ? lowerId ?? undefined : undefined,
      upper_id: mode === "64" ? upperId ?? undefined : undefined,
      tosses: mode === "coins" ? (virtual ? null : (tosses as number[])) : undefined,
    };

    let streamed = false;
    async function fallback() {
      try {
        const res = await api.createReading(body);
        setResult(res);
        setPreview(res.symbol);
      } catch (e) {
        setError(e as ApiError);
      } finally {
        setLoading(false);
      }
    }

    await api.streamReading(body, {
      onDelta: (t) => {
        streamed = true;
        setStreamText((s) => s + t);
      },
      onDone: (res) => {
        setResult(res);
        setPreview(res.symbol);
        setStreamText("");
        setLoading(false);
      },
      onError: (err) => {
        // если ничего не пришло по стриму — пробуем обычный вызов
        if (!streamed) void fallback();
        else {
          setError(err);
          setLoading(false);
        }
      },
    });
  }

  const lastVirtual = mode === "coins" && !tossesComplete;

  return (
    <main className="app">
      <header className="app-header">
        <h1>{copy.appTitle}</h1>
        <p className="muted">{copy.appSubtitle}</p>
        <nav className="tabs">
          <button
            className={tab === "reading" ? "active" : ""}
            onClick={() => setTab("reading")}
          >
            {copy.tabs.reading}
          </button>
          <button
            className={tab === "journal" ? "active" : ""}
            onClick={() => setTab("journal")}
          >
            {copy.tabs.journal}
          </button>
        </nav>
      </header>

      {tab === "journal" && <Journal />}

      {tab === "reading" && (
        <>
          <div className="mode-switch">
            {(["8", "64", "coins"] as Mode[]).map((m) => (
              <button
                key={m}
                className={mode === m ? "active" : ""}
                onClick={() => switchMode(m)}
              >
                {copy.modes[m]}
              </button>
            ))}
          </div>

          <QuestionInput
            value={question}
            onChange={setQuestion}
            onCheck={runCheck}
            checking={checking}
            check={check}
          />

          <details className="how-to">
            <summary>{copy.howTo.title}</summary>
            <p className="muted">{copy.howTo.body}</p>
          </details>

          {mode === "8" && <TrigramGrid selected={trigramId} onSelect={setTrigramId} />}
          {mode === "64" && (
            <HexagramPicker
              lower={lowerId}
              upper={upperId}
              onLower={setLowerId}
              onUpper={setUpperId}
            />
          )}
          {mode === "coins" && (
            <CoinsInput
              tosses={tosses}
              onChange={(i, v) =>
                setTosses((prev) => prev.map((t, idx) => (idx === i ? v : t)))
              }
              onVirtual={() => submit(true)}
            />
          )}

          <button
            type="button"
            className="btn-primary"
            disabled={!canSubmit(question, hasSymbol, loading)}
            onClick={() => submit(false)}
          >
            {loading ? copy.submitLoading : copy.submit}
          </button>

          {loading && !preview && <div className="rr-loading">{copy.submitLoading}</div>}

          {preview && (
            <ReadingResult
              symbol={preview}
              result={result}
              loading={loading}
              error={error}
              streamingText={streamText}
              onRetry={() => submit(lastVirtual)}
            />
          )}

          {result && <FollowUpChat key={result.reading_id} readingId={result.reading_id} />}

          {error && !preview && (
            <div className="plash error">
              <span>{copy.errors.generic}</span>
              <button className="btn-secondary" onClick={() => submit(lastVirtual)}>
                {copy.errors.retry}
              </button>
            </div>
          )}
        </>
      )}
    </main>
  );
}
