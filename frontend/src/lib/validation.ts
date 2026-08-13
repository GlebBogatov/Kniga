// Кнопка «Получить толкование» активна при вопросе ≥3 символов,
// выбранном символе и отсутствии загрузки.
export function canSubmit(question: string, hasSymbol: boolean, loading: boolean): boolean {
  return question.trim().length >= 3 && hasSymbol && !loading;
}
