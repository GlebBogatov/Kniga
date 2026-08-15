"""SQLAlchemy-модели.

- Reading / ChatMessage — гадание и уточняющий чат.
- User / Subscription / UserSession — учётные записи, подписка, сессии.

Reading.user_id опционален: до входа гадания анонимны (user_id = NULL),
после входа привязываются к пользователю.
"""
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


class Reading(Base):
    __tablename__ = "readings"

    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True
    )
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


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("provider", "provider_user_id", name="uq_provider_user"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    provider: Mapped[str] = mapped_column(String(16))       # "vk" | "yandex" | "dev"
    provider_user_id: Mapped[str] = mapped_column(String(64))
    email: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    birth_date: Mapped[date | None] = mapped_column(nullable=True)
    role: Mapped[str] = mapped_column(String(16), default="user")   # user | admin | editor
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False)

    subscription: Mapped["Subscription | None"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True
    )
    plan: Mapped[str] = mapped_column(String(16), default="free")     # free | premium
    status: Mapped[str] = mapped_column(String(16), default="active")  # active|canceled|expired
    current_period_end: Mapped[datetime | None] = mapped_column(nullable=True)
    auto_renew: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="subscription")


class UserSession(Base):
    __tablename__ = "user_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    token: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column()

    user: Mapped["User"] = relationship()


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    tariff_id: Mapped[str] = mapped_column(String(32))
    plan: Mapped[str] = mapped_column(String(16))
    amount: Mapped[int] = mapped_column()                 # рубли
    currency: Mapped[str] = mapped_column(String(8), default="RUB")
    status: Mapped[str] = mapped_column(String(16), default="pending")  # pending|succeeded|canceled|refunded
    provider: Mapped[str] = mapped_column(String(16), default="stub")
    provider_payment_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    receipt_stub: Mapped[str | None] = mapped_column(String(255), nullable=True)  # чек 54-ФЗ (заглушка)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
