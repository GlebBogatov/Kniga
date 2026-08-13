import { copy } from "../copy";
import { HEXAGRAMS, TRIGRAMS, TRIGRAM_ORDER, hexagramNumber } from "../data/reference.generated";
import { TrigramLines } from "./TrigramLines";

function PickerRow({
  label,
  selected,
  onSelect,
}: {
  label: string;
  selected: string | null;
  onSelect: (id: string) => void;
}) {
  return (
    <div className="picker-row">
      <div className="picker-label muted">{label}</div>
      <div className="picker-choices">
        {TRIGRAM_ORDER.map((id) => (
          <button
            key={id}
            type="button"
            className={"picker-chip" + (selected === id ? " selected" : "")}
            onClick={() => onSelect(id)}
          >
            <TrigramLines lines={TRIGRAMS[id].lines} size="sm" />
            <span>{TRIGRAMS[id].name}</span>
          </button>
        ))}
      </div>
    </div>
  );
}

export function HexagramPicker({
  lower,
  upper,
  onLower,
  onUpper,
}: {
  lower: string | null;
  upper: string | null;
  onLower: (id: string) => void;
  onUpper: (id: string) => void;
}) {
  const n = lower && upper ? hexagramNumber(lower, upper) : null;
  const hx = n ? HEXAGRAMS[n] : null;
  return (
    <div className="hexagram-picker">
      <PickerRow label={copy.picker.lower} selected={lower} onSelect={onLower} />
      <PickerRow label={copy.picker.upper} selected={upper} onSelect={onUpper} />
      {lower && upper && hx && (
        <div className="hex-preview">
          <TrigramLines lines={[...TRIGRAMS[lower].lines, ...TRIGRAMS[upper].lines]} size="lg" />
          <div>
            <div className="hex-num">№{n}</div>
            <div className="hex-name">
              {hx.name} «{hx.title}»
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
