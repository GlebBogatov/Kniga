import { useEffect, useState } from "react";

import { api } from "../api/client";
import { copy } from "../copy";
import type { Preset } from "../types";

export function Presets({ onPick }: { onPick: (preset: Preset) => void }) {
  const [presets, setPresets] = useState<Preset[]>([]);

  useEffect(() => {
    api.getPresets().then(setPresets).catch(() => setPresets([]));
  }, []);

  if (presets.length === 0) return null;

  return (
    <div className="presets">
      <div className="muted">{copy.presets.title}</div>
      <div className="presets-chips">
        {presets.map((p) => (
          <button
            key={p.slug}
            type="button"
            className="preset-chip"
            title={p.subtitle}
            onClick={() => onPick(p)}
          >
            {p.title}
          </button>
        ))}
      </div>
    </div>
  );
}
