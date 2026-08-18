import type { UiMode } from "../types";

/**
 * Действующий уровень интерфейса.
 * Приоритет: значение аккаунта → кэш браузера → «простой» по умолчанию.
 */
export function effectiveUiMode(
  userMode: UiMode | null | undefined,
  cached: UiMode | null,
): UiMode {
  return userMode ?? cached ?? "simple";
}
