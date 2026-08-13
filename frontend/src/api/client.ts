import type {
  ApiError,
  ChatReply,
  JournalAnalysis,
  JournalEntry,
  QuestionCheck,
  ReadingResponse,
  Style,
} from "../types";

const BASE = "/api";
const TIMEOUT_MS = 60_000;

async function request<T>(method: string, path: string, body?: unknown): Promise<T> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);
  try {
    const res = await fetch(BASE + path, {
      method,
      headers: body !== undefined ? { "Content-Type": "application/json" } : undefined,
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

export interface ReadingRequestBody {
  mode: "8" | "64" | "coins";
  question: string;
  trigram_id?: string;
  lower_id?: string;
  upper_id?: string;
  tosses?: number[] | null;
  style?: Style | null;
}

export const api = {
  createReading: (body: ReadingRequestBody) =>
    request<ReadingResponse>("POST", "/reading", body),
  checkQuestion: (question: string) =>
    request<QuestionCheck>("POST", "/question/check", { question }),
  getJournal: () => request<JournalEntry[]>("GET", "/journal"),
  deleteEntry: (id: number) => request<{ deleted: number }>("DELETE", `/journal/${id}`),
  analyzeJournal: () => request<JournalAnalysis>("POST", "/journal/analyze", {}),
  chat: (readingId: number, message: string) =>
    request<ChatReply>("POST", `/reading/${readingId}/chat`, { message }),
};
