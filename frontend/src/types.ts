export type Mode = "8" | "64" | "coins";
export type Style = "classic" | "modern" | "short";

export interface TrigramSymbol {
  kind: "trigram";
  id: string;
  name: string;
  hanzi: string;
  lines: number[];
  image: string;
  action: string;
  family: string;
  element: string;
  direction: string;
  classic: string;
}

export interface TrigramBrief {
  id: string;
  name: string;
  hanzi: string;
  lines: number[];
  image: string;
  action: string;
  element: string;
}

export interface HexagramSymbol {
  kind: "hexagram";
  number: number;
  name: string;
  title: string;
  essence: string;
  lines: number[];
  lower: TrigramBrief;
  upper: TrigramBrief;
  tosses?: number[];
  changing_lines?: number[];
  secondary?: HexagramSymbol | null;
}

export type DivinationSymbol = TrigramSymbol | HexagramSymbol;

export interface LineComment {
  line: number;
  text: string;
}

export interface ReadingResponse {
  reading_id: number;
  symbol: DivinationSymbol;
  interpretation: string;
  advice: string;
  caution: string;
  next_step: string;
  lines_commentary?: LineComment[];
}

export interface QuestionCheck {
  quality: "good" | "vague" | "yes_no_ok";
  hint: string;
  crisis: boolean;
}

export interface JournalEntry {
  id: number;
  ts: string | null;
  mode: string;
  symbol_label: string;
  element: string;
  question: string;
  interpretation: string;
  advice: string;
}

export interface JournalAnalysis {
  analysis_markdown: string;
}

export interface ChatTurn {
  role: "user" | "assistant";
  content: string;
}

export interface ChatReply {
  reply: string;
  remaining: number;
}

export interface Preset {
  slug: string;
  topic: string;
  title: string;
  subtitle: string;
  question_template: string;
  prompt_focus: string;
}

export interface ApiError {
  status: number;
  detail: string;
}

export type Provider = "vk" | "yandex";

export interface Subscription {
  plan: "free" | "premium";
  status: "active" | "canceled" | "expired";
  current_period_end: string | null;
  auto_renew: boolean;
}

export interface User {
  id: number;
  provider: string;
  email: string | null;
  name: string | null;
  birth_date: string | null;
  role: "user" | "admin" | "editor";
  subscription: Subscription;
}

export interface AuthResult {
  token: string;
  user: User;
}

export interface ProfilePatch {
  name?: string;
  email?: string;
}

export interface ReadingRequestBody {
  mode: Mode;
  question: string;
  trigram_id?: string;
  lower_id?: string;
  upper_id?: string;
  tosses?: number[] | null;
  style?: Style | null;
  preset_slug?: string;
}

export interface StreamHandlers {
  onDelta: (text: string) => void;
  onDone: (res: ReadingResponse) => void;
  onError: (err: ApiError) => void;
}
