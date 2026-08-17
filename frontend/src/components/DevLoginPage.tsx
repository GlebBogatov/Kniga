import { useEffect, useState } from "react";

import { useAuth } from "../auth";
import { copy } from "../copy";
import type { ApiError } from "../types";

export function DevLoginPage() {
  const { user, loginWithRole } = useAuth();
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    window.scrollTo({ top: 0 });
  }, []);

  async function enter(role: "user" | "editor" | "admin", target: string) {
    setBusy(role);
    setError(null);
    try {
      await loginWithRole(role);
      window.location.hash = target;
    } catch (e) {
      const err = e as ApiError;
      setError(err.status === 403 ? copy.devEntry.disabled : err.detail);
    } finally {
      setBusy(null);
    }
  }

  return (
    <main className="app">
      <a className="legal-back" href="#/">
        ← {copy.footer.back}
      </a>
      <h1 className="legal-title">{copy.devEntry.title}</h1>
      <p className="muted modal-note">{copy.devEntry.note}</p>

      {user && (
        <p className="muted">
          {copy.devEntry.current}: <b>{user.name}</b> ({user.role})
        </p>
      )}
      {error && <div className="plash error">{error}</div>}

      <div className="cab-login">
        <button className="btn-secondary" disabled={busy !== null} onClick={() => void enter("admin", "#/admin")}>
          {copy.devEntry.asAdmin}
        </button>
        <button className="btn-secondary" disabled={busy !== null} onClick={() => void enter("editor", "#/cms")}>
          {copy.devEntry.asEditor}
        </button>
        <button className="btn-secondary" disabled={busy !== null} onClick={() => void enter("user", "#/")}>
          {copy.devEntry.asUser}
        </button>
      </div>
    </main>
  );
}
