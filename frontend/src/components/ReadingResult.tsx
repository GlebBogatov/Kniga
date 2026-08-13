import { copy } from "../copy";
import type { ApiError, DivinationSymbol, ReadingResponse } from "../types";
import { TrigramLines } from "./TrigramLines";

function classicText(symbol: DivinationSymbol): string {
  return symbol.kind === "trigram" ? symbol.classic : symbol.essence;
}

function headerName(symbol: DivinationSymbol): string {
  if (symbol.kind === "trigram") return `${symbol.name} · ${symbol.image}`;
  return `№${symbol.number} ${symbol.name} «${symbol.title}»`;
}

function seal(symbol: DivinationSymbol): string {
  return symbol.kind === "trigram" ? symbol.hanzi : symbol.upper.hanzi;
}

function Block({ title, text }: { title: string; text: string }) {
  return (
    <div className="rr-block">
      <h3>{title}</h3>
      <p>{text}</p>
    </div>
  );
}

export function ReadingResult({
  symbol,
  result,
  loading,
  error,
  onRetry,
  streamingText = "",
}: {
  symbol: DivinationSymbol;
  result: ReadingResponse | null;
  loading: boolean;
  error: ApiError | null;
  onRetry: () => void;
  streamingText?: string;
}) {
  return (
    <section className="reading-result">
      <div className="rr-header">
        <TrigramLines lines={symbol.lines} size="lg" />
        <div className="rr-meta">
          <h2>{headerName(symbol)}</h2>
          {symbol.kind === "trigram" && (
            <div className="muted">
              {symbol.action} · {symbol.family} · {symbol.element} · {symbol.direction}
            </div>
          )}
          {symbol.kind === "hexagram" && (
            <div className="muted">
              {symbol.lower.name} / {symbol.upper.name}
            </div>
          )}
          <div className="rr-classic">
            <b>{copy.result.classic}:</b> {classicText(symbol)}
          </div>
        </div>
        <div className="rr-seal">{seal(symbol)}</div>
      </div>

      {loading && !streamingText && !result && (
        <div className="rr-loading">{copy.submitLoading}</div>
      )}

      {!result && streamingText && (
        <div className="rr-blocks">
          <div className="rr-block">
            <h3>{copy.result.interpretation}</h3>
            <p>
              {streamingText}
              <span className="rr-cursor">▌</span>
            </p>
          </div>
        </div>
      )}

      {error && (
        <div className="plash error">
          <span>{error.status === 503 ? copy.errors.degraded : copy.errors.generic}</span>
          <button type="button" className="btn-secondary" onClick={onRetry}>
            {copy.errors.retry}
          </button>
        </div>
      )}

      {result && (
        <div className="rr-blocks">
          <Block title={copy.result.interpretation} text={result.interpretation} />
          <Block title={copy.result.advice} text={result.advice} />
          <Block title={copy.result.caution} text={result.caution} />
          <Block title={copy.result.nextStep} text={result.next_step} />
          {result.lines_commentary && result.lines_commentary.length > 0 && (
            <div className="rr-block">
              <h3>{copy.result.linesCommentary}</h3>
              <ul>
                {result.lines_commentary.map((lc) => (
                  <li key={lc.line}>
                    <b>{lc.line}:</b> {lc.text}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {symbol.kind === "hexagram" && symbol.secondary && (
        <div className="rr-secondary muted">
          {copy.result.secondary}: №{symbol.secondary.number} {symbol.secondary.name} «
          {symbol.secondary.title}»
        </div>
      )}

      <div className="rr-disclaimer muted">{copy.disclaimer}</div>
    </section>
  );
}
