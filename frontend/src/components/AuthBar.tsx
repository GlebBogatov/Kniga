import { useState } from "react";

import { DEMO } from "../api/client";
import { useAuth } from "../auth";
import { copy } from "../copy";
import type { Provider } from "../types";

export function AuthBar() {
  const { user, loading, login, logout } = useAuth();
  const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [agree, setAgree] = useState(false);
  const [marketing, setMarketing] = useState(false);

  async function doLogin(provider: Provider) {
    setBusy(true);
    try {
      await login(provider);
      setOpen(false);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="auth-bar">
      {loading ? (
        <span className="auth-loading muted">…</span>
      ) : user ? (
        <div className="auth-user">
          {(user.role === "admin" || DEMO) && (
            <a className="auth-admin" href="#/admin">
              {copy.auth.admin}
            </a>
          )}
          {(user.role === "editor" || user.role === "admin" || DEMO) && (
            <a className="auth-admin" href="#/cms">
              {copy.auth.cms}
            </a>
          )}
          <a className="auth-cabinet" href="#/cabinet">
            ☾ {user.name ?? copy.auth.cabinet}
          </a>
          <button className="auth-link" onClick={() => void logout()}>
            {copy.auth.logout}
          </button>
        </div>
      ) : (
        <button className="auth-enter" onClick={() => setOpen(true)}>
          {copy.auth.login}
        </button>
      )}

      {open && (
        <div className="modal-overlay" onClick={() => setOpen(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h3>{copy.auth.loginTitle}</h3>
            <p className="muted modal-note">{copy.auth.loginNote}</p>

            <label className="consent-row">
              <input
                type="checkbox"
                checked={agree}
                onChange={(e) => setAgree(e.target.checked)}
              />
              <span>
                {copy.consent.agreePrefix}
                <a href="#/legal/offer">{copy.consent.offer}</a>
                {copy.consent.and}
                <a href="#/legal/privacy">{copy.consent.privacy}</a>
                {copy.consent.andData}
                <a href="#/legal/consent">{copy.consent.dataConsent}</a>.
              </span>
            </label>
            <label className="consent-row">
              <input
                type="checkbox"
                checked={marketing}
                onChange={(e) => setMarketing(e.target.checked)}
              />
              <span>{copy.consent.marketing}</span>
            </label>

            <button
              className="social-btn vk"
              disabled={busy || !agree}
              onClick={() => void doLogin("vk")}
            >
              {copy.auth.vk}
            </button>
            <button
              className="social-btn yandex"
              disabled={busy || !agree}
              onClick={() => void doLogin("yandex")}
            >
              {copy.auth.yandex}
            </button>
            <button className="modal-close" onClick={() => setOpen(false)}>
              {copy.auth.close}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
