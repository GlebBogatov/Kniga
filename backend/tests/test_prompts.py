from app.services.divination import coins_symbol, hexagram_symbol, trigram_symbol
from app.services.prompts import SAFETY, build_interpretation_prompt


def test_trigram_prompt_has_question_symbol_and_safety():
    s = trigram_symbol("qian")
    p = build_interpretation_prompt(s, "Стоит ли менять работу?")
    assert "Стоит ли менять работу?" in p
    assert SAFETY in p
    assert s["name"] in p


def test_hexagram_prompt_is_hexagram_not_coins():
    s = hexagram_symbol("li", "kan")
    p = build_interpretation_prompt(s, "Вопрос?")
    assert "гексаграмма" in p.lower()
    assert "lines_commentary" not in p


def test_coins_prompt_requests_lines_commentary():
    s = coins_symbol([6, 6, 6, 6, 6, 6])
    p = build_interpretation_prompt(s, "Вопрос?")
    assert "lines_commentary" in p


def test_short_style_applied():
    s = trigram_symbol("li")
    p = build_interpretation_prompt(s, "В?", style="short")
    assert "кратко" in p
