from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import ROUND_DOWN, Decimal

from paylater.domain.calendar import add_months
from paylater.domain.money import CENT, to_cents


@dataclass(frozen=True)
class ScheduledInstallment:
    sequence: int
    due_date: date
    amount: Decimal
    principal: Decimal
    interest: Decimal


def _equal_split(principal: Decimal, term: int) -> list[tuple[Decimal, Decimal]]:
    base = (principal / term).quantize(CENT, rounding=ROUND_DOWN)
    remainder = principal - base * term
    return [(base + (remainder if index == 0 else 0), Decimal("0.00")) for index in range(term)]


def _amortised(principal: Decimal, apr: Decimal, term: int) -> list[tuple[Decimal, Decimal]]:
    rate = apr / 12
    payment = to_cents(principal * rate / (1 - (1 + rate) ** -term))
    balance = principal
    rows: list[tuple[Decimal, Decimal]] = []
    for index in range(term):
        interest = to_cents(balance * rate)
        principal_part = balance if index == term - 1 else payment - interest
        rows.append((principal_part, interest))
        balance -= principal_part
    return rows


def build_schedule(
    principal: Decimal, apr: Decimal, term: int, start: date
) -> list[ScheduledInstallment]:
    if principal <= 0 or principal != to_cents(principal):
        raise ValueError("Principal must be a positive amount in whole cents")
    if term < 1:
        raise ValueError("Term must be at least one month")
    if apr < 0:
        raise ValueError("APR cannot be negative")
    rows = _equal_split(principal, term) if apr == 0 else _amortised(principal, apr, term)
    return [
        ScheduledInstallment(
            sequence=index + 1,
            due_date=add_months(start, index + 1),
            amount=principal_part + interest,
            principal=principal_part,
            interest=interest,
        )
        for index, (principal_part, interest) in enumerate(rows)
    ]
