"""Шаблоны промптов.

Каркас: рабочие формулировки, которые контент-редактор (Таня) шлифует позже.
В system-часть каждого промпта включён блок безопасности (SAFETY).
"""
from ..data.content import CONTENT_DEFAULTS, SAFETY_DEFAULT
from ..data.question_check import QUESTION_CHECK_CRITERIA

# Дефолт блока безопасности; при наличии опубликованного значения (CMS Тани)
# подставляется оно — см. content-параметр в билдерах.
SAFETY = SAFETY_DEFAULT

_STYLE = {
    "classic": "Пиши архаичным, образным слогом, близким к классическому тексту.",
    "modern": "Пиши современным, разговорным, дружелюбным языком.",
    "short": "Пиши предельно кратко — только суть, не более трёх предложений на блок.",
}


def _c(content: dict | None, key: str) -> str:
    """Значение контента: из CMS (content) либо дефолт из реестра."""
    if content and content.get(key) is not None:
        return content[key]
    return CONTENT_DEFAULTS.get(key, "")


def _base_rules(style: str | None, preset_focus: str | None, content: dict | None = None) -> str:
    parts = [
        "Составь толкование строго применительно к этому вопросу. Пиши по-русски, "
        "спокойным, образным, но конкретным языком, без эзотерического тумана. "
        "Обращайся на «вы».",
        _STYLE.get(style or "", ""),
        _c(content, "tone"),
        f"Дополнительный фокус разбора: {preset_focus}" if preset_focus else "",
        _c(content, "safety"),
    ]
    return "\n".join(p for p in parts if p)


def prompt_trigram(symbol: dict, question: str, *, style=None, preset_focus=None, content=None) -> str:
    return (
        "Ты — знаток «Книги перемен» (И Цзин), толкующий гадание.\n\n"
        f"Выпавшая триграмма: {symbol['name']} ({symbol['hanzi']}), образ — "
        f"{symbol['image']}, действие — {symbol['action']}.\n"
        f"Семейный образ: {symbol['family']}. Стихия: {symbol['element']}.\n\n"
        f"Вопрос гадающего: «{question}»\n\n"
        f"{_base_rules(style, preset_focus, content)}\n\n"
        "Ответь на русском объектом с полями: interpretation (3–5 предложений о "
        "ситуации из вопроса), advice (1–2 предложения — конкретный совет), "
        "caution (1 предложение — от чего предостерегает символ), next_step "
        "(1 предложение — первый практический шаг)."
    )


def prompt_hexagram(symbol: dict, question: str, *, style=None, preset_focus=None, content=None) -> str:
    lo, up = symbol["lower"], symbol["upper"]
    return (
        "Ты — знаток «Книги перемен» (И Цзин), толкующий гадание.\n\n"
        f"Выпавшая гексаграмма №{symbol['number']} — {symbol['name']}, "
        f"«{symbol['title']}» (по переводу Ю. К. Щуцкого).\n"
        f"Нижняя триграмма: {lo['name']} ({lo['image']}, {lo['action']}). "
        f"Верхняя триграмма: {up['name']} ({up['image']}, {up['action']}).\n"
        "Опирайся на классическое суждение и образ гексаграммы (традиция "
        "Вильгельма и Щуцкого) и на взаимодействие триграмм.\n\n"
        f"Вопрос гадающего: «{question}»\n\n"
        f"{_base_rules(style, preset_focus, content)}\n\n"
        "Ответь на русском объектом с полями: interpretation (4–6 предложений, "
        "включая взаимодействие верхней и нижней триграмм), advice, caution, "
        "next_step."
    )


def prompt_coins(symbol: dict, question: str, *, style=None, preset_focus=None, content=None) -> str:
    lo, up = symbol["lower"], symbol["upper"]
    changing = symbol.get("changing_lines") or []
    sec = symbol.get("secondary")
    sec_line = (
        f"Вторичная гексаграмма №{sec['number']} — {sec['name']}, «{sec['title']}» "
        "(куда движется ситуация)."
        if sec
        else "Изменяющихся линий нет: ситуация устойчива."
    )
    return (
        "Ты — знаток «Книги перемен» (И Цзин), толкующий гадание по броску монет.\n\n"
        f"Первичная гексаграмма №{symbol['number']} — {symbol['name']}, "
        f"«{symbol['title']}» — ситуация сейчас.\n"
        f"Нижняя триграмма: {lo['name']} ({lo['image']}). "
        f"Верхняя: {up['name']} ({up['image']}).\n"
        f"Изменяющиеся линии (снизу вверх, 1–6): {changing or 'нет'}. {sec_line}\n\n"
        f"Вопрос гадающего: «{question}»\n\n"
        f"{_base_rules(style, preset_focus, content)}\n\n"
        "Ответь на русском объектом с полями: interpretation (4–6 предложений: "
        "первичная гексаграмма — ситуация сейчас, изменяющиеся линии — точки "
        "перехода, вторичная — куда всё движется), advice, caution, next_step, "
        "lines_commentary (массив по каждой изменяющейся линии: объект "
        "{line, text}; если изменяющихся линий нет — пустой массив)."
    )


