import { useEffect } from "react";

import { setAuthToken } from "../api/client";
import { useAuth } from "../auth";
import { copy } from "../copy";

/** Возврат после Яндекс-входа: токен пришёл во фрагменте URL — сохраняем и входим. */
export function AuthCallback({ token }: { token: string }) {
  const { refresh } = useAuth();
  useEffect(() => {
    setAuthToken(token);
    void refresh().finally(() => {
      window.location.hash = "#/cabinet";
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  return (
    <main className="app">
      <p className="muted">{copy.auth.entering}</p>
    </main>
  );
}

/** Экран ошибки входа (state/обмен кода не удались или вход отключён). */
export function AuthError() {
  return (
    <main className="app">
      <a className="legal-back" href="#/">
        ← {copy.footer.back}
      </a>
      <h1 className="legal-title">{copy.auth.errorTitle}</h1>
      <p className="muted">{copy.auth.errorText}</p>
    </main>
  );
}
