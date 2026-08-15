import { useEffect, useState } from "react";

import { api } from "../api/client";
import { useAuth } from "../auth";
import { copy } from "../copy";
import type { Provider, Tariff } from "../types";

export function TariffsPage() {
  const { user, login, refresh } = useAuth();
  const [tariffs, setTariffs] = useState<Tariff[] | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [done, setDone] = useState(false);

  useEffect(() => {
    window.scrollTo({ top: 0 });
    api.getTariffs().then(setTariffs).catch(() => setTariffs([]));
  }, []);

  const premium = user?.subscription.plan === "premium";

  async function buy(t: Tariff) {
    if (!user) return;
    setBusy(t.id);
    try {
      const init = await api.checkout(t.id);
      if (init.stub) {
        await api.devConfirm(init.payment_id);
        await refresh();
        setDone(true);
      } else if (init.confirmation_url) {
        window.location.href = init.confirmation_url; // реальный ЮKassa
      }
    } finally {
      setBusy(null);
    }
  }

  return (
    <main className="app tariffs">
      <a className="legal-back" href="#/">
        ← {copy.footer.back}
      </a>
      <h1 className="legal-title">{copy.tariffs.title}</h1>
      <p className="muted tariffs-sub">{copy.tariffs.subtitle}</p>

      {done ? (
        <div className="tariff-success">
          <h2>{copy.tariffs.successTitle}</h2>
          <p>{copy.tariffs.successBody}</p>
          <a className="btn-secondary" href="#/cabinet">
            {copy.tariffs.toCabinet}
          </a>
        </div>
      ) : premium ? (
        <p className="tariff-current">{copy.tariffs.currentPremium}</p>
      ) : (
        <>
          {!user && (
            <div className="cab-login">
              <p className="muted">{copy.tariffs.loginPrompt}</p>
              <button className="social-btn vk" onClick={() => void login("vk" as Provider)}>
                {copy.auth.vk}
              </button>
              <button
                className="social-btn yandex"
                onClick={() => void login("yandex" as Provider)}
              >
                {copy.auth.yandex}
              </button>
            </div>
          )}

          <div className="tariff-grid">
            {(tariffs ?? []).map((t) => (
              <div key={t.id} className="tariff-card">
                <h2>{t.title}</h2>
                <p className="tariff-price">
                  {t.price.toLocaleString("ru-RU")} ₽
                  <span className="muted">
                    {t.period === "year" ? copy.tariffs.perYear : copy.tariffs.perMonth}
                  </span>
                </p>
                <p className="muted tariff-subtitle">{t.subtitle}</p>
                <button
                  className="btn-primary tariff-buy"
                  disabled={!user || busy !== null}
                  onClick={() => void buy(t)}
                >
                  {busy === t.id ? copy.tariffs.processing : copy.tariffs.buy}
                </button>
              </div>
            ))}
          </div>

          <div className="tariff-features">
            <h3>{copy.tariffs.features}</h3>
            <ul>
              {copy.tariffs.featureList.map((f) => (
                <li key={f}>✦ {f}</li>
              ))}
            </ul>
          </div>

          <p className="muted modal-note tariff-stub">{copy.tariffs.stubNote}</p>
        </>
      )}
    </main>
  );
}
