// Локальная сборка символа для мгновенного показа (до/вместо ответа API).
import type { HexagramSymbol, TrigramBrief, TrigramSymbol } from "../types";
import { HEXAGRAMS, TRIGRAMS, hexagramNumber } from "./reference.generated";

function brief(id: string): TrigramBrief {
  const t = TRIGRAMS[id];
  return {
    id: t.id, name: t.name, hanzi: t.hanzi, lines: t.lines,
    image: t.image, action: t.action, element: t.element,
  };
}

export function trigramPreview(id: string): TrigramSymbol {
  return { kind: "trigram", ...TRIGRAMS[id] };
}

export function hexagramPreview(lower: string, upper: string): HexagramSymbol {
  const n = hexagramNumber(lower, upper);
  const hx = HEXAGRAMS[n];
  return {
    kind: "hexagram",
    number: n, name: hx.name, title: hx.title, essence: hx.essence,
    lines: [...TRIGRAMS[lower].lines, ...TRIGRAMS[upper].lines],
    lower: brief(lower), upper: brief(upper),
  };
}

const BY_LINES: Record<string, string> = {};
for (const id of Object.keys(TRIGRAMS)) BY_LINES[TRIGRAMS[id].lines.join("")] = id;

// Превью первичной гексаграммы по 6 броскам (для мгновенного показа до ответа API).
export function coinsPreview(tosses: number[]): HexagramSymbol {
  const bit = (v: number) => (v === 7 || v === 9 ? 1 : 0);
  const lines = tosses.map(bit);
  const lower = BY_LINES[lines.slice(0, 3).join("")];
  const upper = BY_LINES[lines.slice(3, 6).join("")];
  return hexagramPreview(lower, upper);
}
