import { createContext, useContext, useEffect, useState, type ReactNode } from "react";

import { api, getAuthToken, setAuthToken } from "./api/client";
import type { ProfilePatch, Provider, UiMode, User } from "./types";

// Кэш выбранного интерфейса: чтобы App применил режим мгновенно (до резолва
// авторизации) и чтобы у анонимных гостей был стабильный дефолт — «простой».
const UI_MODE_KEY = "kn_ui_mode";

export function cachedUiMode(): UiMode | null {
  try {
    const v = localStorage.getItem(UI_MODE_KEY);
    return v === "simple" || v === "advanced" ? v : null;
  } catch {
    return null;
  }
}

function setUiModeCache(mode: UiMode | null): void {
  try {
    if (mode) localStorage.setItem(UI_MODE_KEY, mode);
    else localStorage.removeItem(UI_MODE_KEY);
  } catch {
    /* localStorage недоступен — игнорируем */
  }
}

interface AuthState {
  user: User | null;
  loading: boolean;
  login: (provider: Provider) => Promise<void>;
  loginWithRole: (role: "user" | "editor" | "admin") => Promise<void>;
  logout: () => Promise<void>;
  refresh: () => Promise<void>;
  updateProfile: (patch: ProfilePatch) => Promise<void>;
  deleteAccount: () => Promise<void>;
}

const AuthContext = createContext<AuthState | null>(null);

function providerLabel(p: Provider): string {
  return p === "vk" ? "VK" : "Яндекс";
}

// Стабильный «фейковый» id входа на браузер — чтобы повторный вход-заглушка
// возвращал того же пользователя (реальный OAaut подставит настоящий id).
function fakeUid(provider: Provider): string {
  const key = "kn_fake_uid_" + provider;
  try {
    let v = localStorage.getItem(key);
    if (!v) {
      v = "stub-" + Math.random().toString(36).slice(2, 10);
      localStorage.setItem(key, v);
    }
    return v;
  } catch {
    return "stub-" + provider;
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  // Единая точка установки пользователя: синхронно кэширует выбранный интерфейс.
  function syncUser(u: User | null): void {
    setUser(u);
    setUiModeCache(u ? u.ui_mode : null);
  }

  async function refresh() {
    if (!getAuthToken()) {
      syncUser(null);
      setLoading(false);
      return;
    }
    try {
      syncUser(await api.me());
    } catch {
      setAuthToken(null);
      syncUser(null);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function login(provider: Provider) {
    const res = await api.devLogin({
      provider,
      provider_user_id: fakeUid(provider),
      name: `Гость ${providerLabel(provider)}`,
      email: `${provider}@example.com`,
    });
    setAuthToken(res.token);
    syncUser(res.user);
  }

  // Служебный вход с ролью (работает, пока на бэкенде включён ALLOW_DEV_LOGIN).
  async function loginWithRole(role: "user" | "editor" | "admin") {
    const res = await api.devLogin({
      provider: "dev",
      provider_user_id: `owner-${role}`,
      name: role === "admin" ? "Владелец" : role === "editor" ? "Таня" : "Гость",
      email: `${role}@example.com`,
      role,
    });
    setAuthToken(res.token);
    syncUser(res.user);
  }

  async function logout() {
    try {
      await api.logout();
    } catch {
      /* всё равно выходим локально */
    }
    setAuthToken(null);
    syncUser(null);
  }

  async function updateProfile(patch: ProfilePatch) {
    syncUser(await api.updateProfile(patch));
  }

  async function deleteAccount() {
    await api.deleteAccount();
    setAuthToken(null);
    syncUser(null);
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        login,
        loginWithRole,
        logout,
        refresh,
        updateProfile,
        deleteAccount,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth вне AuthProvider");
  return ctx;
}
