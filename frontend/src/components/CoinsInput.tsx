import { copy } from "../copy";

export function CoinsInput({
  tosses,
  onChange,
  onVirtual,
}: {
  tosses: (number | null)[];
  onChange: (index: number, value: number) => void;
  onVirtual: () => void;
}) {
  return (
    <div className="coins-input">
      <div className="muted">{copy.coins.title}</div>
      <div className="coins-row">
        {tosses.map((v, i) => (
          <select
            key={i}
            value={v ?? ""}
            aria-label={`Бросок ${i + 1}`}
            onChange={(e) => onChange(i, Number(e.target.value))}
          >
            <option value="" disabled>
              —
            </option>
            {[6, 7, 8, 9].map((n) => (
              <option key={n} value={n}>
                {n}
              </option>
            ))}
          </select>
        ))}
      </div>
      <button type="button" className="btn-secondary" onClick={onVirtual}>
        {copy.coins.virtual}
      </button>
    </div>
  );
}
