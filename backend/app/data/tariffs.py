"""Тарифы подписки — точка настройки владельца.

Цены и названия — рабочие заглушки. Финальные суммы владелец задаёт здесь
(позже — через админку). Логика оплаты/подписки на цифры не завязана.
"""
from typing import TypedDict


class Tariff(TypedDict):
    id: str
    plan: str          # "premium"
    period: str        # "month" | "year"
    period_days: int
    price: int         # рубли, [TODO владелец: финальная цена]
    title: str
    subtitle: str


TARIFFS: list[Tariff] = [
    {
        "id": "premium_month",
        "plan": "premium",
        "period": "month",
        "period_days": 30,
        "price": 399,  # [TODO владелец]
        "title": "Премиум · месяц",
        "subtitle": "Безлимит гаданий и все функции",
    },
    {
        "id": "premium_year",
        "plan": "premium",
        "period": "year",
        "period_days": 365,
        "price": 2990,  # [TODO владелец]
        "title": "Премиум · год",
        "subtitle": "Год дешевле — как ~7,5 месяцев",
    },
]

TARIFF_BY_ID: dict[str, Tariff] = {t["id"]: t for t in TARIFFS}
