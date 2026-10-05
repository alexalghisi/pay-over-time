from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from paylater.domain.calendar import add_months
from paylater.domain.errors import AmountOutOfRange, UnsupportedTerm
from paylater.domain.markets import Market
from paylater.domain.schedule import ScheduledInstallment, build_schedule


@dataclass(frozen=True)
class Offer:
    term: int
    apr: Decimal
    monthly_payment: Decimal
    total_interest: Decimal
    total_payable: Decimal
    schedule: list[ScheduledInstallment]


def build_offer(market: Market, amount: Decimal, term: int, start: date) -> Offer:
    if not market.accepts(amount):
        raise AmountOutOfRange(
            f"{market.code} accepts {market.min_amount}-{market.max_amount} {market.currency}"
        )
    apr = market.apr_by_term.get(term)
    if apr is None:
        raise UnsupportedTerm(f"{market.code} does not offer a {term}-month plan")
    schedule = build_schedule(amount, apr, term, add_months(start, 1))
    total_interest = sum((row.interest for row in schedule), Decimal("0.00"))
    return Offer(
        term=term,
        apr=apr,
        monthly_payment=schedule[-1].amount if apr == 0 else schedule[0].amount,
        total_interest=total_interest,
        total_payable=amount + total_interest,
        schedule=schedule,
    )


def quote(market: Market, amount: Decimal, start: date) -> list[Offer]:
    return [build_offer(market, amount, term, start) for term in sorted(market.apr_by_term)]
