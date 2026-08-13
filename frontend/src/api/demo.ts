// Демо-реализация API (для GitHub Pages без бэкенда): всё кликается,
// толкования — заглушки, без обращения к ИИ. Включается флагом VITE_DEMO=1.
import { coinsPreview, hexagramPreview, trigramPreview } from "../data/symbol";
import type {
  ChatReply,
  DivinationSymbol,
  JournalAnalysis,
  JournalEntry,
  Preset,
  QuestionCheck,
  ReadingRequestBody,
  ReadingResponse,
  StreamHandlers,
} from "../types";

const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

const BLOCKS = {
  interpretation:
    "Демо-режим: здесь появится толкование, сгенерированное под ваш вопрос. " +
    "Символ говорит о переходном моменте — старое отступает, освобождая место " +
    "новому. Опирайтесь на проверенное и действуйте размеренно.",
  advice: "Двигайтесь небольшими шагами и держитесь ясной цели.",
  caution: "Не торопите события и не принимайте решений сгоряча.",
  next_step: "Запишите один конкретный шаг, который сделаете на этой неделе.",
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
        "## Демо-анализ дневника\n\n" +
        "- Повторяется тема выбора и перемен.\n" +
        "- Баланс стихий смещён к Металлу.\n\n" +
        "Совет: дайте себе время на решение, не форсируйте события.",
    };
  },

  chat: async (readingId: number, _message: string): Promise<ChatReply> => {
    await sleep(400);
    demoChatUsed[readingId] = (demoChatUsed[readingId] ?? 0) + 1;
    return {
      reply:
        "Демо-ответ: уточняю толкование под ваш вопрос. В настоящем режиме здесь " +
        "будет содержательный разбор от ИИ.",
      remaining: Math.max(0, 5 - demoChatUsed[readingId]),
    };
  },

  getPresets: async (): Promise<Preset[]> => PRESETS,
};

const demoChatUsed: Record<number, number> = {};

const PRESETS: Preset[] = [
  { slug: "stoit-li-menyat-rabotu", topic: "career", title: "Стоит ли менять работу", subtitle: "Текущее место, новое, риски и сроки", question_template: "Стоит ли мне менять работу этой весной?", prompt_focus: "" },
  { slug: "vosstanavlivat-li-otnosheniya", topic: "love", title: "Восстанавливать ли отношения", subtitle: "Чувства, границы, реалистичность", question_template: "Стоит ли пытаться восстановить эти отношения?", prompt_focus: "" },
  { slug: "kuda-uhodyat-dengi", topic: "finance", title: "Куда уходят деньги", subtitle: "Привычки, приоритеты, устойчивость", question_template: "Почему мне не удаётся откладывать деньги?", prompt_focus: "" },
  { slug: "stoit-li-pereezzhat", topic: "change", title: "Стоит ли переезжать", subtitle: "Готовность, ресурсы, сроки", question_template: "Стоит ли мне переезжать в другой город?", prompt_focus: "" },
  { slug: "kak-najti-prizvanie", topic: "self", title: "Как найти призвание", subtitle: "Сильные стороны, интерес, смысл", question_template: "В какой сфере мне стоит развиваться?", prompt_focus: "" },
];
