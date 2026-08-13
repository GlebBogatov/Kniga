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

export interface ApiError {
  status: number;
  detail: string;
}
