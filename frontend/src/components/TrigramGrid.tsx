import { TRIGRAMS, TRIGRAM_ORDER } from "../data/reference.generated";
import { TrigramLines } from "./TrigramLines";

export function TrigramGrid({
  selected,
  onSelect,
}: {
  selected: string | null;
  onSelect: (id: string) => void;
}) {
  return (
    <div className="trigram-grid">
      {TRIGRAM_ORDER.map((id) => {
        const t = TRIGRAMS[id];
        return (
          <button
            key={id}
            type="button"
            className={"trigram-card" + (selected === id ? " selected" : "")}
            onClick={() => onSelect(id)}
          >
            <TrigramLines lines={t.lines} size="sm" />
            <div className="tc-name">
              {t.name} <span className="hanzi">{t.hanzi}</span>
            </div>
            <div className="tc-image muted">{t.image}</div>
          </button>
        );
      })}
    </div>
  );
}
