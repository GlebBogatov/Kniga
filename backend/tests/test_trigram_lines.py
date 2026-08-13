from itertools import product

from app.data.trigrams import TRIGRAMS, TRIGRAM_BY_LINES

# Контрольные линии (снизу вверх) — §4.1 плана.
CONTROL = {
    "qian": (1, 1, 1),
    "dui": (1, 1, 0),
    "li": (1, 0, 1),
    "zhen": (1, 0, 0),
    "xun": (0, 1, 1),
    "kan": (0, 1, 0),
    "gen": (0, 0, 1),
    "kun": (0, 0, 0),
}


def test_exactly_eight_unique_ids():
    assert len(TRIGRAMS) == 8
    assert len(set(TRIGRAMS)) == 8
    assert set(TRIGRAMS) == set(CONTROL)


def test_lines_match_control_table():
    for tid, lines in CONTROL.items():
        assert TRIGRAMS[tid]["lines"] == lines, tid


def test_by_lines_covers_all_combinations():
    all_combos = set(product((0, 1), repeat=3))
    assert set(TRIGRAM_BY_LINES) == all_combos
    assert len(set(TRIGRAM_BY_LINES.values())) == 8
    # обратный индекс согласован с прямыми данными
    for tid, t in TRIGRAMS.items():
        assert TRIGRAM_BY_LINES[t["lines"]] == tid
