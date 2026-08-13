// Число сегментов в изображении черты: ян (1) — одна полоса, инь (0) — две.
export function segmentsForLine(bit: number): number {
  return bit === 1 ? 1 : 2;
}
