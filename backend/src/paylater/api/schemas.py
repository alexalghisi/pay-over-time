from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, Field

from paylater.domain.markets import MarketCode
from paylater.domain.money import Currency
from paylater.domain.plans import PlanStatus

Amount = Annotated[Decimal, Field(gt=0, max_digits=12, decimal_places=2)]


class QuoteRequest(BaseModel):
    market: MarketCode
    amount: Amount


class InstallmentOut(BaseModel):
    sequence: int
    due_date: date
    amount: Decimal
    paid: Decimal = Decimal("0.00")


class OfferOut(BaseModel):
    term: int
    apr: Decimal
    monthly_payment: Decimal
    total_interest: Decimal
    total_payable: Decimal
    schedule: list[InstallmentOut]


class QuoteResponse(BaseModel):
    market: MarketCode
    currency: Currency
    amount: Decimal
    offers: list[OfferOut]


class CreatePlanRequest(BaseModel):
    market: MarketCode
    amount: Amount
    term: int = Field(ge=1, le=60)


class PlanOut(BaseModel):
    plan_id: str
    market: MarketCode
    currency: Currency
    principal: Decimal
    apr: Decimal
    term: int
    status: PlanStatus
    outstanding: Decimal
    installments: list[InstallmentOut]


class PaymentRequest(BaseModel):
    amount: Amount


class PaymentOut(BaseModel):
    payment_id: str
    amount: Decimal
    plan: PlanOut


class ErrorOut(BaseModel):
    code: str
    message: str
