from collections import Counter

import pytest

from app.services.divination import (
    coins_symbol,
    hexagram_number_from_lines,
    hexagram_symbol,
    trigram_symbol,
    virtual_toss,
)


def test_six_sevens_is_hex1_no_change():
    s = coins_symbol([7, 7, 7, 7, 7, 7])
    assert s["number"] == 1
    assert s["changing_lines"] == []
    assert s["secondary"] is None
    assert s["lines"] == [1, 1, 1, 1, 1, 1]


def test_six_sixes_is_hex2_all_change_secondary_hex1():
    s = coins_symbol([6, 6, 6, 6, 6, 6])
    assert s["number"] == 2
    assert s["changing_lines"] == [1, 2, 3, 4, 5, 6]
    assert s["secondary"] is not None
    assert s["secondary"]["number"] == 1


def test_hexagram_number_from_lines_li_kan():
    # нижняя ли [1,0,1] + верхняя кань [0,1,0] -> №63
    assert hexagram_number_from_lines([1, 0, 1, 0, 1, 0]) == 63


def test_hexagram_symbol_shape():
    s = hexagram_symbol("li", "kan")
    assert s["kind"] == "hexagram"
    assert s["number"] == 63
    assert s["name"] == "Цзи цзи"
    assert len(s["lines"]) == 6
    assert s["lower"]["id"] == "li"
    assert s["upper"]["id"] == "kan"


def test_trigram_symbol_shape():
    s = trigram_symbol("qian")
    assert s["kind"] == "trigram"
    assert s["lines"] == [1, 1, 1]
    assert s["element"] == "Металл"


def test_virtual_toss_preserves_classic_distribution():
    counts: Counter[int] = Counter()
    for _ in range(3000):
        counts.update(virtual_toss())
    total = sum(counts.values())
    assert set(counts) <= {6, 7, 8, 9}
    young = counts[7] + counts[8]   # ожидаемо ~3/4
    old = counts[6] + counts[9]     # ожидаемо ~1/4
    assert young / total > 0.65
    assert old / total < 0.35


def test_invalid_tosses_rejected():
    with pytest.raises(ValueError):
        coins_symbol([7, 7, 7])           # неверная длина
    with pytest.raises(ValueError):
        coins_symbol([5, 7, 7, 7, 7, 7])  # значение вне {6,7,8,9}


def test_invalid_ids_rejected():
    with pytest.raises(ValueError):
        trigram_symbol("nope")
    with pytest.raises(ValueError):
        hexagram_symbol("qian", "nope")
