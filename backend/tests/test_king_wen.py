from itertools import product

from app.data.hexagrams import HEXAGRAMS, KING_WEN
from app.data.trigrams import TRIGRAMS

# Контрольные точки таблицы Вэнь-вана — §4.2 плана.
CONTROL = {
    1: ("qian", "qian"),
    2: ("kun", "kun"),
    11: ("qian", "kun"),   # Тай
    12: ("kun", "qian"),   # Пи
    63: ("li", "kan"),     # Цзи-цзи
    64: ("kan", "li"),     # Вэй-цзи
    52: ("gen", "gen"),
    29: ("kan", "kan"),
    30: ("li", "li"),
    51: ("zhen", "zhen"),
    57: ("xun", "xun"),
    58: ("dui", "dui"),
}


def test_control_points():
    for n, (lower, upper) in CONTROL.items():
        assert KING_WEN[lower][upper] == n, n
        assert HEXAGRAMS[n]["lower"] == lower
        assert HEXAGRAMS[n]["upper"] == upper


def test_all_64_present():
    assert set(HEXAGRAMS) == set(range(1, 65))


def test_bijection_lower_upper_to_number():
    ids = list(TRIGRAMS)
    numbers = [KING_WEN[lower][upper] for lower, upper in product(ids, repeat=2)]
    # 64 комбинации -> уникальные номера 1..64 без пропусков
    assert sorted(numbers) == list(range(1, 65))


def test_hexagram_composition_matches_king_wen():
    for n, hx in HEXAGRAMS.items():
        assert KING_WEN[hx["lower"]][hx["upper"]] == n
