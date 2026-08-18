import { describe, expect, it } from "vitest";

import { hexagramNumber } from "../data/reference.generated";
import { hexagramPreview, trigramPreview } from "../data/symbol";
import { segmentsForLine } from "../lib/lines";
import { effectiveUiMode } from "../lib/uiMode";
import { canSubmit } from "../lib/validation";

describe("hexagramNumber (вычисление гексаграммы из пары id)", () => {
  it("qian/qian -> 1", () => expect(hexagramNumber("qian", "qian")).toBe(1));
  it("kun/kun -> 2", () => expect(hexagramNumber("kun", "kun")).toBe(2));
  it("li/kan -> 63", () => expect(hexagramNumber("li", "kan")).toBe(63));
  it("kan/li -> 64", () => expect(hexagramNumber("kan", "li")).toBe(64));
});

describe("segmentsForLine (сегменты ян/инь)", () => {
  it("ян = 1 сегмент", () => expect(segmentsForLine(1)).toBe(1));
  it("инь = 2 сегмента", () => expect(segmentsForLine(0)).toBe(2));
});

describe("canSubmit (блокировка кнопки)", () => {
  it("пустой вопрос -> false", () => expect(canSubmit("", true, false)).toBe(false));
  it("короткий вопрос -> false", () => expect(canSubmit("ab", true, false)).toBe(false));
  it("нет символа -> false", () => expect(canSubmit("вопрос?", false, false)).toBe(false));
  it("во время загрузки -> false", () => expect(canSubmit("вопрос?", true, true)).toBe(false));
  it("всё готово -> true", () => expect(canSubmit("вопрос?", true, false)).toBe(true));
});

describe("effectiveUiMode (уровень интерфейса)", () => {
  it("аккаунт важнее кэша", () => expect(effectiveUiMode("advanced", "simple")).toBe("advanced"));
  it("нет аккаунта -> берём кэш", () => expect(effectiveUiMode(null, "advanced")).toBe("advanced"));
  it("нет ни аккаунта, ни кэша -> простой", () => expect(effectiveUiMode(null, null)).toBe("simple"));
  it("undefined аккаунт (гость) -> простой", () => expect(effectiveUiMode(undefined, null)).toBe("simple"));
});

describe("preview-символы", () => {
  it("триграмма", () => {
    const s = trigramPreview("qian");
    expect(s.kind).toBe("trigram");
    expect(s.lines).toEqual([1, 1, 1]);
  });
  it("гексаграмма li/kan = №63", () => {
    const s = hexagramPreview("li", "kan");
    expect(s.number).toBe(63);
    expect(s.lines).toHaveLength(6);
  });
});
