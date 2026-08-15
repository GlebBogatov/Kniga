import { useState } from "react";

import { useAuth } from "../auth";
import { copy } from "../copy";
import type { Provider } from "../types";

export function AuthBar() {
  const { user, loading, login, logout } = useAuth();
  const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState(false);

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
            <button
              className="social-btn vk"
              disabled={busy}
              onClick={() => void doLogin("vk")}
            >
              {copy.auth.vk}
            </button>
            <button
              className="social-btn yandex"
              disabled={busy}
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
