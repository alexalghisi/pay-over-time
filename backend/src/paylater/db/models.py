from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

MONEY = Numeric(12, 2)


class Base(DeclarativeBase):
    pass


class PlanRow(Base):
    __tablename__ = "plans"

    plan_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    market: Mapped[str] = mapped_column(String(2))
    currency: Mapped[str] = mapped_column(String(3))
    principal: Mapped[Decimal] = mapped_column(MONEY)
    apr: Mapped[Decimal] = mapped_column(Numeric(6, 4))
    term: Mapped[int]
    status: Mapped[str] = mapped_column(String(16))
    created_at: Mapped[datetime] = mapped_column(DateTime)
    installments: Mapped[list[InstallmentRow]] = relationship(
        back_populates="plan", order_by="InstallmentRow.sequence", cascade="all, delete-orphan"
    )


class InstallmentRow(Base):
    __tablename__ = "installments"

    plan_id: Mapped[str] = mapped_column(ForeignKey("plans.plan_id"), primary_key=True)
    sequence: Mapped[int] = mapped_column(primary_key=True, autoincrement=False)
    due_date: Mapped[date] = mapped_column(Date)
    amount: Mapped[Decimal] = mapped_column(MONEY)
    paid: Mapped[Decimal] = mapped_column(MONEY)
    plan: Mapped[PlanRow] = relationship(back_populates="installments")


class PaymentRow(Base):
    __tablename__ = "payments"
    __table_args__ = (UniqueConstraint("plan_id", "idempotency_key"),)

    payment_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    plan_id: Mapped[str] = mapped_column(ForeignKey("plans.plan_id"), index=True)
    idempotency_key: Mapped[str] = mapped_column(String(128))
    amount: Mapped[Decimal] = mapped_column(MONEY)
    created_at: Mapped[datetime] = mapped_column(DateTime)
