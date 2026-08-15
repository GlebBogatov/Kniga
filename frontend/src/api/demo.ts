// Демо-реализация API (для GitHub Pages без бэкенда): всё кликается,
// толкования — заглушки, без обращения к ИИ. Включается флагом VITE_DEMO=1.
import { coinsPreview, hexagramPreview, trigramPreview } from "../data/symbol";
import type {
  ApiError,
  AuthResult,
  ChatReply,
  DivinationSymbol,
  JournalAnalysis,
  JournalEntry,
  Preset,
  ProfilePatch,
  QuestionCheck,
  ReadingRequestBody,
  ReadingResponse,
  StreamHandlers,
  User,
} from "../types";

const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

// --- Демо-авторизация (без бэкенда): пользователь хранится в localStorage. ---
const DEMO_USER_KEY = "kn_demo_user";

function readDemoUser(): User | null {
  try {
    const raw = localStorage.getItem(DEMO_USER_KEY);
    return raw ? (JSON.parse(raw) as User) : null;
  } catch {
    return null;
  }
}

function writeDemoUser(user: User | null): void {
  try {
    if (user) localStorage.setItem(DEMO_USER_KEY, JSON.stringify(user));
    else localStorage.removeItem(DEMO_USER_KEY);
  } catch {
    /* нет localStorage — игнорируем */
  }
}

function providerLabel(p: string): string {
  return p === "vk" ? "VK" : p === "yandex" ? "Яндекс" : "гость";
}

const BLOCKS = {
  interpretation:
    "✧ Здесь будет ИИ-мудрость ✧ — толкование «Книги перемен» под ваш вопрос. " +
    "Сейчас это заглушка демо-версии; в рабочем режиме текст генерирует ИИ на " +
    "основе выпавшего символа и вашего вопроса.",
  advice: "Здесь будет совет — одна-две конкретные мысли от ИИ.",
  caution: "Здесь будет предостережение — от чего стоит воздержаться.",
  next_step: "Здесь будет первый практический шаг.",
};

let readingCounter = 100;

function buildSymbol(body: ReadingRequestBody): DivinationSymbol {
  if (body.mode === "8") return trigramPreview(body.trigram_id ?? "qian");
  if (body.mode === "64")
    return hexagramPreview(body.lower_id ?? "qian", body.upper_id ?? "kun");
  const tosses =
    body.tosses ??
    Array.from({ length: 6 }, () => [6, 7, 8, 9][Math.floor(Math.random() * 4)]);
  return coinsPreview(tosses);
}

function fullResponse(body: ReadingRequestBody): ReadingResponse {
  return { reading_id: ++readingCounter, symbol: buildSymbol(body), ...BLOCKS };
}

