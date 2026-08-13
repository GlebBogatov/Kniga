"""SQLAlchemy-модели: Reading (гадание) и ChatMessage (уточняющий чат).

Аутентификации нет (однопользовательское), но структура рассчитана на
добавление user_id позже без переписывания логики.
"""
from datetime import datetime

from sqlalchemy import ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


class Reading(Base):
    __tablename__ = "readings"

    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    mode: Mapped[str] = mapped_column(String(8))            # "8" | "64" | "coins"
    symbol_key: Mapped[str] = mapped_column(String(32))     # "qian" | "li+kan"
    symbol_label: Mapped[str] = mapped_column(String(255))
    element: Mapped[str] = mapped_column(String(64))
    question: Mapped[str] = mapped_column(Text)
    interpretation: Mapped[str] = mapped_column(Text)
    advice: Mapped[str] = mapped_column(Text)
    caution: Mapped[str] = mapped_column(Text)
    next_step: Mapped[str] = mapped_column(Text)
    prompt_snapshot: Mapped[str] = mapped_column(Text)      # контекст для чата уточнений

    messages: Mapped[list["ChatMessage"]] = relationship(
        back_populates="reading", cascade="all, delete-orphan",
        order_by="ChatMessage.id",
    )


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    reading_id: Mapped[int] = mapped_column(
        ForeignKey("readings.id", ondelete="CASCADE"), index=True
    )
    role: Mapped[str] = mapped_column(String(16))           # "user" | "assistant"
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    reading: Mapped["Reading"] = relationship(back_populates="messages")
