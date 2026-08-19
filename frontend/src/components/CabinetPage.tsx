import { useEffect, useState } from "react";

import { DEMO, api, startYandexLogin } from "../api/client";
import { useAuth } from "../auth";
import { copy } from "../copy";
import type { Provider, Subscription, UiMode } from "../types";
import { Journal } from "./Journal";

function statusLabel(s: Subscription["status"]): string {
  return s === "active"
    ? copy.cabinet.statusActive
    : s === "canceled"
      ? copy.cabinet.statusCanceled
      : copy.cabinet.statusExpired;
}

export function CabinetPage() {
  const { user, loading, login, logout, updateProfile, deleteAccount, refresh } =
    useAuth();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [uiSaving, setUiSaving] = useState(false);

  useEffect(() => {
    window.scrollTo({ top: 0 });
  }, []);

  useEffect(() => {
    if (user) {
      setName(user.name ?? "");
      setEmail(user.email ?? "");
    }
  }, [user?.id]); // eslint-disable-line react-hooks/exhaustive-deps

  async function save() {
    setSaving(true);
    setSaved(false);
    try {
      await updateProfile({ name, email });
      setSaved(true);
    } finally {
      setSaving(false);
    }
  }

  async function removeAccount() {
    if (!window.confirm(copy.cabinet.deleteConfirm)) return;
    await deleteAccount();
    window.location.hash = "#/";
  }

  async function setUiMode(mode: UiMode) {
    if (uiSaving || user?.ui_mode === mode) return;
    setUiSaving(true);
    try {
      await updateProfile({ ui_mode: mode });
    } finally {
      setUiSaving(false);
    }
  }

  if (loading) {
    return (
      <main className="app">
        <p className="muted">{copy.journal.loading}</p>
      </main>
    );
  }

  if (!user) {
    return (
      <main className="app cabinet">
        <a className="legal-back" href="#/">
          ← {copy.footer.back}
        </a>
        <h1 className="legal-title">{copy.cabinet.title}</h1>
        <p className="muted">{copy.cabinet.loginPrompt}</p>
        <div className="cab-login">
          <button className="social-btn vk" onClick={() => void login("vk" as Provider)}>
            {copy.auth.vk}
          </button>
          <button
            className="social-btn yandex"
            onClick={() => (DEMO ? void login("yandex" as Provider) : startYandexLogin())}
          >
            {copy.auth.yandex}
          </button>
        </div>
        <p className="muted modal-note">{copy.auth.loginNote}</p>
      </main>
    );
  }

  const sub = user.subscription;
  const premium = sub.plan === "premium";

  return (
    <main className="app cabinet">
      <a className="legal-back" href="#/">
        ← {copy.footer.back}
      </a>
      <h1 className="legal-title">{copy.cabinet.title}</h1>

      {/* Профиль */}
      <section className="cab-card">
        <h2>{copy.cabinet.profile}</h2>
        <label className="cab-field">
          <span>{copy.cabinet.name}</span>
          <input value={name} onChange={(e) => setName(e.target.value)} maxLength={120} />
        </label>
        <label className="cab-field">
          <span>{copy.cabinet.email}</span>
          <input value={email} onChange={(e) => setEmail(e.target.value)} maxLength={255} />
        </label>
        <p className="muted cab-provider">
          {copy.cabinet.provider}: {user.provider.toUpperCase()}
        </p>
        <div className="cab-actions">
          <button className="btn-secondary" disabled={saving} onClick={save}>
            {saving ? copy.cabinet.saving : copy.cabinet.save}
          </button>
          {saved && <span className="muted">{copy.cabinet.saved}</span>}
        </div>
      </section>

      {/* Интерфейс */}
      <section className="cab-card">
        <h2>{copy.cabinet.uiTitle}</h2>
        <p className="muted">{copy.cabinet.uiHint}</p>
        <div className="ui-switch">
          <button
            className={user.ui_mode === "simple" ? "active" : ""}
            disabled={uiSaving}
            onClick={() => void setUiMode("simple")}
          >
            {copy.cabinet.uiSimple}
          </button>
          <button
            className={user.ui_mode === "advanced" ? "active" : ""}
            disabled={uiSaving}
            onClick={() => void setUiMode("advanced")}
          >
            {copy.cabinet.uiAdvanced}
          </button>
        </div>
        <p className="muted ui-desc">
          {user.ui_mode === "simple"
            ? copy.cabinet.uiSimpleDesc
            : copy.cabinet.uiAdvancedDesc}
        </p>
      </section>

      {/* Подписка */}
      <section className="cab-card">
        <h2>{copy.cabinet.subscription}</h2>
        <p className="cab-plan">
          <span className={premium ? "plan-badge premium" : "plan-badge"}>
            {premium ? copy.cabinet.planPremium : copy.cabinet.planFree}
          </span>
          <span className="muted"> · {statusLabel(sub.status)}</span>
        </p>
        {sub.current_period_end && (
          <p className="muted">
            {copy.cabinet.periodEnd}:{" "}
            {new Date(sub.current_period_end).toLocaleDateString("ru-RU")}
          </p>
        )}
        {premium && (
          <p className="muted">
            {sub.auto_renew ? copy.cabinet.autoRenewOn : copy.cabinet.autoRenewOff}
          </p>
        )}
        <div className="cab-actions">
          <a className="btn-secondary" href="#/tariffs">
            {copy.cabinet.manage}
          </a>
          {premium && sub.auto_renew && (
            <button
              className="btn-secondary"
              onClick={async () => {
                await api.cancelSubscription();
                await refresh();
              }}
            >
              {copy.cabinet.cancelRenew}
            </button>
          )}
        </div>
      </section>

      {/* История */}
      <section className="cab-card">
        <h2>{copy.cabinet.history}</h2>
        <Journal />
      </section>

      {/* Опасная зона */}
      <section className="cab-card cab-danger">
        <h2>{copy.cabinet.danger}</h2>
        <p className="muted">{copy.cabinet.deleteHint}</p>
        <div className="cab-actions">
          <button className="btn-secondary" onClick={() => void logout()}>
            {copy.cabinet.logout}
          </button>
          <button className="btn-danger" onClick={() => void removeAccount()}>
            {copy.cabinet.deleteBtn}
          </button>
        </div>
      </section>
    </main>
  );
}
