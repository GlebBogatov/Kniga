import { DEMO } from "../api/client";
import { copy } from "../copy";
import type { QuestionCheck } from "../types";

export function QuestionInput({
  value,
  onChange,
  onCheck,
  checking,
  check,
}: {
  value: string;
  onChange: (v: string) => void;
  onCheck: () => void;
  checking: boolean;
  check: QuestionCheck | null;
}) {
  return (
    <div className="question-input">
      <label className="q-label">{copy.question.label}</label>
      <textarea
        id="question-field"
        value={value}
        maxLength={500}
        rows={3}
        placeholder={copy.question.placeholder}
        onChange={(e) => onChange(e.target.value)}
      />
      <div className="q-footer">
        <span className="muted">{copy.question.counter(value.length)}</span>
        <button
          type="button"
          className="btn-secondary"
          onClick={onCheck}
          disabled={checking || value.trim().length < 3}
        >
          {checking ? copy.question.checking : copy.question.check}
        </button>
      </div>
      {check &&
        (check.crisis ? (
          <div className="plash crisis">{copy.question.crisis}</div>
        ) : check.quality === "vague" && check.hint ? (
          <div className="plash hint">
            {copy.question.hintVague} {check.hint}
          </div>
        ) : (
          <div className="plash ok">
            {DEMO ? copy.question.demoStub : copy.question.ok}
          </div>
        ))}
    </div>
  );
}
