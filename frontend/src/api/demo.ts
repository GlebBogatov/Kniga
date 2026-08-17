// Демо-реализация API (для GitHub Pages без бэкенда): всё кликается,
// толкования — заглушки, без обращения к ИИ. Включается флагом VITE_DEMO=1.
import { coinsPreview, hexagramPreview, trigramPreview } from "../data/symbol";
import type {
  AdminMetrics,
  AdminUser,
  ApiError,
  AuthResult,
  ChatReply,
  CheckoutInit,
  CmsPreview,
  ConfirmResult,
  ContentItem,
  ContentVersion,
  DivinationSymbol,
  JournalAnalysis,
  JournalEntry,
  PaymentEntry,
  Preset,
  PresetAdmin,
  ProfilePatch,
  QuestionCheck,
  ReadingRequestBody,
  ReadingResponse,
  StreamHandlers,
  SymbolOfDay,
  Tariff,
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

// Демо-тарифы (совпадают с backend/data/tariffs.py).
const DEMO_TARIFFS: Tariff[] = [
  { id: "premium_month", plan: "premium", period: "month", period_days: 30, price: 399, title: "Премиум · месяц", subtitle: "Безлимит гаданий и все функции" },
  { id: "premium_year", plan: "premium", period: "year", period_days: 365, price: 2990, title: "Премиум · год", subtitle: "Год дешевле — как ~7,5 месяцев" },
];
const DEMO_TARIFF_BY_ID: Record<string, Tariff> = Object.fromEntries(
  DEMO_TARIFFS.map((t) => [t.id, t]),
);

// Демо-данные админки (без бэкенда): несколько выдуманных пользователей.
function daysFromNow(d: number): string {
  return new Date(Date.now() + d * 86400000).toISOString();
}
const demoAdmin: AdminUser[] = [
  { id: 2, created_at: daysFromNow(-40), provider: "vk", email: "maria@example.com", name: "Мария", role: "user", is_blocked: false, subscription: { plan: "premium", status: "active", current_period_end: daysFromNow(18), auto_renew: true }, readings: 24, payments: [{ id: 11, tariff_id: "premium_month", amount: 399, currency: "RUB", status: "succeeded", receipt: "Чек (заглушка)", created_at: daysFromNow(-12) }] },
  { id: 3, created_at: daysFromNow(-20), provider: "yandex", email: "ivan@example.com", name: "Иван", role: "user", is_blocked: false, subscription: { plan: "free", status: "active", current_period_end: null, auto_renew: false }, readings: 5, payments: [] },
  { id: 4, created_at: daysFromNow(-9), provider: "vk", email: "olga@example.com", name: "Ольга", role: "user", is_blocked: false, subscription: { plan: "premium", status: "active", current_period_end: daysFromNow(6), auto_renew: false }, readings: 11, payments: [{ id: 12, tariff_id: "premium_year", amount: 2990, currency: "RUB", status: "succeeded", receipt: "Чек (заглушка)", created_at: daysFromNow(-9) }] },
  { id: 5, created_at: daysFromNow(-3), provider: "yandex", email: "spam@example.com", name: "Гость", role: "user", is_blocked: true, subscription: { plan: "free", status: "active", current_period_end: null, auto_renew: false }, readings: 1, payments: [] },
];

function demoMetrics(): AdminMetrics {
  const revenue = demoAdmin
    .flatMap((u) => u.payments ?? [])
    .filter((p) => p.status === "succeeded")
    .reduce((s, p) => s + p.amount, 0);
  return {
    users_total: demoAdmin.length,
    users_premium: demoAdmin.filter((u) => u.subscription.plan === "premium").length,
    readings_total: demoAdmin.reduce((s, u) => s + u.readings, 0),
    payments_succeeded: demoAdmin.flatMap((u) => u.payments ?? []).filter((p) => p.status === "succeeded").length,
    revenue_total: revenue,
  };
}

// Демо-контент CMS (мирроринг backend/data/content.py).
interface DemoContentField {
  key: string;
  group: string;
  label: string;
  multiline: boolean;
  default: string;
}
const DEMO_CONTENT_REGISTRY: DemoContentField[] = [
  { key: "safety", group: "Безопасность", label: "Блок безопасности (добавляется во все ответы ИИ)", multiline: true, default: "Важно: не давай медицинских, юридических или финансовых предписаний; не предсказывай смерть, диагнозы и исход болезни. Если вопрос касается здоровья, самоповреждения или острого кризиса — мягко порекомендуй обратиться к профильному специалисту вместо толкования." },
  { key: "tone", group: "Тон толкования", label: "Дополнительное указание о тоне (необязательно)", multiline: true, default: "" },
  { key: "qc_good", group: "Проверка вопроса", label: "Признак хорошего вопроса", multiline: false, default: "конкретный, про решение или ситуацию" },
  { key: "qc_good_example", group: "Проверка вопроса", label: "Пример хорошего вопроса", multiline: false, default: "остаться в компании или искать работу в марте" },
  { key: "qc_vague", group: "Проверка вопроса", label: "Признак расплывчатого вопроса", multiline: false, default: "размытый, без конкретной ситуации или решения" },
  { key: "qc_vague_example", group: "Проверка вопроса", label: "Пример расплывчатого вопроса", multiline: false, default: "какая у меня судьба" },
  { key: "qc_hint", group: "Проверка вопроса", label: "Как писать подсказку при расплывчатом вопросе", multiline: false, default: "1–2 предложения, как переформулировать вопрос конкретнее" },
  { key: "qc_crisis", group: "Проверка вопроса", label: "Что считать кризисным вопросом", multiline: true, default: "о самоповреждении, суициде, остром психологическом кризисе" },
];
const demoContentState: Record<string, { draft: string | null; published: string | null }> =
  Object.fromEntries(DEMO_CONTENT_REGISTRY.map((f) => [f.key, { draft: null, published: null }]));
const demoContentVersions: Record<string, ContentVersion[]> = {};
let demoVersionId = 1;

function demoContentItems(): ContentItem[] {
  return DEMO_CONTENT_REGISTRY.map((f) => {
    const st = demoContentState[f.key];
    const effective = st.published ?? f.default;
    return {
      ...f,
      published: st.published,
      draft: st.draft,
      effective,
      dirty: st.draft !== null && st.draft !== effective,
    };
  });
}

// Демо-лимит бесплатного тарифа: чтобы показать путь «лимит → оплата → премиум».
const DEMO_FREE_LIMIT = 3;
let demoReadings = 0;

function demoQuotaError(): ApiError | null {
  const user = readDemoUser();
  if (user && user.subscription.plan !== "premium" && demoReadings >= DEMO_FREE_LIMIT) {
    return {
      status: 402,
      detail:
        `Достигнут дневной лимит бесплатного тарифа (${DEMO_FREE_LIMIT}). ` +
        "Оформите подписку для безлимита.",
    };
  }
  return null;
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
    const q = demoQuotaError();
    if (q) throw q;
    await sleep(400);
    demoReadings++;
    return fullResponse(body);
  },

  streamReading: async (body: ReadingRequestBody, h: StreamHandlers): Promise<void> => {
    const q = demoQuotaError();
    if (q) {
      h.onError(q);
      return;
    }
    const symbol = buildSymbol(body);
    for (const word of BLOCKS.interpretation.split(" ")) {
      await sleep(35);
      h.onDelta(word + " ");
    }
    await sleep(200);
    demoReadings++;
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

  getSymbolOfDay: async (): Promise<SymbolOfDay> => {
    const user = readDemoUser();
    if (!user) throw { status: 401, detail: "Требуется вход." } as ApiError;
    if (user.subscription.plan !== "premium")
      throw { status: 402, detail: "Символ дня доступен по подписке." } as ApiError;
    const ids = ["qian", "dui", "li", "zhen", "xun", "kan", "gen", "kun"];
    const symbol = trigramPreview(ids[new Date().getDate() % 8]);
    return {
      symbol,
      reflection:
        "✧ Здесь будет короткое размышление-настрой ИИ на день по этому символу " +
        "(заглушка демо). ✧",
      date: new Date().toISOString().slice(0, 10),
    };
  },

  getPresets: async (): Promise<Preset[]> =>
    demoPresets()
      .filter((p) => p.is_active)
      .map(({ slug, topic, title, subtitle, question_template, prompt_focus }) => ({
        slug,
        topic,
        title,
        subtitle,
        question_template,
        prompt_focus,
      })),

  cmsPresets: async (): Promise<PresetAdmin[]> => demoPresets(),
  cmsPresetCreate: async (data: Partial<PresetAdmin>): Promise<PresetAdmin> => {
    const list = demoPresets();
    const item: PresetAdmin = {
      id: demoPresetId++,
      slug: (data.title || "preset").toLowerCase().replace(/[^a-zа-я0-9]+/g, "-") + "-" + demoPresetId,
      topic: data.topic ?? "other",
      title: data.title ?? "Новый вопрос",
      subtitle: data.subtitle ?? "",
      question_template: data.question_template ?? "",
      prompt_focus: data.prompt_focus ?? "",
      sort_order: list.length,
      is_active: data.is_active ?? true,
    };
    list.push(item);
    return item;
  },
  cmsPresetUpdate: async (id: number, data: Partial<PresetAdmin>): Promise<PresetAdmin> => {
    const item = demoPresets().find((p) => p.id === id)!;
    Object.assign(item, data);
    return item;
  },
  cmsPresetDelete: async (id: number): Promise<{ deleted: number }> => {
    const list = demoPresets();
    const i = list.findIndex((p) => p.id === id);
    if (i >= 0) list.splice(i, 1);
    return { deleted: id };
  },

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

  // --- Тарифы и оплата (заглушка) ---
  getTariffs: async (): Promise<Tariff[]> => DEMO_TARIFFS,

  checkout: async (tariffId: string): Promise<CheckoutInit> => {
    await sleep(200);
    const t = DEMO_TARIFF_BY_ID[tariffId];
    return {
      payment_id: 1,
      amount: t ? t.price : 0,
      currency: "RUB",
      confirmation_url: null,
      stub: true,
    };
  },

  devConfirm: async (): Promise<ConfirmResult> => {
    await sleep(300);
    const user = readDemoUser();
    if (!user) throw { status: 401, detail: "Требуется вход." } as ApiError;
    user.subscription = {
      plan: "premium",
      status: "active",
      current_period_end: new Date(Date.now() + 30 * 86400000).toISOString(),
      auto_renew: true,
    };
    writeDemoUser(user);
    demoReadings = 0; // премиум снимает лимит
    return {
      user,
      payment: {
        id: 1,
        tariff_id: "premium_month",
        amount: 399,
        currency: "RUB",
        status: "succeeded",
        receipt: "Чек (заглушка) отправлен на email",
        created_at: new Date().toISOString(),
      },
    };
  },

  cancelSubscription: async (): Promise<User> => {
    const user = readDemoUser();
    if (!user) throw { status: 401, detail: "Требуется вход." } as ApiError;
    user.subscription.auto_renew = false;
    writeDemoUser(user);
    return user;
  },

  getPayments: async (): Promise<PaymentEntry[]> => {
    const user = readDemoUser();
    if (!user || user.subscription.plan !== "premium") return [];
    return [
      {
        id: 1,
        tariff_id: "premium_month",
        amount: 399,
        currency: "RUB",
        status: "succeeded",
        receipt: "Чек (заглушка) отправлен на email",
        created_at: new Date().toISOString(),
      },
    ];
  },

  // --- Админка (заглушка) ---
  adminMetrics: async (): Promise<AdminMetrics> => demoMetrics(),

  adminUsers: async (query?: string): Promise<AdminUser[]> => {
    if (!query) return demoAdmin;
    const q = query.toLowerCase();
    return demoAdmin.filter(
      (u) =>
        (u.email ?? "").toLowerCase().includes(q) ||
        (u.name ?? "").toLowerCase().includes(q),
    );
  },

  adminUser: async (id: number): Promise<AdminUser> => {
    const u = demoAdmin.find((x) => x.id === id);
    if (!u) throw { status: 404, detail: "Пользователь не найден." } as ApiError;
    return u;
  },

  adminBlock: async (id: number, blocked: boolean): Promise<AdminUser> => {
    const u = demoAdmin.find((x) => x.id === id)!;
    u.is_blocked = blocked;
    return u;
  },

  adminGrant: async (id: number, tariffId: string): Promise<AdminUser> => {
    const u = demoAdmin.find((x) => x.id === id)!;
    const t = DEMO_TARIFF_BY_ID[tariffId];
    u.subscription = {
      plan: "premium",
      status: "active",
      current_period_end: daysFromNow(t ? t.period_days : 30),
      auto_renew: true,
    };
    return u;
  },

  adminSetFree: async (id: number): Promise<AdminUser> => {
    const u = demoAdmin.find((x) => x.id === id)!;
    u.subscription = { plan: "free", status: "active", current_period_end: null, auto_renew: false };
    return u;
  },

  adminRefund: async (id: number, paymentId: number): Promise<PaymentEntry> => {
    const u = demoAdmin.find((x) => x.id === id)!;
    const p = (u.payments ?? []).find((x) => x.id === paymentId)!;
    p.status = "refunded";
    return p;
  },

  // --- CMS (заглушка) ---
  cmsList: async (): Promise<ContentItem[]> => demoContentItems(),

  cmsSave: async (key: string, value: string): Promise<{ ok: boolean }> => {
    if (demoContentState[key]) demoContentState[key].draft = value;
    return { ok: true };
  },

  cmsPublish: async (key: string): Promise<{ ok: boolean }> => {
    const st = demoContentState[key];
    const field = DEMO_CONTENT_REGISTRY.find((f) => f.key === key)!;
    const value = st.draft ?? field.default;
    st.published = value;
    (demoContentVersions[key] ??= []).unshift({
      id: demoVersionId++,
      value,
      created_at: new Date().toISOString(),
    });
    return { ok: true };
  },

  cmsRevert: async (key: string): Promise<{ ok: boolean }> => {
    if (demoContentState[key]) demoContentState[key].draft = null;
    return { ok: true };
  },

  cmsVersions: async (key: string): Promise<ContentVersion[]> =>
    demoContentVersions[key] ?? [],

  cmsRestore: async (key: string, versionId: number): Promise<{ ok: boolean }> => {
    const v = (demoContentVersions[key] ?? []).find((x) => x.id === versionId);
    if (v && demoContentState[key]) demoContentState[key].draft = v.value;
    return { ok: true };
  },

  cmsPreview: async (question: string): Promise<CmsPreview> => {
    const d = (k: string) => {
      const st = demoContentState[k];
      const f = DEMO_CONTENT_REGISTRY.find((x) => x.key === k)!;
      return st.draft ?? st.published ?? f.default;
    };
    return {
      interpretation_prompt:
        "Ты — знаток «Книги перемен» (И Цзин), толкующий гадание.\n" +
        "Выпавшая триграмма: Цянь (乾), образ — Небо.\n" +
        `Вопрос гадающего: «${question}»\n` +
        (d("tone") ? d("tone") + "\n" : "") +
        d("safety") +
        "\n(демо-предпросмотр собранной инструкции для ИИ)",
      question_check_prompt:
        `Оцени вопрос для гадания И-Цзин: «${question}».\n` +
        `Хороший вопрос — ${d("qc_good")} («${d("qc_good_example")}»), ` +
        `а не ${d("qc_vague")} («${d("qc_vague_example")}»). ` +
        `Кризисный — ${d("qc_crisis")}.`,
    };
  },
};

const demoChatUsed: Record<number, number> = {};

// Демо-состояние пресетов (сидируется из PRESETS при первом обращении).
let demoPresetAdmin: PresetAdmin[] | null = null;
let demoPresetId = 100;
function demoPresets(): PresetAdmin[] {
  if (demoPresetAdmin === null) {
    demoPresetAdmin = PRESETS.map((p, i) => ({
      ...p,
      id: i + 1,
      sort_order: i,
      is_active: true,
    }));
    demoPresetId = PRESETS.length + 1;
  }
  return demoPresetAdmin;
}

const PRESETS: Preset[] = [
  { slug: "stoit-li-menyat-rabotu", topic: "career", title: "Стоит ли менять работу", subtitle: "Текущее место, новое, риски и сроки", question_template: "Стоит ли мне менять работу этой весной?", prompt_focus: "" },
  { slug: "vosstanavlivat-li-otnosheniya", topic: "love", title: "Восстанавливать ли отношения", subtitle: "Чувства, границы, реалистичность", question_template: "Стоит ли пытаться восстановить эти отношения?", prompt_focus: "" },
  { slug: "kuda-uhodyat-dengi", topic: "finance", title: "Куда уходят деньги", subtitle: "Привычки, приоритеты, устойчивость", question_template: "Почему мне не удаётся откладывать деньги?", prompt_focus: "" },
  { slug: "stoit-li-pereezzhat", topic: "change", title: "Стоит ли переезжать", subtitle: "Готовность, ресурсы, сроки", question_template: "Стоит ли мне переезжать в другой город?", prompt_focus: "" },
  { slug: "kak-najti-prizvanie", topic: "self", title: "Как найти призвание", subtitle: "Сильные стороны, интерес, смысл", question_template: "В какой сфере мне стоит развиваться?", prompt_focus: "" },
];
