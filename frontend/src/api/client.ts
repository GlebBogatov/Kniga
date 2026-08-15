import type {
  ApiError,
  AuthResult,
  ChatReply,
  CheckoutInit,
  ConfirmResult,
  JournalAnalysis,
  JournalEntry,
  PaymentEntry,
  Preset,
  ProfilePatch,
  QuestionCheck,
  ReadingRequestBody,
  ReadingResponse,
  StreamHandlers,
  Tariff,
  User,
} from "../types";
import { demoApi } from "./demo";

const BASE = "/api";
const TIMEOUT_MS = 60_000;

const TOKEN_KEY = "kn_auth_token";

export function getAuthToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

export function setAuthToken(token: string | null): void {
  try {
    if (token) localStorage.setItem(TOKEN_KEY, token);
    else localStorage.removeItem(TOKEN_KEY);
  } catch {
    /* localStorage недоступен — игнорируем */
  }
}

function authHeaders(hasBody: boolean): Record<string, string> {
  const h: Record<string, string> = {};
  if (hasBody) h["Content-Type"] = "application/json";
  const token = getAuthToken();
  if (token) h["Authorization"] = `Bearer ${token}`;
  return h;
}

async function request<T>(method: string, path: string, body?: unknown): Promise<T> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);
  try {
    const res = await fetch(BASE + path, {
      method,
      headers: authHeaders(body !== undefined),
      body: body !== undefined ? JSON.stringify(body) : undefined,
      signal: controller.signal,
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      throw {
        status: res.status,
        detail: (data as { detail?: string }).detail ?? "Ошибка запроса",
      } as ApiError;
    }
    return data as T;
  } catch (e) {
    if (e instanceof DOMException && e.name === "AbortError") {
      throw { status: 0, detail: "Превышено время ожидания." } as ApiError;
    }
    if (e && typeof e === "object" && "status" in e) throw e;
    throw { status: 0, detail: "Сеть недоступна." } as ApiError;
  } finally {
    clearTimeout(timer);
  }
}

function parseSseEvent(raw: string): { event: string; data: unknown } | null {
  let event = "message";
  let dataStr = "";
  for (const line of raw.split("\n")) {
    if (line.startsWith("event:")) event = line.slice(6).trim();
    else if (line.startsWith("data:")) dataStr += line.slice(5).trim();
  }
  if (!dataStr) return null;
  try {
    return { event, data: JSON.parse(dataStr) };
  } catch {
    return null;
  }
}

async function streamReading(body: ReadingRequestBody, h: StreamHandlers): Promise<void> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);
  try {
    const res = await fetch(BASE + "/reading/stream", {
      method: "POST",
      headers: authHeaders(true),
      body: JSON.stringify(body),
      signal: controller.signal,
    });
    if (!res.ok || !res.body) {
      const data = await res.json().catch(() => ({}));
      h.onError({
        status: res.status,
        detail: (data as { detail?: string }).detail ?? "Ошибка запроса",
      });
      return;
    }
    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buf = "";
    for (;;) {
      const { value, done } = await reader.read();
      if (done) break;
      buf += decoder.decode(value, { stream: true });
      let idx: number;
      while ((idx = buf.indexOf("\n\n")) !== -1) {
        const ev = parseSseEvent(buf.slice(0, idx));
        buf = buf.slice(idx + 2);
        if (!ev) continue;
        if (ev.event === "delta") h.onDelta((ev.data as { text: string }).text);
        else if (ev.event === "done") h.onDone(ev.data as ReadingResponse);
        else if (ev.event === "error")
          h.onError({ status: 502, detail: (ev.data as { detail: string }).detail });
      }
    }
  } catch (e) {
    if (e instanceof DOMException && e.name === "AbortError")
      h.onError({ status: 0, detail: "Превышено время ожидания." });
    else h.onError({ status: 0, detail: "Сеть недоступна." });
  } finally {
    clearTimeout(timer);
  }
}

const realApi = {
  createReading: (body: ReadingRequestBody) =>
    request<ReadingResponse>("POST", "/reading", body),
  streamReading,
  checkQuestion: (question: string) =>
    request<QuestionCheck>("POST", "/question/check", { question }),
  getJournal: () => request<JournalEntry[]>("GET", "/journal"),
  deleteEntry: (id: number) => request<{ deleted: number }>("DELETE", `/journal/${id}`),
  analyzeJournal: () => request<JournalAnalysis>("POST", "/journal/analyze", {}),
  chat: (readingId: number, message: string) =>
    request<ChatReply>("POST", `/reading/${readingId}/chat`, { message }),
  getPresets: () => request<Preset[]>("GET", "/presets"),

  // Авторизация. Вход через VK/Яндекс пока заглушка (dev-login).
  devLogin: (body: {
    provider: string;
    provider_user_id: string;
    email?: string;
    name?: string;
  }) => request<AuthResult>("POST", "/auth/dev-login", body),
  me: () => request<User>("GET", "/auth/me"),
  updateProfile: (patch: ProfilePatch) => request<User>("PATCH", "/auth/me", patch),
  logout: () => request<{ ok: boolean }>("POST", "/auth/logout", {}),
  deleteAccount: () => request<{ deleted: boolean }>("DELETE", "/auth/account"),

  // Тарифы и оплата. Провайдер пока заглушка (dev-confirm вместо реального ЮKassa).
  getTariffs: () => request<Tariff[]>("GET", "/tariffs"),
  checkout: (tariffId: string) =>
    request<CheckoutInit>("POST", "/payments/checkout", { tariff_id: tariffId }),
  devConfirm: (paymentId: number) =>
    request<ConfirmResult>("POST", `/payments/dev-confirm/${paymentId}`, {}),
  cancelSubscription: () => request<User>("POST", "/subscription/cancel", {}),
  getPayments: () => request<PaymentEntry[]>("GET", "/payments"),
};

export const DEMO = import.meta.env.VITE_DEMO === "1";
export const api = DEMO ? demoApi : realApi;
