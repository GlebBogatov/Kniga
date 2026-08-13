"""Восемь триграмм (ба-гуа).

Источник данных — канонический файл «восемь_триграмм_классические_расшифровки.md»
(«Шо гуа чжуань», Ю. К. Щуцкий, R. Wilhelm). Все поля, кроме `classic`, —
выверенный факт. `classic` (развёрнутая проза-толкование) — заглушка,
наполняется контент-редактором позже.

Соглашение о линиях: `lines[0]` — НИЖНЯЯ линия, `lines[2]` — верхняя.
1 = ян (сплошная), 0 = инь (прерывистая).
"""
from typing import TypedDict


class Trigram(TypedDict):
    id: str
    name: str          # русская транслитерация имени
    hanzi: str
    lines: tuple[int, int, int]
    image: str         # образ (Небо, Огонь, ...)
    action: str        # свойство/действие по Щуцкому (Творчество, Сцепление, ...)
    family: str        # семейный образ (Отец, Средняя дочь, ...)
    element: str       # стихия у-син
    direction: str     # сторона света (посленебесный порядок Вэнь-вана)
    classic: str       # [TODO Таня] — развёрнутое классическое толкование


TRIGRAMS: dict[str, Trigram] = {
    "qian": {
        "id": "qian", "name": "Цянь", "hanzi": "乾", "lines": (1, 1, 1),
        "image": "Небо", "action": "Творчество", "family": "Отец",
        "element": "Металл", "direction": "Северо-запад", "classic": "[TODO Таня]",
    },
    "kun": {
        "id": "kun", "name": "Кунь", "hanzi": "坤", "lines": (0, 0, 0),
        "image": "Земля", "action": "Исполнение", "family": "Мать",
        "element": "Почва", "direction": "Юго-запад", "classic": "[TODO Таня]",
    },
    "zhen": {
        "id": "zhen", "name": "Чжэнь", "hanzi": "震", "lines": (1, 0, 0),
        "image": "Гром", "action": "Возбуждение", "family": "Старший сын",
        "element": "Дерево", "direction": "Восток", "classic": "[TODO Таня]",
    },
    "xun": {
        "id": "xun", "name": "Сюнь", "hanzi": "巽", "lines": (0, 1, 1),
        "image": "Ветер", "action": "Проникновение", "family": "Старшая дочь",
        "element": "Дерево", "direction": "Юго-восток", "classic": "[TODO Таня]",
    },
    "kan": {
        "id": "kan", "name": "Кань", "hanzi": "坎", "lines": (0, 1, 0),
        "image": "Вода", "action": "Погружение", "family": "Средний сын",
        "element": "Вода", "direction": "Север", "classic": "[TODO Таня]",
    },
    "li": {
        "id": "li", "name": "Ли", "hanzi": "離", "lines": (1, 0, 1),
        "image": "Огонь", "action": "Сцепление", "family": "Средняя дочь",
        "element": "Огонь", "direction": "Юг", "classic": "[TODO Таня]",
    },
    "gen": {
        "id": "gen", "name": "Гэнь", "hanzi": "艮", "lines": (0, 0, 1),
        "image": "Гора", "action": "Незыблемость", "family": "Младший сын",
        "element": "Почва", "direction": "Северо-восток", "classic": "[TODO Таня]",
    },
    "dui": {
        "id": "dui", "name": "Дуй", "hanzi": "兌", "lines": (1, 1, 0),
        "image": "Водоём", "action": "Разрешение", "family": "Младшая дочь",
        "element": "Металл", "direction": "Запад", "classic": "[TODO Таня]",
    },
}

# Обратный индекс: набор из трёх линий (снизу вверх) -> id триграммы.
# Нужен для расчёта гексаграммы из шести линий (режим монет) и валидации.
TRIGRAM_BY_LINES: dict[tuple[int, int, int], str] = {
    t["lines"]: t["id"] for t in TRIGRAMS.values()
}
