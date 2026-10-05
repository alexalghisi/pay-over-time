from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum

from paylater.domain.errors import InvalidPayment
from paylater.domain.markets import MarketCode
from paylater.domain.money import Currency, to_cents
from paylater.domain.offers import Offer


class PlanStatus(StrEnum):
    ACTIVE = "active"
    PAID_OFF = "paid_off"


@dataclass
class Installment:
    sequence: int
    due_date: date
    amount: Decimal
    paid: Decimal = Decimal("0.00")

    @property
    def outstanding(self) -> Decimal:
        return self.amount - self.paid


@dataclass(frozen=True)
class Allocation:
    sequence: int
    amount: Decimal


@dataclass
class Plan:
    plan_id: str
    market: MarketCode
    currency: Currency
    principal: Decimal
    apr: Decimal
    term: int
    created_at: datetime
    installments: list[Installment]
    status: PlanStatus = PlanStatus.ACTIVE

    @classmethod
    def from_offer(
        cls,
        plan_id: str,
        market: MarketCode,
        currency: Currency,
        principal: Decimal,
        offer: Offer,
        created_at: datetime,
    ) -> Plan:
        return cls(
            plan_id=plan_id,
            market=market,
            currency=currency,
            principal=principal,
            apr=offer.apr,
            term=offer.term,
            created_at=created_at,
            installments=[
                Installment(row.sequence, row.due_date, row.amount) for row in offer.schedule
            ],
        )

    @property
    def outstanding(self) -> Decimal:
        return sum((item.outstanding for item in self.installments), Decimal("0.00"))

    def next_due(self) -> Installment | None:
        return next((item for item in self.installments if item.outstanding > 0), None)

    def apply_payment(self, amount: Decimal) -> list[Allocation]:
        if amount <= 0 or amount != to_cents(amount):
            raise InvalidPayment("Payment must be a positive amount in whole cents")
        if self.status is PlanStatus.PAID_OFF:
            raise InvalidPayment("Plan is already paid off")
        if amount > self.outstanding:
            raise InvalidPayment(f"Payment exceeds the outstanding balance of {self.outstanding}")
        remaining = amount
        allocations: list[Allocation] = []
        for item in self.installments:
            if remaining == 0:
                break
            share = min(item.outstanding, remaining)
            if share > 0:
                item.paid += share
                remaining -= share
                allocations.append(Allocation(item.sequence, share))
        if self.outstanding == 0:
            self.status = PlanStatus.PAID_OFF
        return allocations