def build_interpretation_prompt(symbol: dict, question: str, *, style=None, preset_focus=None, content=None) -> str:
    if symbol["kind"] == "trigram":
        return prompt_trigram(symbol, question, style=style, preset_focus=preset_focus, content=content)
    if "changing_lines" in symbol:  # режим монет
        return prompt_coins(symbol, question, style=style, preset_focus=preset_focus, content=content)
    return prompt_hexagram(symbol, question, style=style, preset_focus=preset_focus, content=content)


def _symbol_line(symbol: dict) -> str:
    if symbol["kind"] == "trigram":
        return (
            f"Выпавшая триграмма: {symbol['name']} ({symbol['hanzi']}), образ — "
            f"{symbol['image']}, действие — {symbol['action']}, стихия — {symbol['element']}."
        )
    lo, up = symbol["lower"], symbol["upper"]
    line = (
        f"Выпавшая гексаграмма №{symbol['number']} — {symbol['name']}, «{symbol['title']}». "
        f"Нижняя: {lo['name']} ({lo['image']}), верхняя: {up['name']} ({up['image']})."
    )
    if "changing_lines" in symbol:
        line += f" Изменяющиеся линии: {symbol.get('changing_lines') or 'нет'}."
    return line


def prompt_interpretation_stream(symbol: dict, question: str, *, style=None, preset_focus=None, content=None) -> str:
    """Только прозаический текст толкования (для потоковой передачи)."""
    return (
        "Ты — знаток «Книги перемен» (И Цзин), толкующий гадание.\n"
        f"{_symbol_line(symbol)}\n"
        f"Вопрос гадающего: «{question}»\n"
        f"{_base_rules(style, preset_focus, content)}\n"
        "Дай ТОЛЬКО связный текст толкования (4–6 предложений) применительно к "
        "вопросу. Без списков, без заголовков, без JSON."
    )


def prompt_trailer(symbol: dict, question: str, interpretation: str, *, style=None) -> str:
    """Добор полей advice/caution/next_step (+lines_commentary) после стрима."""
    coins = "changing_lines" in symbol
    extra = (
        " и lines_commentary (массив объектов {line, text} по каждой изменяющейся "
        "линии; если их нет — пустой массив)"
        if coins
        else ""
    )
    return (
        "Ты — знаток «Книги перемен». Вот твоё толкование гадания на вопрос "
        f"«{question}»:\n{interpretation}\n\n"
        "На его основе дай объект с полями advice (1–2 предложения — конкретный "
        "совет), caution (1 предложение — предостережение), next_step (1 предложение "
        f"— первый практический шаг){extra}. Пиши по-русски, на «вы»."
    )


def chat_system_prompt(symbol_label: str, question: str, interpretation: str, advice: str) -> str:
    return (
        "Ты — знаток «Книги перемен», продолжающий разбор уже сделанного гадания.\n"
        f"Исходное гадание: {symbol_label}. Вопрос гадающего: «{question}».\n"
        f"Твоё толкование было: {interpretation} Совет: {advice}\n"
        "Отвечай на уточняющие вопросы кратко (до 120 слов), по-русски, на «вы», "
        "опираясь на значение выпавшего символа. Не выдумывай новые символы и не "
        "проводи новое гадание — если вопрос выходит за рамки, предложи сделать "
        "новое гадание.\n" + SAFETY
    )


def question_check_prompt(question: str, content: dict | None = None) -> str:
    # Критерии («что такое хороший/расплывчатый/кризисный вопрос») редактируются
    # Таней через CMS (ключи qc_*); при отсутствии публикации — дефолты реестра.
    def g(key: str, fallback: str) -> str:
        if content and content.get(key) is not None:
            return content[key]
        return fallback

    qc = QUESTION_CHECK_CRITERIA
    return (
        f"Оцени вопрос для гадания И-Цзин: «{question}».\n"
        f"Хороший вопрос — {g('qc_good', qc['good'])} "
        f"(«{g('qc_good_example', qc['good_example'])}»), "
        f"а не {g('qc_vague', qc['vague'])} "
        f"(«{g('qc_vague_example', qc['vague_example'])}»). "
        f"Отдельно определи, не является ли вопрос кризисным "
        f"({g('qc_crisis', qc['crisis'])}).\n"
        'Ответь объектом с полями: quality (одно из "good", "vague", "yes_no_ok"), '
        f"hint (если vague — {g('qc_hint', qc['hint_instruction'])}; иначе пустая строка), "
        "crisis (true, если вопрос кризисный, иначе false)."
    )


def journal_analysis_prompt(entries_json: str) -> str:
    return (
        "Ты — знаток «Книги перемен», анализирующий дневник гаданий человека.\n"
        f"Записи (от новых к старым): {entries_json}\n"
        "Найди: 1) повторяющиеся темы вопросов; 2) баланс стихий и что он "
        "означает; 3) динамику символов во времени; 4) один общий совет. Пиши "
        "по-русски, на «вы», структурируй markdown-заголовками, без эзотерического "
        "тумана, до 300 слов.\n"
        "Ответь объектом с полем analysis_markdown (строка с markdown-текстом)."
    )
