import { useEffect, useState } from "react";

import { api } from "../api/client";
import { useAuth } from "../auth";
import { copy } from "../copy";
import type { ApiError, SymbolOfDay as SymbolOfDayT } from "../types";

export function SymbolOfDay() {
  const { user } = useAuth();
  const [data, setData] = useState<SymbolOfDayT | null>(null);
  const [locked, setLocked] = useState(false);

  useEffect(() => {
    setData(null);
    setLocked(false);
    if (!user) return;
    api
      .getSymbolOfDay()
      .then(setData)
      .catch((e) => {
        if ((e as ApiError).status === 402) setLocked(true);
      });
  }, [user?.id, user?.subscription.plan]);

  if (!user) return null;

  if (locked) {
    return (
      <div className="sod-teaser">
        <span>✦ {copy.symbolOfDay.teaser}</span>
        <a className="btn-secondary" href="#/tariffs">
          {copy.symbolOfDay.open}
        </a>
      </div>
    );
  }

  if (!data || data.symbol.kind !== "trigram") return null;

  return (
    <div className="sod-card">
      <div className="sod-symbol">
        <span className="sod-hanzi">{data.symbol.hanzi}</span>
        <div>
          <div className="sod-title">{copy.symbolOfDay.title}</div>
          <div className="sod-name">
            {data.symbol.name} · {data.symbol.image}
          </div>
        </div>
      </div>
      <p className="sod-reflection">{data.reflection}</p>
    </div>
  );
}