export const demoApi = {
  createReading: async (body: ReadingRequestBody): Promise<ReadingResponse> => {
    await sleep(400);
    return fullResponse(body);
  },

  streamReading: async (body: ReadingRequestBody, h: StreamHandlers): Promise<void> => {
    const symbol = buildSymbol(body);
    for (const word of BLOCKS.interpretation.split(" ")) {
      await sleep(35);
      h.onDelta(word + " ");
    }
    await sleep(200);
    h.onDone({ reading_id: ++readingCounter, symbol, ...BLOCKS });
  },

  checkQuestion: async (): Promise<QuestionCheck> => {
    await sleep(300);
    return { quality: "good", hint: "", crisis: false };
  },

  getJournal: async (): Promise<JournalEntry[]> => [
    {
      id: 2,
      ts: "2026-08-13T10:15:00",
      mode: "64",
      symbol_label: "Гексаграмма №11 Тай «Расцвет»",
      element: "Металл / Почва",
      question: "Стоит ли начинать новый проект этой осенью?",
      interpretation: BLOCKS.interpretation,
      advice: BLOCKS.advice,
    },
    {
      id: 1,
      ts: "2026-08-12T21:40:00",
      mode: "8",
      symbol_label: "Триграмма Ли (Огонь)",
      element: "Огонь",
      question: "На чём мне сейчас сосредоточиться?",
      interpretation: BLOCKS.interpretation,
      advice: BLOCKS.advice,
    },
  ],

  deleteEntry: async (id: number): Promise<{ deleted: number }> => ({ deleted: id }),

  analyzeJournal: async (): Promise<JournalAnalysis> => {
    await sleep(500);
    return {
      analysis_markdown:
        "## Здесь будет анализ дневника от ИИ\n\n" +
        "ИИ найдёт повторяющиеся темы вопросов, баланс стихий и динамику " +
        "символов во времени, а затем даст один общий совет. Сейчас это " +
        "заглушка демо-версии.",
    };
  },

  chat: async (readingId: number, _message: string): Promise<ChatReply> => {
    await sleep(400);
    demoChatUsed[readingId] = (demoChatUsed[readingId] ?? 0) + 1;
    return {
      reply:
        "Здесь будет ответ ИИ на ваш уточняющий вопрос. Сейчас это заглушка " +
        "демо-версии.",
      remaining: Math.max(0, 5 - demoChatUsed[readingId]),
    };
  },

  getPresets: async (): Promise<Preset[]> => PRESETS,

  // --- Авторизация (заглушка) ---
  devLogin: async (body: {
    provider: string;
    provider_user_id: string;
    email?: string;
    name?: string;
  }): Promise<AuthResult> => {
    await sleep(300);
    const user: User = {
      id: 1,
      provider: body.provider,
      email: body.email ?? `${body.provider}@example.com`,
      name: body.name ?? `Гость ${providerLabel(body.provider)}`,
      birth_date: null,
      role: "user",
      subscription: {
        plan: "free",
        status: "active",
        current_period_end: null,
        auto_renew: false,
      },
    };
    writeDemoUser(user);
    return { token: "demo-token", user };
  },

  me: async (): Promise<User> => {
    const user = readDemoUser();
    if (!user) throw { status: 401, detail: "Требуется вход." } as ApiError;
    return user;
  },

  updateProfile: async (patch: ProfilePatch): Promise<User> => {
    const user = readDemoUser();
    if (!user) throw { status: 401, detail: "Требуется вход." } as ApiError;
    if (patch.name !== undefined) user.name = patch.name;
    if (patch.email !== undefined) user.email = patch.email;
    writeDemoUser(user);
    return user;
  },

  logout: async (): Promise<{ ok: boolean }> => {
    writeDemoUser(null);
    return { ok: true };
  },

  deleteAccount: async (): Promise<{ deleted: boolean }> => {
    writeDemoUser(null);
    return { deleted: true };
  },
};

const demoChatUsed: Record<number, number> = {};

const PRESETS: Preset[] = [
  { slug: "stoit-li-menyat-rabotu", topic: "career", title: "Стоит ли менять работу", subtitle: "Текущее место, новое, риски и сроки", question_template: "Стоит ли мне менять работу этой весной?", prompt_focus: "" },
  { slug: "vosstanavlivat-li-otnosheniya", topic: "love", title: "Восстанавливать ли отношения", subtitle: "Чувства, границы, реалистичность", question_template: "Стоит ли пытаться восстановить эти отношения?", prompt_focus: "" },
  { slug: "kuda-uhodyat-dengi", topic: "finance", title: "Куда уходят деньги", subtitle: "Привычки, приоритеты, устойчивость", question_template: "Почему мне не удаётся откладывать деньги?", prompt_focus: "" },
  { slug: "stoit-li-pereezzhat", topic: "change", title: "Стоит ли переезжать", subtitle: "Готовность, ресурсы, сроки", question_template: "Стоит ли мне переезжать в другой город?", prompt_focus: "" },
  { slug: "kak-najti-prizvanie", topic: "self", title: "Как найти призвание", subtitle: "Сильные стороны, интерес, смысл", question_template: "В какой сфере мне стоит развиваться?", prompt_focus: "" },
];
